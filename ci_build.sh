#!/bin/bash

pip install cython
pip install numpy
pip install git+https://github.com/pandas-dev/pandas.git#egg=pandas
pip install typeguard
pip install -e git+https://github.com/berkerpeksag/astor#egg=astor
pip install -e git+https://github.com/dalejung/asttools#egg=asttools
pip install .
