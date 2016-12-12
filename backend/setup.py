from setuptools import setup


name = 'senic.nuimo_hub'


setup(name=name,
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
    include_package_data=True,
    package_dir={name: 'senic/nuimo_hub'},
    package_data={
        name: [
            'migrations/*.py',
            'migrations/versions/*.py',
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
        'alembic',
        'click',
        'colander',
        'cornice<2.0',
        'psycopg2',
        'pyramid',
        'pyramid_tm',
        'pytz',
        'requests',
        'waitress',
        'zope.sqlalchemy',
    ],
    extras_require={
        'development': [
            'webtest',
            'docutils',
            'devpi-client',
            'jinja2',
            'pbr',
            'Sphinx',
            'repoze.sphinx.autointerface',
            'flake8',
            'mock',
            'pep8 < 1.6',
            'pyramid_debugtoolbar',
            'pytest',
            'py >= 1.4.17',
            'pyflakes',
            'pytest-flakes',
            'pytest-pep8',
            'pytest-cov',
            'python-dateutil',
            'tox',
            'pyquery',
            'setuptools-git',
        ],
    },
    entry_points="""
        [paste.app_factory]
        main = senic.nuimo_hub:main
        [pytest11]
        backrest = senic.nuimo_hub.testing
    """,
)
