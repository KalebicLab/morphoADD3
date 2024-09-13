#@File		(label = "Image to analyze")			filename
#@float 	(label = "Minimum branch length")		minBranchLength
#@float		(label = "Maximum branch width")		maxBranchWidth
#@boolean 	(label = "Define a region of interest")		setRoi
#@boolean 	(label = "Manually update soma mask")		updateSomaMask
#@boolean 	(label = "Use image calibration")		useImageUnit
##@boolean 	(label = "Save results")			saveResults

# Author: Benoit Lombardot
# 2017-12-12 : version 1.3 , remove soma from number of end point if necessary, build an enlarged output image to show the full sholl circles
# 2017-12-13 : version 1.3.1 , update the branching index to use the new number of end points



from ij import IJ
from ij.plugin import Duplicator
from ij.plugin import ImageCalculator
from ij.gui import PolygonRoi
from ij.gui import OvalRoi
from ij.gui import Overlay
from ij.gui import Wand
from ij.plugin.frame import RoiManager
from ij import ImagePlus
from ij.measure import ResultsTable
from ij import WindowManager;
from ij.text import TextWindow;
from ij.gui import WaitForUserDialog

from sc.fiji.analyzeSkeleton import AnalyzeSkeleton_
from de.mpicbg.scf.skeletonanalysis import SkeletonAnalyser
from de.mpicbg.scf.skeletonanalysis import PathDrawer

from java.awt import Color;

import math, os
import time, datetime


imp0 = IJ.openImage( filename.getPath() )
imp0Name = imp0.getTitle()
pixType = imp0.getType()
if (pixType==ImagePlus.COLOR_256) or (pixType==ImagePlus.COLOR_RGB):
	IJ.run(imp0, "8-bit", "");
	
if setRoi:
	imp0.show()
	IJ.setTool("rectangle")
	WaitForUserDialog("Select roi","Please selection a region of interest to analyse").show()
	imp0.hide()
	imp0 = Duplicator().run(imp0)
	
imageName = imp0.getTitle()
folderName = os.path.split( filename.getParent() )[1]


pWidth = 1
pDepth = 1
unit = "pixel"
R=maxBranchWidth
if useImageUnit:
	pWidth = imp0.getCalibration().pixelWidth
	pDepth = imp0.getCalibration().pixelDepth
	unit   = imp0.getCalibration().getXUnit()
	R = R/pWidth
	#minBranchLength = minBranchLength/pWidth 
R=int(R)

########################################
# build a skeleton mask ################

IJ.log("building skeleton image...")

# create a mask of the neuron
mask0 = Duplicator().run(imp0)
IJ.run(mask0, "Invert", "stack")
IJ.setThreshold(mask0, 1, 255)
IJ.run(mask0, "Convert to Mask", "stack")
IJ.run(mask0, "Invert", "")
if useImageUnit:
	IJ.run(mask0, "Analyze Particles...", "size="+str(maxBranchWidth*maxBranchWidth)+"-Infinity show=Masks add in_situ")
else:
	IJ.run(mask0, "Analyze Particles...", "size="+str(maxBranchWidth*maxBranchWidth)+"-Infinity pixel show=Masks add in_situ")
	
	
IJ.run(mask0, "Invert", "")

#IJ.run(mask0, "Maximum...", "stack radius="+str(int(2)))
#IJ.run(mask0, "Minimum...", "stack radius="+str(2))

# create a mask of the soma
maskSoma = Duplicator().run(mask0)
IJ.run(maskSoma, "Minimum...", "stack radius="+str(R))
IJ.run(maskSoma, "Maximum...", "stack radius="+str(int(R*1)))

if updateSomaMask :
	IJ.setThreshold(maskSoma, 128, 255)
	IJ.run(maskSoma, "Create Selection", "");
	IJ.resetThreshold(maskSoma)
	somaRoiAux = maskSoma.getRoi()
	maskSoma.killRoi()
	IJ.setTool("brush")
	imp0.setRoi(somaRoiAux)
	imp0.show()
	WaitForUserDialog(" please use the brush tool to correct the soma selection").show()
	imp0.hide()
	somaRoiAux = imp0.getRoi()
	imp0.killRoi()
	# create a new maskSoma
	ip = maskSoma.getProcessor().createProcessor(imp0.getWidth(), imp0.getHeight() )
	ip.setValue(255)
	ip.fill(somaRoiAux)
	maskSoma = ImagePlus("new mask Soma", ip)

# create a skeleton of the mask
skelRaw = Duplicator().run(mask0)
IJ.run(skelRaw, "Skeletonize (2D/3D)", "");

