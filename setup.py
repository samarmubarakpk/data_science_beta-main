from setuptools import setup, find_packages

setup(
    name="data-mining-workflow-designer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "networkx>=2.5",
        "numpy>=1.19.0",
        "pandas>=1.2.0",
        "pillow>=8.0.0",
        "torch>=1.8.0",
        "torchvision>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "workflow-designer=src.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A desktop application for data mining workflows",
    keywords="data-mining, machine-learning, workflow, gui",
    python_requires=">=3.8",
)
