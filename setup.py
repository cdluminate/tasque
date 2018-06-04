from setuptools import setup, find_packages

setup(name='tq1',
      version='0.4.5',
      description='Simple Command Line Job Manager',
      long_description=open('./README.md', 'r').read(),
      long_description_content_type='text/markdown',
      url='https://github.com/CDLuminate/tq',
      author='Mo Zhou',
      author_email='cdluminate@gmail.com',
      license='MIT',
      packages=['tq'],
      entry_points={'console_scripts': ['tq=tq:main']},
      )
