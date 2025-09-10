"""
Setup script for the ePetCare Vet Desktop application.
"""

import sys
from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Additional requirements for building the executable
if 'bdist_app' in sys.argv:
    requirements.append('pyinstaller>=5.8.0')

setup(
    name="epetcare_vet_desktop",
    version="1.0.0",
    description="ePetCare Vet Desktop Application",
    author="ePetCare",
    author_email="info@epetcare.local",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'epetcare_vet_desktop=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Healthcare Industry',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.13',
    ],
)
