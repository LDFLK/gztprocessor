from setuptools import setup, find_packages

setup(
    name="gztprocessor",
    version="0.1.0",
    description="A package to process Sri Lankan gazette data and generate CSV outputs to seed Neo4j database.",
    author="Sehansi Perera",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "nltk",
        "rapidfuzz"
    ],
    python_requires=">=3.8",
    extras_require={
        "api": ["fastapi", "uvicorn"]
    },
)