# print the soma mask on the skeleton image (AND)
skeletonImp = Duplicator().run(skelRaw)
skeletonImp = ImageCalculator().run('OR create stack', skeletonImp, maskSoma)

#skeletonImp.show()


	
########################################
# build a skeleton #####################

IJ.log("building skeleton data structure (analyze skeleton plugin)...")

skel = AnalyzeSkeleton_();
skel.setup("", skeletonImp);
pruneCycleMode = AnalyzeSkeleton_.NONE
pruneEndPoints = False
calcShortestPath = False
silent = True
verbose = False
simpleSkeletonResult = skel.run(pruneCycleMode, pruneEndPoints, calcShortestPath, skeletonImp, silent, verbose)


drawLongestShortestPath = False
stackSkelClass = skel.getResultImage( drawLongestShortestPath )
impSkelClass = ImagePlus('skeleton', stackSkelClass )
#impSkelClass.show()

# select the largest graph (i.e with the most slabs voxels)
graphs = simpleSkeletonResult.getGraph()
maxGraph=None
maxPixNumber=0
pixNumberPerGrah = simpleSkeletonResult.getSlabs()
for graph, pixNumber in zip(graphs, pixNumberPerGrah) :
	if pixNumber>maxPixNumber :
		maxGraph = graph
		maxPixNumber = pixNumber



####################################
# analyze the skeleton #############

IJ.log("Analyze skeleton")

IJ.log("building skeleton data structure (analyze skeleton class)...")

# set the skeleton data structure in the analysis class 
skeletonAnalyser = SkeletonAnalyser(maxGraph)
	
# filter out the end branch shorter than threshold
skeletonAnalyser.setVoxelSize([pWidth, pWidth, pDepth])

IJ.log("prune data structure (analyze skeleton class)...")
removedEdges=[]
if minBranchLength>0 :
	removedEdges = skeletonAnalyser.cutLeafEdgesShorterThan(minBranchLength);

soma = skeletonAnalyser.getLargestJunction()
somaPos = skeletonAnalyser.getCenterOfJunction(soma)
somaEdge = skeletonAnalyser.getEdgesStartingAtJunction(soma)
nStartEdge = len(somaEdge) 

# build shortest path between each leaf and soma 


# associate each shortest path to a process

IJ.log("measure longest shortest path ...")

leafs = skeletonAnalyser.getLeafs()
somaToLeafPaths = []
pathId = 0
processPathId = [0]*nStartEdge

count=0
nLeafs = len(leafs)
for leaf in leafs:
	count += 1
	IJ.log("Process leaf "+str(count)+"/"+str(nLeafs))
	if skeletonAnalyser.junctionsEqual(leaf, soma):
		continue
		
	path = skeletonAnalyser.getShortestPath(leaf, soma)
	if path == None :
		continue
		
	pathId +=1	
	pathData={}
	pathData["path"]=path
	pathData["pathId"] = pathId
	
	length = skeletonAnalyser.getLengthAlongPath(path)
	lengthInSoma = skeletonAnalyser.getDistanceBetweenStartingPointAndJunctionCenter(path[0])
	pathData["length"] = length - lengthInSoma
	
	pStart = path[0].getSlabs()[0]
	pEnd = SkeletonAnalyser.getCenterOfJunction( path[-1].getV2() )
	pathData["euclidLength"] = skeletonAnalyser.getPointDistance(pStart, pEnd)
	
	pathData["lengthRatio"] = pathData["length"]/pathData["euclidLength"]

	
	for edge, processId in zip(somaEdge, range(nStartEdge)):
		if skeletonAnalyser.edgesEqual( edge, path[-1] ): 
			pathData["processId"]= processId
			pathData["processPathId"] = processPathId[processId]
			pathData["name"] = "process-"+str(processId+1)+"-"+str(processPathId[processId]+1)
			
			processPathId[processId] += 1
			
	somaToLeafPaths.append( pathData )

nProcesses = 0
for numPath in processPathId :
	if numPath>0 :
		nProcesses += 1

# determine the longest path in each process
maxLength = [0]*nStartEdge
for pathData in somaToLeafPaths :
	length = pathData["length"]
	processId = pathData["processId"]
	if length>maxLength[processId] :
		maxLength[processId] = length

for pathData in somaToLeafPaths :
	length = pathData["length"]
	processId = pathData["processId"]
	if length==maxLength[processId] :
		pathData["isLongest"] = True
	else:
		pathData["isLongest"] = False
		
	
	
IJ.log("Sholl analysis ...")
		
# create a roi for the soma
ip = maskSoma.getProcessor().convertToFloatProcessor()
wand = Wand(ip)
wand.autoOutline(somaPos.x, somaPos.y, 255,255, Wand.EIGHT_CONNECTED)
roiSoma=None
if not wand.npoints == 0 :
	roiSoma = PolygonRoi(wand.xpoints, wand.ypoints, wand.npoints, PolygonRoi.POLYGON)
	roiSoma.setStrokeColor(Color.blue)	

