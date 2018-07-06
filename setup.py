import json_serde
import setuptools

from os import path

base_dir = path.abspath(path.dirname(__file__))

with open(path.join(base_dir, 'README.md')) as f:
    long_description = f.read()

setuptools.setup(
    name='json-serde',
    version=json_serde.__version__,
    author='heartsucker',
    author_email='heartsucker@autistici.org',
    url='https://github.com/heartsucker/python-json-serde',
    description='JSON de/serializers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_dir={'json_serde': 'json_serde'},
    packages=['json_serde'],
    platforms='any',
    python_requires='>=3.4',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ),
)
