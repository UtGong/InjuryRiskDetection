import os
import sys

# Add the package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_DEBUG_PLUGINS'] = '0'

from risk_identification.joint_angle_risk import get_joint_angles, check_joint_angles, output_risks

def test_joint_angle_risk():
    # Define your motion file and joint names (update these paths/names as needed)
    motion_file = os.path.abspath(os.path.join(package_root, "data", "01_01_ik.mot"))
    joints= [
    'knee_angle_r', 'knee_angle_l', 
    'hip_flexion_r', 'hip_adduction_r', 'hip_rotation_r', 
    'ankle_angle_r', 'subtalar_angle_r', 'mtp_angle_r',
    'hip_flexion_l', 'hip_adduction_l', 'hip_rotation_l', 
    'ankle_angle_l', 'subtalar_angle_l', 'mtp_angle_l',
    'lumbar_bending', 'lumbar_extension', 'lumbar_twist',  # These are lumbar related joints
    'scapula_abduction_r', 'scapula_elevation_r', 'scapula_upward_rot_r',  # For shoulder abduction (right side)
    'scapula_abduction_l', 'scapula_elevation_l', 'scapula_upward_rot_l'   # For shoulder abduction (left side)
    ]
    
    joint_data = get_joint_angles(motion_file, joints_to_analyze=joints, plot=True)
    injury_risks = check_joint_angles(joint_data, body_weight=70)
    risk_report = output_risks(injury_risks)
    
    # Print results from the test
    for risk in risk_report:
        print(f"Risk detected: {risk['Risk detected in']}")
        print(f"  Type: {risk['Type']}")
        print(f"  Measured value: {risk['Measured value']} (threshold: {risk['Safety threshold']})")
        print(f"  Time: {risk['Time']}")
        print(f"  Rationale: {risk['Rationale']}")
        if 'Note' in risk:
            print(f"  Note: {risk['Note']}")
        print()


if __name__ == "__main__":
    test_joint_angle_risk()
