## Create the environment
The first step you need to do is to create a Python environment with all the libraries needed to run correctly the code.

These are the main steps:

1. Install Anaconda
2. Create a conda environment based on Python 3.11
3. Install all the needed libraries

### Install Anaconda
Refer to the documentation relevant for your OS.

see: [Anaconda docs](https://docs.anaconda.com/)

### Create a conda environment
```
conda create -n oraculus python==3.11
```
Obviously, you can change the name of the environment.
The code has been tested with `Python 3.11`. If you want to change the version, you need to re-test.

### Install all the libraries
A list of the needed libraries is in the file libraries.txt

To install all the libraries you can download the file requirements.txt from the Github repo and execute
```
pip install -r requirements.txt
```

