from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="doteq",
    version="1.0.0",
    author="James Jewhurst / Marcel Melo (idea)",
    author_email="",
    description="Keep .env files in sync with .env.example",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PineStreetSoftware/doteq",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=8.0.0",
        "colorama>=0.4.4",
    ],
    entry_points={
        "console_scripts": [
            "doteq=doteq.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

