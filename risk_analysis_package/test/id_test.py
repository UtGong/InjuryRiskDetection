import os
import sys
import opensim as osim

# Add the package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

from motion_data_computing.setup_generation.generate_grf import generate_complete_grf
from motion_data_computing.setup_generation.create_external_loads import create_external_loads_file
from motion_data_computing.setup_generation.create_inverse_dynamics_setup import create_inverse_dynamics_setup
from motion_data_computing.inverse_dynamic.run_inverse_dynamics import run_inverse_dynamics

def test_inverse_dynamics_pipeline():
    # Paths to required files
    model_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/bsm.osim" # Model file
    ik_table_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/output_motion_segment_0_ik.mot"  # IK data file
    output_dir = os.path.abspath("../data")
    print("Writing to:", output_dir)

    body_weight = 75 * 9.81  # Example body weight in N (adjust as needed)
    setup_name = "0101"  # Base name for the setup files

    # Step 1: Generate GRF (Ground Reaction Forces)
    print("Generating GRF...")
    ik_table = osim.TimeSeriesTable(ik_table_path)
    complete_grf = generate_complete_grf(ik_table, body_weight)
    grf_mot_file = os.path.join(output_dir, f"{setup_name}_grf.sto")
    osim.STOFileAdapter().write(complete_grf, grf_mot_file)
    print(f"GRF generated and saved to: {grf_mot_file}")

    # Step 2: Create External Loads XML file
    print("Creating External Loads file...")
    ext_loads_file = os.path.join(output_dir, f"{setup_name}_grf.xml")
    ext_loads_file = os.path.abspath(ext_loads_file)
    create_external_loads_file(ext_loads_file, grf_mot_file)
    print(f"External Loads file created at: {ext_loads_file}")

    print("Creating Inverse Dynamics setup file...")
    coordinates_file = ik_table_path  # Same as IK data (could be a .mot or .sto file)
    setup_file = create_inverse_dynamics_setup(
        output_dir=output_dir,
        setup_name=setup_name,
        model_file=model_path,
        coordinates_file=coordinates_file,
        grf_mot_file=grf_mot_file,
        time_range=(0.4, 1.6),
        lowpass_cutoff=6.0
    )
    print(f"Inverse Dynamics setup file created at: {setup_file}")

    # Step 4: Run Inverse Dynamics
    print("Running Inverse Dynamics...")
    output_file = run_inverse_dynamics(setup_file, grf_mot_file)
    print(f"Inverse Dynamics completed. Output file: {output_file}")

if __name__ == "__main__":
    test_inverse_dynamics_pipeline()
