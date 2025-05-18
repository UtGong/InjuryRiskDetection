import os
import sys

# Add the package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

from risk_identification.joint_force_torque_risk import (
    analyze_joint_loads,
    analyze_injury_risks_from_sto,
    output_risks
)

# Path to the already generated inverse dynamics results file (.sto)
sto_file = "/home/ubuntu/injury_detection/risk_analysis_package/data/ResultsInverseDynamics/inverse_dynamics.sto"

# Example: Load and analyze joint loads, saving the plot
results = analyze_joint_loads(sto_file, body_weight=70, plot=True,
                            plot_save_path="/home/ubuntu/injury_detection/risk_analysis_package/data/joint_loads_plot.png")

# Print peaks for moments
print("Peak Moments:")
for joint, vals in results['peaks']['moments'].items():
    print(f"{joint}: max={vals['max']:.2f}, min={vals['min']:.2f}")

# Analyze additional injury risks from the sto file
risks = analyze_injury_risks_from_sto(sto_file, body_weight=70)

# Output and print the injury risk results
risk_results = output_risks(risks)
if isinstance(risk_results, list):
    for risk in risk_results:
        print(f"Risk detected: {risk['Risk detected in']}")
        print(f"  Type: {risk['Type']}")
        print(f"  Measured value: {risk['Measured value']}")
        print(f"  Safety threshold: {risk['Safety threshold']}")
        print(f"  Time: {risk['Time']}")
        print(f"  Rationale: {risk['Rationale']}")
        if 'Note' in risk:
            print(f"  Note: {risk['Note']}")
else:
    print(risk_results["message"])
