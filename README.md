# DQPB

[![license](https://img.shields.io/github/license/timpol/pysoplot.svg)](https://github.com/timpol/pysoplot/blob/master/LICENSE.txt)

**DQPB** is a GUI application for geochronology that focuses on calculating disequilibrium U-Pb ages and plotting results, although it can also be used for computing standard equilibrium U-Pb ages, performing linear regression and computing weighted averages.  The software allows isotopic data to be read directly from open Microsoft Excel spreadsheets, and results (both graphical and numerical) printed back to the same sheet once computations are completed. In this way, it aims to emulate the ease of use of Ken Ludwig’s popular Isoplot/Ex program. The program is distributed on Windows and macOS as a stand-alone application and does not require a pre-existing Python installation to run.


DQPB can be used to:
*	Calculate disequilibrium U-Pb concordia intercept ages on a Tera-Wasserburg diagram
*	Calculate disequilibrium 238U-206Pb and 235U-207Pb isochron ages 
*	Calculate disequilibrium single-analysis 206Pb/238U and 207Pb/235U ages
*	Calculate “207Pb-correced” ages
*	Calculate initial equilibrium U-Pb  ages using the above approaches
*	Compute “concordant” initial [234U/238U] values from isochron age data using the routine described in Engel et al., (2019) 
*	Perform linear regression using algorithms that are based on classical statistics (i.e., the model 1, 2, and 3 popularised by Isoplot (Ludwig, 2012), or robust statistics (i.e., the spine algorithm of Powell et al., (2020) and a new ‘robust model 2’ algorithm).
*	Compute weighted averages that optionally account for error covariances using both classical and robust algorithms
*	Plot disequilibrium concordia curves on Tera-Wasserburg diagrams, accounting for different states of initial or present disequilibrium.

For more info, see the online DQPB [documentation](https://timpol.github.io/DQPB/)

![Example](/resources/Screenshot.png)

The functionality of DQPB is also available as part of a pure Python package for more experienced Python users. For this version, see: https://www.github.com/timpol/pysoplot.


# Basic Installation

The easiest way to install DQPB on macOS and Windows is to simply download the latest installer [here](https://github.com/timpol/DQPB/releases/latest). These installers provide a pre-built stand-alone version of the software, that does not require Python to be pre-installed.  

See the DQPB [documentation](https://timpol.github.io/DQPB/) for more details on getting started.


# Citation

If using DQPB in published work, please cite the companion Gchron [article](https://gchron.copernicus.org/articles/5/181/2023/):

    @misc{pollard_2023,
      author       = {Pollard, Timothy and Woodhead, Jon and Hellstrom, John and Engel, John and Powell, Roger and Drysdale, Russell},
      title        = {{DQP}: software for calculating disequilibrium U–Pb ages},
      journaltitle = {Geochronology},
      year         = {2023},
      volume       = {5},
      pages        = {181--196},
      date         = {2023},
      doi          = {10.5194/gchron-5-181-2023},
      url          = {https://gchron.copernicus.org/articles/5/181/2023/},
    }


In addition, please cite primary works upon which the algorithms implemented in DQPB are based. Further information may be found within the [documentation](https://timpol.github.io/DQPB/) and in the DQPB source code.

# License

The DQPB source code is released under the MIT license. 

## Contact

[Timothy Pollard](mailto:pollard@student.unimelb.edu.au)