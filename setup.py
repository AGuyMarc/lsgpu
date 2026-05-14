from setuptools import setup

setup(
    name="lsgpu",
    version="0.1.3",
    description="List GPUs with details — like lscpu/lsusb but for graphics cards",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Guy-Marc Aprin",
    license="GPL-2.0",
    py_modules=["lsgpu"],
    entry_points={
        "console_scripts": [
            "lsgpu=lsgpu:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Hardware",
        "Topic :: Utilities",
    ],
)
