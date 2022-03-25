import os

# Helper function for updateing Loaned devices excel sheet


def fileExists(file):
    if os.path.isfile(file):
        os.remove(file)
    else:
        return
    ...


def initD():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(os.getcwd())
    ...
