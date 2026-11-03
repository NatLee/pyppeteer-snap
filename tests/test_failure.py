"""When a page cannot be loaded, the snapshot functions print the reason and
return None. They must not add a second, misleading error about an unset
variable."""
import pyppesnap.snapshot as snapshot


def test_failed_snapshot_reports_only_the_real_error(chromium, capsys):
    chromium.browser.page.goto_error = Exception('net::ERR_NAME_NOT_RESOLVED at https://no-such-host.invalid')

    result = snapshot.get_image_snapshot_by_url('https://no-such-host.invalid')

    out = capsys.readouterr().out
    assert result is None
    assert 'ERR_NAME_NOT_RESOLVED' in out
    assert 'local variable' not in out
    assert chromium.browser.closed
