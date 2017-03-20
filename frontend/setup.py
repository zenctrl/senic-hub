from setuptools import setup
from os import path, walk


name = 'senic.nuimo_hub_frontend'


def find_data(top):
    for dirpath, _, files in walk(top):
        base = dirpath.replace(top, '../frontend', 1)
        yield base, [path.join(dirpath, name) for name in files]


setup(
    name=name,
    version_format='{tag}.{commitcount}+{gitsha}',
    url='https://github.com/getsenic/nuimo-hub-app',
    author='Senic GmbH',
    author_email='developers@senic.com',
    description='The frontend application for the Senic Hub',
    include_package_data=True,
    data_files=sorted(find_data('distribution')),
    zip_safe=False,
    setup_requires=[
        'setuptools >= 34.0.1',
        'setuptools-git-version'
    ],
    install_requires=[
        'setuptools',
    ],
)
