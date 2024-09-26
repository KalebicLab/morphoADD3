# Morphological Analysis Pipeline from Segmented Images

The scripts contained in this repository will reproduce the morphological analysis presented in Barelli et al, "Morphoregulatory ADD3 underlies glioblastoma growth and formation of tumor-tumor connections".

### Installation
Download the scripts and example data either manually or by cloning this repository.
In Fiji, install the "protrusion_analysis.py" script by going to "Plugins -> Install" and selecting the script
from https://git.mpi-cbg.de/scicomp/kalebic_et_al_progenitors_processes_analysis, download the `SkeletonAnalysis_-1.2.0.jar` file and place it in the `plugins` folder of Fiji.
Restart Fiji


### Using the script

Open `batch_process_analysis.ijm` in Fiji and run the macro. Where prompted, select an `Input directory` where in the input images to analyze are stored, and an `Output directory` where the output file should be stored. You may also adjust the `Minimum Branch Length` and `Maximum Branch Width` parameters to fit your data. The default values of `1` and `20` respectively work for the supplied test images. Press `OK` to run the script.


### Expected data
2D binary images with background set to 0 and foreground set to 255. Two example images (`001.tif` and `002.tif` are available in the `test_data` folder. 

### Expected output
For each input image, the script will generate an output image (`result_<filename>.tif`)showing outlines of the cell body, as wel as primary and secondary branches, and a series of concentric circles. Numerical data are stored in two csv files, `<filename>_cellInfo.csv`, which contains summary information about the cell and `<filename>_processInfo.csv`, which contains detailed information about each individual protruion measured.

### Validating the installation
Running the script with the input folder `test_data` should reproduce the output files in the `test_output` folder. This was tested using Fiji 2.14.0/1.54f.


