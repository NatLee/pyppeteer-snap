"""Take a snapshot of a website with a headless Chromium driven by pyppeteer.

Every call starts its own Chromium, loads the page, captures it and closes
Chromium again. The work runs on a private event loop in a worker thread, so
the caller's event loop is left alone, and the functions also work where a
loop is already running (Jupyter, async web frameworks).
"""
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.chromium_downloader import check_chromium, download_chromium
from pyppeteer.errors import BrowserError
from pyppeteer.page import Page

#: Something that captures a loaded page, e.g. :func:`shot_with_image`.
Capture = Callable[[Page], Awaitable[Any]]

#: Seconds one snapshot may take: start Chromium, load the page, capture it.
#: Downloading Chromium on the first run does not count.
SNAPSHOT_TIMEOUT = 120
#: Seconds the page may take to load (the same as pyppeteer's default).
NAVIGATION_TIMEOUT = 30
#: Seconds Chromium gets to quit before it is killed.
CLOSE_TIMEOUT = 10

#: The browser window in CSS pixels when the caller does not choose one.
DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 900
#: Image pixels per CSS pixel: a 1600 x 900 window gives a 1600 x 900 PNG.
DEVICE_SCALE_FACTOR = 1
#: CSS pixels added to the PDF sheet's height, so that rounding cannot push
#: the end of the page onto a second sheet.
PDF_EXTRA_HEIGHT = 5
#: Chromium switches that let it run in containers and on CI: no sandbox
#: (unavailable when running as root, as in most Docker images), no /dev/shm
#: (tiny in Docker), and no GPU.
CHROMIUM_ARGS = (
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--no-zygote',
    '--disable-gpu',
)


def _launch_options() -> Dict[str, Any]:
    """Everything pyppeteer's launch() is given."""
    return {
        'headless': True,
        'args': list(CHROMIUM_ARGS),
        # The snapshot runs in a worker thread, and Python only lets the main
        # thread install signal handlers.
        'handleSIGINT': False,
        'handleSIGTERM': False,
        'handleSIGHUP': False,
        # _close() always closes Chromium. pyppeteer's own exit hook would run
        # on an event loop that is closed by then, and only print a traceback.
        'autoClose': False,
    }


async def shot_with_image(page: Page) -> str:
    """Capture the viewport as a PNG, base64-encoded text."""
    return await page.screenshot({'encoding': 'base64'})


async def shot_with_pdf(page: Page) -> bytes:
    """Capture the whole page as a single-page PDF, base64-encoded bytes."""
    dimensions = await page.evaluate(
        """() => {
            return {
                width: document.scrollingElement.scrollWidth,
                height: document.documentElement.offsetHeight,
            }
        }"""
    )
    data = await page.pdf(
        {
            'printBackground': True,
            'width': dimensions['width'],
            'height': dimensions['height'] + PDF_EXTRA_HEIGHT,
        }
    )
    return base64.b64encode(data)


async def _close(browser: Browser) -> None:
    """Close Chromium, and kill it if it does not quit in time."""
    try:
        await asyncio.wait_for(browser.close(), CLOSE_TIMEOUT)
    except BaseException as error:
        process = browser.process  # None only for a browser from connect()
        if process is not None and process.poll() is None:
            process.kill()
        # Let a cancellation (the time limit ran out while closing) carry on.
        if not isinstance(error, Exception):
            raise


async def _snapshot(url: str, capture: Capture, width: int, height: int, is_mobile: bool) -> Any:
    """Open ``url`` in a new headless Chromium and return ``capture(page)``.

    Errors are raised, and Chromium is closed in every case.
    """
    browser = await launch(options=_launch_options())
    try:
        page = await browser.newPage()
        await page.setViewport(
            {
                'width': width,
                'height': height,
                'deviceScaleFactor': DEVICE_SCALE_FACTOR,
                'isMobile': is_mobile,
            }
        )
        await page.goto(url, {'timeout': NAVIGATION_TIMEOUT * 1000})
        return await capture(page)
    finally:
        await _close(browser)


