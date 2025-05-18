import numpy as np
from opensim import Storage, ArrayDouble
import matplotlib.pyplot as plt

def compute_velocity_and_acceleration(angles, time, min_data_points=3):
    """Compute velocities and accelerations from joint angles."""
    if len(angles) < min_data_points:
        raise ValueError(f"Data is too short. At least {min_data_points} data points are required.")
    
    velocities = np.gradient(angles, time)  # First derivative (velocity)
    accelerations = np.gradient(velocities, time)  # Second derivative (acceleration)
    return velocities, accelerations

# def plot_kinematic_risks(time, velocities, accelerations, risky_times, threshold, measure, coordinate, save_path=None):
#     """Plot velocities/accelerations with risky periods highlighted."""
#     plt.figure(figsize=(10, 6))
    
#     # Plot velocity or acceleration
#     if measure == 'velocity':
#         plt.plot(time, velocities, label='Velocity (deg/s)', color='blue')
#     elif measure == 'acceleration':
#         plt.plot(time, accelerations, label='Acceleration (deg/s²)', color='red')
    
#     # Highlight the risky periods
#     for risk_time in risky_times:
#         plt.axvspan(risk_time - 0.1, risk_time + 0.1, color='yellow', alpha=0.5)
    
#     # Set title and labels
#     plt.title(f'{coordinate} - {measure.capitalize()} Over Time')
#     plt.xlabel('Time (s)')
#     plt.ylabel(f'{measure.capitalize()}')
#     plt.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold: {threshold} {measure}')
#     plt.legend(loc='best')
#     plt.grid(True)
    
#     # Save or show the plot
#     if save_path:
#         plt.savefig(save_path)
#         print(f"Plot saved to {save_path}")
#     else:
#         plt.show()

def check_kinematic_injury_risk(ik_mot_path, osim_model_path=None, 
                               so_activation_path=None, so_force_path=None):
    """
    Kinematic injury risk assessment using OpenSim data.
    Returns detected risks with detailed information.
    """
    def get_storage_columns(storage):
        """Get column labels from Storage"""
        labels = storage.getColumnLabels()
        return [str(labels.get(i)) for i in range(labels.size())]
    
    # Initialize results
    results = {
        'metadata': {
            'ik_file': ik_mot_path,
            'warnings': []
        },
        'detected_risks': []
    }
    
    try:
        # Load IK data
        ik_sto = Storage(ik_mot_path)
        available_columns = get_storage_columns(ik_sto)
        
        # Get time vector
        time_array = ArrayDouble()
        ik_sto.getTimeColumn(time_array)
        time = np.array([time_array.get(i) for i in range(time_array.size())])
        
        # Define injury criteria (thresholds in deg/s or deg/s²)
        criteria = {
            'Patellar Tendinopathy': {
                'coordinate': 'knee_angle_r',
                'measure': 'velocity',
                'threshold': 500,  # deg/s
                'condition': '>',
                'required_columns': ['knee_angle_r'],
                'rationale': 'Excessive knee velocity can strain patellar tendon'
            },
            'Lumbar Shear Stress': {
                'coordinate': 'pelvis_rotation',
                'measure': 'acceleration', 
                'threshold': 200,  # deg/s²
                'condition': '>',
                'required_columns': ['pelvis_rotation'],
                'rationale': 'High lumbar acceleration causes shear forces'
            },
            'UCL Tear Risk': {
                'coordinate': 'shoulder_r_z',
                'measure': 'velocity',
                'threshold': 3000,  # deg/s
                'condition': '>',
                'required_columns': ['shoulder_r_z'],
                'rationale': 'Rapid shoulder rotation risks UCL damage'
            }
        }
        
        # Process each risk criterion
        for risk_name, params in criteria.items():
            # Check for required columns
            missing_cols = [col for col in params['required_columns'] 
                           if col not in available_columns]
            if missing_cols:
                results['metadata']['warnings'].append(f"Missing columns for {risk_name}: {missing_cols}")
                continue
            
            # Get angle data
            data_array = ArrayDouble()
            ik_sto.getDataColumn(params['coordinate'], data_array)
            angles = np.array([data_array.get(i) for i in range(data_array.size())])
            
            # Compute derivatives
            velocities, accelerations = compute_velocity_and_acceleration(angles, time)
            
            # Get measure values (velocity or acceleration)
            measure_values = velocities if params['measure'] == 'velocity' else accelerations
            peak_value = np.max(np.abs(measure_values))
            
            # Check risk condition
            if params['condition'] == '>':
                at_risk = peak_value > params['threshold']
            else:
                at_risk = peak_value < params['threshold']
            
            # If risk detected, find exact time points
            if at_risk:
                risky_indices = np.where(np.abs(measure_values) > params['threshold'])[0]
                risky_times = time[risky_indices].tolist()
                
                risk_details = {
                    'risk_type': risk_name,
                    'coordinate': params['coordinate'],
                    'measure': params['measure'],
                    'measured_value': float(peak_value),
                    'threshold': params['threshold'],
                    'units': 'deg/s' if params['measure'] == 'velocity' else 'deg/s²',
                    'risky_times': risky_times,
                    'rationale': params['rationale']
                }
                
                # Plot the risk (velocity or acceleration) over time
                # plot_save_path = f"{risk_name.replace(' ', '_')}_plot.png"
                # plot_kinematic_risks(time, velocities, accelerations, risky_times, params['threshold'], params['measure'], params['coordinate'], save_path=plot_save_path)
                
                # Add muscle data if available and relevant
                if so_force_path and risk_name == 'Patellar Tendinopathy' and 'rect_fem_r' in available_columns:
                    force_sto = Storage(so_force_path)
                    force_array = ArrayDouble()
                    force_sto.getDataColumn('rect_fem_r', force_array)
                    quad_force = np.array([force_array.get(i) for i in range(force_array.size())])
                    
                    # Get corresponding muscle forces at risky times
                    force_time_array = ArrayDouble()
                    force_sto.getTimeColumn(force_time_array)
                    force_time = np.array([force_time_array.get(i) for i in range(force_time_array.size())])
                    
                    force_values = []
                    for t in risky_times:
                        idx = np.argmin(np.abs(force_time - t))
                        force_values.append(float(quad_force[idx]))
                    
                    risk_details['muscle_loading'] = {
                        'muscle': 'rect_fem_r',
                        'peak_force': float(np.max(force_values)),
                        'units': 'N',
                        'values_at_risk_times': force_values
                    }
                
                results['detected_risks'].append(risk_details)
    
    except Exception as e:
        results['metadata']['error'] = str(e)
        results['metadata']['warnings'].append(f"Processing failed: {str(e)}")
    
    return results