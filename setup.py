import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(here, 'README.rst')).read()

requires = []

setup(
    name='Batteries',
    version='0.1',
    description="Various batteries for Pyramid, SQLAlchemy and Python general programming",
    long_description=readme,
    classifiers=[
        "Programming Language :: Python",
    ],
    author='Jesse Dhillon',
    author_email='jesse@deva0.net',
    url='https://github.com/jessedhillon',
    keywords='util paste',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='batteries',
    install_requires = requires,
)
