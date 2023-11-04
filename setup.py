#!/usr/bin/env python

from setuptools import setup

setup(
    name='rwisimulation',
    version='2.0',
    description='Run simulations in Remcom Wireless InSite',
    author='LASSE',
    author_email='pedosb@gmail.com',
    url='https://github.com/lasseufpa/5gm-rwi-simulation',
    entry_points={
        'console_scripts': [
            'rwi-simulation = rwisimulation.simulation:main',
            'rwi-save-tfrecord = rwisimulation.tfrecord:main [tf,shapely]'
        ]
    },
    py_modules=[''],
    install_requires=['numpy(>=1.14)', 'pyreadline', 'attrdict(>=2.0.1)'],
    extras_require={
        'tf': 'tensorflow(>=1.4)',
        'shapely': 'Shapely(>=1.6.3)',
    }
)
