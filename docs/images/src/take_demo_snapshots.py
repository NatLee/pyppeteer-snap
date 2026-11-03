"""Produce the real output shown in the README images, using pyppesnap itself.

    python docs/images/src/take_demo_snapshots.py

Needs Linux with Chromium's system libraries, pdftoppm (poppler-utils) and
`file`. Writes to docs/images/src/out/ (not committed):

  demo-snapshot.png   get_image_snapshot_by_url() of demo-page.html
  demo-snapshot.pdf   get_pdf_snapshot_by_url() of the same page
  demo-pdf-page.png   that PDF page as an image
  terminal.js         the commands shown in terminal.html and what they printed

demo.html and terminal.html then frame these files. Render them with a
Chromium-based browser as described at the top of each file.
"""
import base64
import functools
import http.server
import json
import pathlib
import subprocess
import tempfile
import threading

from pyppesnap import get_image_snapshot_by_url, get_pdf_snapshot_by_url

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'
COMMANDS = [
    'pyppesnap --url https://example.com',
    'pyppesnap --url https://example.com --type pdf | sed -n 5p | base64 -d > example.pdf',
    'file example.pdf',
]


def serve(directory):
    """Serve ``directory`` on a free local port (the OS picks it)."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def snapshot_demo_page():
    server = serve(HERE)
    try:
        host, port = server.server_address[:2]
        url = 'http://{}:{}/demo-page.html'.format(host, port)
        (OUT / 'demo-snapshot.png').write_bytes(base64.b64decode(get_image_snapshot_by_url(url)))
        (OUT / 'demo-snapshot.pdf').write_bytes(base64.b64decode(get_pdf_snapshot_by_url(url)))
    finally:
        server.shutdown()
    subprocess.run(['pdftoppm', '-png', '-r', '48', '-singlefile',
                    str(OUT / 'demo-snapshot.pdf'), str(OUT / 'demo-pdf-page')], check=True)


def run_terminal_commands():
    session = []
    with tempfile.TemporaryDirectory() as workdir:
        for command in COMMANDS:
            result = subprocess.run(command, shell=True, cwd=workdir, check=True,
                                    stdout=subprocess.PIPE, universal_newlines=True)
            session.append({'command': command, 'output': result.stdout})
    (OUT / 'terminal.js').write_text('window.SESSION = {};\n'.format(json.dumps(session, indent=1)))


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    snapshot_demo_page()
    run_terminal_commands()
