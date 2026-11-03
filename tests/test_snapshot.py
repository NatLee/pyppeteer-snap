"""How a snapshot drives Chromium: options, cleanup, time limits, event loops
and error messages. Uses the fake Chromium from conftest.py."""
import asyncio
import base64
import gc
import time

from pyppeteer.errors import BrowserError

import pyppesnap
import pyppesnap.snapshot as snapshot

URL = 'https://example.com'


def test_image_snapshot_returns_the_png_and_closes_chromium(chromium):
    assert pyppesnap.get_image_snapshot_by_url(URL) == 'iVBORw0KGgo='

    page = chromium.browser.page
    assert page.viewport == {'width': 1600, 'height': 900, 'deviceScaleFactor': 1, 'isMobile': False}
    assert page.goto_calls == [(URL, {'timeout': 30000})]
    assert chromium.browser.closed


def test_viewport_follows_the_arguments(chromium):
    pyppesnap.get_image_snapshot_by_url(URL, width=390, height=844, is_mobile=True)

    assert chromium.browser.page.viewport == {
        'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'isMobile': True}


def test_pdf_snapshot_is_base64_bytes_of_the_whole_page(chromium):
    result = pyppesnap.get_pdf_snapshot_by_url(URL)

    assert result == base64.b64encode(b'%PDF-1.4 fake')
    # One page as large as the document, plus a small margin against a second page.
    assert chromium.browser.page.pdf_options == {'printBackground': True, 'width': 800, 'height': 1205}
    assert chromium.browser.closed


def test_chromium_runs_headless_without_signal_handlers(chromium):
    pyppesnap.get_image_snapshot_by_url(URL)

    options = chromium.launch_kwargs['options']
    assert options['headless'] is True
    assert '--no-sandbox' in options['args']
    # The snapshot runs in a worker thread, where Python cannot install signal handlers.
    assert options['handleSIGINT'] is options['handleSIGTERM'] is options['handleSIGHUP'] is False
    # pyppesnap closes Chromium itself; pyppeteer's exit hook only printed a traceback.
    assert options['autoClose'] is False


def test_chromium_is_closed_when_opening_a_tab_fails(chromium, capsys):
    # Before, Chromium kept running in the background here.
    chromium.browser.new_page_error = RuntimeError('could not open a tab')

    assert pyppesnap.get_image_snapshot_by_url(URL) is None
    assert 'could not open a tab' in capsys.readouterr().out
    assert chromium.browser.closed


def test_a_page_that_never_loads_hits_the_time_limit(chromium, monkeypatch, capsys):
    monkeypatch.setattr(snapshot, 'SNAPSHOT_TIMEOUT', 0.5)
    chromium.browser.page.goto_delay = 60

    started = time.monotonic()
    result = pyppesnap.get_image_snapshot_by_url(URL)

    assert result is None
    assert time.monotonic() - started < 10
    # Before, a time-out printed an empty line.
    assert capsys.readouterr().out.strip() == (
        'Could not take a snapshot of https://example.com: gave up after 0.5 s')
    assert chromium.browser.closed


def test_chromium_that_does_not_quit_is_killed(chromium, monkeypatch):
    monkeypatch.setattr(snapshot, 'CLOSE_TIMEOUT', 0.2)
    chromium.browser.close_delay = 60

    assert pyppesnap.get_image_snapshot_by_url(URL) == 'iVBORw0KGgo='
    assert chromium.browser.process.killed


def test_chromium_download_does_not_count_against_the_time_limit(chromium, monkeypatch):
    monkeypatch.setattr(snapshot, 'SNAPSHOT_TIMEOUT', 0.5)
    monkeypatch.setattr(snapshot, '_ensure_chromium', lambda: time.sleep(1))

    assert pyppesnap.get_image_snapshot_by_url(URL) == 'iVBORw0KGgo='


def test_the_callers_event_loop_is_left_alone(chromium):
    # Before, the caller's loop was replaced by a closed one, so later asyncio code failed.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        pyppesnap.get_image_snapshot_by_url(URL)

        assert asyncio.get_event_loop() is loop
        assert not loop.is_closed()
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def test_works_where_an_event_loop_is_already_running(chromium):
    # e.g. a Jupyter notebook or an async web framework. Before, this returned None.
    async def caller():
        return pyppesnap.get_image_snapshot_by_url(URL)

    loop = asyncio.new_event_loop()
    try:
        assert loop.run_until_complete(caller()) == 'iVBORw0KGgo='
    finally:
        loop.close()


def test_no_pending_task_warnings_after_a_snapshot(chromium, caplog):
    # pyppeteer leaves background tasks running; they used to be reported as
    # "Task was destroyed but it is pending!" after every snapshot.
    async def leave_a_task_behind(page):
        asyncio.ensure_future(asyncio.sleep(3600))
        return 'done'

    assert snapshot.get_snapshot_by_url(URL, leave_a_task_behind) == 'done'
    gc.collect()

    assert 'Task was destroyed' not in caplog.text


def test_error_message_names_the_url_and_the_reason(chromium, capsys):
    chromium.browser.page.goto_error = Exception('net::ERR_CONNECTION_REFUSED at http://localhost:1')

    pyppesnap.get_pdf_snapshot_by_url('http://localhost:1')

    assert capsys.readouterr().out.strip() == (
        'Could not take a snapshot of http://localhost:1: net::ERR_CONNECTION_REFUSED at http://localhost:1')


def test_url_without_scheme_gets_a_hint(chromium, capsys):
    chromium.browser.page.goto_error = Exception('Protocol error (Page.navigate): Cannot navigate to invalid URL')

    assert pyppesnap.get_image_snapshot_by_url('example.com') is None
    assert '(the URL needs a scheme, e.g. https://example.com)' in capsys.readouterr().out


def test_chromium_that_does_not_start_gets_a_hint(chromium, capsys):
    chromium.launch_error = BrowserError('Browser closed unexpectedly:\n')

    assert pyppesnap.get_image_snapshot_by_url(URL) is None
    out = capsys.readouterr().out
    assert 'Browser closed unexpectedly:' in out
    assert 'system libraries' in out


def test_only_the_first_matching_hint_is_added(chromium, capsys):
    # A URL without a scheme is the likelier cause, so that hint wins.
    chromium.launch_error = BrowserError('Browser closed unexpectedly:\n')

    assert pyppesnap.get_image_snapshot_by_url('example.com') is None
    out = capsys.readouterr().out
    assert out.count(' (') == 1
    assert '(the URL needs a scheme, e.g. https://example.com)' in out
    assert 'system libraries' not in out


def test_old_coroutine_still_prints_and_returns_none(chromium, capsys):
    chromium.browser.page.goto_error = Exception('boom')

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            snapshot.launch_ptppeteer_with_url(URL, 1600, 900, False, snapshot.shot_with_image))
    finally:
        loop.close()

    assert result is None
    assert 'boom' in capsys.readouterr().out
    assert chromium.browser.closed
