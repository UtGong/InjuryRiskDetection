import opensim as osim
import os
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional


def create_ik_setup_file(
    model_file_path: str,
    marker_file_path: str,
    output_motion_path: str,
    setup_file_path: str,
    time_range: Tuple[float, float] = (0.0, 1.0),
    sample_setup_path: Optional[str] = None
) -> str:
    """
    Create an OpenSim IK setup file based on a sample XML or from scratch.
    
    Args:
        model_file_path: Path to the .osim model file
        marker_file_path: Path to the .trc marker file
        output_motion_path: Path for the output .mot file
        setup_file_path: Where to save the generated setup file
        time_range: Tuple with start and end time (default: (0.0, 1.0))
        sample_setup_path: Optional path to a sample setup XML to use as template
        
    Returns:
        Path to the created setup file
    """
    if sample_setup_path and os.path.exists(sample_setup_path):
        # Use sample file as template
        tree = ET.parse(sample_setup_path)
        root = tree.getroot()
        
        # Update model file path
        model_elem = root.find(".//model_file")
        if model_elem is not None:
            model_elem.text = model_file_path
            
        # Update marker file path
        marker_elem = root.find(".//marker_file")
        if marker_elem is not None:
            marker_elem.text = marker_file_path
            
        # Update output motion file path
        output_elem = root.find(".//output_motion_file")
        if output_elem is not None:
            output_elem.text = output_motion_path
            
        # Update time range
        time_range_elem = root.find(".//time_range")
        if time_range_elem is not None:
            time_range_elem.text = f" {time_range[0]} {time_range[1]}"
            
        # Write the updated XML
        tree.write(setup_file_path)
    else:
        # Create a basic setup file from scratch
        ik_tool = osim.InverseKinematicsTool()
        ik_tool.setName("ik_analysis")
        ik_tool.set_model_file(model_file_path)
        ik_tool.set_marker_file(marker_file_path)
        ik_tool.set_output_motion_file(output_motion_path)
        ik_tool.set_time_range(0, time_range[0])
        ik_tool.set_time_range(1, time_range[1])
        ik_tool.set_constraint_weight(20)
        ik_tool.set_accuracy(1e-5)
        
        ik_tool.print(setup_file_path)
    return setup_file_path


def get_trc_marker_info(marker_file_path: str) -> dict:
    """
    Get information about markers in a TRC file.
    
    Args:
        marker_file_path: Path to the .trc marker file
        
    Returns:
        Dictionary with marker information
    """
    marker_data = osim.MarkerData(marker_file_path)
    
    marker_info = {
        "num_markers": marker_data.getNumMarkers(),
        "num_frames": marker_data.getNumFrames(),
        "time_range": (marker_data.getStartFrameTime(), marker_data.getLastFrameTime()),
        "marker_names": []
    }
    
    # # Get all marker names
    # for i in range(marker_data.getNumMarkers()):
    #     marker_info["marker_names"].append(marker_data.getMarkerNames(i))
    
    # Get all marker names
    marker_info["marker_names"] = [marker_data.getMarkerNames().get(i) for i in range(marker_data.getMarkerNames().size())]

    return marker_info


def check_markers_exist(marker_file_path: str, required_markers: List[str]) -> List[str]:
    """
    Check if required markers exist in the TRC file.
    
    Args:
        marker_file_path: Path to the .trc marker file
        required_markers: List of marker names to check
        
    Returns:
        List of missing marker names
    """
    marker_data = osim.MarkerData(marker_file_path)
    missing_markers = []
    
    for marker_name in required_markers:
        if marker_data.getMarkerIndex(marker_name) == -1:
            missing_markers.append(marker_name)
            
    return missing_markers


def generate_output_path(marker_file_path: str) -> str:
    """
    Generate output motion file path based on marker file name.
    
    Args:
        marker_file_path: Path to the .trc marker file
        
    Returns:
        Path for the output motion file
    """
    # Get directory and filename without extension
    directory = os.path.dirname(marker_file_path)
    filename = os.path.basename(marker_file_path)
    base_name = os.path.splitext(filename)[0]
    
    # new_directory is directory without the last two split with "/"
    new_directory = os.path.dirname(os.path.dirname(directory))
    
    
    # Create output filename with _ik.mot suffix
    output_filename = f"{base_name}_ik.mot"
    output_path = os.path.join(new_directory, output_filename)
    print(f"[INFO] ---------Generated output path: {output_path}")
    
    return output_path


