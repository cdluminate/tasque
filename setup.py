from setuptools import setup, find_packages

setup(name='tq',
      version='0.2',
      packages=['tq'],
      entry_points={'console_scripts': ['tq=tq:main']},
      )
