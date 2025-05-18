import os
import time
import opensim as osim

from motion_data_computing.setup_generation.generate_grf import generate_complete_grf
from motion_data_computing.setup_generation.create_external_loads import create_external_loads_file
from motion_data_computing.setup_generation.create_inverse_dynamics_setup import create_inverse_dynamics_setup

def run_inverse_dynamics(setup_file_path, grf_mot_file):
    """Run inverse dynamics using the provided setup file path."""
    print(f"Running Inverse Dynamics with setup file: {setup_file_path}")
    
    if not os.path.exists(setup_file_path):
        raise FileNotFoundError(f"Setup file not found: {setup_file_path}")
    
    # Get the absolute path of the setup file's directory
    setup_dir = os.path.dirname(os.path.abspath(setup_file_path))
    print(f"Setting up directory: {setup_dir}")
    
    # Load the Inverse Dynamics Tool
    id_tool = osim.InverseDynamicsTool(setup_file_path)
    
    def resolve_file_path(filename, setup_dir):
        """Helper function to resolve file paths with fallback locations"""
        # First try path relative to setup file
        primary_path = os.path.abspath(os.path.join(setup_dir, filename))
        if os.path.exists(primary_path):
            return primary_path
            
        # Fallback to package data directory
        package_data_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../../data"))
        secondary_path = os.path.join(package_data_dir, os.path.basename(filename))
        if os.path.exists(secondary_path):
            return secondary_path
            
        # If not found in either location
        raise FileNotFoundError(
            f"File not found at either location:\n"
            f"1. {primary_path}\n"
            f"2. {secondary_path}"
        )
    
    # Resolve model file path
    model_file = resolve_file_path(id_tool.getModelFileName(), setup_dir)
    id_tool.setModelFileName(model_file)
    print(f"Model file set to: {model_file}")
    
    # Resolve coordinates file path
    coords_file = resolve_file_path(id_tool.getCoordinatesFileName(), setup_dir)
    id_tool.setCoordinatesFileName(coords_file)
    
    # Handle GRF data carefully
    ext_loads_file = os.path.abspath(os.path.join(setup_dir, id_tool.getExternalLoadsFileName()))
    
    if not os.path.exists(grf_mot_file):
        raise FileNotFoundError(f"GRF data file not found: {grf_mot_file}")
    
    # Verify or recreate external loads file if necessary
    if not os.path.exists(ext_loads_file):
        print("Creating new external loads file...")
        # create_external_loads_file(ext_loads_file, grf_mot_file)
    
    id_tool.setExternalLoadsFileName(ext_loads_file)
    
    # Set results directory
    results_dir = os.path.abspath(os.path.join(setup_dir, "ResultsInverseDynamics"))
    os.makedirs(results_dir, exist_ok=True)
    id_tool.setResultsDir(results_dir)
    
    # Run the inverse dynamics tool
    print("Running Inverse Dynamics...")
    try:
        if not id_tool.run():
            raise RuntimeError("Inverse Dynamics computation failed")
    except Exception as e:
        raise RuntimeError(f"Inverse Dynamics failed: {str(e)}")
    
    # Process results
    output_file = os.path.join(results_dir, id_tool.getOutputGenForceFileName())
    if not os.path.exists(output_file):
        raise FileNotFoundError(f"Results file not found: {output_file}")
    
    print(f"Inverse Dynamics completed successfully. Results saved in: {output_file}")
    
    return output_file

def extract_base_output_path(ik_file_path):
    """
    Extract the base output path from an IK file path.
    
    For a path like "/home/ubuntu/injury_detection/risk_analysis_package/data/KD_injured/trc_data/trials/KD_injured_ik.mot",
    returns "/home/ubuntu/injury_detection/risk_analysis_package/data/KD_injured"
    
    Args:
        ik_file_path: Path to the IK motion file
        
    Returns:
        Base output path
    """
    # Split the path into components
    path_parts = ik_file_path.split('/')
    
    # Find the index of 'data' in the path
    try:
        data_index = path_parts.index('data')
        
        # Extract up to one component after 'data'
        if data_index + 1 < len(path_parts):
            base_output_parts = path_parts[:data_index + 2]
            base_output_path = '/'.join(base_output_parts)
            return base_output_path
    except ValueError:
        # If 'data' is not in the path, return the directory containing the IK file
        return os.path.dirname(ik_file_path)
        
    # Fallback if the expected structure is not found
    return os.path.dirname(ik_file_path)

def run_inverse_dynamics_pipeline(model_path: str ,ik_mot_path: str, marker_file_path: str) -> str:
    """
    Runs the full inverse dynamics pipeline:
    1. Generate GRF
    2. Create External Loads
    3. Generate Setup XML
    4. Run ID
    
    Args:
        ik_mot_path: Path to the output IK .mot file
        marker_file_path: Path to the original .trc marker file used for IK
    
    Returns:
        Path to the inverse dynamics output file
    """
    # Configurable paths
    # model_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/bsm.osim"
    # output_dir = "/home/ubuntu/injury_detection/risk_analysis_package/data"
    output_dir = extract_base_output_path(ik_mot_path)
    
    setup_name = os.path.splitext(os.path.basename(marker_file_path))[0]
    body_weight = 75 * 9.81  # N

    # Extract time range from marker file
    marker_data = osim.MarkerData(marker_file_path)
    time_range = (marker_data.getStartFrameTime(), marker_data.getLastFrameTime())

    # Step 1: Generate GRF
    ik_table = osim.TimeSeriesTable(ik_mot_path)
    complete_grf = generate_complete_grf(ik_table, body_weight)
    grf_mot_file = os.path.join(output_dir, f"{setup_name}_improved_grf.sto")
    osim.STOFileAdapter().write(complete_grf, grf_mot_file)
    print(f"[INFO] GRF saved to: {grf_mot_file}")

    # Step 2: Create External Loads XML
    ext_loads_file = os.path.join(output_dir, f"{setup_name}_grf.xml")
    create_external_loads_file(ext_loads_file, grf_mot_file)
    print(f"[INFO] External Loads created at: {ext_loads_file}")

    # Step 3: Create Inverse Dynamics Setup XML
    setup_file = create_inverse_dynamics_setup(
        output_dir=output_dir,
        setup_name=setup_name,
        model_file=model_path,
        coordinates_file=ik_mot_path,
        grf_mot_file=grf_mot_file,
        time_range=time_range,
        lowpass_cutoff=6.0
    )
    print(f"[INFO] ID setup file created at: {setup_file}")

    # Step 4: Run Inverse Dynamics
    print("[INFO] Running Inverse Dynamics...")
    start_time = time.time()
    output_file = run_inverse_dynamics(setup_file, grf_mot_file)
    print(f"[INFO] Inverse Dynamics completed. Output file: {output_file}")
    print(f"[INFO] Total time taken for running ID tool: {time.time() - start_time:.2f} seconds")

    return output_file, ext_loads_file