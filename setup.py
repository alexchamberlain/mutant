import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mutant",
    version="0.0.1",
    author="Alex Chamberlain",
    author_email="alex@alexchamberlain.co.uk",
    description="A forward reasoning logic language for RDF.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexchamberlain/mutant",
    packages=["hexastore"],
    package_data={"hexastore": ["lark/*.lark", "rules/*.mtt"]},
    scripts=["mutant.py"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
