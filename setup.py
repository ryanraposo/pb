from setuptools import setup, find_packages

setup(
    name="procboss",
    version="0.3.1",
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
    long_description=open("README.md", encoding="utf8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ryanraposo/pb",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
