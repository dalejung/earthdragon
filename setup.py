from distutils.core import setup

DISTNAME = 'earthdragon'
FULLVERSION = '0.1'

setup(
    name=DISTNAME,
    version=FULLVERSION,
    packages=['earthdragon'],
    install_requires=[
        # 'asttools',
        'toolz',
        'typeguard',
        'more_itertools',
        'module_name',
        'frozendict',
        'line_profiler',
    ]
)
