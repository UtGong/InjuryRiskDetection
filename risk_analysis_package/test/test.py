import os
import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Add the package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

# Define output directory to save results
output_dir = os.path.join(package_root, "data", "output", f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
os.makedirs(output_dir, exist_ok=True)

# Define file paths for the input data (update these as needed)
ik_file = os.path.join(package_root, "data", "/home/ubuntu/injury_detection/risk_analysis_package/data/output_motion_segment_0_ik.mot")
model_file = os.path.join(package_root, "data", "bsm.osim")
so_activation_file = os.path.join(package_root, "data", "ResultStaticOptimization", "SO_StaticOptimization_activation.sto")
so_force_file = os.path.join(package_root, "data", "ResultStaticOptimization", "SO_StaticOptimization_force.sto")
setup_file_path = os.path.join(package_root, "data", "ResultStaticOptimization", "SO_StaticOptimization_controls.xml")
sto_file = os.path.join(package_root, "data", "ResultsInverseDynamics", "inverse_dynamics.sto")

# Function to remove non-serializable objects (like Matplotlib figures)
def remove_non_serializable(obj):
    """Recursively remove non-serializable objects from results."""
    if isinstance(obj, dict):
        for key, value in list(obj.items()):
            if isinstance(value, (dict, list)):
                remove_non_serializable(value)
            elif isinstance(value, plt.Figure):  # Handle the figure object
                del obj[key]
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                remove_non_serializable(item)
            elif isinstance(item, plt.Figure):
                del obj[i]

# Function to run all the risk assessments and save results
def run_all_risk_assessments():
    # Initialize a dictionary to store all results
    all_results = {}

    try:
        # Test joint angle risk
        from risk_identification.joint_angle_risk import get_joint_angles, check_joint_angles, output_risks
        joint_data = get_joint_angles(ik_file, joints_to_analyze=['knee_angle_r', 'knee_angle_l', 'hip_flexion_r'], plot=False)
        injury_risks = check_joint_angles(joint_data, body_weight=70)
        joint_risk_report = output_risks(injury_risks)
        all_results['joint_angle_risk'] = joint_risk_report
        print("Joint angle risk assessment completed.")

        # Test joint force and torque risk
        from risk_identification.joint_force_torque_risk import analyze_joint_loads, analyze_injury_risks_from_sto, output_risks
        joint_load_results = analyze_joint_loads(sto_file, body_weight=70, plot=False)
        injury_risks = analyze_injury_risks_from_sto(sto_file, body_weight=70)
        joint_torque_risk_report = output_risks(injury_risks)
        all_results['joint_force_torque_risk'] = joint_torque_risk_report
        print("Joint force and torque risk assessment completed.")

        # Test kinematic data risk
        from risk_identification.kinematic_data_risk import check_kinematic_injury_risk
        kinematic_risk_report = check_kinematic_injury_risk(ik_mot_path=ik_file, osim_model_path=model_file, 
                                                            so_activation_path=so_activation_file, so_force_path=so_force_file)
        all_results['kinematic_injury_risk'] = kinematic_risk_report
        print("Kinematic data risk assessment completed.")

        # Test muscle forces and activations risk
        from risk_identification.muscle_forces_activations_risk import extract_muscle_forces_activations, generate_risk_report
        muscle_results = extract_muscle_forces_activations(setup_file_path, plot=False)
        muscle_risk_report = generate_risk_report(muscle_results['forces'], muscle_results['activations'], body_weight=70, 
                                                 output_file=os.path.join(output_dir, 'muscle_forces_risk_report.txt'))
        all_results['muscle_forces_risk'] = muscle_risk_report
        print("Muscle forces and activations risk assessment completed.")

        # Test posture and alignment risk
        from risk_identification.posture_alignment_risk import extract_motion_risk
        posture_alignment_risk_report = extract_motion_risk(ik_file=ik_file, model_file=model_file, 
                                                           so_activation_file=so_activation_file, so_force_file=so_force_file, 
                                                           output_dir=output_dir)
        all_results['posture_alignment_risk'] = posture_alignment_risk_report
        print("Posture and alignment risk assessment completed.")

        # Remove non-serializable objects (like figures) before saving
        remove_non_serializable(all_results)

        # Save the results to a file
        results_file = os.path.join(output_dir, 'comprehensive_risk_assessment_results.json')
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=4)
        print(f"Risk assessment results saved to: {results_file}")

    except Exception as e:
        print(f"An error occurred during the assessment: {str(e)}")

# Run the assessment
run_all_risk_assessments()
