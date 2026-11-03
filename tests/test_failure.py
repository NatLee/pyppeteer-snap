"""When a page cannot be loaded, the snapshot functions print the reason and
return None. They must not add a second, misleading error about an unset
variable."""
import pyppesnap.snapshot as snapshot


class FakePage:
    async def setViewport(self, viewport):
        pass

    async def goto(self, url):
        raise Exception('net::ERR_NAME_NOT_RESOLVED at ' + url)


class FakeBrowser:
    closed = False

    async def newPage(self):
        return FakePage()

    async def close(self):
        self.closed = True


def test_failed_snapshot_reports_only_the_real_error(monkeypatch, capsys):
    browser = FakeBrowser()

    async def fake_launch(*args, **kwargs):
        return browser

    monkeypatch.setattr(snapshot, 'launch', fake_launch)

    result = snapshot.get_image_snapshot_by_url('https://no-such-host.invalid')

    out = capsys.readouterr().out
    assert result is None
    assert 'ERR_NAME_NOT_RESOLVED' in out
    assert 'local variable' not in out
    assert browser.closed
