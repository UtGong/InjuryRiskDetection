import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from opensim import Model, TimeSeriesTable, Storage
import os
from datetime import datetime

def extract_motion_risk(ik_file, model_file, so_activation_file=None, so_force_file=None, output_dir=None):
    """
    Enhanced posture and alignment risk assessment with detailed metrics and visualization.

    Parameters:
    - ik_file (str): Path to the kinematic data (ik.mot)
    - model_file (str): Path to the OpenSim model (e.g., bsm.osim)
    - so_activation_file (str): Optional path to static optimization activation results
    - so_force_file (str): Optional path to static optimization force results
    - output_dir (str): Optional directory to save reports and plots

    Returns:
    - dict: Comprehensive risk assessment with metrics, plots, and recommendations
    """
    
    # Initialize results dictionary
    results = {
        'risks': [],
        'metrics': {},
        'plots': {},
        'recommendations': [],
        'summary': {}
    }

    # Load data
    ik_table = TimeSeriesTable(ik_file)
    time = np.array(ik_table.getIndependentColumn())
    
    # Create output directory if provided
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # ======================
    # 1. Trunk Lean Analysis
    # ======================
    try:
        # Get shoulder markers (convert from Vec3 to numpy arrays)
        l_shoulder = np.array([[ik_table.getDependentColumn('shoulder_l_x')[i],
                                ik_table.getDependentColumn('shoulder_l_y')[i],
                                ik_table.getDependentColumn('shoulder_l_z')[i]] 
                                for i in range(ik_table.getNumRows())])
        
        r_shoulder = np.array([[ik_table.getDependentColumn('shoulder_r_x')[i],
                                ik_table.getDependentColumn('shoulder_r_y')[i],
                                ik_table.getDependentColumn('shoulder_r_z')[i]] 
                                for i in range(ik_table.getNumRows())])
        
        # Calculate trunk lean angles (frontal plane)
        trunk_lean = np.degrees(np.arctan2(r_shoulder[:,1] - l_shoulder[:,1],
                                            r_shoulder[:,0] - l_shoulder[:,0]))
        
        # Risk assessment
        lean_threshold = 15  # degrees
        risky_frames = np.where(np.abs(trunk_lean) > lean_threshold)[0]
        
        if len(risky_frames) > 0:
            # Group consecutive indices to find continuous risk periods
            risk_periods = []
            current_period = [risky_frames[0]]
            
            for i in range(1, len(risky_frames)):
                if risky_frames[i] == risky_frames[i-1] + 1:
                    current_period.append(risky_frames[i])
                else:
                    risk_periods.append(current_period)
                    current_period = [risky_frames[i]]
            
            risk_periods.append(current_period)
            
            # Report each risk period
            for period in risk_periods:
                start_time = time[period[0]]
                end_time = time[period[-1]]
                max_lean = np.max(np.abs(trunk_lean[period]))
                
                results['risks'].append({
                    'Risk Type': 'Excessive Trunk Lean',
                    'Measured Value': f'{max_lean:.2f}° (maximum in period)',
                    'Safety Threshold': f'< {lean_threshold}° deviation',
                    'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                    'Duration': f'{end_time - start_time:.2f}s',
                    'Rationale': 'Excessive lateral trunk lean increases spinal loading and compensatory mechanisms'
                })
                
                results['recommendations'].append(
                    f"Correct lateral trunk lean (max {max_lean:.1f}° exceeds {lean_threshold}° threshold). " +
                    f"Potential causes: weak hip abductors, compensatory movement, or balance deficits."
                )
        
        # Generate plot
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(time, trunk_lean, label='Trunk Lean Angle')
        ax.axhline(y=lean_threshold, color='r', linestyle='--', label='Safe Threshold')
        ax.axhline(y=-lean_threshold, color='r', linestyle='--')
        ax.fill_between(time, lean_threshold, trunk_lean, where=(trunk_lean>lean_threshold), 
                        color='red', alpha=0.3, label='Risk Zone')
        ax.fill_between(time, -lean_threshold, trunk_lean, where=(trunk_lean<-lean_threshold), 
                        color='red', alpha=0.3)
        ax.set_title('Trunk Lean Analysis')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Angle (degrees)')
        ax.legend()
        ax.grid(True)
        results['plots']['trunk_lean'] = fig
        
        # Store metrics
        results['metrics']['trunk_lean'] = {
            'data': trunk_lean.tolist(),
            'time': time.tolist(),
            'max_value': float(np.max(np.abs(trunk_lean))),
            'mean_value': float(np.mean(np.abs(trunk_lean))),
            'threshold': lean_threshold,
            'time_above_threshold_pct': len(risky_frames) / len(time) * 100
        }
        
        # Save plot if output directory provided
        if output_dir:
            fig.savefig(os.path.join(output_dir, 'trunk_lean_analysis.png'), dpi=300)
            plt.close(fig)

    except Exception as e:
        results['risks'].append({
            'Risk Type': 'Trunk Lean Analysis Error',
            'Error': str(e),
            'Rationale': 'Failed to compute trunk lean angles from marker data'
        })

    # ========================
    # 2. Foot Pronation Analysis
    # ========================
    try:
        # Check both feet if available
        for side in ['_r', '_l']:
            if f'mtp_angle{side}' in ik_table.getColumnLabels():
                foot_angle = np.array(ik_table.getDependentColumn(f'mtp_angle{side}').to_numpy())
                
                pronation_threshold = 10  # degrees
                risky_frames = np.where(np.abs(foot_angle) > pronation_threshold)[0]
                
                if len(risky_frames) > 0:
                    # Group consecutive indices to find continuous risk periods
                    risk_periods = []
                    current_period = [risky_frames[0]]
                    
                    for i in range(1, len(risky_frames)):
                        if risky_frames[i] == risky_frames[i-1] + 1:
                            current_period.append(risky_frames[i])
                        else:
                            risk_periods.append(current_period)
                            current_period = [risky_frames[i]]
                    
                    risk_periods.append(current_period)
                    
                    # Report each risk period
                    for period in risk_periods:
                        start_time = time[period[0]]
                        end_time = time[period[-1]]
                        max_pronation = np.max(np.abs(foot_angle[period]))
                        
                        side_label = 'Right' if side == '_r' else 'Left'
                        results['risks'].append({
                            'Risk Type': f'{side_label} Foot Overpronation',
                            'Measured Value': f'{max_pronation:.2f}° (maximum in period)',
                            'Safety Threshold': f'< {pronation_threshold}° deviation',
                            'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                            'Duration': f'{end_time - start_time:.2f}s',
                            'Rationale': 'Excessive foot pronation can lead to increased stress on the plantar fascia, Achilles tendon, and medial knee structures'
                        })
                        
                        results['recommendations'].append(
                            f"Address {side_label.lower()} foot overpronation (max {max_pronation:.1f}° exceeds {pronation_threshold}° threshold). " +
                            f"Consider gait retraining, foot strengthening, or orthotic intervention."
                        )
                
                # Generate plot
                fig, ax = plt.subplots(figsize=(10,5))
                ax.plot(time, foot_angle, label=f'Foot Angle {side[1:].upper()}')
                ax.axhline(y=pronation_threshold, color='r', linestyle='--', label='Safe Threshold')
                ax.axhline(y=-pronation_threshold, color='r', linestyle='--')
                ax.fill_between(time, pronation_threshold, foot_angle, 
                                where=(foot_angle>pronation_threshold), 
                                color='red', alpha=0.3, label='Risk Zone')
                ax.fill_between(time, -pronation_threshold, foot_angle, 
                                where=(foot_angle<-pronation_threshold), 
                                color='red', alpha=0.3)
                ax.set_title(f'Foot Pronation Analysis {side[1:].upper()}')
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Angle (degrees)')
                ax.legend()
                ax.grid(True)
                results['plots'][f'foot_pronation{side}'] = fig
                
                # Store metrics
                results['metrics'][f'foot_pronation{side}'] = {
                    'data': foot_angle.tolist(),
                    'time': time.tolist(),
                    'max_value': float(np.max(np.abs(foot_angle))),
                    'mean_value': float(np.mean(np.abs(foot_angle))),
                    'threshold': pronation_threshold,
                    'time_above_threshold_pct': len(risky_frames) / len(time) * 100
                }
                
                # Save plot if output directory provided
                if output_dir:
                    fig.savefig(os.path.join(output_dir, f'foot_pronation_{side[1:]}_analysis.png'), dpi=300)
                    plt.close(fig)

    except Exception as e:
        results['risks'].append({
            'Risk Type': 'Foot Pronation Analysis Error',
            'Error': str(e),
            'Rationale': 'Failed to compute foot pronation angles'
        })

    # ========================
    # 3. Pelvic Tilt Analysis
    # ========================
    try:
        if 'pelvis_tilt' in ik_table.getColumnLabels():
            pelvic_tilt = np.array(ik_table.getDependentColumn('pelvis_tilt').to_numpy())
            
            tilt_threshold = 15  # degrees
            risky_frames = np.where(np.abs(pelvic_tilt) > tilt_threshold)[0]
            
            if len(risky_frames) > 0:
                # Group consecutive indices to find continuous risk periods
                risk_periods = []
                current_period = [risky_frames[0]]
                
                for i in range(1, len(risky_frames)):
                    if risky_frames[i] == risky_frames[i-1] + 1:
                        current_period.append(risky_frames[i])
                    else:
                        risk_periods.append(current_period)
                        current_period = [risky_frames[i]]
                
                risk_periods.append(current_period)
                
                # Report each risk period
                for period in risk_periods:
                    start_time = time[period[0]]
                    end_time = time[period[-1]]
                    max_tilt = np.max(np.abs(pelvic_tilt[period]))
                    
                    tilt_direction = "anterior" if np.mean(pelvic_tilt[period]) > 0 else "posterior"
                    
                    results['risks'].append({
                        'Risk Type': f'Excessive {tilt_direction.capitalize()} Pelvic Tilt',
                        'Measured Value': f'{max_tilt:.2f}° (maximum in period)',
                        'Safety Threshold': f'< {tilt_threshold}° deviation',
                        'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                        'Duration': f'{end_time - start_time:.2f}s',
                        'Rationale': f'Excessive {tilt_direction} pelvic tilt can lead to lumbar spine stress, hip joint impingement, and altered movement mechanics'
                    })
                    
                    if tilt_direction == "anterior":
                        rec = f"Correct excessive anterior pelvic tilt (max {max_tilt:.1f}° exceeds {tilt_threshold}° threshold). " + \
                                f"Consider addressing hip flexor tightness and core strengthening."
                    else:
                        rec = f"Correct excessive posterior pelvic tilt (max {max_tilt:.1f}° exceeds {tilt_threshold}° threshold). " + \
                                f"Consider addressing hamstring tightness and lumbar stabilization."
                        
                    results['recommendations'].append(rec)
            
            # Generate plot
            fig, ax = plt.subplots(figsize=(10,5))
            ax.plot(time, pelvic_tilt, label='Pelvic Tilt Angle')
            ax.axhline(y=tilt_threshold, color='r', linestyle='--', label='Safe Threshold')
            ax.axhline(y=-tilt_threshold, color='r', linestyle='--')
            ax.fill_between(time, tilt_threshold, pelvic_tilt, 
                            where=(pelvic_tilt>tilt_threshold), 
                            color='red', alpha=0.3, label='Risk Zone')
            ax.fill_between(time, -tilt_threshold, pelvic_tilt, 
                            where=(pelvic_tilt<-tilt_threshold), 
                            color='red', alpha=0.3)
            ax.set_title('Pelvic Tilt Analysis')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Angle (degrees)')
            ax.legend()
            ax.grid(True)
            results['plots']['pelvic_tilt'] = fig
            
            # Store metrics
            results['metrics']['pelvic_tilt'] = {
                'data': pelvic_tilt.tolist(),
                'time': time.tolist(),
                'max_value': float(np.max(np.abs(pelvic_tilt))),
                'mean_value': float(np.mean(np.abs(pelvic_tilt))),
                'threshold': tilt_threshold,
                'time_above_threshold_pct': len(risky_frames) / len(time) * 100
            }
            
            # Save plot if output directory provided
            if output_dir:
                fig.savefig(os.path.join(output_dir, 'pelvic_tilt_analysis.png'), dpi=300)
                plt.close(fig)

    except Exception as e:
        results['risks'].append({
            'Risk Type': 'Pelvic Tilt Analysis Error',
            'Error': str(e),
            'Rationale': 'Failed to compute pelvic tilt angles'
        })

    # ==================================
    # 4. Knee Valgus/Varus Analysis
    # ==================================
    try:
        if all(col in ik_table.getColumnLabels() for col in ['knee_valgus_r', 'knee_valgus_l']):
            for side in ['_r', '_l']:
                knee_angle = np.array(ik_table.getDependentColumn(f'knee_valgus{side}').to_numpy())
                
                valgus_threshold = 10  # degrees inward
                varus_threshold = -8   # degrees outward
                
                valgus_frames = np.where(knee_angle > valgus_threshold)[0]
                varus_frames = np.where(knee_angle < varus_threshold)[0]
                
                # Process valgus risk periods
                if len(valgus_frames) > 0:
                    # Group consecutive indices to find continuous risk periods
                    risk_periods = []
                    current_period = [valgus_frames[0]]
                    
                    for i in range(1, len(valgus_frames)):
                        if valgus_frames[i] == valgus_frames[i-1] + 1:
                            current_period.append(valgus_frames[i])
                        else:
                            risk_periods.append(current_period)
                            current_period = [valgus_frames[i]]
                    
                    risk_periods.append(current_period)
                    
                    # Report each risk period
                    side_label = 'Right' if side == '_r' else 'Left'
                    for period in risk_periods:
                        start_time = time[period[0]]
                        end_time = time[period[-1]]
                        max_valgus = np.max(knee_angle[period])
                        
                        results['risks'].append({
                            'Risk Type': f'{side_label} Knee Valgus',
                            'Measured Value': f'{max_valgus:.2f}° (maximum in period)',
                            'Safety Threshold': f'< {valgus_threshold}° inward',
                            'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                            'Duration': f'{end_time - start_time:.2f}s',
                            'Rationale': 'Excessive knee valgus can increase MCL, ACL strain and patellofemoral stress'
                        })
                        
                        results['recommendations'].append(
                            f"Address {side_label.lower()} knee valgus collapse (max {max_valgus:.1f}° exceeds {valgus_threshold}° threshold). " +
                            f"Focus on hip abductor/external rotator strengthening and neuromuscular control."
                        )
                
                # Process varus risk periods
                if len(varus_frames) > 0:
                    # Group consecutive indices to find continuous risk periods
                    risk_periods = []
                    current_period = [varus_frames[0]]
                    
                    for i in range(1, len(varus_frames)):
                        if varus_frames[i] == varus_frames[i-1] + 1:
                            current_period.append(varus_frames[i])
                        else:
                            risk_periods.append(current_period)
                            current_period = [varus_frames[i]]
                    
                    risk_periods.append(current_period)
                    
                    # Report each risk period
                    side_label = 'Right' if side == '_r' else 'Left'
                    for period in risk_periods:
                        start_time = time[period[0]]
                        end_time = time[period[-1]]
                        max_varus = np.min(knee_angle[period])
                        
                        results['risks'].append({
                            'Risk Type': f'{side_label} Knee Varus',
                            'Measured Value': f'{max_varus:.2f}° (maximum in period)',
                            'Safety Threshold': f'> {varus_threshold}° outward',
                            'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                            'Duration': f'{end_time - start_time:.2f}s',
                            'Rationale': 'Excessive knee varus can increase lateral joint stress and LCL strain'
                        })
                        
                        results['recommendations'].append(
                            f"Address {side_label.lower()} knee varus thrust (max {max_varus:.1f}° exceeds {varus_threshold}° threshold). " +
                            f"Consider lateral stabilization training and addressing potential hip abductor overactivity."
                        )
                
                # Generate plot
                fig, ax = plt.subplots(figsize=(10,5))
                ax.plot(time, knee_angle, label=f'Knee Valgus/Varus Angle {side[1:].upper()}')
                ax.axhline(y=valgus_threshold, color='r', linestyle='--', label='Valgus Threshold')
                ax.axhline(y=varus_threshold, color='b', linestyle='--', label='Varus Threshold')
                ax.fill_between(time, valgus_threshold, knee_angle, 
                                where=(knee_angle>valgus_threshold), 
                                color='red', alpha=0.3, label='Valgus Risk Zone')
                ax.fill_between(time, varus_threshold, knee_angle, 
                                where=(knee_angle<varus_threshold), 
                                color='blue', alpha=0.3, label='Varus Risk Zone')
                ax.set_title(f'Knee Valgus/Varus Analysis {side[1:].upper()}')
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Angle (degrees)')
                ax.legend()
                ax.grid(True)
                results['plots'][f'knee_valgus{side}'] = fig
                
                # Store metrics
                results['metrics'][f'knee_valgus{side}'] = {
                    'data': knee_angle.tolist(),
                    'time': time.tolist(),
                    'max_valgus': float(np.max(knee_angle)),
                    'max_varus': float(np.min(knee_angle)),
                    'mean_value': float(np.mean(knee_angle)),
                    'valgus_threshold': valgus_threshold,
                    'varus_threshold': varus_threshold,
                    'time_in_valgus_pct': len(valgus_frames) / len(time) * 100,
                    'time_in_varus_pct': len(varus_frames) / len(time) * 100
                }
                
                # Save plot if output directory provided
                if output_dir:
                    fig.savefig(os.path.join(output_dir, f'knee_valgus_{side[1:]}_analysis.png'), dpi=300)
                    plt.close(fig)

    except Exception as e:
        results['risks'].append({
            'Risk Type': 'Knee Valgus/Varus Analysis Error',
            'Error': str(e),
            'Rationale': 'Failed to compute knee valgus/varus angles'
        })

    # ==================================
    # 5. Muscle Activation Correlation
    # ==================================
    if so_activation_file and so_force_file:
        try:
            # Load muscle data
            activation_table = TimeSeriesTable(so_activation_file)
            force_table = TimeSeriesTable(so_force_file)
            
            # Example: Check for over-activation of specific muscles
            target_muscles = ['rect_fem_r', 'rect_fem_l', 'glut_max_r', 'glut_max_l', 
                                'gaslat_r', 'gaslat_l', 'gasmed_r', 'gasmed_l']
            
            for muscle in target_muscles:
                if muscle in activation_table.getColumnLabels():
                    activation = np.array(activation_table.getDependentColumn(muscle).to_numpy())
                    force = np.array(force_table.getDependentColumn(muscle).to_numpy())
                    
                    # Find peak activation times
                    activation_threshold = 0.8  # 80% activation threshold
                    peak_activation_frames = np.where(activation > activation_threshold)[0]
                    
                    if len(peak_activation_frames) > 0:
                        # Group consecutive indices to find continuous risk periods
                        risk_periods = []
                        current_period = [peak_activation_frames[0]]
                        
                        for i in range(1, len(peak_activation_frames)):
                            if peak_activation_frames[i] == peak_activation_frames[i-1] + 1:
                                current_period.append(peak_activation_frames[i])
                            else:
                                risk_periods.append(current_period)
                                current_period = [peak_activation_frames[i]]
                        
                        risk_periods.append(current_period)
                        
                        # Report each risk period
                        muscle_name = muscle.replace('_', ' ').replace('r', 'right').replace('l', 'left')
                        
                        for period in risk_periods:
                            start_time = time[period[0]]
                            end_time = time[period[-1]]
                            max_activation = np.max(activation[period])
                            max_force = np.max(force[period])
                            
                            results['risks'].append({
                                'Risk Type': f'{muscle_name.title()} Overactivation',
                                'Measured Value': f'{max_activation:.2f} activation, {max_force:.1f}N force',
                                'Safety Threshold': f'< {activation_threshold} sustained activation',
                                'Time Period': f'{start_time:.2f}s to {end_time:.2f}s',
                                'Duration': f'{end_time - start_time:.2f}s',
                                'Rationale': f'Prolonged high activation of {muscle_name} can lead to muscle fatigue, imbalance, and compensatory movement patterns'
                            })
                            
                            results['recommendations'].append(
                                f"Investigate {muscle_name} overactivation ({max_activation:.0%} of maximum). " +
                                f"Consider movement efficiency training and assessing potential compensatory patterns."
                            )
                        
                        # Generate plot
                        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,8), sharex=True)
                        ax1.plot(time, activation, label=f'{muscle_name.title()} Activation')
                        ax1.axhline(y=activation_threshold, color='r', linestyle='--', label='Threshold')
                        ax1.fill_between(time, activation_threshold, activation, 
                                        where=(activation>activation_threshold), 
                                        color='red', alpha=0.3, label='Risk Zone')
                        ax1.set_title(f'{muscle_name.title()} Activation Analysis')
                        ax1.set_ylabel('Activation Level')
                        ax1.legend()
                        ax1.grid(True)
                        
                        ax2.plot(time, force, label=f'{muscle_name.title()} Force')
                        ax2.set_xlabel('Time (s)')
                        ax2.set_ylabel('Force (N)')
                        ax2.legend()
                        ax2.grid(True)
                        
                        plt.tight_layout()
                        results['plots'][f'{muscle}_activation'] = fig
                        
                        # Store metrics
                        results['metrics'][f'{muscle}_activation'] = {
                            'activation_data': activation.tolist(),
                            'force_data': force.tolist(),
                            'time': time.tolist(),
                            'max_activation': float(np.max(activation)),
                            'max_force': float(np.max(force)),
                            'mean_activation': float(np.mean(activation)),
                            'activation_threshold': activation_threshold,
                            'time_above_threshold_pct': len(peak_activation_frames) / len(time) * 100
                        }
                        
                        # Save plot if output directory provided
                        if output_dir:
                            fig.savefig(os.path.join(output_dir, f'{muscle}_activation_analysis.png'), dpi=300)
                            plt.close(fig)

        except Exception as e:
            results['risks'].append({
                'Risk Type': 'Muscle Activation Analysis Error',
                'Error': str(e),
                'Rationale': 'Failed to analyze muscle activation patterns'
            })

    # Generate summary
    valid_risks = [risk for risk in results['risks'] if 'Error' not in risk]
    
    if valid_risks:
        # Calculate total risk duration
        total_duration = sum(float(risk['Duration'].replace('s', '')) for risk in valid_risks 
                            if 'Duration' in risk)
        
        # Determine overall risk level
        if len(valid_risks) > 5 or total_duration > 2.0:
            overall_risk = "High"
        elif len(valid_risks) > 2 or total_duration > 1.0:
            overall_risk = "Moderate"
        else:
            overall_risk = "Low"
        
        # Count risks by type
        risk_types = {}
        for risk in valid_risks:
            risk_type = risk['Risk Type']
            if risk_type in risk_types:
                risk_types[risk_type] += 1
            else:
                risk_types[risk_type] = 1
        
        # Create summary
        risk_summary = f"Detected {len(valid_risks)} instances of potential posture/alignment risks covering {total_duration:.2f}s of motion."
        for risk_type, count in risk_types.items():
            risk_summary += f"\n- {risk_type}: {count} instances detected"
        
        results['summary'] = {
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "motion_duration_s": float(time[-1] - time[0]),
            "overall_risk_level": overall_risk,
            "risk_count": len(valid_risks),
            "risk_types_count": len(risk_types),
            "total_risk_duration": total_duration,
            "risk_summary": risk_summary
        }
    else:
        results['summary'] = {
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "motion_duration_s": float(time[-1] - time[0]),
            "overall_risk_level": "Low",
            "risk_count": 0,
            "risk_summary": "No significant posture or alignment risks detected in this motion."
        }
    
    # Save comprehensive report if output directory provided
    if output_dir:
        with open(os.path.join(output_dir, 'posture_alignment_risk_report.txt'), 'w') as f:
            f.write(f"POSTURE AND ALIGNMENT RISK REPORT\n")
            
    return results