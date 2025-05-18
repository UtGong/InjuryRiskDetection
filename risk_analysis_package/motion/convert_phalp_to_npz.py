import numpy as np
import pickle
import os
import argparse
from tqdm import tqdm
import json
import joblib

def load_pkl(pkl_path):
    """Load PHALP results from PKL file with robust error handling."""
    print(f"Attempting to load file: {pkl_path}")
    
    # Check file existence
    if not os.path.exists(pkl_path):
        raise FileNotFoundError(f"File not found: {pkl_path}")
    
    # Try different loading methods
    try:
        with open(pkl_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e1:
        print(f"Standard pickle loading failed: {e1}")
        try:
            with open(pkl_path, 'rb') as f:
                return pickle.load(f, encoding='latin1')
        except Exception as e2:
            print(f"Pickle loading with latin1 encoding failed: {e2}")
            try:
                return joblib.load(pkl_path)
            except Exception as e3:
                print(f"Joblib loading failed: {e3}")
                try:
                    with open(pkl_path, 'r') as f:
                        return json.load(f)
                except Exception as e4:
                    print(f"JSON loading failed: {e4}")
                    raise ValueError(f"Could not load file {pkl_path} with any known method")

def extract_single_person_data(data, track_id=0):
    """
    Extract data for a single person across all frames.
    If track_id is None, use the person with the most frames.
    Default is track_id 0.
    """
    # Print data structure info for debugging
    print(f"Data type: {type(data)}")
    if isinstance(data, dict):
        print(f"Dictionary with {len(data)} keys")
        if len(data) > 0:
            sample_keys = list(data.keys())[:5]
            print(f"Sample keys: {sample_keys}")
            sample_key = sample_keys[0]
            print(f"Sample value type for key '{sample_key}': {type(data[sample_key])}")
            if isinstance(data[sample_key], dict):
                print(f"Sample value keys: {list(data[sample_key].keys())}")
    
    # Count frame appearances for each track ID
    track_counts = {}
    for frame_key in data:
        frame_data = data[frame_key]
        if 'tracked_ids' not in frame_data or len(frame_data['tracked_ids']) == 0:
            continue
            
        for tid in frame_data['tracked_ids']:
            if tid not in track_counts:
                track_counts[tid] = 0
            track_counts[tid] += 1
    
    print(f"Found track IDs with counts: {track_counts}")
    
    # If track_id is None, pick the one with most appearances
    if track_id is None:
        if not track_counts:
            raise ValueError("No tracks found in the data")
        track_id = max(track_counts, key=track_counts.get)
        print(f"Selected track ID {track_id} with {track_counts[track_id]} frames")
    elif track_id in track_counts:
        print(f"Using specified track ID {track_id} with {track_counts[track_id]} frames")
    else:
        print(f"Warning: Specified track ID {track_id} not found in data. Available track IDs: {list(track_counts.keys())}")
        if track_counts:
            track_id = max(track_counts, key=track_counts.get)
            print(f"Using track ID {track_id} with most frames ({track_counts[track_id]} frames) instead")
        else:
            raise ValueError("No tracks found in the data")
    
    # Sort frame keys by time
    try:
        sorted_frames = sorted(data.keys(), key=lambda k: data[k]['time'])
    except (KeyError, TypeError):
        print("Warning: Couldn't sort frames by time, using default order")
        sorted_frames = list(data.keys())
    
    # Extract data for the selected track
    extracted_data = {
        'frames': [],
        'trans': [],
        'betas': None,  # Initialize as None, we'll set the first valid betas we find
        'poses': [],
        'times': []
    }
    
    betas_set = False  # Flag to track if we've set betas already
    
    for frame_key in sorted_frames:
        frame_data = data[frame_key]
        if 'tracked_ids' not in frame_data or len(frame_data['tracked_ids']) == 0:
            continue
            
        # Find the index of the selected track in this frame
        if track_id in frame_data['tracked_ids']:
            idx = frame_data['tracked_ids'].index(track_id)
            
            # Store the frame key
            extracted_data['frames'].append(frame_key)
            
            # Store the time
            extracted_data['times'].append(frame_data.get('time', 0))
            
            # Extract translation (use camera if available, otherwise zeros)
            if 'camera' in frame_data and idx < len(frame_data['camera']):
                extracted_data['trans'].append(frame_data['camera'][idx])
            else:
                extracted_data['trans'].append(np.zeros(3))
            
            # Extract SMPL parameters
            if 'smpl' in frame_data and idx < len(frame_data['smpl']):
                smpl_data = frame_data['smpl'][idx]
                
                # Extract betas (shape parameters) - only once
                if not betas_set and 'betas' in smpl_data:
                    extracted_data['betas'] = smpl_data['betas']
                    betas_set = True
                    print(f"Set betas with shape: {np.array(smpl_data['betas']).shape}")
                
                # Extract pose parameters
                pose = []
                # Add global orientation
                if 'global_orient' in smpl_data:
                    rot_mat = smpl_data['global_orient']
                    # Convert rotation matrix to flattened representation
                    pose.extend(rot_mat.reshape(-1))
                
                # Add body pose
                if 'body_pose' in smpl_data:
                    body_pose = smpl_data['body_pose']
                    # Convert rotation matrices to flattened representation
                    pose.extend(body_pose.reshape(-1))
                
                if pose:  # Only append if we have pose data
                    extracted_data['poses'].append(pose)
                else:
                    print(f"Warning: No pose data found for frame {frame_key}")
    
    # Print extraction summary
    print(f"Extracted {len(extracted_data['frames'])} frames")
    print(f"Poses shape: {np.array(extracted_data['poses']).shape if extracted_data['poses'] else 'No poses'}")
    if extracted_data['betas'] is not None:
        print(f"Betas shape: {np.array(extracted_data['betas']).shape}")
    else:
        print("No betas found")
    
    return extracted_data, track_id

def convert_to_npz_format(extracted_data, framerate=30, reference_npz=None):
    """Convert extracted data to the format expected by SMPL2AddBiomechanics."""
    # Check if we have any frames
    if not extracted_data['frames']:
        raise ValueError("No frames found for the selected track")
    
    # Convert lists to numpy arrays
    trans = np.array(extracted_data['trans'])
    poses = np.array(extracted_data['poses'])
    
    print(f"Converted trans shape: {trans.shape}")
    print(f"Converted poses shape: {poses.shape}")
    
    # Handle betas - ensure it's 16 dimensions
    betas = np.zeros(16)
    if extracted_data['betas'] is not None:
        betas_array = np.array(extracted_data['betas'])
        betas_len = min(betas_array.size, 16)
        betas[:betas_len] = betas_array.flatten()[:betas_len]
    
    # Handle dmpls (dynamic mesh parameters)
    num_frames = len(extracted_data['frames'])
    
    # Load reference data if available
    ref_data = None
    if reference_npz is not None:
        print(f"Loading reference NPZ from {reference_npz}")
        ref_data = np.load(reference_npz, allow_pickle=True)
    
    # Get reference shapes for format fixing
    ref_poses_shape = None
    if ref_data is not None and 'poses' in ref_data:
        ref_poses_shape = ref_data['poses'].shape
        print(f"Reference poses shape: {ref_poses_shape}")
    
    # Fix poses to match reference format if needed
    if ref_poses_shape is not None and len(ref_poses_shape) == 2 and ref_poses_shape[1] != poses.shape[1]:
        print(f"Reshaping poses from width {poses.shape[1]} to {ref_poses_shape[1]}")
        
        # Create an empty poses array with the correct shape
        fixed_poses = np.zeros((num_frames, ref_poses_shape[1]))
        
        # Determine how much data we can safely copy
        if poses.shape[1] < ref_poses_shape[1]:
            # Our poses are smaller than reference - copy what we have
            fixed_poses[:, :poses.shape[1]] = poses
            print(f"Padded missing pose parameters with zeros")
        else:
            # Our poses are larger - truncate 
            fixed_poses = poses[:, :ref_poses_shape[1]]
            print(f"Truncated extra pose parameters")
        
        poses = fixed_poses
    
    # Handle dmpls using reference if available
    if ref_data is not None and 'dmpls' in ref_data:
        ref_dmpls = ref_data['dmpls']
        
        # If reference has fewer frames than our data, loop the reference
        if len(ref_dmpls) < num_frames:
            # Calculate how many times to repeat the reference
            repeat_count = int(np.ceil(num_frames / len(ref_dmpls)))
            ref_dmpls = np.tile(ref_dmpls, (repeat_count, 1))
        
        # Take only what we need
        dmpls = ref_dmpls[:num_frames]
        print(f"Using dmpls from reference file with shape {dmpls.shape}")
    else:
        # Create empty dmpls as we don't have this data
        dmpls = np.zeros((num_frames, 8))
        print("Using zero-filled dmpls")
    
    # Create gender (assume 'neutral' as default)
    gender = 'neutral'
    
    # If reference has gender, use that instead
    if ref_data is not None and 'gender' in ref_data:
        gender = ref_data['gender']
        print(f"Using gender from reference file: {gender}")
    
    return {
        'trans': trans,
        'poses': poses,
        'betas': betas,
        'dmpls': dmpls,
        'gender': gender,
        'mocap_framerate': np.array(framerate)
    }

def save_npz(output_path, npz_data):
    """Save data in NPZ format."""
    np.savez(
        output_path,
        trans=npz_data['trans'],
        poses=npz_data['poses'],
        betas=npz_data['betas'],
        dmpls=npz_data['dmpls'],
        gender=npz_data['gender'],
        mocap_framerate=npz_data['mocap_framerate']
    )
    print(f"Saved NPZ file to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Convert PHALP PKL results to SMPL NPZ format compatible with SMPL2AddBiomechanics')
    parser.add_argument('--input', type=str, required=True, help='Path to PHALP PKL results file')
    parser.add_argument('--output', type=str, required=True, help='Path to save the NPZ file')
    parser.add_argument('--track_id', type=int, default=0, help='Specific track ID to extract (default: 0)')
    parser.add_argument('--framerate', type=float, default=30.0, help='Motion capture framerate (default: 30 fps)')
    parser.add_argument('--reference_npz', type=str, required=True, help='Path to reference NPZ file for format compatibility')
    parser.add_argument('--auto_select', action='store_true', help='Automatically select the person with most frames instead of using track_id')
    
    args = parser.parse_args()
    
    # Load PHALP results
    print(f"Loading PHALP results from {args.input}")
    try:
        phalp_data = load_pkl(args.input)
    except Exception as e:
        print(f"Error loading file: {e}")
        exit(1)
    
    # Extract data for a single person
    selected_track_id = None if args.auto_select else args.track_id
    print(f"Extracting data for {'the person with most frames' if args.auto_select else f'track ID {args.track_id}'}...")
    extracted_data, track_id = extract_single_person_data(phalp_data, selected_track_id)
    print(f"Extracted {len(extracted_data['frames'])} frames for track ID {track_id}")
    
    # Convert to NPZ format and fix formats to match reference
    print("Converting to NPZ format compatible with SMPL2AddBiomechanics...")
    npz_data = convert_to_npz_format(extracted_data, args.framerate, args.reference_npz)
    
    # Print shapes for verification
    print(f"Final trans shape: {npz_data['trans'].shape}")
    print(f"Final poses shape: {npz_data['poses'].shape}")
    print(f"Final betas shape: {npz_data['betas'].shape}")
    print(f"Final dmpls shape: {npz_data['dmpls'].shape}")
    
    # Save NPZ file
    save_npz(args.output, npz_data)
    print("Conversion completed successfully! Saved to path:", args.output)

if __name__ == "__main__":
    main()