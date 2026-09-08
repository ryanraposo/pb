import re
from pathlib import Path

from setuptools import find_packages, setup


def read_version():
    text = Path("pb").joinpath("__init__.py").read_text(encoding="utf8")
    return re.search(r'__version__\s*=\s*"(.*?)"', text).group(1)


setup(
    name="procboss",
    version=read_version(),
    packages=find_packages(include=["pb", "pb.*"]),
    entry_points={
        "console_scripts": [
            "pb=pb.main:main",
        ],
    },
    install_requires=["tabulate", "termcolor"],
    author="ryanraposo",
    author_email="raposo.ryan@gmail.com",
    description="A process management tool that lists or kills processes by name and port.",
    long_description=Path("README.md").read_text(encoding="utf8"),
    long_description_content_type="text/markdown",
    url="https://github.com/ryanraposo/pb",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
