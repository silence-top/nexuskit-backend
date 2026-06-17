from setuptools import setup, find_packages

setup(
    name="nexuskit-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "pydantic>=2.0.0",
        "pyjwt",
    ],
)