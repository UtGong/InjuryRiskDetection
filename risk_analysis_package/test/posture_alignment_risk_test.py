import os
import sys
import json
from datetime import datetime
import traceback

# Add package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

try:
    # Import the module - check if it's accessible
    from risk_identification.posture_alignment_risk import extract_motion_risk
    print("Successfully imported the module")

    # Create output directory for plots and reports
    output_dir = os.path.join(package_root, "data", "output", f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")

    # Define paths to input files
    ik_file = os.path.join(package_root, "data", "01_01_ik.mot")
    model_file = os.path.join(package_root, "data", "bsm.osim")
    so_activation_file = os.path.join(package_root, "data", "ResultStaticOptimization", "SO_StaticOptimization_activation.sto")
    so_force_file = os.path.join(package_root, "data", "ResultStaticOptimization", "SO_StaticOptimization_force.sto")

    # Check if input files exist
    for file_path in [ik_file, model_file, so_activation_file, so_force_file]:
        if os.path.exists(file_path):
            print(f"File exists: {file_path}")
        else:
            print(f"WARNING: File does not exist: {file_path}")

    # Run the risk assessment function with try/except
    print("\nRunning extract_motion_risk function...")
    risk_report = extract_motion_risk(
        ik_file=ik_file,
        model_file=model_file,
        so_activation_file=so_activation_file,
        so_force_file=so_force_file,
        output_dir=output_dir
    )
    
    # Check if risk_report is None
    if risk_report is None:
        print("ERROR: extract_motion_risk function returned None")
        sys.exit(1)
        
    # Print results summary
    print("\n=== POSTURE AND ALIGNMENT RISK ASSESSMENT ===")
    
    # Check if summary is in the risk_report
    if 'summary' not in risk_report:
        print("WARNING: 'summary' key not found in risk_report")
        risk_report['summary'] = {}
    
    print(f"Overall Risk Level: {risk_report['summary'].get('overall_risk_level', 'Unknown')}")
    print(f"Risk Count: {risk_report['summary'].get('risk_count', 0)}")
    print(f"Total Risk Duration: {risk_report['summary'].get('total_risk_duration', 0):.2f}s")

    # Print detailed risks
    if 'risks' not in risk_report:
        print("WARNING: 'risks' key not found in risk_report")
        risk_report['risks'] = []
        
    if risk_report['risks']:
        print("\n=== DETECTED RISKS ===")
        for i, risk in enumerate(risk_report['risks'], 1):
            if isinstance(risk, dict):
                if 'Error' not in risk:
                    print(f"{i}. {risk.get('Risk Type', 'Unknown Risk')}")
                    print(f"   - Measured Value: {risk.get('Measured Value', 'N/A')}")
                    print(f"   - Safety Threshold: {risk.get('Safety Threshold', 'N/A')}")
                    print(f"   - Time Period: {risk.get('Time Period', 'N/A')}")
                    print(f"   - Duration: {risk.get('Duration', 'N/A')}")
                else:
                    print(f"{i}. ERROR in {risk.get('Risk Type', 'Unknown')}: {risk.get('Error', 'Unknown error')}")
            else:
                print(f"{i}. WARNING: Risk entry is not a dictionary: {risk}")

    # Show recommendations
    if 'recommendations' not in risk_report:
        print("WARNING: 'recommendations' key not found in risk_report")
        risk_report['recommendations'] = []
        
    if risk_report['recommendations']:
        print("\n=== RECOMMENDATIONS ===")
        for i, rec in enumerate(risk_report['recommendations'], 1):
            print(f"{i}. {rec}")

    # Save full results to JSON file for later analysis
    try:
        serializable_report = risk_report.copy()
        serializable_report.pop('plots', None)  # Remove matplotlib plots that can't be serialized
        
        # Convert numpy values to regular Python types if metrics exist
        if 'metrics' in serializable_report:
            for metric_name, metric_data in serializable_report.get('metrics', {}).items():
                for key, value in metric_data.items():
                    if isinstance(value, (list, tuple)) and value and hasattr(value[0], 'item'):
                        metric_data[key] = [float(x) for x in value]
                    elif hasattr(value, 'item'):
                        metric_data[key] = float(value)
        
        with open(os.path.join(output_dir, 'risk_assessment_results.json'), 'w') as f:
            json.dump(serializable_report, f, indent=2)
            print(f"\nResults successfully saved to: {os.path.join(output_dir, 'risk_assessment_results.json')}")
    except Exception as e:
        print(f"ERROR saving JSON results: {str(e)}")

    print(f"\nAnalysis complete. Results saved to: {output_dir}")

except ImportError as e:
    print(f"ERROR importing module: {str(e)}")
    print("Make sure the module is in the correct location and the package structure is proper.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    print("Stack trace:")
    traceback.print_exc()