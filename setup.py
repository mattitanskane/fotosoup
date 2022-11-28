from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name = 'fotosoup',
    version = '0.0.1',
    author = 'Matti Tanskanen',
    license = 'GNU GENERAL PUBLIC LICENSE',
    description = 'Rename images in an opinionated way and move them between files.',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = 'https://github.com/mattitanskane/fotosoup',
    py_modules = ['main'],
    packages = find_packages(),
    python_requires='>=3.9',
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Operating System :: Only tested on MacOs Monterey",
    ],
    entry_points = '''
        [console_scripts]
        cooltool=main:app
    '''
)