import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
#: owner/name on GitHub. The project URLs and the README links on PyPI point here.
REPOSITORY = 'NatLee/pyppeteer-snap'
GITHUB = 'https://github.com/' + REPOSITORY
RAW_FILES = 'https://raw.githubusercontent.com/' + REPOSITORY

VERSION = re.search(
    r'''^__version__ = ['"]([^'"]+)['"]''',
    (HERE / 'src' / 'pyppesnap' / '__init__.py').read_text(encoding='utf-8'),
    re.MULTILINE,
).group(1)
#: Releases are tagged v<version> (see `git tag`), so this is the tree the release was built from.
RELEASE_TAG = 'v' + VERSION

# A link target that is relative to the repository: no scheme ("https:", "mailto:"),
# no in-page anchor and no site-absolute path.
_RELATIVE = r'(?![A-Za-z][A-Za-z0-9+.-]*:|[#/])'
# Embedded files (HTML src/srcset, Markdown images) need the raw file ...
_EMBEDDED = re.compile(r'(\b(?:src|srcset)="|!\[[^\]]*\]\()' + _RELATIVE)
# ... links (HTML href, Markdown links) the GitHub page of the file or folder.
_LINKED = re.compile(r'(\bhref="|(?<!!)\[[^\]]*\]\()' + _RELATIVE)


def absolute_links(markdown: str, ref: str) -> str:
    """Point every relative link in ``markdown`` at this repository's files in ``ref``.

    The README uses relative links, which work on GitHub and in a clone. PyPI shows
    the text on its own, where they would all be broken.
    """
    markdown = _EMBEDDED.sub(r'\g<1>{}/{}/'.format(RAW_FILES, ref), markdown)
    return _LINKED.sub(r'\g<1>{}/blob/{}/'.format(GITHUB, ref), markdown)


LONG_DESCRIPTION = absolute_links((HERE / 'README.md').read_text(encoding='utf-8'), RELEASE_TAG)

if __name__ == '__main__':
    # setuptools runs this file as __main__. The guard lets the tests import the
    # functions above without installing setuptools.
    import setuptools

    setuptools.setup(
        name='PyppeSnap',
        version=VERSION,
        author='Nat Lee',
        author_email='natlee.work@gmail.com',
        description='Get a snapshot from a website by using Pyppeteer.',
        keywords='pyppeteer, snapshot',
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/markdown',
        url=GITHUB,
        project_urls={
            'Documentation': GITHUB,
            'Bug Reports': GITHUB + '/issues',
            'Source Code': GITHUB,
            # 'Funding': '',
            # 'Say Thanks!': '',
        },
        package_dir={'': 'src'},
        packages=setuptools.find_packages(where='src'),
        classifiers=[
            # see https://pypi.org/classifiers/
            'Development Status :: 5 - Production/Stable',

            'Intended Audience :: Developers',
            'Topic :: Software Development :: Build Tools',

            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
            'Programming Language :: Python :: 3.13',
            'Programming Language :: Python :: 3.14',
            'Programming Language :: Python :: 3 :: Only',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
        ],
        python_requires='>=3.7',
        # pyppeteer brings its own compatible websockets and pyee. Pinning those two
        # (websockets 8.1, pyee 6.0.0) forced pyppeteer 0.0.25, which hangs on
        # Python 3.10+. 1.0.2 is the newest pyppeteer that still runs on Python 3.7.
        install_requires=['pyppeteer>=1.0.2'],
        extras_require={
            'dev': ['check-manifest'],
            'test': ['pytest'],
        },
        entry_points={
            'console_scripts': [
                'pyppesnap=pyppesnap.cli:main'
            ]
        }
    )
