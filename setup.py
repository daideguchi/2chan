from setuptools import setup, find_packages

setup(
    name="2chan",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "lxml>=4.9.3",
        "pandas>=2.1.1",
        "openpyxl>=3.1.2",
        "PyYAML>=6.0.1",
        "pillow>=10.0.1",
    ],
    extras_require={
        "dev": [
            "black>=23.9.1",
            "flake8>=6.1.0",
            "pytest>=7.4.2",
            "pytest-cov>=4.1.0",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="2ちゃんねるまとめサイトスクレイパー",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)