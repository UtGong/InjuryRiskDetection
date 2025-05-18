import os
import numpy as np
import opensim as osim
import matplotlib.pyplot as plt

def get_joint_angles(motion_file_path, joints_to_analyze, plot=False):
    """
    Load motion data from the specified file, extract joint angle columns for the given joints,
    and compute their peaks.
    
    Parameters:
        motion_file_path (str): Path to the motion file (.mot or .sto).
        joints_to_analyze (list): List of joint angle column names to extract.
        plot (bool): If True, plot the joint angles over time and save the plot.
    
    Returns:
        dict: Contains 'time', 'angles' (dict of numpy arrays), and 'peaks' (max and min for each joint).
    """
    if not os.path.exists(motion_file_path):
        raise FileNotFoundError(f"Motion file not found: {motion_file_path}")
    
    # Load the motion file using OpenSim
    table = osim.TimeSeriesTable(motion_file_path)
    
    # Get time vector from the independent column
    time = np.array(table.getIndependentColumn())
    n_frames = len(time)
    
    angles = {}
    peaks = {}
    for joint in joints_to_analyze:
        try:
            # Retrieve the joint angle column and convert to a NumPy array
            angle_col = table.getDependentColumn(joint)
            angle_data = np.zeros(angle_col.size())
            for i in range(angle_col.size()):
                angle_data[i] = angle_col[i]
            angles[joint] = angle_data
            peaks[joint] = {
                'max': np.max(angle_data),
                'min': np.min(angle_data),
                'max_time': time[np.argmax(angle_data)],  # time when max angle occurs
                'min_time': time[np.argmin(angle_data)]   # time when min angle occurs
            }
        except Exception as e:
            print(f"Warning: Could not process joint '{joint}'. Error: {str(e)}")
            angles[joint] = np.full(n_frames, np.nan)
            peaks[joint] = {'max': np.nan, 'min': np.nan, 'max_time': np.nan, 'min_time': np.nan}
    
    if plot:
        # Plotting the joint angles
        n_joints = len(joints_to_analyze)
        fig, axs = plt.subplots(n_joints, 1, figsize=(10, 3 * n_joints))
        if n_joints == 1:
            axs = [axs]
        fig.suptitle('Joint Angles Over Time')
        
        # Plot each joint's angle
        for i, joint in enumerate(joints_to_analyze):
            axs[i].plot(time, angles[joint], label=joint)
            axs[i].set_title(joint)
            axs[i].set_xlabel('Time (s)')
            axs[i].set_ylabel('Angle (rad)')
            axs[i].grid(True)
            axs[i].legend()
        
        # Save the plot with a name based on the motion file path
        plot_dir = os.path.dirname(motion_file_path)
        plot_filename = os.path.join(plot_dir, os.path.basename(motion_file_path).replace(".mot", "_joint_angles_plot.png"))
        plt.tight_layout()
        plt.savefig(plot_filename)
        print(f"Plot saved to {plot_filename}")
        plt.close()
    
    return {
        'time': time,
        'angles': angles,
        'peaks': peaks
    }

