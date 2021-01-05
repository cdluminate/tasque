from setuptools import setup, find_packages

setup(name='tq1',
      version='0.90.0',
      description='Zero-Config Single-Node Workload Manager',
      long_description=open('./README.md', 'r').read(),
      long_description_content_type='text/markdown',
      url='https://github.com/CDLuminate/tasque',
      author='Mo Zhou',
      author_email='lumin@debian.org',
      license='MIT',
      packages=['tasque'],
      entry_points={'console_scripts': ['tq=tasque.cli:main']},
      )
