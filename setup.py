from setuptools import setup, find_packages

print find_packages()

setup(
    name = "Network Rail",
    version = "0.1",
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'nrtable = networkrail.receiver:main',
        ],
    }
)