def check_joint_angles(joint_data, body_weight=None):
    """
    Check joint angles against predefined injury risk thresholds.
    
    Parameters:
        joint_data (dict): Output from get_joint_angles(), with keys:
            'time'   - Time vector.
            'angles' - Dictionary of joint angles (in radians).
            'peaks'  - Dictionary of maximum and minimum angles.
        body_weight (float): Optional body weight in kg (if force-dependent thresholds are needed).
    
    Returns:
        dict: Dictionary with keys as risk identifiers and values as details (type, measured value, threshold, rationale, etc.).
    """
    # Convert angles and peaks from radians to degrees.
    angles_deg = {joint: np.rad2deg(data) for joint, data in joint_data['angles'].items()}
    peaks_deg = {}
    for joint in joint_data['peaks']:
        peaks_deg[joint] = {
            'max': np.rad2deg(joint_data['peaks'][joint]['max']),
            'min': np.rad2deg(joint_data['peaks'][joint]['min']),
            'max_time': joint_data['peaks'][joint]['max_time'],
            'min_time': joint_data['peaks'][joint]['min_time']
        }
    
    risks = {}
    
    # Knee Joint Checks (example thresholds)
    if 'knee_angle_r' in angles_deg or 'knee_angle_l' in angles_deg:
        for side in ['r', 'l']:
            joint = f'knee_angle_{side}'
            if joint in angles_deg:
                max_valgus = peaks_deg[joint]['max']
                if max_valgus > 10:
                    risks[f'{joint}_valgus'] = {
                        'type': 'ACL injury risk',
                        'value': f'{max_valgus:.1f}°',
                        'time': f'{peaks_deg[joint]["max_time"]:.2f}s',
                        'threshold': '>10°',
                        'rationale': 'Excessive valgus increases ACL strain due to lateral shear forces'
                    }
                min_flexion = peaks_deg[joint]['min']
                if min_flexion < 30:
                    risks[f'{joint}_flexion'] = {
                        'type': 'Patellar tendon stress',
                        'value': f'{min_flexion:.1f}°',
                        'time': f'{peaks_deg[joint]["min_time"]:.2f}s',
                        'threshold': '<30°',
                        'rationale': 'Insufficient flexion during deceleration increases patellar tendon stress'
                    }
                if peaks_deg[joint]['min'] < -5:
                    risks[f'{joint}_hyperextension'] = {
                        'type': 'PCL stress',
                        'value': f'{peaks_deg[joint]["min"]:.1f}°',
                        'time': f'{peaks_deg[joint]["min_time"]:.2f}s',
                        'threshold': '>5° hyperextension',
                        'rationale': 'Hyperextension stresses the posterior cruciate ligament'
                    }
    
    # Hip Joint Checks
    for side in ['r', 'l']:
        adduction_joint = f'hip_adduction_{side}'
        rotation_joint = f'hip_rotation_{side}'
        
        if adduction_joint in angles_deg:
            max_flexion = peaks_deg[adduction_joint]['max']
            if max_flexion > 90:
                risks[f'hip_flexion_{side}'] = {
                    'type': 'Lumbar spine compression risk',
                    'value': f'{max_flexion:.1f}°',
                    'time': f'{peaks_deg[adduction_joint]["max_time"]:.2f}s',
                    'threshold': '>90°',
                    'rationale': 'Deep flexion with load risks lumbar spine compression',
                    'note': 'Requires torque >2 Nm/kg to confirm risk'
                }
        
        if rotation_joint in angles_deg:
            max_rotation = max(abs(peaks_deg[rotation_joint]['max']),
                               abs(peaks_deg[rotation_joint]['min']))
            if max_rotation > 25:
                risks[f'hip_rotation_{side}'] = {
                    'type': 'Labral tear risk',
                    'value': f'{max_rotation:.1f}°',
                    'time': f'{peaks_deg[rotation_joint]["max_time"]:.2f}s',
                    'threshold': '>25°',
                    'rationale': 'Excessive rotation during pivoting risks labral tears'
                }
    
    # Shoulder Joint Checks
    for side in ['r', 'l']:
        # Use scapula abduction instead of shoulder abduction
        adduction_joint = f'scapula_abduction_{side}'
        # Rotation in shoulder might be related to x, y, z position or other measurements
        rotation_joint = f'scapula_upward_rot_{side}'
        
        if adduction_joint in angles_deg:
            max_abduction = peaks_deg[adduction_joint]['max']
            if max_abduction > 90:
                risks[f'scapula_abduction_{side}'] = {
                    'type': 'Supraspinatus tendon strain',
                    'value': f'{max_abduction:.1f}°',
                    'time': f'{peaks_deg[adduction_joint]["max_time"]:.2f}s',
                    'threshold': '>90°',
                    'rationale': 'High abduction with rapid acceleration stresses the supraspinatus tendon'
                }
        
        if rotation_joint in angles_deg:
            max_rotation = peaks_deg[rotation_joint]['max']
            if max_rotation > 25:
                risks[f'scapula_upward_rot_{side}'] = {
                    'type': 'Labral tear risk',
                    'value': f'{max_rotation:.1f}°',
                    'time': f'{peaks_deg[rotation_joint]["max_time"]:.2f}s',
                    'threshold': '>25°',
                    'rationale': 'Excessive rotation during movement risks labral tears'
                }
    
    # Spine Check (if lumbar flexion data available)
    if 'lumbar_bending' in angles_deg:
        max_bending = peaks_deg['lumbar_bending']['max']
        if max_bending > 45:
            risks['lumbar_bending'] = {
                'type': 'Disc herniation risk',
                'value': f'{max_bending:.1f}°',
                'time': f'{peaks_deg["lumbar_bending"]["max_time"]:.2f}s',
                'threshold': '>45°',
                'rationale': 'Excessive flexion with load increases disc herniation risk',
                'note': 'Requires asymmetric load >15% body weight to confirm risk'
            }
    
    return risks

def output_risks(risks):
    """Output the formatted risk results."""
    if not risks:
        return {"message": "No significant injury risks detected."}
    
    risk_results = []
    for risk, details in risks.items():
        risk_info = {
            "Risk detected in": risk,
            "Type": details['type'],
            "Measured value": details['value'],
            "Safety threshold": details['threshold'],
            "Time": details['time'],
            "Rationale": details['rationale']
        }
        if 'note' in details:
            risk_info["Note"] = details['note']
        risk_results.append(risk_info)
    
    return risk_results