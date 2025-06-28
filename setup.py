from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="fs_clean",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="FlipSync - Agentic Architecture for E-commerce",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/FS_MAIN",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
    install_requires=requirements,
)
