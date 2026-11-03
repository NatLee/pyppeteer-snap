"""A fake Chromium for tests that check how pyppesnap drives the browser."""
import asyncio
from types import SimpleNamespace

import pytest

import pyppesnap.snapshot as snapshot


class FakeProcess:
    def __init__(self):
        self.killed = False

    def poll(self):
        return -9 if self.killed else None

    def kill(self):
        self.killed = True


class FakePage:
    def __init__(self):
        self.viewport = None
        self.goto_calls = []
        self.goto_error = None
        self.goto_delay = 0
        self.pdf_options = None

    async def setViewport(self, viewport):
        self.viewport = viewport

    async def goto(self, url, options=None):
        self.goto_calls.append((url, options))
        if self.goto_delay:
            await asyncio.sleep(self.goto_delay)
        if self.goto_error:
            raise self.goto_error

    async def screenshot(self, options):
        assert options == {'encoding': 'base64'}
        return 'iVBORw0KGgo='

    async def evaluate(self, script):
        return {'width': 800, 'height': 1200}

    async def pdf(self, options):
        self.pdf_options = options
        return b'%PDF-1.4 fake'


class FakeBrowser:
    def __init__(self):
        self.page = FakePage()
        self.process = FakeProcess()
        self.new_page_error = None
        self.close_delay = 0
        self.closed = False

    async def newPage(self):
        if self.new_page_error:
            raise self.new_page_error
        return self.page

    async def close(self):
        if self.close_delay:
            await asyncio.sleep(self.close_delay)
        self.closed = True


@pytest.fixture
def chromium(monkeypatch):
    """Replace Chromium with a FakeBrowser and skip the Chromium download.

    Set ``chromium.launch_error`` to make the launch fail.
    """
    state = SimpleNamespace(browser=FakeBrowser(), launch_kwargs=None, launch_error=None)

    async def fake_launch(*args, **kwargs):
        state.launch_kwargs = kwargs
        if state.launch_error:
            raise state.launch_error
        return state.browser

    monkeypatch.setattr(snapshot, 'launch', fake_launch)
    monkeypatch.setattr(snapshot, '_ensure_chromium', lambda: None, raising=False)
    return state
