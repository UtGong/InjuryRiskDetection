import os
import sys
import time

# Add the package root to sys.path
current_dir = os.path.dirname(__file__)
package_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, package_root)

from motion_data_computing.static_optimization.run_static_optimization import run_static_optimization


model_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/bsm.osim"
ik_table_path = "/home/ubuntu/injury_detection/risk_analysis_package/data/output_motion_segment_0_ik.mot"
output_dir = os.path.abspath("../data")
ext_loads_file = os.path.join(output_dir, "0101_grf.xml")

start_time = time.time()

so_results_dir = run_static_optimization(
    model_file=model_path,
    coordinates_file=ik_table_path,
    ext_loads_file=ext_loads_file,
    results_dir=os.path.join(output_dir, "ResultStaticOptimization"),
    setup_xml=os.path.join(output_dir, "SO_AnalyzeTool_setup.xml")
)

run_time = time.time() - start_time
print(f"Static Optimization completed in {run_time:.2f} seconds.")