SomaAreaPix = soma.getPoints().size()
somaRPix = math.sqrt( SomaAreaPix/math.pi )



# Sholl measures: find number of edge cutting the circle of radius R
# for each edge go through the points and measures the distance to the soma
# 	measure 1: count +1 every time we crosse the circle
#	measure 2: count +1 if the edge crosss at least once the circle
def getDistances(edge, p0):
	
	dist = []
	
	p = skeletonAnalyser.getCenterOfJunction( edge.getV1() )
	dist.append(skeletonAnalyser.getPointDistance(p0,p))
	
	slab = edge.getSlabs()
	for p in slab : 
		dist.append(skeletonAnalyser.getPointDistance(p0,p))
	
	p = skeletonAnalyser.getCenterOfJunction( edge.getV2() )
	dist.append(skeletonAnalyser.getPointDistance(p0,p))

	return dist


def sholl(edges, thresh):
	mes1 = 0
	mes2 = 0
	
	for edge in edges:
		dList = getDistances(edge, somaPos)
		statusList = [d>thresh for d in dList]
		#print statusList
		prevStatus = statusList[0]
		incMes2=0
		for status in statusList[1:]:
			if not prevStatus == status :
				mes1 += 1 
				incMes2=1
			prevStatus=status
		mes2 += incMes2
	
	return mes1, mes2;
	
edges = skeletonAnalyser.getAllEdges()


sholl1=[]
sholl2=[]
for i in range(2,5):
	val1, val2 = sholl(edges, somaRPix*i*pWidth)
	sholl1.append(val1)
	sholl2.append(val2)


	


###############################################################################
# display soma, processes, pruned branches, and longest shortest path #########

IJ.log("Visualize results...")


# create rois for visualisation of results
def getPathAsRoi(path, excludeFirstJunction=True, excludeLastJunction=False):

	if path==None :
		return None
		
	x = []
	y = []
	for edge in path:
		p = SkeletonAnalyser.getCenterOfJunction( edge.getV1() )
		x.append(p.x+0.5)
		y.append(p.y+0.5)
		
		slab = edge.getSlabs()
		for p in slab:
			x.append(p.x+0.5)
			y.append(p.y+0.5)

		p = SkeletonAnalyser.getCenterOfJunction( edge.getV2() )
		x.append(p.x+0.5)
		y.append(p.y+0.5)
	
	if excludeFirstJunction :
		x = x[1:]	
		y = y[1:]

	if excludeLastJunction :
		x = x[:-1]	
		y = y[:-1]

			
	return PolygonRoi(x,y,PolygonRoi.POLYLINE)


	


ov = Overlay()

excludeFirstPoint = False
excludeLastPoint = True
for pathData in somaToLeafPaths :
	path = pathData["path"]
	roi = getPathAsRoi(path, excludeFirstPoint, excludeLastPoint)
	roi.setName( pathData["name"] )
	pathData["roi"] = roi 

for pathData in somaToLeafPaths :
	if not pathData["isLongest"]:
		roi = pathData["roi"].clone()
		roi.setStrokeColor(Color.blue)
		ov.add(roi)

for pathData in somaToLeafPaths :
	if pathData["isLongest"]:
		roi = pathData["roi"].clone()
		roi.setStrokeColor(Color.green)
		ov.add(roi)

excludeFirstPoint = True
for edge in removedEdges :
	path = [edge]
	roi = getPathAsRoi(path, excludeFirstPoint,excludeLastPoint)
	roi.setStrokeColor(Color.red)
	ov.add(roi)

for i in range(2,5):
	rCirc = i*somaRPix
	circRoi = OvalRoi(somaPos.x-rCirc, somaPos.y-rCirc, rCirc*2, rCirc*2)
	circRoi.setStrokeColor( Color.cyan )
	ov.add(circRoi)
ov.add(roiSoma)

impResults = Duplicator().run(imp0)
impResults.setOverlay(ov)
#impResults.show()
#impSkelClass.show()

###################################################
# create an enlarged result image #################

margin=50 # in pixel
xm = min(0, somaPos.x-4*somaRPix-margin)
width = imp0.getWidth()
xM = max( width , somaPos.x+4*somaRPix+margin)
ym = min(0, somaPos.y-4*somaRPix-margin)
height = imp0.getWidth()
yM = max( height , somaPos.y+4*somaRPix+margin)

newWidth = int(xM-xm)
newHeight = int(yM-ym)
dx =  int(max(0, -xm))
dy =  int(max(0, -ym))

