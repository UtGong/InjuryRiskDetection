import os
import sys

# Add package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

from risk_identification.muscle_forces_activations_risk import (
    extract_muscle_forces_activations,
    generate_risk_report
)

# Path to static optimization results files
forces_file = "/home/ubuntu/injury_detection/risk_analysis_package/data/ResultStaticOptimization/SO_StaticOptimization_force.sto"
activations_file = "/home/ubuntu/injury_detection/risk_analysis_package/data/ResultStaticOptimization/SO_StaticOptimization_activation.sto"
setup_file_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/ResultStaticOptimization/SO_StaticOptimization_controls.xml"

results = extract_muscle_forces_activations(setup_file_path, plot=True, plot_save_path="/home/ubuntu/injury_detection/risk_analysis_package/data/muscle_plot.png")
body_weight = 70  # kg

risk_report = generate_risk_report(
    results['forces'], 
    results['activations'],
    body_weight,
    output_file="/home/ubuntu/injury_detection/risk_analysis_package/data/muscle_force_risk_report.txt"
)
