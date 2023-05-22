from setuptools import setup

setup(
    name="charchecker",
    packages=["charchecker"],
    include_package_data=True,
    install_requires=[
        "pyyaml",
    ],
    entry_points={"console_scripts": ["icc==illegal_character_check.__main__:main"]},
    description="Check a path for illegal characters",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/scuc/Illegal-Character-Check",
    author="Real Python",
    author_email="steven.cucolo@natgeo.com",
    license="MIT",
)
