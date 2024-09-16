#!/usr/bin/env python

from distutils.core import setup

with open('superdsm/version.py') as fin:
    exec(fin.read(), globals())

setup(
    name = 'SuperDSM',
    version = VERSION,
    description = 'SuperDSM is a globally optimal segmentation method based on superadditivity and deformable shape models for cell nuclei in fluorescence microscopy images and beyond.',
    author = 'Leonid Kostrykin',
    author_email = 'leonid.kostrykin@bioquant.uni-heidelberg.de',
    url = 'https://kostrykin.com',
    license = 'MIT',
    packages = ['superdsm', 'superdsm._libs', 'superdsm._libs.sparse_dot_mkl'],
    python_requires = '>=3.11',
    install_requires = [
        'numpy>=1.26,<2',
        'scipy>=1.13.1,<2',
        'scikit-image>=0.24.0',
        'ipython>=7.31.1',
        'dill>=0.3.2',
        'ray>=0.8.7',
        'cvxopt>=1.3.2',
        'cvxpy>=1.5.3',
        'matplotlib>=3.0',
        'mkl>=2020.0',
        'imagecodecs>=2024.6.1',
        'repype==1.0.0,<1.1',
    ],
)
