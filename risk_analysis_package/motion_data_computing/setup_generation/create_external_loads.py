import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def create_external_loads_file(output_path, grf_mot_file, body_mapping=None):
    """Create an ExternalLoads XML file for OpenSim."""
    if body_mapping is None:
        body_mapping = {'right': 'calcn_r', 'left': 'calcn_l'}
    
    # Get absolute paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
    print(f"Parent directory: {parent_dir}")
    
    # Create full output path
    output_path = os.path.abspath(os.path.join(parent_dir, output_path))
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create root element
    opensim_doc = Element("OpenSimDocument", Version="20302")
    ext_loads = SubElement(opensim_doc, "ExternalLoads", name="GRF")
    objects = SubElement(ext_loads, "objects")
    
    # Create force elements
    for side in ['right', 'left']:
        force = SubElement(objects, "ExternalForce", name=side)
        SubElement(force, "isDisabled").text = "false"
        SubElement(force, "applied_to_body").text = body_mapping[side]
        SubElement(force, "force_expressed_in_body").text = "ground"
        SubElement(force, "point_expressed_in_body").text = "ground"
        
        prefix = "1_" if side == "left" else ""
        SubElement(force, "force_identifier").text = f"{prefix}ground_force_v"
        SubElement(force, "point_identifier").text = f"{prefix}ground_force_p"
        SubElement(force, "torque_identifier").text = f"{prefix}ground_torque_"
        SubElement(force, "data_source_name").text = "Unassigned"
    
    SubElement(ext_loads, "groups")
    SubElement(ext_loads, "datafile").text = os.path.basename(grf_mot_file)
    
    # Create pretty XML
    rough_xml = tostring(opensim_doc, 'utf-8')
    parsed_xml = minidom.parseString(rough_xml)
    pretty_xml = parsed_xml.toprettyxml(indent="\t")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(pretty_xml)
    
    print(f"Created ExternalLoads file: {output_path}")
    return output_path