# sirilStarless
Uses starnet++ with Siril to automate the generation of Starless and Stars only images given a fit file input

## Command Line Execution
Simply run the starRemoval.py file with parameters:-

python3 starRemoval.py -s <Path to 'fit' file to Process>

The Starnet++ application installation must exist in the same directory as the python file.
Requires Siril to be installed > v1.06

Output will be written to the same folder as the input file and will include the following: -
* <source file>_starless.fit - fit Starless file
* <source file>_stars.fit - fit stars only
* <source file>_starless.tif - tif 16 bit Starless file
* <source file>_stars.tif - tif 16 bit stars only
