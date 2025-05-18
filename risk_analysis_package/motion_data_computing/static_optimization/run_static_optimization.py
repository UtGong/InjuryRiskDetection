import os
import time
import opensim as osim

def run_static_optimization(model_file, coordinates_file, ext_loads_file,
                            start_time=0, end_time=2.4,
                            results_dir="SO_Results", setup_xml="SO_AnalyzeTool_setup.xml"):
    """
    Configure and run Static Optimization using OpenSim's AnalyzeTool.
    
    Parameters:
        model_file (str): Path to the OpenSim model file (.osim).
        coordinates_file (str): Path to the coordinate/motion file (.mot or .sto).
        ext_loads_file (str): Path to the ExternalLoads XML file.
        start_time (float): Start time for the analysis.
        end_time (float): End time for the analysis.
        results_dir (str): Directory where results are stored.
        setup_xml (str): XML file name where the static optimization configuration is saved.
    
    Returns:
        str: The results directory where the analysis outputs are stored.
    """
    # Create a StaticOptimization analysis object.
    so = osim.StaticOptimization()
    
    # Create an AnalyzeTool for static optimization.
    so_analyze_tool = osim.AnalyzeTool()
    so_analyze_tool.setName("SO")
    
    # Set the model file, coordinates file, and external loads file.
    so_analyze_tool.setModelFilename(model_file)
    so_analyze_tool.setCoordinatesFileName(coordinates_file)
    so_analyze_tool.setExternalLoadsFileName(ext_loads_file)
    
    # Add the StaticOptimization analysis to the AnalyzeTool's analysis set.
    so_analyze_tool.updAnalysisSet().cloneAndAppend(so)
    
    # Configure the analyze tool.
    so_analyze_tool.setReplaceForceSet(False)
    so_analyze_tool.setStartTime(start_time)
    so_analyze_tool.setFinalTime(end_time)
    
    # Ensure results directory exists.
    os.makedirs(results_dir, exist_ok=True)
    so_analyze_tool.setResultsDir(results_dir)
    
    # Write the configuration to an XML file.
    so_analyze_tool.printToXML(setup_xml)
    print(f"Static Optimization setup written to: {setup_xml}")
    
    # Reload the configuration (ensuring it gets read correctly).
    so_analyze_tool = osim.AnalyzeTool(setup_xml, True)
    
    # Run the analysis.
    print("[INFO] Running Static Optimization...")
    start_run_time = time.time()
    so_analyze_tool.run()
    run_time = time.time() - start_run_time
    print(f"[INFO] Total time taken for running SO tool: {run_time:.2f} seconds.")
    print("[INFO] Static Optimization completed.")
    
    return results_dir
