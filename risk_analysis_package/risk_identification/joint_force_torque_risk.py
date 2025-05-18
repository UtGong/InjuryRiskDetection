import os
import numpy as np
import opensim as osim
import matplotlib.pyplot as plt

def plot_joint_loads(time, moments, forces, body_weight=None, save_path=None):
    """
    Plot joint moments and forces over time.
    
    Parameters:
        time (array-like): Time vector.
        moments (dict): Dictionary of joint moments (torques); keys are joint names and values are moment data.
        forces (dict): Dictionary of joint forces; keys are joint names and values are force data.
        body_weight (float): Optional body weight in kg (for labeling normalization).
        save_path (str): If provided, save the plot to this file; otherwise, show the plot.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot moments (e.g., for lower-extremity joints)
    for joint, data in moments.items():
        # Optionally, filter joints of interest here:
        if any(x in joint for x in ['hip', 'knee', 'ankle']):
            ax1.plot(time, data, label=joint)
    ax1.set_title('Joint Moments')
    ylabel_moments = 'Moment (Nm/kg)' if body_weight else 'Moment (Nm)'
    ax1.set_ylabel(ylabel_moments)
    ax1.legend(loc='best')
    ax1.grid(True)
    
    # Plot forces
    for joint, data in forces.items():
        ax2.plot(time, data, label=joint)
    ax2.set_title('Joint Forces')
    ax2.set_xlabel('Time (s)')
    ylabel_forces = 'Force (N/kg)' if body_weight else 'Force (N)'
    ax2.set_ylabel(ylabel_forces)
    ax2.legend(loc='best')
    ax2.grid(True)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
        print(f"Joint loads plot saved to: {save_path}")
        plt.close(fig)
    else:
        plt.show()

def extract_joint_forces_torques(setup_file_path, plot=False, plot_save_path=None):
    """
    Load inverse dynamics results from a .sto file and extract joint forces and torques.
    
    Assumes that inverse dynamics has already been run and the results file exists in the ResultsInverseDynamics folder.
    
    Parameters:
        setup_file_path (str): Path to the inverse dynamics setup file (used to infer results directory).
        plot (bool): Whether to plot the joint loads.
        plot_save_path (str): File path to save the plot (if plot is True).
    
    Returns:
        dict: Contains time, forces, torques, and peak values.
    """
    if not os.path.exists(setup_file_path):
        raise FileNotFoundError(f"Setup file not found: {setup_file_path}")
    
    setup_dir = os.path.dirname(setup_file_path)
    results_dir = os.path.join(setup_dir, "ResultsInverseDynamics")
    output_file = os.path.join(results_dir, "inverse_dynamics.sto")
    
    if not os.path.exists(output_file):
        raise FileNotFoundError(f"Results file not found: {output_file}")
    
    print("Loading inverse dynamics results...")
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
        # Save the plot if a file path is provided.
        plot_joint_loads(time, torques, forces, body_weight=None, save_path=plot_save_path)
    
    # Compute peaks for each signal.
    peaks['forces'] = {k: {'max': np.max(v), 'min': np.min(v)} for k, v in forces.items()}
    peaks['torques'] = {k: {'max': np.max(v), 'min': np.min(v)} for k, v in torques.items()}
    
    return {
        'time': time,
        'forces': forces,
        'torques': torques,
        'peaks': peaks
    }

def analyze_joint_loads(sto_file_path, body_weight=None, plot=True, plot_save_path=None):
    """
    Analyze joint moments and forces from inverse dynamics results stored in a .sto file.
    
    Parameters:
        sto_file_path (str): Path to the inverse dynamics results (.sto) file.
        body_weight (float): Optional body weight in kg for normalization.
        plot (bool): Whether to plot and save the joint loads.
        plot_save_path (str): File path to save the plot.
    
    Returns:
        dict: Contains time, moments, forces, peak values, and any identified risks.
    """
    if not os.path.exists(sto_file_path):
        raise FileNotFoundError(f"Results file not found: {sto_file_path}")
    
    table = osim.TimeSeriesTable(sto_file_path)
    time = np.array(table.getIndependentColumn())
    
    moments = {}
    forces = {}
    
    # Categorize data into moments and forces.
    for label in table.getColumnLabels():
        col = table.getDependentColumn(label)
        data = np.array([col[i] for i in range(col.size())])
        if '_moment' in label:
            moments[label.replace('_moment', '')] = data
        elif '_force' in label:
            forces[label] = data
    
    # Normalize by body weight if provided.
    if body_weight:
        bw_newtons = body_weight * 9.81
        moments = {k: v / bw_newtons for k, v in moments.items()}
        forces = {k: v / bw_newtons for k, v in forces.items()}
    
    def get_peaks(data_dict):
        return {joint: {
            'max': np.max(values),
            'min': np.min(values),
            'mean': np.mean(values),
            'std': np.std(values)
        } for joint, values in data_dict.items()}
    
    peak_moments = get_peaks(moments)
    peak_forces = get_peaks(forces)
    
    # Example risk assessment (customize thresholds as needed)
    def assess_risks(peaks):
        risks = {}
        if 'knee_angle_r' in peaks:
            if peaks['knee_angle_r']['max'] > 1.5:  # threshold example in Nm/kg
                risks['knee_r_extension'] = {
                    'value': peaks['knee_angle_r']['max'],
                    'threshold': '>1.5 Nm/kg',
                    'risk': 'ACL injury risk'
                }
        if 'hip_flexion_r' in peaks:
            if peaks['hip_flexion_r']['max'] > 2.0:
                risks['hip_r_flexion'] = {
                    'value': peaks['hip_flexion_r']['max'],
                    'threshold': '>2.0 Nm/kg',
                    'risk': 'Hip flexor strain risk'
                }
        return risks
    
    risks = assess_risks(peak_moments)
    
    if plot:
        plot_joint_loads(time, moments, forces, body_weight=body_weight, save_path=plot_save_path)
    
    return {
        'time': time,
        'moments': moments,
        'forces': forces,
        'peaks': {
            'moments': peak_moments,
            'forces': peak_forces
        },
        'risks': risks
    }

def analyze_injury_risks_from_sto(sto_file_path, body_weight):
    """
    Analyze injury risks from inverse dynamics results stored in a .sto file.
    
    This function extracts joint forces and torques, then applies risk criteria.
    
    Parameters:
        sto_file_path (str): Path to inverse_dynamics.sto file.
        body_weight (float): Body weight in kg.
    
    Returns:
        dict: Detected risks with details.
    """
    if not os.path.exists(sto_file_path):
        raise FileNotFoundError(f"Results file not found: {sto_file_path}")
    
    table = osim.TimeSeriesTable(sto_file_path)
    time = np.array(table.getIndependentColumn())
    
    forces = {}
    torques = {}
    
    for label in table.getColumnLabels():
        data = np.array([table.getDependentColumn(label)[i] for i in range(table.getDependentColumn(label).size())])
        if '_force' in label:
            joint = label.replace('_force', '')
            forces[joint] = data
        elif '_moment' in label:
            joint = label.replace('_moment', '')
            torques[joint] = data
    
    risks = {}
    bw_newtons = body_weight * 9.81  # Convert kg to N
    
    # Example: Knee Joint Analysis
    for side in ['r', 'l']:
        shear_force_key = 'pelvis_tz'  # Adjust key based on your model's column name
        if shear_force_key in forces:
            max_shear = np.max(np.abs(forces[shear_force_key]))
            if max_shear > 0.2 * bw_newtons:
                risks[f'knee_{side}_shear'] = {
                    'type': 'ACL injury risk',
                    'value': f'{max_shear:.1f} N ({max_shear/bw_newtons*100:.1f}% BW)',
                    'threshold': '>20% body weight',
                    'rationale': 'Excessive anterior shear force during deceleration'
                }
        
        rot_torque_key = f'hip_rotation_{side}'
        if rot_torque_key in torques:
            max_torque = np.max(np.abs(torques[rot_torque_key]))
            if max_torque > 1.5 * body_weight:
                risks[f'knee_{side}_rotation'] = {
                    'type': 'Meniscal stress risk',
                    'value': f'{max_torque:.2f} Nm ({max_torque/body_weight:.2f} Nm/kg)',
                    'threshold': '>1.5 Nm/kg',
                    'rationale': 'High internal rotation torque during cutting'
                }
    
    # Additional analyses for ankle and shoulder can be added similarly.
    return risks

def output_risks(risks):
    risk_results = []
    
    for risk_name, details in risks.items():
        if 'value' in details and 'threshold' in details:
            risk_info = {
                "Risk detected in": risk_name,
                "Type": details['type'],
                "Measured value": details['value'],
                "Safety threshold": details['threshold'],
                "Rationale": details['rationale'],
                "Time": details.get('time', 'N/A')  # Ensure time is included
            }
            # Add optional fields (like 'Note')
            if 'note' in details:
                risk_info["Note"] = details['note']
            risk_results.append(risk_info)
        else:
            risk_results.append({
                "message": f"Missing 'value' or 'threshold' for risk: {risk_name}"
            })
    
    if not risk_results:
        return {"message": "No significant injury risks detected."}
    
    return risk_results

