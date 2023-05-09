from setuptools import setup

setup(
    name="illegal character check",
    packages=["charchecker"],
    include_package_data=True,
    install_requires=[],
    entry_points={"console_scripts": ["icc==illegal_character_check.__main__:main"]},
)
