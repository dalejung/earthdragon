from distutils.core import setup

DISTNAME='earthdragon'
FULLVERSION='0.1'

setup(
    name=DISTNAME,
    version=FULLVERSION,
    packages=['earthdragon'],
    install_requires = [
        'asttools',
        'toolz'
    ]
)
