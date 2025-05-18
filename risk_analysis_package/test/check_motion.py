import os
import sys
import time
import subprocess
import opensim as osim

# Add the package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

from motion_data_computing.inverse_kinematic.run_inverse_kinematic import run_ik_from_marker_file
from motion_data_computing.inverse_dynamic.run_inverse_dynamics import run_inverse_dynamics_pipeline
from motion_data_computing.static_optimization.run_static_optimization import run_static_optimization
from risk_identification.run_analysis_pipeline import run_all_risk_assessments


def convert_tracking_to_npz(input_pkl_path):
    # Define paths
    base_name = os.path.splitext(os.path.basename(input_pkl_path))[0]
    output_dir = "/home/ubuntu/injury_detection/risk_analysis_package/motion/npz_result"
    output_npz_path = os.path.join(output_dir, f"{base_name}.npz")
    reference_npz_path = "/home/ubuntu/injury_detection/risk_analysis_package/motion/sample_npz.npz"

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Build command
    command = [
        "python", "/home/ubuntu/injury_detection/risk_analysis_package/motion/convert_phalp_to_npz.py",
        "--input", input_pkl_path,
        "--output", output_npz_path,
        "--auto_select",
        "--reference_npz", reference_npz_path
    ]

    print(f"[INFO] Converting {input_pkl_path} to {output_npz_path}")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("[ERROR] Conversion failed:")
        print(result.stderr)
        raise RuntimeError("Conversion to .npz failed.")
    else:
        print("[INFO] Conversion successful.")

    return output_npz_path

def run_smpl2addbio(npz_path):
    import shutil

    smpl2addbio_script = "/home/ubuntu/injury_detection/SMPL2AddBiomechanics/smpl2ab/smpl2addbio.py"
    tmp_smpl_folder = "/home/ubuntu/injury_detection/trc_data"
    data_folder = "/home/ubuntu/injury_detection/risk_analysis_package/data"
    # output folder = data_folder + base name
    base_name = os.path.splitext(os.path.basename(npz_path))[0]
    output_folder = os.path.join(data_folder, base_name)
    print(f"[INFO] Output folder: {output_folder}")

    # Prepare working directory
    os.makedirs(tmp_smpl_folder, exist_ok=True)
    shutil.copy(npz_path, tmp_smpl_folder)

    # Run smpl2addbio
    command = [
        "python", smpl2addbio_script,
        "-i", tmp_smpl_folder,
        "-o", output_folder,
        "--body_model", "smpl",
        "--no_confirm"
    ]

    print(f"[INFO] Generating TRC using smpl2addbio.py for {npz_path}")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("[ERROR] TRC generation failed:")
        print(result.stderr)
        raise RuntimeError("TRC generation failed.")
    else:
        print("[INFO] TRC generation completed.")

    # Determine output .trc path
    subject_name = os.path.basename(tmp_smpl_folder)
    base_name = os.path.splitext(os.path.basename(npz_path))[0]
    trc_path = os.path.join(output_folder, subject_name, "trials", base_name + ".trc")

    if not os.path.exists(trc_path):
        raise FileNotFoundError(f"Expected TRC file not found: {trc_path}")

    return trc_path

def extract_base_output_path(ik_file_path):
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

if __name__ == "__main__":
    start_time = time.time()
    
    pkl_path = "/home/ubuntu/injury_detection/risk_analysis_package/motion/tracking_result/KD_injured.pkl"
    model_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/bsm.osim"
    
    # npz_path = "/home/ubuntu/injury_detection/risk_analysis_package/motion/npz_result/KD_injured.npz"
    # trc_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/KD_injured/trc_data/trials/KD_injured.trc"
    # ik_mot_file = "/home/ubuntu/injury_detection/risk_analysis_package/data/KD_injured/KD_injured_ik.mot"
    # # id_file = "/home/ubuntu/injury_detection/risk_analysis_package/data/KD_injured/ResultsInverseDynamics/inverse_dynamics.sto"
    # # ext_load_file = "/home/ubuntu/injury_detection/risk_analysis_package/data/KD_injured/KD_injured_grf.xml"
    # # so_results_dir = "/home/ubuntu/injury_detection/risk_analysis_package/data/KD_injured/ResultStaticOptimization"

    npz_path = convert_tracking_to_npz(pkl_path)
    trc_path = run_smpl2addbio(npz_path)
    ik_mot_file = run_ik_from_marker_file(trc_path)
    id_file, ext_load_file = run_inverse_dynamics_pipeline(model_path, ik_mot_file, trc_path)
    
    output_dir = extract_base_output_path(ik_mot_file)
    marker_data = osim.MarkerData(trc_path)
    
    marker_info = {
        "time_range": (marker_data.getStartFrameTime(), marker_data.getLastFrameTime()),
    }
    
    so_results_dir = run_static_optimization(
        model_file=model_path,
        coordinates_file=ik_mot_file,
        ext_loads_file=ext_load_file,
        results_dir=os.path.join(output_dir, "ResultStaticOptimization"),
        setup_xml=os.path.join(output_dir, "SO_AnalyzeTool_setup.xml"),
        start_time=marker_info["time_range"][0],
        end_time=marker_info["time_range"][1] - 0.01
    )

    # Define input files for risk analysis
    setup_controls = os.path.join(so_results_dir, "SO_StaticOptimization_controls.xml")
    so_activation = os.path.join(so_results_dir, "SO_StaticOptimization_activation.sto")
    so_force = os.path.join(so_results_dir, "SO_StaticOptimization_force.sto")

    risk_output_dir = os.path.join(output_dir, "output")
    os.makedirs(risk_output_dir, exist_ok=True)

    run_all_risk_assessments(
        ik_file=ik_mot_file,
        model_file=model_path,
        so_activation_file=so_activation,
        so_force_file=so_force,
        setup_file_path=setup_controls,
        sto_file=id_file,
        output_dir=risk_output_dir
    )
    print(f"[INFO] Risk analysis completed. Results saved in {risk_output_dir}")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"[INFO] Total elapsed time: {elapsed_time:.2f} seconds")
    print("[INFO] All tasks completed successfully.")

