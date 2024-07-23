# SRTA Implementation of OLAF
![](https://calcog.org/wp-content/uploads/2020/07/SRTA_Logo_final.jpg)

This is the implementation of [OLAF](https://github.com/ManhanGroup/OLAF) prepared by Manhan for the Shasta Regional Transportation Agency in 2024, to support ongoing land use and travel demand forecasting activities.

## Development Notes
The model is intended as a companion to the ShastaSIM activity-based travel demand model maintained by SRTA, and uses the same system of parcel-based geographic analysis units.  Model parameters were estimated based upon statistical analysis of development dynamics observed in both Shasta parcel datasets (for 2012 and 2023) as well as US Census data (from 2011-2019).

## User Configuration
A single [YAML](https://yaml.org/)-format configuration file is used to specify the input data location (in CSV format).  Base year input data must be requested separately from SRTA.

## Dependencies
Aside from Python 3, the script requires NumPy, Pandas and PyYAML.  These can be installed using the command:

`pip3 install pandas numpy pyyaml`

It is good practice to create a virtual environment before doing this, e.g.:

`python3 -m venv env && source env/bin/activate`

## Disclaimer
This script should be considered Beta software, published under an MIT license.  It makes use of Pandas functions which perform arbitrary executions on a dataframe and therefore could possibly present a security vulnerability.  The author assumes no liability whatsoever for any damages incurred by users.
