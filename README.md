# PyppeSnap

[![Test](https://github.com/NatLee/pyppeteer-snap/actions/workflows/test.yml/badge.svg)](https://github.com/NatLee/pyppeteer-snap/actions/workflows/test.yml)[![Release](https://github.com/NatLee/pyppeteer-snap/actions/workflows/release.yml/badge.svg)](https://github.com/NatLee/pyppeteer-snap/actions/workflows/release.yml)

![image](https://i.imgur.com/hgXl2l6.png)

![pdf](https://i.imgur.com/JLe9bYi.png)

This is a tool for getting snapshot with base64 encoding from a website.

As DEMO image you see, just need one URL input to function.

This package support `image` and `pdf` with encoded base64.

## Installation

```bash
pip install pyppesnap
```

Check it on [Pypi](https://pypi.org/project/PyppeSnap/).

Works on Python 3.7–3.14. The package is called `PyppeSnap` on PyPI and is imported as `pyppesnap`.

**First run downloads Chromium.** [Pyppeteer](https://github.com/pyppeteer/pyppeteer) drives a headless Chromium.
The first snapshot downloads a Chromium build (about 100–200 MB) into your user folder, so it takes a while and needs
internet access. On a minimal Linux image (for example `python:3.12-slim` in Docker) Chromium also needs some system
libraries, e.g. on Debian/Ubuntu:

```bash
apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2
```

## Usage

Common use with code below.

- Get image

```python
from pyppesnap import get_image_snapshot_by_url
url = 'https://www.google.com'
print(get_image_snapshot_by_url(url))
```

- Get PDF

```python
from pyppesnap import get_pdf_snapshot_by_url
url = 'https://www.google.com'
print(get_pdf_snapshot_by_url(url))
```

> You need to give a valid URL like start with `http`, or Pyppeteer cannot navigate it.

What you get back:

| Function | Returns | On failure |
|---|---|---|
| `get_image_snapshot_by_url(url)` | PNG as base64 text (`str`) | prints the reason, returns `None` |
| `get_pdf_snapshot_by_url(url)` | PDF as base64 (`bytes`) | prints the reason, returns `None` |

To save a snapshot as a file:

```python
import base64
from pyppesnap import get_image_snapshot_by_url, get_pdf_snapshot_by_url

with open('page.png', 'wb') as f:
    f.write(base64.b64decode(get_image_snapshot_by_url('https://example.com')))
with open('page.pdf', 'wb') as f:
    f.write(base64.b64decode(get_pdf_snapshot_by_url('https://example.com')))
```

- CLI

You can try CLI mode for testing.

```bash
pyppesnap --url https://www.google.com --type img
```

And the output here.

```
------------- Parameters ---------------
URL: https://www.google.com
Type: img
--------------- Base64 ------------------
iVBORw0KGgoAAAANSUhEUgAABkAAAAOECAYAAAD
...
CCAAAAAAAkM7/B83ojRnTa7oSAAAAAElFTkSuQmCC
-------------------------------------
```

Both `--type img` and `--type pdf` print plain base64 text that you can pass to any base64 decoder.

This tool can be used with web frameworks to get a snapshot, check details in [./example](https://github.com/NatLee/pyppeteer-snap/tree/main/example).

## Development

```bash
pip install -e ".[test]"
pytest tests      # takes real snapshots of example.com, so it needs internet access and Chromium
tox -e py         # what CI runs: check-manifest + tests
```
