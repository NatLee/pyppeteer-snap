import re

import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()
# PyPI cannot show the README images by their relative path: point them at GitHub.
long_description = re.sub(
    r'(src|srcset)="docs/',
    r'\1="https://raw.githubusercontent.com/NatLee/pyppeteer-snap/main/docs/',
    long_description,
)

setuptools.setup(
    name='PyppeSnap',
    author='Nat Lee',
    author_email='natlee.work@gmail.com',
    description='Get a snapshot from a website by using Pyppeteer.',
    keywords='pyppeteer, snapshot',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/NatLee/pyppeteer-snap',
    project_urls={
        'Documentation': 'https://github.com/NatLee/pyppeteer-snap',
        'Bug Reports': 'https://github.com/NatLee/pyppeteer-snap/issues',
        'Source Code': 'https://github.com/NatLee/pyppeteer-snap',
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
