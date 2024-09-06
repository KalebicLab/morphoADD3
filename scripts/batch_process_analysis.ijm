setBatchMode(true);
#@ File (label = "Input directory", style = "directory") folder
#@ File (label = "Input directory", style = "directory") save_folder

file_list = getFileList(folder);
number_of_files = file_list.length;

f = save_folder + File.separator + "cellInfo.csv";




for (i = 0; i < file_list.length; i++) {
	print(i);
    file_path = folder + File.separator + file_list[i];
   
	print(file_path);
	run("Bio-Formats Windowless Importer", "open="+file_path);
	run("8-bit");
	run("Invert LUT");
	run("Invert");

	run("my process",  "filename=[" + file_path + "] minbranchlength=1.0 maxbranchwidth=20.0 setroi=false updatesomamask=false useimageunit=false saveresults=true");
	
	IJ.renameResults("Neuron Analysis - cell Information","Results");
	selectWindow("Results");
	saveAs("Results", save_folder + File.separator + "cellInfo.csv");
	IJ.renameResults("Results","Neuron Analysis - cell Information");
	
	IJ.renameResults("Neuron Analysis - process Information","Results");
	selectWindow("Results");
	saveAs("Results", save_folder + File.separator + file_list[i] + "_processesInfo.csv");
	IJ.renameResults("Results","Neuron Analysis - process Information");

	
	selectWindow("enlarged_DUP_"+file_list[i]);
	save_path = save_folder + File.separator + "result_" + file_list[i];
    saveAs("Tiff", save_path);
    run("Close");
    
    
    
}






