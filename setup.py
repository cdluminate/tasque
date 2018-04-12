from setuptools import setup, find_packages

setup(name='tq',
      version='0.2.1',
      description='Command Line Scheduler',
      long_description=open('./README.md', 'r').read(),
      url='https://github.com/CDLuminate/tq',
      author='Mo Zhou',
      author_email='cdluminate@gmail.com',
      packages=['tq'],
      entry_points={'console_scripts': ['tq=tq:main']},
      )
