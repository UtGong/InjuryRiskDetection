# InjuryRiskDetection

**A system for automatic injury risk detection from athlete videos, leveraging advanced pose estimation and biomechanical analysis.**

---

## Overview

**InjuryRiskDetection** enables users to assess injury risk for athletes directly from video input.
The system’s main feature is a pipeline that:

1. **Performs pose estimation** on the athlete in the input video to extract 3D body poses.
2. **Computes biomechanical metrics** based on the estimated poses, including:

   * Joint angles
   * Joint forces and torques
   * Kinematic data
   * Muscle forces and activations
   * Posture alignment
3. **Detects injury risk** by analyzing these metrics, flagging movements or patterns associated with increased injury probability.

This fully automated pipeline brings together state-of-the-art computer vision and biomechanics modeling for practical athlete health monitoring.

---

## Main Feature

Given a sports video, the system will:

* Automatically extract the athlete’s pose frame-by-frame using pose estimation.
* Process the pose data to compute joint-level biomechanics (angles, forces, torques, muscle activations, etc.).
* Analyze the resulting biomechanical signals to detect high-risk movements or postures.
* Summarize the risk findings to inform injury prevention or intervention strategies.

The **full process and a sample test case** can be found in
`risk_analysis_package/test/test.py`.

---

## Example Project Structure

```
InjuryRiskDetection/
├── risk_analysis_package/
│   ├── risk_identification/
│   ├── motion_data_computing/
│   ├── data/
│   ├── motion/
│   ├── test/                # ← test.py: demo and full pipeline example
│   └── README.md
├── jupyter_notebooks/
│   └── risk_analysis/
├── SMPL2AddBiomechanics/
├── trc_data/
└── requirements.txt
```

---

## Getting Started

Clone and install requirements:

```bash
git clone https://github.com/UtGong/InjuryRiskDetection.git
cd InjuryRiskDetection
pip install -r requirements.txt
```

**Run the end-to-end demo:**

```bash
python risk_analysis_package/test/test.py
```

Or, open a Jupyter notebook in `jupyter_notebooks/risk_analysis/` to try interactive analysis.

---

## Contribution

Contributions are welcome!
Feel free to open an issue or pull request.

---

## License

This project is licensed under the MIT License.