def _ensure_chromium() -> None:
    """Download Chromium on the first run, before the time limit starts."""
    if not check_chromium():
        download_chromium()


def _run_snapshot(url: str, capture: Capture, width: int, height: int, is_mobile: bool) -> Any:
    """Take the snapshot on a new event loop in the current (worker) thread.

    asyncio.run() also cancels the tasks pyppeteer leaves running. Without
    that, Python prints "Task was destroyed but it is pending!" after every
    snapshot.
    """
    _ensure_chromium()
    return asyncio.run(
        asyncio.wait_for(_snapshot(url, capture, width, height, is_mobile), SNAPSHOT_TIMEOUT)
    )


#: The README section on Chromium's system libraries.
_INSTALL_HELP_URL = 'https://github.com/NatLee/pyppeteer-snap#installation'
#: What to tell the user for failures with a known cause: (does it apply to
#: this URL and error?, the hint). The first hint that applies is shown, so
#: the likelier cause goes first. A new known cause is a new row.
_HINTS: Tuple[Tuple[Callable[[str, BaseException], bool], str], ...] = (
    (lambda url, error: '://' not in url,
     'the URL needs a scheme, e.g. https://{url}'),
    (lambda url, error: isinstance(error, BrowserError),
     'Chromium did not start. On Linux it may need extra system libraries, see ' + _INSTALL_HELP_URL),
)


def describe_error(url: str, error: BaseException) -> str:
    """Explain in one line why the snapshot of ``url`` failed."""
    reason = str(error).strip()
    if not reason:
        if isinstance(error, asyncio.TimeoutError):
            reason = 'gave up after {} s'.format(SNAPSHOT_TIMEOUT)
        else:
            reason = type(error).__name__
    message = 'Could not take a snapshot of {}: {}'.format(url, reason)
    for applies, hint in _HINTS:
        if applies(url, error):
            return '{} ({})'.format(message, hint.format(url=url))
    return message


def get_snapshot_by_url(url: str, method: Capture, width: int = DEFAULT_WIDTH,
                        height: int = DEFAULT_HEIGHT, is_mobile: bool = False) -> Any:
    """Return ``method(page)`` for ``url``; on failure print the reason and return None."""
    try:
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix='pyppesnap') as worker:
            return worker.submit(_run_snapshot, url, method, width, height, is_mobile).result()
    except Exception as error:
        print(describe_error(url, error))
        return None


def get_image_snapshot_by_url(url: str, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                              is_mobile: bool = False) -> Optional[str]:
    """Return a PNG of the page's first ``width`` x ``height`` pixels as base64 text.

    On failure, print the reason and return None.
    """
    return get_snapshot_by_url(url=url, method=shot_with_image, width=width, height=height, is_mobile=is_mobile)


def get_pdf_snapshot_by_url(url: str, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                            is_mobile: bool = False) -> Optional[bytes]:
    """Return the whole page as a single-page PDF, base64-encoded bytes.

    ``width`` and ``height`` set the browser window the page is laid out in.
    On failure, print the reason and return None.
    """
    return get_snapshot_by_url(url=url, method=shot_with_pdf, width=width, height=height, is_mobile=is_mobile)


async def launch_ptppeteer_with_url(url: str, width: int, height: int, is_mobile: bool,
                                    method: Capture) -> Any:
    """Old coroutine, kept so code that imported it keeps working.

    Like before, it prints the reason and returns None when the snapshot fails.

    Compatibility shim for code written against 1.0.x. It runs on the
    caller's loop, without the overall time limit, and keeps the old typo in
    its name. It was never in the README: remove it in the next major release
    (2.0.0). New code should call get_snapshot_by_url().
    """
    try:
        return await _snapshot(url, method, width, height, is_mobile)
    except Exception as error:
        print(describe_error(url, error))
        return None
