import os
import numpy as np
import pandas as pd
import opensim as osim
import matplotlib.pyplot as plt

def plot_muscle_forces_and_activations(time, forces, activations, body_weight=None, save_path=None):
    """
    Plot muscle forces and activations over time.
    
    Parameters:
        time (array-like): Time vector.
        forces (dict): Dictionary of muscle forces; keys are muscle names and values are force data.
        activations (dict): Dictionary of muscle activations; keys are muscle names and values are activation data.
        body_weight (float): Optional body weight in kg (for labeling normalization).
        save_path (str): If provided, save the plot to this file; otherwise, show the plot.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot forces
    for muscle, force in forces.items():
        ax1.plot(time, force, label=muscle)
    ax1.set_title('Muscle Forces')
    ylabel_forces = 'Force (N/kg)' if body_weight else 'Force (N)'
    ax1.set_ylabel(ylabel_forces)
    ax1.legend(loc='best')
    ax1.grid(True)

    # Plot activations
    for muscle, activation in activations.items():
        ax2.plot(time, activation, label=muscle)
    ax2.set_title('Muscle Activations')
    ax2.set_xlabel('Time (s)')
    ylabel_activations = 'Activation' if body_weight else 'Activation'
    ax2.set_ylabel(ylabel_activations)
    ax2.legend(loc='best')
    ax2.grid(True)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
        print(f"Muscle forces and activations plot saved to: {save_path}")
        plt.close(fig)
    else:
        plt.show()


def extract_muscle_forces_activations(setup_file_path, plot=False, plot_save_path=None):
    """
    Extract muscle forces and activations from a .sto file.
    
    Assumes that static optimization has already been run and the results file exists in the ResultsStaticOptimization folder.
    
    Parameters:
        setup_file_path (str): Path to the static optimization setup file.
        plot (bool): Whether to plot the muscle forces and activations.
        plot_save_path (str): File path to save the plot (if plot is True).
    
    Returns:
        dict: Contains time, forces, activations, and peak values.
    """
    if not os.path.exists(setup_file_path):
        raise FileNotFoundError(f"Setup file not found: {setup_file_path}")
    
    results_dir = os.path.dirname(setup_file_path)
    forces_file = os.path.join(results_dir, "SO_StaticOptimization_force.sto")
    activations_file = os.path.join(results_dir, "SO_StaticOptimization_activation.sto")

    if not os.path.exists(forces_file) or not os.path.exists(activations_file):
        raise FileNotFoundError(f"Static optimization results files not found.")
    
    # Load static optimization results
    forces_table = osim.TimeSeriesTable(forces_file)
    activations_table = osim.TimeSeriesTable(activations_file)
    
    # Convert to pandas DataFrames
    forces_df = pd.DataFrame(forces_table.getMatrix().to_numpy(), 
                             columns=forces_table.getColumnLabels(),
                             index=forces_table.getIndependentColumn())
    activations_df = pd.DataFrame(activations_table.getMatrix().to_numpy(),
                                  columns=activations_table.getColumnLabels(),
                                  index=activations_table.getIndependentColumn())
    
    time = forces_df.index.to_numpy()

    # Compute peak values
    forces_peaks = forces_df.max(axis=0)
    activations_peaks = activations_df.max(axis=0)

    if plot:
        # Save the plot if a file path is provided.
        plot_muscle_forces_and_activations(time, forces_df.to_dict(orient='list'), 
                                           activations_df.to_dict(orient='list'), 
                                           save_path=plot_save_path)
    
    return {
        'time': time,
        'forces': forces_df,
        'activations': activations_df,
        'peaks': {
            'forces': forces_peaks,
            'activations': activations_peaks
        }
    }


# def calculate_muscle_risks(forces_df, activations_df, body_weight):
#     """Calculate risk metrics from muscle forces and activations."""
#     metrics = {}
    
#     # Hamstring to Quadriceps Ratio (HQR)
#     hamstrings = ['bflh_r', 'bfsh_r', 'semimem_r', 'semiten_r']
#     quads = ['vaslat_r', 'vasmed_r', 'vasint_r', 'recfem_r']
    
#     hq_ratio = activations_df[hamstrings].mean(axis=1) / activations_df[quads].mean(axis=1)
#     metrics['hq_ratio'] = hq_ratio
#     metrics['hq_risk'] = hq_ratio < 0.6  # Risk threshold
    
#     # Gastrocnemius Overload
#     gastroc_forces = forces_df[['gaslat_r', 'gasmed_r']].mean(axis=1)
#     metrics['gastroc_overload'] = gastroc_forces > (3 * body_weight)
    
#     # Gluteus Medius Delay (requires comparison to healthy baseline)
#     glu_med = activations_df['glmed1_r']
#     metrics['glu_med_activation'] = glu_med
    
#     return metrics


# def detect_activation_delay(activation_curve, threshold=0.1, baseline=None):
#     """Detect activation delay relative to baseline or absolute threshold"""
#     if baseline is not None:
#         # Compare to healthy baseline curve
#         delay_samples = np.argmax(activation_curve > threshold) - np.argmax(baseline > threshold)
#         return delay_samples * (1/100)  # Assuming 100 Hz data
#     else:
#         return np.argmax(activation_curve > threshold) * (1/100)


# def calculate_injury_risks(forces_df, activations_df, body_weight):
#     """Assess and calculate injury risks based on muscle forces and activations."""
#     risk_metrics = []

#     # Hamstring to Quadriceps Ratio (HQR)
#     hamstrings = ['bflh_r', 'bfsh_r', 'semimem_r', 'semiten_r']
#     quads = ['vaslat_r', 'vasmed_r', 'vasint_r', 'recfem_r']
    
#     hq_ratio = activations_df[hamstrings].mean(axis=1) / activations_df[quads].mean(axis=1)
#     metrics = {
#         'hq_ratio': hq_ratio,
#         'hq_risk': hq_ratio < 0.6  # Risk threshold
#     }
    
#     # Gastrocnemius Overload
#     gastroc_forces = forces_df[['gaslat_r', 'gasmed_r']].mean(axis=1)
#     gastroc_overload = gastroc_forces > (3 * body_weight)
    
#     metrics['gastroc_overload'] = gastroc_overload

#     # Gluteus Medius Delay (requires comparison to healthy baseline)
#     glu_med = activations_df['glmed1_r']
#     metrics['glu_med_activation'] = glu_med

#     # Example risk validation
#     def validate_risks():
#         # Gastrocnemius Overload: Find time points where the force exceeds threshold
#         risky_time_indices = np.where(gastroc_overload)[0]
#         risky_times = forces_df.index[risky_time_indices].tolist()

#         for risky_time in risky_times:
#             # Corrected way to access gastroc_forces using the right indices
#             risk_metrics.append({
#                 'Risk detected in': 'Gastrocnemius Overload',
#                 'Type': 'Achilles Tendon Overload Risk',
#                 'Measured value': f'{gastroc_forces.iloc[risky_time]:.2f} N (threshold: >3x body weight)',
#                 'Safety threshold': '> 3x body weight',
#                 'Time': f'{risky_time:.2f}s',  # Use time in seconds
#                 'Rationale': 'High forces on gastrocnemius increase Achilles tendon stress'
#             })

#     validate_risks()

#     return risk_metrics


def calculate_injury_risks(forces_df, activations_df, body_weight):
    """
    Assess and calculate injury risks based on muscle forces and activations.
    
    Parameters:
        forces_df (pd.DataFrame): DataFrame containing muscle forces over time
        activations_df (pd.DataFrame): DataFrame containing muscle activations over time
        body_weight (float): Body weight in kg for normalized force calculations
        
    Returns:
        list: List of dictionaries containing detailed risk metrics including:
              - Risk type
              - Measured values
              - Thresholds
              - Time periods when risks occurred
              - Rationale
    """
    risk_metrics = []
    time_array = forces_df.index.to_numpy()
    
    # 1. Hamstring to Quadriceps Ratio (HQR)
    hamstrings = [col for col in activations_df.columns if any(muscle in col for muscle in ['bflh', 'bfsh', 'semimem', 'semiten'])]
    quads = [col for col in activations_df.columns if any(muscle in col for muscle in ['vaslat', 'vasmed', 'vasint', 'recfem'])]
    
    # Only proceed if we have both hamstring and quad data
    if hamstrings and quads:
        ham_activation = activations_df[hamstrings].mean(axis=1)
        quad_activation = activations_df[quads].mean(axis=1)
        
        # Avoid division by zero
        quad_activation = quad_activation.replace(0, np.nan)
        hq_ratio = ham_activation / quad_activation
        
        # Find contiguous regions where HQ ratio is below threshold
        hq_threshold = 0.6
        risky_indices = np.where(hq_ratio < hq_threshold)[0]
        
        if len(risky_indices) > 0:
            # Group consecutive indices to find continuous risk periods
            risk_periods = []
            current_period = [risky_indices[0]]
            
            for i in range(1, len(risky_indices)):
                if risky_indices[i] == risky_indices[i-1] + 1:
                    current_period.append(risky_indices[i])
                else:
                    risk_periods.append(current_period)
                    current_period = [risky_indices[i]]
            
            risk_periods.append(current_period)
            
            # Report each risk period
            for period in risk_periods:
                start_time = time_array[period[0]]
                end_time = time_array[period[-1]]
                min_ratio = hq_ratio.iloc[period].min()
                
                risk_metrics.append({
                    'Risk Type': 'ACL Injury Risk (Hamstring-Quadriceps Imbalance)',
                    'Measured Value': f'{min_ratio:.2f} ratio (minimum in period)',
                    'Safety Threshold': f'> {hq_threshold} (H:Q ratio)',
                    'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                    'Duration': f'{end_time - start_time:.2f}s',
                    'Rationale': 'Low hamstring to quadriceps ratio indicates insufficient hamstring strength to counteract quadriceps force, increasing ACL strain'
                })
    
    # 2. Gastrocnemius Overload
    gastroc_cols = [col for col in forces_df.columns if any(muscle in col for muscle in ['gaslat', 'gasmed'])]
    
    if gastroc_cols:
        gastroc_forces = forces_df[gastroc_cols].mean(axis=1)
        gastroc_threshold = 3 * body_weight
        gastroc_overload = gastroc_forces > gastroc_threshold
        
        risky_indices = np.where(gastroc_overload)[0]
        
        if len(risky_indices) > 0:
            # Group consecutive indices to find continuous risk periods
            risk_periods = []
            current_period = [risky_indices[0]]
            
            for i in range(1, len(risky_indices)):
                if risky_indices[i] == risky_indices[i-1] + 1:
                    current_period.append(risky_indices[i])
                else:
                    risk_periods.append(current_period)
                    current_period = [risky_indices[i]]
            
            risk_periods.append(current_period)
            
            # Report each risk period
            for period in risk_periods:
                start_time = time_array[period[0]]
                end_time = time_array[period[-1]]
                max_force = gastroc_forces.iloc[period].max()
                
                risk_metrics.append({
                    'Risk Type': 'Achilles Tendon Overload Risk',
                    'Measured Value': f'{max_force:.2f} N (max in period), {max_force/body_weight:.2f}x body weight',
                    'Safety Threshold': f'< {gastroc_threshold:.2f} N ({3}x body weight)',
                    'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                    'Duration': f'{end_time - start_time:.2f}s',
                    'Rationale': 'High forces on gastrocnemius increase Achilles tendon stress and rupture risk'
                })
    
    # 3. Gluteus Medius Underactivation
    glute_cols = [col for col in activations_df.columns if 'glmed' in col]
    
    if glute_cols:
        glute_activation = activations_df[glute_cols].mean(axis=1)
        glute_threshold = 0.3  # Minimum activation threshold during stance phase
        
        # Assuming first half of motion is stance phase (customize as needed)
        stance_indices = np.arange(len(time_array) // 2)
        
        glute_underactivation = glute_activation.iloc[stance_indices] < glute_threshold
        risky_indices = stance_indices[glute_underactivation.values]
        
        if len(risky_indices) > 0:
            # Group consecutive indices to find continuous risk periods
            risk_periods = []
            if len(risky_indices) > 0:
                current_period = [risky_indices[0]]
                
                for i in range(1, len(risky_indices)):
                    if risky_indices[i] == risky_indices[i-1] + 1:
                        current_period.append(risky_indices[i])
                    else:
                        risk_periods.append(current_period)
                        current_period = [risky_indices[i]]
                
                risk_periods.append(current_period)
            
            # Report each risk period
            for period in risk_periods:
                start_time = time_array[period[0]]
                end_time = time_array[period[-1]]
                min_activation = glute_activation.iloc[period].min()
                
                risk_metrics.append({
                    'Risk Type': 'Hip Instability / Knee Valgus Risk',
                    'Measured Value': f'{min_activation:.2f} activation (minimum in period)',
                    'Safety Threshold': f'> {glute_threshold} activation during stance',
                    'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                    'Duration': f'{end_time - start_time:.2f}s',
                    'Rationale': 'Insufficient gluteus medius activation can lead to hip drop, increased knee valgus, and IT band syndrome'
                })
    
    # 4. Rectus Femoris Overactivation during late swing
    rectus_cols = [col for col in activations_df.columns if 'recfem' in col]
    
    if rectus_cols:
        rectus_activation = activations_df[rectus_cols].mean(axis=1)
        rectus_threshold = 0.5  # High activation threshold during late swing
        
        # Assuming late swing is the last quarter of motion (customize as needed)
        late_swing_start = int(len(time_array) * 0.75)
        late_swing_indices = np.arange(late_swing_start, len(time_array))
        
        rectus_overactivation = rectus_activation.iloc[late_swing_indices] > rectus_threshold
        risky_indices = late_swing_indices[rectus_overactivation.values]
        
        if len(risky_indices) > 0:
            # Group consecutive indices to find continuous risk periods
            risk_periods = []
            current_period = [risky_indices[0]]
            
            for i in range(1, len(risky_indices)):
                if risky_indices[i] == risky_indices[i-1] + 1:
                    current_period.append(risky_indices[i])
                else:
                    risk_periods.append(current_period)
                    current_period = [risky_indices[i]]
            
            risk_periods.append(current_period)
            
            # Report each risk period
            for period in risk_periods:
                start_time = time_array[period[0]]
                end_time = time_array[period[-1]]
                max_activation = rectus_activation.iloc[period].max()
                
                risk_metrics.append({
                    'Risk Type': 'Hamstring Strain Risk',
                    'Measured Value': f'{max_activation:.2f} activation (maximum in period)',
                    'Safety Threshold': f'< {rectus_threshold} activation during late swing',
                    'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                    'Duration': f'{end_time - start_time:.2f}s',
                    'Rationale': 'High rectus femoris activation during late swing can oppose hamstring function and increase strain injury risk'
                })
    
    return risk_metrics


def summarize_injury_risks(risk_metrics):
    """
    Summarize and output injury risk analysis.
    
    Parameters:
        risk_metrics (list): List of risk dictionaries from calculate_injury_risks
        
    Returns:
        dict: Summary of risk metrics with counts and overall assessment
    """
    if not risk_metrics:
        return {
            "overall_risk_level": "Low",
            "risk_count": 0,
            "risk_summary": "No significant musculoskeletal injury risks detected in this motion."
        }
    
    # Count risks by type
    risk_types = {}
    for risk in risk_metrics:
        risk_type = risk['Risk Type']
        if risk_type in risk_types:
            risk_types[risk_type] += 1
        else:
            risk_types[risk_type] = 1
    
    # Calculate total risk duration
    total_duration = sum(float(risk['Duration'].replace('s', '')) for risk in risk_metrics)
    
    # Determine overall risk level
    if len(risk_metrics) > 5 or total_duration > 2.0:
        overall_risk = "High"
    elif len(risk_metrics) > 2 or total_duration > 1.0:
        overall_risk = "Moderate"
    else:
        overall_risk = "Low"
    
    # Create summary
    risk_summary = f"Detected {len(risk_metrics)} instances of potential injury risks covering {total_duration:.2f}s of motion."
    for risk_type, count in risk_types.items():
        risk_summary += f"\n- {risk_type}: {count} instances detected"
    
    return {
        "overall_risk_level": overall_risk,
        "risk_count": len(risk_metrics),
        "risk_summary": risk_summary,
        "risk_details": risk_metrics
    }


def generate_risk_report(forces_df, activations_df, body_weight, output_file=None):
    """
    Generate a comprehensive risk report based on muscle forces and activations.
    
    Parameters:
        forces_df (pd.DataFrame): DataFrame containing muscle forces over time
        activations_df (pd.DataFrame): DataFrame containing muscle activations over time
        body_weight (float): Body weight in kg
        output_file (str): Optional file path to save report
        
    Returns:
        dict: Complete risk assessment
    """
    # Calculate detailed risks
    risk_metrics = calculate_injury_risks(forces_df, activations_df, body_weight)
    
    # Get summary
    risk_summary = summarize_injury_risks(risk_metrics)
    
    # Generate report
    report = {
        "analysis_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "body_weight_kg": body_weight,
        "motion_duration_s": forces_df.index[-1] - forces_df.index[0],
        "overall_risk_assessment": risk_summary["overall_risk_level"],
        "risk_summary": risk_summary["risk_summary"],
        "detailed_risks": risk_metrics
    }
    
    # Save report if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"MUSCLE FORCE ACTIVATION RISK REPORT\n")
            f.write(f"=================================\n\n")
            f.write(f"Analysis Date: {report['analysis_timestamp']}\n")
            f.write(f"Motion Duration: {report['motion_duration_s']:.2f}s\n")
            f.write(f"Subject Body Weight: {report['body_weight_kg']:.1f} kg\n\n")
            
            f.write(f"OVERALL RISK ASSESSMENT: {report['overall_risk_assessment']}\n\n")
            f.write(f"{risk_summary['risk_summary']}\n\n")
            
            if risk_metrics:
                f.write(f"DETAILED RISK ANALYSIS:\n")
                f.write(f"======================\n\n")
                
                for i, risk in enumerate(risk_metrics, 1):
                    f.write(f"Risk #{i}: {risk['Risk Type']}\n")
                    f.write(f"  Time Period: {risk['Time Period']}\n")
                    f.write(f"  Duration: {risk['Duration']}\n")
                    f.write(f"  Measured Value: {risk['Measured Value']}\n")
                    f.write(f"  Safety Threshold: {risk['Safety Threshold']}\n")
                    f.write(f"  Rationale: {risk['Rationale']}\n\n")
            
            f.write(f"RECOMMENDATIONS:\n")
            f.write(f"===============\n\n")
            
            # Generate recommendations based on detected risks
            risk_types = set(risk['Risk Type'] for risk in risk_metrics)
            
            recommendations = {
                "ACL Injury Risk (Hamstring-Quadriceps Imbalance)": 
                    "Focus on hamstring strengthening exercises (Nordic curls, Romanian deadlifts) to improve H:Q ratio.",
                "Achilles Tendon Overload Risk":
                    "Gradually progress loading of calf muscles and consider monitoring ground reaction forces during activity.",
                "Hip Instability / Knee Valgus Risk":
                    "Implement targeted gluteus medius strengthening exercises and neuromuscular control drills.",
                "Hamstring Strain Risk":
                    "Address rectus femoris overactivity with stretching and eccentric hamstring strengthening."
            }
            
            for risk_type in risk_types:
                if risk_type in recommendations:
                    f.write(f"• {recommendations[risk_type]}\n")
            
            print(f"Risk report saved to: {output_file}")
    
    return report