from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='annote',
    version='1.0.0',
    description='The ANNOTE GUI Python package',
    url='https://github.com/rgroh1996/ANNOTE',
    author='René Groh',
    author_email='rene.groh@fau.de',
    license='MIT License',
    packages=find_packages(),
    package_data={'': ['images/*.png']},
    install_requires=[
        "pyqtgraph>=0.10.0",
        "numpy>=1.23.5",
        "flammkuchen>=1.0.2",
        "pyqt6>=6.5.1",
        "scipy>=1.10.1",
        "pandas>=2.0.3",
        "librosa>=0.10.0"
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="annotation, labelling",
    project_urls={
        "Source": "https://github.com/rgroh1996/ANNOTE",
        "Tracker": "https://github.com/rgroh1996/ANNOTE/issues",
    },
    entry_points={
        'console_scripts': [
            'annote = src.main:main'
        ]
    },
    include_package_data=True,
)
