import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(here, 'README.rst'), 'r').read()
changes = open(os.path.join(here, 'CHANGES.rst'), 'r').read()

requires = ['SQLAlchemy', 'python-dateutil<=1.5']

setup(
    name='sqlalchemy-batteries',
    version='0.3',
    description="Various batteries for SQLAlchemy models",
    long_description="{}\n\n{}".format(readme, changes),
    classifiers=[
        "Programming Language :: Python",
    ],
    author='Jesse Dhillon',
    author_email='jesse@deva0.net',
    url='https://github.com/jessedhillon/batteries',
    keywords='util paste',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='batteries',
    install_requires = requires,
)
