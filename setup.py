from setuptools import setup
from os import path, walk
import platform

name = 'senic_hub'


def find_data(top):
    for dirpath, _, files in walk(top):
        base = dirpath.replace(top, 'senic-hub-htdocs', 1)
        yield base, [path.join(dirpath, name) for name in files]


if platform.system() == 'Linux':
    install_requires = [
        # backend
        'click',
        'colander',
        'cornice==2.3.0',
        'cryptoyaml',
        'netdisco==0.9.2',
        'nuimo>=0.3.0,<0.4.0',
        'pyramid',
        'pyramid_tm',
        'pytz',
        'requests',
        'cornice_swagger',
        # nuimo_app
        'websocket-client>=0.40.0',
        'soco==0.12',
        'phue==0.9',
        'lightify>=1.0.5',
        'pyinotify==0.9.6',
        'raven',
        'multiprocessing_logging',
    ]
else:
    install_requires = [
        # backend
        'click',
        'colander',
        'cornice==2.3.0',
        'cryptoyaml',
        'netdisco==0.9.2',
        'nuimo>=0.3.0,<0.4.0',
        'pyramid',
        'pyramid_tm',
        'pytz',
        'requests',
        'cornice_swagger',
        # nuimo_app
        'websocket-client>=0.40.0',
        'soco==0.12',
        'phue==0.9',
        'lightify>=1.0.5',
        'raven',
        'multiprocessing_logging',
    ]

setup(
    name=name,
    version_format='{tag}.{commitcount}+{gitsha}',
    url='https://github.com/getsenic/senic-hub',
    author='Senic GmbH',
    author_email='developers@senic.com',
    license="MIT",
    description='...',
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    packages=[name],
    include_package_data=True,
    package_dir={name: 'senic_hub'},
    package_data={
        name: [
            '.coveragerc',
            'senic_hub/backend/tests/*.py',
            'senic_hub/backend/tests/data/*.*',
            'senic_hub/backend/views/*.*',
        ],
    },
    zip_safe=False,
    setup_requires=[
        'setuptools-git >= 0',
        'setuptools-git-version'
    ],
    install_requires=install_requires,
    extras_require={
        'development': [
            'tox',
        ],
    },
    entry_points="""
        [paste.app_factory]
        main = senic_hub.backend:main
        [console_scripts]
        netwatch = senic_hub.backend.netwatch:netwatch_cli
        bluenet = senic_hub.bluenet.bluenet:bluenet_cli
        create_configurations = senic_hub.backend.commands:create_nuimo_app_cfg
        device_discovery = senic_hub.backend.device_discovery:command
        nuimo_app = senic_hub.nuimo_app.__main__:main
    """,
)
