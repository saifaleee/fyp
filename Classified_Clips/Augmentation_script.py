import os
import cv2

# Define folder paths
input_folders = {
    "left": "Left_Kicks",
    "right": "Right_Kicks",
    "center": "Center_Kicks",
}
output_folders = {
    "left": "right_augmented",
    "right": "left_augmented",
    "center": "center_augmented",
}

# Ensure output folders exist
for folder in output_folders.values():
    os.makedirs(folder, exist_ok=True)

# Function to augment videos by mirroring
def augment_video(input_path, output_path):
    try:
        # Open the video file
        cap = cv2.VideoCapture(input_path)
        
        # Get the video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip the frame horizontally
            flipped_frame = cv2.flip(frame, 1)
            
            # Write the flipped frame to the output video
            out.write(flipped_frame)
        
        # Release the video objects
        cap.release()
        out.release()
        
        print(f"Saved augmented video: {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

# Process each folder
for category, input_folder in input_folders.items():
    output_folder = output_folders[category]
    
    for video_file in os.listdir(input_folder):
        input_path = os.path.join(input_folder, video_file)
        # Ensure it's a video file (you can refine this filter)
        if os.path.isfile(input_path) and video_file.lower().endswith(('.mp4', '.mov', '.avi')):
            # Define the output file path
            output_path = os.path.join(output_folder, video_file)
            # Augment and save the video
            augment_video(input_path, output_path)

print("All videos processed.")
