# DQPB

[![license](https://img.shields.io/github/license/timpol/pysoplot.svg)](https://github.com/timpol/pysoplot/blob/master/LICENSE.txt)

**DQPB** is a GUI application for geochronology that focuses on calculating disequilibrium U-Pb ages and plotting results, although it can also be used for computing standard equilibrium U-Pb ages, performing linear regression and computing weighted averages.  The software allows isotopic data to be read directly from open Microsoft Excel spreadsheets, and results (both graphical and numerical) printed back to the same sheet once computations are completed. In this way, it aims to emulate the ease of use of Ken Ludwig’s popular Isoplot/Ex program. The program is distributed on Windows and macOS as a stand-alone application and does not require a pre-existing Python installation to run.

DQPB can be used to:
*	Calculate disequilibrium U-Pb concordia intercept ages on a Tera-Wasserburg diagram
*	Calculate disequilibrium 238U-206Pb and 235U-207Pb isochron ages 
*	Calculate disequilibrium single-analysis 206Pb/238U and 207Pb/235U ages
*	Calculate “modified 207Pb” ages using an approach similar to Sakata (2018)
*	Calculate initial equilibrium U-Pb  ages using the above approaches
*	Compute “concordant” initial [234U/238U] values from isochron age data using the routine described in Engel et al., (2019) 
*	Perform linear regression using algorithms that are based on classical statistics (i.e., the model 1, 2, and 3 popularised by Isoplot (Ludwig, 2012), or robust statistics (i.e., the spine algorithm of Powell et al., (2020) and a new ‘robust model 2’ algorithm).
*	Compute weighted averages that optionally account for error covariances using both classical and robust algorithms
*	Plot disequilibrium concordia curves on Tera-Wasserburg diagrams, accounting for different states of initial or present disequilibrium.

![Example](/resources/Screenshot.png)

The functionality of DQPB is also available as part of a pure Python package for more experienced Python users. For this version, see: https://www.github.com/timpol/pysoplot.

# Basic Installation

The easiest way to install DQPB on macOS and Windows is to simply download the latest installer [here](https://github.com/timpol/DQPB/releases/latest). These installers provide a pre-built stand-alone version of the software, that does not require Python to be pre-installed.  

## Mac
1. Download the Mac .dmg [installer](https://github.com/timpol/DQPB/releases/latest)
2. Open the .dmg and drag the DQPB icon into your Applications folder to install the software.
3. Navigate to your Applications folder.
4. Right-click on the icon and select "Open" to launch the Application for the first time.

**Note**: the application may not launch if you double-click on the icon the first time you try to open it. Instead, you should right-click and select "Open". 

4. A security message may pop up telling you that this file is from an “unknown developer” and asking if you wish to continue. DQPB is open-source software distributed free of charge so we have opted not to pay fees to Apple to codesign the application, and so this warning cannot be avoided.
5. When running DQPB for the first time, you will probably be asked to give permission to DQPB to "control Excel". You must click OK, otherwise DQPB will not be able to read data from Excel and the application will not function.

## Windows

1. Download the Windows .exe [installer](https://github.com/timpol/DQPB/releases/latest).
2. Launch the installer and follow the usual steps to install the software.
3. When opening the installer, a Windows Defender warning may pop up informing you that this is an "unrecognized" app. DQPB is open-source software distributed free of charge so we have opted not to pay fees to Microsoft or other third-parties in order to codesign the application. Therefore, this warning cannot be avoided. If this happens, click the "More info" link, then click "Run anway".
4. The application can now be launched from the start menu. If for some reason the icon does not appear, go to the installation directory (usually C:\Program Files\DQPB\) and double-click the DQPB.exe icon.

## Advanced Installation Methods 

DQPB will also soon be available for installation via pip (Python's package manager) for users who have a working Python distribution. Further details coming soon...

# Usage 

See the pdf user guide [here](https://github.com/timpol/DQPB/blob/main/docs/DQPB-v0.1.0-user-guide.pdf) to get started. 

Complete online documentation will
be available soon...

# Citation

If using DQPB in published work, please cite:

(details coming soon...)

In addition, please cite the primary references of any algorithms implemented in DQPB. See the Acknowledgements section below or the source code for further details.

# Acknowledgements

Coming soon...

# License

The DQPB source code is released under the MIT license. 

## Contact

[Timothy Pollard](mailto:pollard@student.unimelb.edu.au)