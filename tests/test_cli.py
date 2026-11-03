"""The command line tool prints the snapshot as plain base64 text and reports
failures with a non-zero exit status."""
import sys

import pyppesnap.cli as cli


def fake_snapshot(monkeypatch, type_, take):
    """Make `--type type_` call `take(url)` instead of opening Chromium."""
    prints, _ = cli.SNAPSHOTS[type_]
    monkeypatch.setitem(cli.SNAPSHOTS, type_, (prints, take))


def run_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, 'argv', ['pyppesnap'] + list(args))
    status = cli.main()
    return status, capsys.readouterr().out.splitlines()


def test_pdf_is_printed_as_plain_base64(monkeypatch, capsys):
    # get_pdf_snapshot_by_url returns base64 as bytes
    fake_snapshot(monkeypatch, 'pdf', lambda url: b'JVBERi0xLjQK')

    status, lines = run_cli(monkeypatch, capsys, '--url', 'https://example.com', '--type', 'pdf')

    assert status == 0
    assert 'JVBERi0xLjQK' in lines
    assert not any(line.startswith("b'") for line in lines)


def test_image_is_printed_as_plain_base64(monkeypatch, capsys):
    # get_image_snapshot_by_url returns base64 as str
    fake_snapshot(monkeypatch, 'img', lambda url: 'iVBORw0KGgo=')

    status, lines = run_cli(monkeypatch, capsys, '--url', 'https://example.com', '--type', 'img')

    assert status == 0
    assert lines == [
        '------------- Parameters ---------------',
        'URL: https://example.com',
        'Type: img',
        '--------------- Base64 ------------------',
        'iVBORw0KGgo=',
        '-------------------------------------',
    ]


def test_type_defaults_to_img_and_ignores_case(monkeypatch, capsys):
    fake_snapshot(monkeypatch, 'img', lambda url: 'png')
    fake_snapshot(monkeypatch, 'pdf', lambda url: b'pdf')

    assert run_cli(monkeypatch, capsys, '--url', 'https://example.com')[1][4] == 'png'
    assert run_cli(monkeypatch, capsys, '--url', 'https://example.com', '--type', 'PDF')[1][4] == 'pdf'


def test_main_accepts_an_argument_list(monkeypatch, capsys):
    fake_snapshot(monkeypatch, 'img', lambda url: 'png')

    assert cli.main(['--url', 'https://example.com']) == 0
    assert 'png' in capsys.readouterr().out.splitlines()


def test_failed_snapshot_exits_with_1(monkeypatch, capsys):
    # The snapshot function prints the reason itself and returns None.
    fake_snapshot(monkeypatch, 'img', lambda url: print('Could not take a snapshot'))

    status, lines = run_cli(monkeypatch, capsys, '--url', 'https://no-such-host.invalid')

    assert status == 1
    assert lines[3:] == [
        'Could not take a snapshot',
        '------------- ERROR ---------------',
        'No snapshot was taken, see the reason above.',
    ]
    assert 'None' not in lines


def test_missing_url_exits_with_2(monkeypatch, capsys):
    status, lines = run_cli(monkeypatch, capsys)

    assert status == 2
    assert 'Please give a URL with --url, like `https://example.com`.' in lines


def test_unknown_type_exits_with_2(monkeypatch, capsys):
    status, lines = run_cli(monkeypatch, capsys, '--url', 'https://example.com', '--type', 'jpg')

    assert status == 2
    assert 'Please select type `img` or `pdf`.' in lines


def test_help_names_the_default_window_size():
    # 1600 x 900 is the documented default of get_image_snapshot_by_url().
    assert 'PNG of the first 1600x900 pixels (default)' in ' '.join(cli.get_parser().format_help().split())