ipResults = imp0.getProcessor().createProcessor(newWidth, newHeight)
ipResults.setValue(255)
ipResults.fill()

ipResults.insert( imp0.getProcessor() ,dx ,dy )

impResult2 = ImagePlus( 'enlarged_' + impResults.getTitle() , ipResults )

ov2 = Overlay()
for i in range( ov.size() ):
	roi = ov.get(i).clone()
	rect = roi.getBounds()
	roi.setLocation( rect.x + dx , rect.y + dy )
	ov2.add(roi)

impResult2.setOverlay( ov2 )
impResult2.show()


###############################################
# add shortest path to the roi manager ########

roiManager = RoiManager.getInstance()
if roiManager==None :
	roiManager = RoiManager()
roiManager.reset()
roiManager.runCommand(impResults,"Show None");
for pathData in somaToLeafPaths :
	roi = pathData["roi"].clone()
	roi.setStrokeColor(Color.yellow)
	roiManager.addRoi(roi)


###############################################
# number of end point #########################

nEndPoints = leafs.size()
if nStartEdge < 2 : # the soma is a leaf but not a process endpoint
	nEndPoints = nEndPoints-1
	
##################################################
# create results table to visualize the data #####

def getResultsTable(name, reset=False):
	win = WindowManager.getWindow(name)
	if ( (win!=None) & isinstance(win,TextWindow) ) :	
		rt = win.getTextPanel().getResultsTable();
		if reset:
			rt.reset()
	else:
		rt = ResultsTable();
	return rt

# cell measures
rt_cellInfo_Name = "Neuron Analysis - cell Information"
rt_cellInfo = getResultsTable(rt_cellInfo_Name)

rt_cellInfo.incrementCounter()
rt_cellInfo.addValue("Folder name", folderName )
rt_cellInfo.addValue("Image name", 	imp0Name )
rt_cellInfo.addValue("cell type", 	folderName.split(" ")[-1] )
rt_cellInfo.addValue("# processes", nProcesses )
rt_cellInfo.addValue("# end points", nEndPoints )
rt_cellInfo.addValue("Somar R", 	somaRPix*pWidth)
rt_cellInfo.addValue("Sholl 2R", 	sholl1[0])
rt_cellInfo.addValue("Sholl 3R", 	sholl1[1])
rt_cellInfo.addValue("Sholl 4R", 	sholl1[2])
rt_cellInfo.addValue("Process branching", nEndPoints/float(nProcesses) )

rt_cellInfo.show(rt_cellInfo_Name)

# process measures
rt_processInfo_Name = "Neuron Analysis - process Information"
rt_processInfo = getResultsTable(rt_processInfo_Name)

for pathData in somaToLeafPaths :	
	if pathData["isLongest"]:
		rt_processInfo.incrementCounter()
		rt_processInfo.addValue("Folder name", 				folderName )
		rt_processInfo.addValue("Image name", 				imp0Name )
		rt_processInfo.addValue("Process Id", 				pathData["processId"]+1 )
		rt_processInfo.addValue("Longest path name",		pathData["name"] )
		rt_processInfo.addValue("process length", 			pathData["length"] )
		rt_processInfo.addValue("process euclidean length", pathData["euclidLength"] )
		rt_processInfo.addValue("length ratio", 			pathData["lengthRatio"] )

rt_processInfo.show(rt_processInfo_Name)




#if saveResults :
	IJ.log("Saving results ...")
	basename = folderName # os.path.splitext(imp0.getTitle())[0]
	name_ffile = os.path.splitext(imp0.getTitle())[0]
	savePath = filename.getParent()
	
	saveNameRoiSet = os.path.join( savePath,name_ffile +"_Roiset.zip" )
	roiManager = RoiManager.getInstance()
	roiManager.runCommand(imp0,"Deselect")
	roiManager.runCommand("Save", saveNameRoiSet )
	
	saveNameCellInfo = os.path.join( savePath, name_ffile +"_CellInfo.xls" )
	IJ.selectWindow( rt_cellInfo_Name )
	IJ.saveAs("Results", saveNameCellInfo )
	rt_cellInfo.saveAs(saveNameCellInfo)
	
	saveNameProcessInfo = os.path.join( savePath, name_ffile +"_ProcessInfo.xls" )
	rt_processInfo.saveAs(saveNameProcessInfo)
	IJ.selectWindow( rt_processInfo_Name )
	IJ.saveAs("Results", saveNameProcessInfo )

	IJ.selectWindow(impResult2.getTitle() )
	savenameResultImage = os.path.join( savePath, name_ffile +"_results.tif" )
	IJ.saveAs("Tiff", savenameResultImage )
	
IJ.log("done!")