def run_inverse_kinematics(
    setup_file_path: str,
    verify_files: bool = True
) -> bool:
    """
    Run OpenSim Inverse Kinematics analysis.
    
    Args:
        setup_file_path: Path to the IK setup file
        verify_files: Whether to verify files exist before running
        
    Returns:
        True if successful, False otherwise
    """
    if verify_files:
        # Extract file paths from setup
        tree = ET.parse(setup_file_path)
        root = tree.getroot()
        
        model_path = root.find(".//model_file").text
        marker_path = root.find(".//marker_file").text
        
        # Check files exist
        if not os.path.exists(model_path):
            print(f"ERROR: Model file not found: {model_path}")
            return False
            
        if not os.path.exists(marker_path):
            print(f"ERROR: Marker file not found: {marker_path}")
            return False
    
    try:
        # Create and run IK tool
        inverse_kinematics_tool = osim.InverseKinematicsTool(setup_file_path)
        
        # Print configuration
        print("Name:", inverse_kinematics_tool.getName())
        print("Model File:", inverse_kinematics_tool.get_model_file())
        print("Marker File:", inverse_kinematics_tool.get_marker_file())
        print("Output File:", inverse_kinematics_tool.get_output_motion_file())
        print("Accuracy:", inverse_kinematics_tool.get_accuracy())
        print(f"Time Range: [{inverse_kinematics_tool.get_time_range(0)}, {inverse_kinematics_tool.get_time_range(1)}]")
        print("Constraint Weight:", inverse_kinematics_tool.get_constraint_weight())
        
        # Run with error catching
        result = inverse_kinematics_tool.run()
        return True
    except Exception as e:
        print(f"Error running IK: {e}")
        return False
    
def run_ik_from_marker_file(marker_file_path: str) -> str:
    """
    Given a marker (.trc) file path, run IK and return the output .mot file path.
    Uses default base_dir, model path, and optional sample XML if available.
    """
    base_dir = '/home/ubuntu/injury_detection/risk_analysis_package/data'
    print(f"[INFO] Base directory for output: {base_dir}")
    model_file = os.path.join(base_dir, 'bsm.osim')
    sample_setup = os.path.join(base_dir, 'sample_IK.xml')

    output_file = generate_output_path(marker_file_path)
    setup_filename = os.path.splitext(os.path.basename(marker_file_path))[0] + "_setup_IK.xml"
    setup_file = os.path.join(os.path.dirname(output_file), setup_filename)

    try:
        marker_info = get_trc_marker_info(marker_file_path)
        time_range = marker_info['time_range']
        test_time_range = (time_range[0], min(time_range[0] + 0.1, time_range[1]))
    except Exception as e:
        raise RuntimeError(f"Failed to load marker file or extract time range: {e}")

    # Generate setup XML
    create_ik_setup_file(
        model_file_path=model_file,
        marker_file_path=marker_file_path,
        output_motion_path=output_file,
        setup_file_path=setup_file,
        time_range=test_time_range,
        sample_setup_path=sample_setup if os.path.exists(sample_setup) else None
    )

    print(f"[INFO] Running IK using setup file: {setup_file}")
    success = run_inverse_kinematics(setup_file)

    if not success:
        raise RuntimeError("Inverse kinematics failed.")
    
    print(f"[INFO] IK completed successfully. Output file: {output_file}")
    return output_file



def main():
    """
    Main function to demonstrate the IK workflow.
    """
    # Define paths
    base_dir = '/home/ubuntu/injury_detection/risk_analysis_package/data'
    model_file = os.path.join(base_dir, 'bsm.osim')
    marker_file = os.path.join(base_dir, 'output_motion.trc')
    
    # Generate output file path based on marker file name
    output_file = generate_output_path(marker_file)
    
    setup_file = os.path.join(base_dir, 'generated_setup_IK.xml')
    sample_setup = os.path.join(base_dir, 'setup_IK.xml')  # Optional
    
    # Check if input files exist
    print(f"Model file exists: {os.path.exists(model_file)}")
    print(f"Marker file exists: {os.path.exists(marker_file)}")
    print(f"Output will be written to: {output_file}")
    
    # Get marker information
    try:
        marker_info = get_trc_marker_info(marker_file)
        print(f"Number of markers in TRC: {marker_info['num_markers']}")
        print(f"Number of frames: {marker_info['num_frames']}")
        print(f"Time range: {marker_info['time_range'][0]} to {marker_info['time_range'][1]}")
        
        # Check for required markers (customize as needed)
        required_markers = ["R.ASIS", "L.ASIS", "V.Sacral"]
        missing_markers = check_markers_exist(marker_file, required_markers)
        
        if missing_markers:
            print("WARNING: The following markers are missing:")
            for marker in missing_markers:
                print(f"  - {marker}")
            print("\nAvailable markers in TRC file:")
            for marker in marker_info["marker_names"]:
                print(f"  - {marker}")
                
            # Prompt user about continuing despite missing markers
            response = input("Continue with IK despite missing markers? (y/n): ")
            if response.lower() != 'y':
                print("Exiting as requested.")
                return
    except Exception as e:
        print(f"Error reading marker file: {e}")
        return
    
    # Create a setup file with appropriate time range from the marker data
    time_range = marker_info['time_range']
    # Optionally use a shorter time range for testing
    test_time_range = (time_range[0], min(time_range[0] + 0.1, time_range[1]))
    
    # Create setup file (with sample if available, otherwise create from scratch)
    if os.path.exists(sample_setup):
        create_ik_setup_file(
            model_file,
            marker_file,
            output_file,
            setup_file,
            test_time_range,
            sample_setup
        )
    else:
        create_ik_setup_file(
            model_file,
            marker_file,
            output_file,
            setup_file,
            test_time_range
        )
    
    print(f"Generated setup file: {setup_file}")
    
    # Run IK
    success = run_inverse_kinematics(setup_file)
    
    if success:
        print("Inverse kinematics completed successfully!")
        print(f"Output motion file: {output_file}")
    else:
        print("Inverse kinematics failed.")


if __name__ == "__main__":
    main()