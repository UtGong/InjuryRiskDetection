import opensim as osim

# Load the model.
model = osim.Model('/home/ubuntu/injury_detection/jupyter_notebooks/risk/motionConfig/bsm.osim')

# Define a StaticOptimization object.
so = osim.StaticOptimization()

# Set start and end times for the analysis.
start_time = 0.3
end_time = 1.5
so.setStartTime(start_time)
so.setEndTime(end_time)

# Create analyze tool for static optimization.
so_analyze_tool = osim.AnalyzeTool()
so_analyze_tool.setName("SO")

# Set model file, motion files and external load file names.
so_analyze_tool.setModelFilename("/home/ubuntu/injury_detection/jupyter_notebooks/risk/motionConfig/bsm.osim")
so_analyze_tool.setCoordinatesFileName("/home/ubuntu/injury_detection/jupyter_notebooks/risk/motionConfig/01_01_ik.mot")
so_analyze_tool.setExternalLoadsFileName("/home/ubuntu/injury_detection/jupyter_notebooks/risk/motionConfig/0101_Setup_InverseDynamics.xml")

# Add analysis.
so_analyze_tool.updAnalysisSet().cloneAndAppend(so)

# Configure analyze tool.
so_analyze_tool.setReplaceForceSet(False)
so_analyze_tool.setStartTime(start_time)
so_analyze_tool.setFinalTime(end_time)

# Directory where results are stored.
so_analyze_tool.setResultsDir("SO_Results")

# Print configuration of analyze tool to a xml file.
so_analyze_tool.printToXML("SO_AnalyzeTool_setup.xml")

# Load configuration and run the analyses. 
so_analyze_tool = osim.AnalyzeTool("SO_AnalyzeTool_setup.xml", True)

so_analyze_tool.run()