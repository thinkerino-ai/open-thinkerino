import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "aitools",
    version = "0.0.1",
    author = "Daniele Trebbi",
    author_email = "dRain88@gmail.com",
    description = ("Various symbolic AI tools"),
    license = "MIT",
    keywords = "logic unification",
    url = "https://github.com/OneManEquipe/aitools",
    packages=['aitools', 'tests'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"
        "License :: OSI Approved :: MIT License",
    ],
)