"""PyppeSnap: snapshots of websites as base64 PNG or PDF, taken with pyppeteer."""
__version__ = "1.1.0"

from .snapshot import get_image_snapshot_by_url
from .snapshot import get_pdf_snapshot_by_url
from .cli import main

__all__ = ['get_image_snapshot_by_url', 'get_pdf_snapshot_by_url', 'main']
