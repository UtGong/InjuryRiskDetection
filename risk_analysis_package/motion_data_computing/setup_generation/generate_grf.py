import numpy as np
import opensim as osim

def generate_complete_grf(ik_table, body_weight, foot_marker='foot_r_z'):
    """Generate full GRF data with all 18 components for OpenSim"""
    time = ik_table.getIndependentColumn()
    grf_data = osim.TimeSeriesTable()
    
    # All required GRF components
    grf_components = [
        "ground_force_vx", "ground_force_vy", "ground_force_vz",
        "ground_force_px", "ground_force_py", "ground_force_pz",
        "1_ground_force_vx", "1_ground_force_vy", "1_ground_force_vz",
        "1_ground_force_px", "1_ground_force_py", "1_ground_force_pz",
        "ground_torque_x", "ground_torque_y", "ground_torque_z",
        "1_ground_torque_x", "1_ground_torque_y", "1_ground_torque_z"
    ]
    grf_data.setColumnLabels(grf_components)
    
    # 1. Detect contact periods automatically
    try:
        foot_z = ik_table.getDependentColumn(foot_marker).to_numpy()
        print("foot_z:", foot_z)  # Debugging line
        contact_threshold = np.percentile(foot_z, 10) + 0.02  # 2cm above lowest
        print("contact_threshold:", contact_threshold)  # Debugging line
        in_contact = foot_z < contact_threshold
        print("Contact periods:", np.sum(in_contact))  # Debugging line
    except Exception as e:
        print(f"Error with foot marker: {e}. Using time-based contact estimation")
        in_contact = np.zeros(len(time), dtype=bool)
        for i, t in enumerate(time):
            if 0.4 <= (t % 1.0) <= 0.8:  # For cyclic motion
                in_contact[i] = True
        print("Using time-based contact estimation. Contact periods:", np.sum(in_contact))  # Debugging line
    
    # 2. Generate biomechanically realistic GRF patterns
    for i, t in enumerate(time):
        if in_contact[i]:
            # Calculate normalized contact progress (0-1)
            contact_start = max(0, i - np.argmax(in_contact[:i][::-1])) if in_contact[i] else 0
            contact_end = min(len(time)-1, i + np.argmax(in_contact[i:])) if in_contact[i] else 0
            
            # Prevent division by zero
            if contact_end != contact_start:
                contact_progress = (i - contact_start) / (contact_end - contact_start)
            else:
                contact_progress = 0.0  # Or use a default value like 0.0
            
            # Vertical force (double peak)
            vy = body_weight * (1.5 * np.exp(-12.5*(contact_progress-0.25)**2) + 
                               1.0 * np.exp(-12.5*(contact_progress-0.75)**2))
            
            # Horizontal forces
            vx = body_weight * 0.15 * np.sin(2*np.pi*contact_progress)
            vz = body_weight * (-0.3 * np.exp(-20*(contact_progress-0.3)**2) + 
                               0.25 * np.exp(-20*(contact_progress-0.7)**2))
            
            # Center of Pressure trajectory (heel to toe)
            cop_x = 0.1 * np.sin(np.pi*contact_progress)  # Mediolateral
            cop_y = 0.05 + 0.15*contact_progress         # Anteroposterior
            cop_z = 0.0
            
            # Torques (small physiological values)
            tx = body_weight * 0.01 * np.sin(2*np.pi*contact_progress)
            ty = body_weight * 0.005 * (1 - 2*contact_progress)
            tz = body_weight * 0.01 * np.cos(2*np.pi*contact_progress)
            
            # Calculate the "1" set of forces and torques by applying slight offsets
            # Adjust the "1" set to be slightly different from the original, representing a second contact source
            vy_1 = vy * 0.9
            vx_1 = vx * 1.1
            vz_1 = vz * 1.1
            cop_x_1 = cop_x * 1.05
            cop_y_1 = cop_y * 0.95
            cop_z_1 = cop_z * 1.05
            tx_1 = tx * 0.9
            ty_1 = ty * 1.1
            tz_1 = tz * 0.95
            
            # Ensure all 18 columns are filled
            row_values = [
                vx, vy, vz, cop_x, cop_y, cop_z,   # Forces and COP (ground)
                vx_1, vy_1, vz_1, cop_x_1, cop_y_1, cop_z_1,  # Forces and COP (1_ground)
                tx, ty, tz, tx_1, ty_1, tz_1        # Torques (ground and 1_ground)
            ]
        else:
            # Swing phase - minimal residual forces (ensure all columns are filled)
            row_values = [
                body_weight * 0.01 * np.random.randn(),  # ground_force_vx
                body_weight * 0.02,                      # ground_force_vy
                body_weight * 0.01 * np.random.randn(),  # ground_force_vz
                0.0, 0.0, 0.0,                          # ground_force_px, py, pz
                body_weight * 0.01 * np.random.randn(),  # 1_ground_force_vx
                body_weight * 0.02,                      # 1_ground_force_vy
                body_weight * 0.01 * np.random.randn(),  # 1_ground_force_vz
                0.0, 0.0, 0.0,                          # 1_ground_force_px, py, pz
                0.0, 0.0, 0.0,                          # ground_torque_x, y, z
                0.0, 0.0, 0.0                           # 1_ground_torque_x, y, z
            ]
            
        # Ensure no NaN values
        row_values = [0.0 if np.isnan(x) else x for x in row_values]
        grf_data.appendRow(t, osim.RowVector(row_values))
    
    return grf_data

