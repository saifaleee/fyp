import cv2
import os

# Input and output folder paths
input_folder = "../test_clips"
output_folder = "../testing/Extracted_Frames_test"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

def extract_26_frames(video_path, output_folder):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Ensure the video is valid
    if not cap.isOpened():
        print(f"Error: Unable to process video {video_path} or it is not 24fps.")
        return
    
    # Get original file name (without extension)
    original_name = os.path.splitext(os.path.basename(video_path))[0]

    # Always include the first 3 and last 3 frames
    first_frames = list(range(0, min(3, total_frames)))  # First 3 frames
    last_frames = list(range(max(total_frames - 3, 0), total_frames))  # Last 3 frames
    
    # Determine middle frames
    middle_frame_count = 26 - len(first_frames) - len(last_frames)  # Frames left for the middle section
    middle_start = len(first_frames)  # Start after first 3 frames
    middle_end = total_frames - len(last_frames)  # End before last 3 frames

    # Pick middle frames with consistent gaps
    middle_frames = []
    if middle_frame_count > 0 and middle_start < middle_end:
        gap = (middle_end - middle_start) / middle_frame_count  # Floating point gap
        middle_frames = [int(middle_start + i * gap) for i in range(middle_frame_count)]

    # Combine all selected frames
    frame_indices = sorted(set(first_frames + middle_frames + last_frames))

    # Prepare to save a new video
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_name = os.path.join(output_folder, f"{original_name}_extracted.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_name, fourcc, fps, (width, height))
    
    # Read and save selected frames
    frame_counter = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_counter in frame_indices:
            out.write(frame)
        frame_counter += 1
    
    # Release resources
    cap.release()
    out.release()
    print(f"Extracted 26 frames saved as {output_name}")

# Process all videos in the input folder
for video_file in os.listdir(input_folder):
    if video_file.endswith(('.mp4', '.avi', '.mov')):
        video_path = os.path.join(input_folder, video_file)
        extract_26_frames(video_path, output_folder)
