setBatchMode(true);
#@ File (label = "Input directory", style = "directory") folder
#@ File (label = "Output directory", style = "directory") save_folder
#@ Float (label = "Minimum Branch Length",  value=1.0, stepSize=1) minbranchlength
#@ Float (label = "Maximum Branch Width",  value=20.0, stepSize=1) maxbranchwidth
file_list = getFileList(folder);
number_of_files = file_list.length;

f = save_folder + File.separator + "cellInfo.csv";




for (i = 0; i < file_list.length; i++) {


    file_path = folder + File.separator + file_list[i];
   	
	print("running file at: " + file_path);

	run("protrusion analysis",  "filename=[" + file_path + "] minbranchlength="+minbranchlength+" maxbranchwidth=" +  maxbranchwidth +" setroi=false updatesomamask=false useimageunit=false saveResults=true");
	
	IJ.renameResults("Neuron Analysis - cell Information","Results");
	selectWindow("Results");
	saveAs("Results", save_folder + File.separator + file_list[i] + "_cellInfo.csv");
	IJ.renameResults("Results","Neuron Analysis - cell Information - saved");
	
	IJ.renameResults("Neuron Analysis - process Information","Results");
	selectWindow("Results");
	saveAs("Results", save_folder + File.separator + file_list[i] + "_processesInfo.csv");
	IJ.renameResults("Results","Neuron Analysis - process Information - saved");

	
	selectWindow("enlarged_DUP_"+file_list[i]);
	save_path = save_folder + File.separator + "result_" + file_list[i];
    saveAs("Tiff", save_path);
    close("*");
    print("Done");
    wait(2000);
    
}






