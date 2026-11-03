"""PyPI shows the README without the repository around it, so setup.py turns
every relative link in it into an absolute GitHub link, pinned to the release
tag. The README itself only uses relative links to this repository."""
import pathlib
import re
import runpy

ROOT = pathlib.Path(__file__).resolve().parent.parent
SETUP = runpy.run_path(str(ROOT / 'setup.py'), run_name='setup_under_test')
absolute_links = SETUP['absolute_links']

RAW = 'https://raw.githubusercontent.com/NatLee/pyppeteer-snap/v9.9.9/'
PAGE = 'https://github.com/NatLee/pyppeteer-snap/blob/v9.9.9/'


def test_embedded_images_point_at_the_file_in_the_release_tag():
    readme = ('<source srcset="docs/images/hero-dark.png">\n'
              '<img src="docs/images/hero-light.png" alt="hero">\n'
              '![demo](docs/images/demo-light.png)\n')

    assert absolute_links(readme, 'v9.9.9') == (
        '<source srcset="' + RAW + 'docs/images/hero-dark.png">\n'
        '<img src="' + RAW + 'docs/images/hero-light.png" alt="hero">\n'
        '![demo](' + RAW + 'docs/images/demo-light.png)\n')


def test_links_point_at_the_github_page_in_the_release_tag():
    readme = '[`example/`](example/) and <a href="LICENSE">MIT</a>'

    assert absolute_links(readme, 'v9.9.9') == (
        '[`example/`](' + PAGE + 'example/) and <a href="' + PAGE + 'LICENSE">MIT</a>')


def test_absolute_links_and_anchors_are_left_alone():
    readme = ('[PyPI](https://pypi.org/project/PyppeSnap/) [up](#installation) '
              '<img src="https://img.shields.io/pypi/v/PyppeSnap"> [mail](mailto:a@b.c) '
              '<a href="/NatLee">x</a>')

    assert absolute_links(readme, 'v9.9.9') == readme


def test_the_long_description_links_to_the_tag_of_this_version():
    version = SETUP['VERSION']
    description = SETUP['LONG_DESCRIPTION']

    assert 'raw.githubusercontent.com/NatLee/pyppeteer-snap/v{}/docs/images/hero-light.png'.format(
        version) in description
    assert absolute_links(description, 'v' + version) == description


def test_the_readme_links_to_its_own_files_relatively():
    # Absolute links to this repository's files would bypass the rewrite above,
    # and would keep pointing at whatever branch they name.
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')

    assert re.findall(r'github(?:usercontent)?\.com/NatLee/pyppeteer-snap/(?:blob|tree|raw|main)/', readme) == []
