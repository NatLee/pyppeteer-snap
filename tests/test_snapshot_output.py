"""Real-browser checks: a snapshot must decode to a real PNG / PDF.

Each snapshot runs in a child process with a time limit. With the old
dependency pins (pyppeteer 0.0.25 + websockets 8.1) the call never returns
on Python 3.10 and newer, so a plain call would hang the test run instead
of failing it.
"""
import base64
import subprocess
import sys
import unittest

URL = 'https://example.com'
# The first run also downloads Chromium (about 100-200 MB).
TIME_LIMIT = 300

CHILD = '''
import sys
import pyppesnap
data = getattr(pyppesnap, sys.argv[1])(sys.argv[2])
print("TYPE:" + type(data).__name__)
print("DATA:" + (data.decode() if isinstance(data, bytes) else str(data)))
'''


def take_snapshot(function_name):
    """Return (type name, base64 text) printed by the child process."""
    try:
        result = subprocess.run(
            [sys.executable, '-c', CHILD, function_name, URL],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=TIME_LIMIT,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            '{}() did not return within {} s'.format(function_name, TIME_LIMIT))
    found = {}
    for line in result.stdout.splitlines():
        if line[:5] in ('TYPE:', 'DATA:'):
            found[line[:4]] = line[5:]
    if len(found) != 2:
        raise AssertionError('{}() crashed:\n{}'.format(
            function_name, result.stderr[-2000:]))
    return found['TYPE'], found['DATA']


class TestSnapshotOutput(unittest.TestCase):

    def test_image_snapshot_is_base64_png(self):
        type_name, data = take_snapshot('get_image_snapshot_by_url')
        self.assertEqual(type_name, 'str')
        self.assertTrue(base64.b64decode(data).startswith(b'\x89PNG\r\n\x1a\n'))

    def test_pdf_snapshot_is_base64_pdf(self):
        type_name, data = take_snapshot('get_pdf_snapshot_by_url')
        self.assertEqual(type_name, 'bytes')
        self.assertTrue(base64.b64decode(data).startswith(b'%PDF-'))


if __name__ == '__main__':
    unittest.main()
