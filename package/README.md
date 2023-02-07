Building Stand-Alone Application
=================================

The current version was compiled using:

* Python 3.10.7
* PyQt5 5.15.8
* scipy 1.10.0
* numpy 1.24.2
* matplotlib 3.6.3
* xlwings 0.29.1
* pysoplot 0.0.3b1
* pyinstaller 5.7.0
* pyinstaller-hooks-contrib 2022.15

Mac
----

1. Install official Python distribution.
2. Create a Python virtual environment and activate it.
3. Install DQPB locally:
    * pip install .
4. Run the Pyinstaller script
    * pyinstaller dqpb.spec

Win
----

Same as above, but ensure inno setup is installed.
