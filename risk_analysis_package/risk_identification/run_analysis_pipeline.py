import os

def run_all_risk_assessments(ik_file, model_file, so_activation_file, so_force_file, setup_file_path, sto_file, output_dir):
    import matplotlib.pyplot as plt
    import json
    from datetime import datetime

    def remove_non_serializable(obj):
        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                if isinstance(value, (dict, list)):
                    remove_non_serializable(value)
                elif isinstance(value, plt.Figure):
                    del obj[key]
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    remove_non_serializable(item)
                elif isinstance(item, plt.Figure):
                    del obj[i]

    all_results = {}
    try:
        # Joint angle risk
        from risk_identification.joint_angle_risk import get_joint_angles, check_joint_angles, output_risks
        joint_data = get_joint_angles(ik_file, joints_to_analyze=['knee_angle_r', 'knee_angle_l', 'hip_flexion_r'], plot=False)
        injury_risks = check_joint_angles(joint_data, body_weight=70)
        all_results['joint_angle_risk'] = output_risks(injury_risks)
        print("Joint angle risk assessment completed.")

        # Joint force and torque risk
        from risk_identification.joint_force_torque_risk import analyze_joint_loads, analyze_injury_risks_from_sto, output_risks
        analyze_joint_loads(sto_file, body_weight=70, plot=False)  # Can be used if visual needed
        injury_risks = analyze_injury_risks_from_sto(sto_file, body_weight=70)
        all_results['joint_force_torque_risk'] = output_risks(injury_risks)
        print("Joint force and torque risk assessment completed.")

        # Kinematic data risk
        from risk_identification.kinematic_data_risk import check_kinematic_injury_risk
        kinematic_risk = check_kinematic_injury_risk(ik_file, model_file, so_activation_file, so_force_file)
        all_results['kinematic_injury_risk'] = kinematic_risk
        print("Kinematic data risk assessment completed.")

        # Muscle forces and activations risk
        from risk_identification.muscle_forces_activations_risk import extract_muscle_forces_activations, generate_risk_report
        muscle_data = extract_muscle_forces_activations(setup_file_path, plot=False)
        muscle_report = generate_risk_report(
            muscle_data['forces'], 
            muscle_data['activations'], 
            body_weight=70,
            output_file=os.path.join(output_dir, 'muscle_forces_risk_report.txt')
        )
        all_results['muscle_forces_risk'] = muscle_report
        print("Muscle forces and activations risk assessment completed.")

        # Posture and alignment risk
        from risk_identification.posture_alignment_risk import extract_motion_risk
        posture_risk = extract_motion_risk(
            ik_file=ik_file, 
            model_file=model_file, 
            so_activation_file=so_activation_file,
            so_force_file=so_force_file,
            output_dir=output_dir
        )
        all_results['posture_alignment_risk'] = posture_risk
        print("Posture and alignment risk assessment completed.")

        # Serialize results
        remove_non_serializable(all_results)
        result_file = os.path.join(output_dir, 'comprehensive_risk_assessment_results.json')
        with open(result_file, 'w') as f:
            json.dump(all_results, f, indent=4)
        print(f"[INFO] Risk assessment results saved to: {result_file}")

    except Exception as e:
        print(f"[ERROR] An error occurred during risk assessment: {str(e)}")
