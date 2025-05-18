import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
# The line `from .create_external_loads import create_external_loads_file` is importing the
# `create_external_loads_file` function from a module named `create_external_loads` that is located in
# the same directory as the current script (hence the dot notation). This allows the current script to
# use the `create_external_loads_file` function to create an external loads file as part of the
# Inverse Dynamics pipeline setup.
from .create_external_loads import create_external_loads_file

def create_inverse_dynamics_setup(output_dir, setup_name, model_file, coordinates_file, grf_mot_file, time_range=(0.4, 1.6), lowpass_cutoff=6.0):
    """Create a complete Inverse Dynamics pipeline (both external loads and setup files)."""
    os.makedirs(output_dir, exist_ok=True)

    # Create external loads file
    ext_loads_file = os.path.join(output_dir, f"{setup_name}_grf.xml")
    create_external_loads_file(ext_loads_file, grf_mot_file)

    # Create inverse dynamics setup file
    setup_file = os.path.join(output_dir, f"{setup_name}_Setup_InverseDynamics.xml")
    
    opensim_doc = Element("OpenSimDocument", Version="20302")
    id_tool = SubElement(opensim_doc, "InverseDynamicsTool", name=setup_name)
    
    # Add elements to setup file
    SubElement(id_tool, "results_directory").text = os.path.join(output_dir, "ResultsInverseDynamics")
    SubElement(id_tool, "input_directory").text = output_dir
    SubElement(id_tool, "model_file").text = os.path.basename(model_file)
    SubElement(id_tool, "time_range").text = f"{time_range[0]:.8f} {time_range[1]:.8f}"
    SubElement(id_tool, "forces_to_exclude").text = "Muscles"
    SubElement(id_tool, "external_loads_file").text = ext_loads_file
    SubElement(id_tool, "coordinates_file").text = coordinates_file
    SubElement(id_tool, "lowpass_cutoff_frequency_for_coordinates").text = f"{lowpass_cutoff:.8f}"
    SubElement(id_tool, "output_gen_force_file").text = "inverse_dynamics.sto"
    
    # Create pretty XML
    rough_xml = tostring(opensim_doc, 'utf-8')
    parsed_xml = minidom.parseString(rough_xml)
    pretty_xml = parsed_xml.toprettyxml(indent="\t")
    
    # Write to file
    with open(setup_file, 'w') as f:
        f.write(pretty_xml)
    
    print(f"Created Inverse Dynamics setup file: {setup_file}")
    return setup_file
