# Football Penalty Analysis System

## Overview
This project is a comprehensive system for analyzing football (soccer) penalty kicks using computer vision and pose estimation. It processes videos of penalty kicks, segments them into key frames, augments the dataset, and analyzes both the player's pose and the goal area.

## Features
- Video frame extraction (26 key frames per kick)
- Dataset augmentation through horizontal flipping
- Goal area detection and visualization
- 3D pose estimation using MMPose
- Kick direction classification (Left/Center/Right)
- Video processing pipeline with quality checks

## Project Structure
Classified_Clips/
├── Left_Kicks/ # Original left-direction kicks
├── Right_Kicks/ # Original right-direction kicks
├── Center_Kicks/ # Original center-direction kicks
├── Results/ # Processed videos
│ ├── Processed_Left_Kicks/
│ ├── Processed_Right_Kicks/
│ ├── Processed_Center_Kicks/
│ ├── Processed_aug_Left_Kicks/
│ ├── Processed_aug_Right_Kicks/
│ └── Processed_aug_Center_Kicks/
└── Keypoints/ # Extracted pose keypoints

## Dependencies
- Python 3.8+
- OpenCV
- NumPy
- MMPose
- Ultralytics YOLO

## Installation
bash
pip install opencv-python numpy mmpose ultralytics pandas

## Usage
1. Organize your penalty kick videos into appropriate directories:
python:Classified_Clips/organize_files.py
startLine: 4
endLine: 31

2. Run the main processing pipeline:
bash
python main.py


The pipeline includes:
1. Frame count verification
2. Extraction of 26 key frames
3. Dataset augmentation
4. Pose estimation
5. Goal area visualization

## Components

### 1. Frame Extraction
Extracts 26 key frames from each video, including:
- First 3 frames
- Last 3 frames
- 20 evenly distributed middle frames

### 2. Data Augmentation
Creates mirrored versions of kicks to double the dataset size and balance directional distribution.

### 3. Pose Estimation
Uses MMPose to extract 17 key body points from each frame, saving data in both JSON and CSV formats.

### 4. Goal Visualization
Implements goal area detection and visualization with:
- Goal post detection
- Area segmentation into three regions
- Color-coded probability zones

## Output
- Processed videos with 26 frames
- Augmented dataset with mirrored kicks
- 3D pose keypoints in JSON/CSV format
- Visualized goal areas with probability zones

## Notes
- Ensure input videos have sufficient frames (≥26)
- Goal visualization works best with clear view of goal posts
- Pose estimation requires good lighting and visible player

## License
MIT License

## Contributors
Saif Ali Khan
Abdullah Khan
Hamza Khalid