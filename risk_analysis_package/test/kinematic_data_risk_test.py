import os
import sys

# Add package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

from risk_identification.kinematic_data_risk import check_kinematic_injury_risk

def test_kinematic_injury_risk():
    """Test function that prints detected risks in the required format"""
    # Define paths (update these as needed)
    ik_mot_path = os.path.abspath(os.path.join(package_root, "data", "01_01_ik.mot"))
    osim_model_path = os.path.abspath(os.path.join(package_root, "data", "bsm.osim"))
    so_activation_path = os.path.abspath(os.path.join(package_root, "data", "SO_Results", "SO_StaticOptimization_activation.sto"))
    so_force_path = os.path.abspath(os.path.join(package_root, "data", "ResultStaticOptimization", "SO_StaticOptimization_force.sto"))
    
    # Run analysis
    risk_report = check_kinematic_injury_risk(
        ik_mot_path=ik_mot_path,
        osim_model_path=osim_model_path,
        so_activation_path=so_activation_path,
        so_force_path=so_force_path
    )
    
    # Print results
    print("\n=== KINEMATIC INJURY RISK ASSESSMENT ===")
    print(f"Analyzed file: {risk_report['metadata']['ik_file']}")
    
    if not risk_report['detected_risks']:
        print("\nNo injury risks detected - all values within safe thresholds")
    else:
        for risk in risk_report['detected_risks']:
            print(f"\nRISK DETECTED: {risk['risk_type']}")
            print(f"- Affected coordinate: {risk['coordinate']}")
            print(f"- Measure type: {risk['measure']}")
            print(f"- Peak value: {risk['measured_value']:.1f} {risk['units']}")
            print(f"- Safety threshold: {risk['threshold']} {risk['units']}")
            print(f"- Rationale: {risk['rationale']}")
            
            # Format time points nicely
            times_str = ", ".join(f"{t:.3f}s" for t in risk['risky_times'])
            print(f"- Risk occurs at time(s): {times_str}")
            
            if 'muscle_loading' in risk:
                muscle = risk['muscle_loading']
                print(f"- Muscle loading (peak): {muscle['peak_force']:.1f} {muscle['units']}")
                forces_str = ", ".join(f"{f:.1f}N" for f in muscle['values_at_risk_times'])
                print(f"- Muscle forces at risk times: {forces_str}")
    
    # Print any warnings
    if risk_report['metadata']['warnings']:
        print("\nWARNINGS:")
        for warning in risk_report['metadata']['warnings']:
            print(f"- {warning}")

if __name__ == "__main__":
    test_kinematic_injury_risk()