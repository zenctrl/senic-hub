from setuptools import setup


name = 'senic.nuimo_hub'


setup(
    name=name,
    version_format='{tag}.{commitcount}+{gitsha}',
    url='https://github.com/getsenic/nuimo-hub-app',
    author='Senic GmbH',
    author_email='tom@senic.com',
    description='...',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    packages=[name],
    namespace_packages=['senic'],
    include_package_data=True,
    package_dir={name: 'senic/nuimo_hub'},
    package_data={
        name: [
            '.coveragerc',
            'tests/*.py',
            'tests/data/*.*',
            'views/*.*',
        ],
    },
    zip_safe=False,
    setup_requires=[
        'setuptools-git >= 0',
        'setuptools-git-version'
    ],
    install_requires=[
        'click',
        'colander',
        'cornice<2.0',
        'nuimo>=0.2.3',
        'pyramid',
        'pyramid_tm',
        'pytz',
        'requests',
        'cryptoyaml',
        'wifi',
        'netdisco==0.9.1',
    ],
    extras_require={
        'development': [
            'tox',
        ],
    },
    entry_points="""
        [paste.app_factory]
        main = senic.nuimo_hub:main
        [console_scripts]
        scan_wifi = senic.nuimo_hub.commands:scan_wifi
        enter_wifi_setup = senic.nuimo_hub.commands:enter_wifi_setup
        join_wifi = senic.nuimo_hub.commands:join_wifi
        setup_nuimo = senic.nuimo_hub.commands:setup_nuimo
        create_configurations = senic.nuimo_hub.commands:create_configuration_files_and_restart_apps
        device_discovery = senic.nuimo_hub.commands:discover_devices
    """,
)
