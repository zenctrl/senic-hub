from setuptools import setup


NAME = "senic.nuimo_app"


setup(
    name=NAME,
    description="Nuimo app for the Senic hub",
    version_format="{tag}.{commitcount}+{gitsha}",
    author="Senic GmbH",
    author_email="developers@senic.com",
    license="MIT",
    url="https://github.com/getsenic/senic-hub-nuimo-app",
    packages=[
        NAME,
    ],
    namespace_packages=[
        "senic",
    ],
    package_dir={
        NAME: "senic/nuimo_app",
    },
    install_requires=[
        "websocket-client==0.40.0",
        "nuimo",
    ],
    extras_require={
        "development": [
            "devpi-client",
            "wheel",
        ],
    },
    setup_requires=[
        "setuptools-git >= 0",
        "setuptools-git-version",
    ],
    tests_require=[
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "nuimo_app = {}.__main__:main".format(NAME),
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)
