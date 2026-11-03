"""The command line tool prints the snapshot as plain base64 text."""
import sys

import pyppesnap.cli as cli


def run_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, 'argv', ['pyppesnap'] + list(args))
    cli.main()
    return capsys.readouterr().out.splitlines()


def test_pdf_is_printed_as_plain_base64(monkeypatch, capsys):
    # get_pdf_snapshot_by_url returns base64 as bytes
    monkeypatch.setattr(cli, 'get_pdf_snapshot_by_url', lambda url: b'JVBERi0xLjQK')

    lines = run_cli(monkeypatch, capsys, '--url', 'https://example.com', '--type', 'pdf')

    assert 'JVBERi0xLjQK' in lines
    assert not any(line.startswith("b'") for line in lines)


def test_image_is_printed_as_plain_base64(monkeypatch, capsys):
    # get_image_snapshot_by_url returns base64 as str
    monkeypatch.setattr(cli, 'get_image_snapshot_by_url', lambda url: 'iVBORw0KGgo=')

    lines = run_cli(monkeypatch, capsys, '--url', 'https://example.com', '--type', 'img')

    assert 'iVBORw0KGgo=' in lines
