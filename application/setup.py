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
        'pyramid',
        'pyramid_tm',
        'pytz',
        'requests',
        'senic.cryptoyaml',
        'wifi',
    ],
    extras_require={
        'development': [
            'devpi-client',
            'docutils',
            'flake8',
            'jinja2',
            'mock',
            'pbr',
            'pdbpp',
            'pep8 < 1.6',
            'py >= 1.4.17',
            'pyflakes',
            'pyquery',
            'pyramid_debugtoolbar',
            'pytest',
            'pytest-cov',
            'pytest-flakes',
            'pytest-pep8',
            'python-dateutil',
            'repoze.sphinx.autointerface',
            'setuptools-git',
            'Sphinx',
            'tox',
            'waitress',
            'webtest',
        ],
    },
    entry_points="""
        [paste.app_factory]
        main = senic.nuimo_hub:main
        [console_scripts]
        scan_wifi = senic.nuimo_hub.commands:scan_wifi
        join_wifi = senic.nuimo_hub.commands:join_wifi
    """,
)
