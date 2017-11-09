# coding:utf-8
from setuptools import setup, find_packages
import os


def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    with open(path, 'r') as f:
        return f.read()


__version__ = "0.2.0"

setup(
    name='slavem',
    version=__version__,
    keywords='slavem',
    description=u'监控全网服务的服务',
    long_description=read("README.md"),

    url='https://github.com/lamter/slavem',
    author='lamter',
    author_email='lamter.fu@gmail.com',

    packages=find_packages(),
    package_data={
    },
    install_requires=read("requirements.txt").splitlines(),
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License'],
)
