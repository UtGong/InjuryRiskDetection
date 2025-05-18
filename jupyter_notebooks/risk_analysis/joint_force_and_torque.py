import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_DEBUG_PLUGINS'] = '0'
import numpy as np
import matplotlib.pyplot as plt
import opensim as osim
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def plot_joint_loads(time, forces, torques):
    """
    Plot joint forces and torques over time.
    
    Parameters:
    - time (array-like): Time array.
    - forces (dict): Dictionary of forces, where keys are joint names and values are the force data.
    - torques (dict): Dictionary of torques, where keys are joint names and values are the torque data.
    """
    
    # Create figure for joint forces and torques
    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    
    # Plot forces
    axs[0].set_title('Joint Forces over Time')
    for joint, force in forces.items():
        axs[0].plot(time, force, label=joint)
    axs[0].set_xlabel('Time (s)')
    axs[0].set_ylabel('Force (N)')
    axs[0].legend(loc='best')

    # Plot torques
    axs[1].set_title('Joint Torques over Time')
    for joint, torque in torques.items():
        axs[1].plot(time, torque, label=joint)
    axs[1].set_xlabel('Time (s)')
    axs[1].set_ylabel('Torque (Nm)')
    axs[1].legend(loc='best')
    
    # Show the plot
    plt.tight_layout()
    plt.show()

def extract_joint_forces_torques(setup_file_path, plot=False):
    """
    Run inverse dynamics and extract joint forces and torques.
    """
    print(f"Extracting joint forces and torques from setup file: {setup_file_path}")
    if not os.path.exists(setup_file_path):
        raise FileNotFoundError(f"Setup file not found: {setup_file_path}")
    
    setup_dir = os.path.dirname(setup_file_path)
    
    print("Running Inverse Dynamics...")
    
    # Load tool and verify files
    id_tool = osim.InverseDynamicsTool(setup_file_path)
    
    # Verify model file
    model_file = os.path.abspath(os.path.join(setup_dir, id_tool.getModelFileName()))
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"Model file not found: {model_file}")
    id_tool.setModelFileName(model_file)
    
    # Verify coordinates file
    coords_file = os.path.abspath(os.path.join(setup_dir, id_tool.getCoordinatesFileName()))
    if not os.path.exists(coords_file):
        raise FileNotFoundError(f"Coordinates file not found: {coords_file}")
    id_tool.setCoordinatesFileName(coords_file)
    
    # Handle GRF data carefully
    grf_mot_file = os.path.abspath(os.path.join(setup_dir, "synthetic_grf.sto"))
    ext_loads_file = os.path.abspath(os.path.join(setup_dir, id_tool.getExternalLoadsFileName()))
    
    if not os.path.exists(grf_mot_file):
        raise FileNotFoundError(f"GRF data file not found: {grf_mot_file}")
    
    # Verify or recreate external loads file
    if not os.path.exists(ext_loads_file):
        print("Creating new external loads file...")
        create_external_loads_file(ext_loads_file, grf_mot_file)
    
    # Verify the GRF file has required columns
    try:
        grf_table = osim.TimeSeriesTable(grf_mot_file)
        required_columns = [
            'ground_force_v', 'ground_force_p', 'ground_torque_',
            '1_ground_force_v', '1_ground_force_p', '1_ground_torque_'
        ]
        missing = [col for col in required_columns if not any(col in label for label in grf_table.getColumnLabels())]
        if missing:
            raise ValueError(f"GRF file missing required columns: {missing}")
    except Exception as e:
        raise RuntimeError(f"Invalid GRF data: {str(e)}")
    
    id_tool.setExternalLoadsFileName(ext_loads_file)
    
    # Set results directory
    results_dir = os.path.abspath(os.path.join(setup_dir, "ResultsInverseDynamics"))
    os.makedirs(results_dir, exist_ok=True)
    id_tool.setResultsDir(results_dir)
    
    # Run the tool
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
    
    print("Inverse Dynamics completed successfully.")
    table = osim.TimeSeriesTable(output_file)
    time = np.array(table.getIndependentColumn())
    
    forces = {}
    torques = {}
    peaks = {'forces': {}, 'torques': {}}
    
    for label in table.getColumnLabels():
        data = np.array(table.getDependentColumn(label)).flatten()
        if '_force' in label:
            forces[label.replace('_force', '')] = data
        elif '_moment' in label:
            torques[label.replace('_moment', '')] = data
    
    if plot:
        plot_joint_loads(time, forces, torques)
    
    return {
        'time': time,
        'forces': forces,
        'torques': torques,
        'peaks': {
            'forces': {k: {'max': np.max(v), 'min': np.min(v)} for k,v in forces.items()},
            'torques': {k: {'max': np.max(v), 'min': np.min(v)} for k,v in torques.items()}
        }
    }
    
setup_file = 'motionConfig/0101_Setup_InverseDynamics.xml'
load_data = extract_joint_forces_torques(setup_file, plot=False)