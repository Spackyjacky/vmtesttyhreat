#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="threatpad",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive SOC incident notes application with IOC handling capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/threatpad-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Text Editors",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "threatpad=threatpad:main",
        ],
    },
    keywords="security, SOC, incident response, IOC, cyber security, threat hunting",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/threatpad-py/issues",
        "Source": "https://github.com/yourusername/threatpad-py",
        "Documentation": "https://github.com/yourusername/threatpad-py/wiki",
    },
)