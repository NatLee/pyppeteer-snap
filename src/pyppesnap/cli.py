"""The ``pyppesnap`` command: print a snapshot of a website as base64 text."""
import argparse
from typing import Optional, Sequence

from .snapshot import DEFAULT_HEIGHT, DEFAULT_WIDTH, get_image_snapshot_by_url, get_pdf_snapshot_by_url

#: --type value -> (what it prints, the function that takes it). The first one is the default.
SNAPSHOTS = {
    'img': ('PNG of the first {}x{} pixels'.format(DEFAULT_WIDTH, DEFAULT_HEIGHT), get_image_snapshot_by_url),
    'pdf': ('the whole page', get_pdf_snapshot_by_url),
}
TYPES = tuple(SNAPSHOTS)
DEFAULT_TYPE = TYPES[0]


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='pyppesnap',
        description='PyppeSnap CLI: print a snapshot of a website as base64 text.',
    )
    parser.add_argument('--url', type=str,
                        help='the page to snapshot, with its scheme, e.g. https://example.com')
    parser.add_argument('--type', type=str, default=DEFAULT_TYPE, help='; '.join(
        '{}: {}{}'.format(name, prints, ' (default)' if name == DEFAULT_TYPE else '')
        for name, (prints, _) in SNAPSHOTS.items()))
    return parser


def _print_error(message: str) -> None:
    print('------------- ERROR ---------------')
    print(message)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command; return the exit status (0 success, 1 snapshot failed, 2 bad options)."""
    parser = get_parser()
    args = parser.parse_args(argv)
    url = args.url
    type_ = args.type.lower()
    print('------------- Parameters ---------------')
    print(f'URL: {url}')
    print(f'Type: {type_}')

    if not url:
        _print_error('Please give a URL with --url, like `https://example.com`.')
        parser.print_help()
        return 2
    if type_ not in TYPES:
        _print_error('Please select type {}.'.format(' or '.join('`{}`'.format(name) for name in TYPES)))
        parser.print_help()
        return 2

    data = SNAPSHOTS[type_][1](url)
    if data is None:
        # The snapshot function has already printed the reason.
        _print_error('No snapshot was taken, see the reason above.')
        return 1

    # The PDF snapshot is base64 bytes: print it as text, not as b'...'.
    if isinstance(data, bytes):
        data = data.decode('ascii')
    print('--------------- Base64 ------------------')
    print(data)
    print('-------------------------------------')
    return 0

