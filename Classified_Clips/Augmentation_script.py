import os
import cv2

def augment_video(input_path, output_path):
    try:
        # Open the video file
        cap = cv2.VideoCapture(input_path)
        
        # Get the video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip the frame horizontally (mirror across x-axis)
            flipped_frame = cv2.flip(frame, 1)
            
            # Write the flipped frame to the output video
            out.write(flipped_frame)
        
        # Release the video objects
        cap.release()
        out.release()
        
        print(f"Saved augmented video: {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

def augment_clips(results_folder):
    # Define the input and output folder mappings
    folder_mappings = {
        "Processed_Left_Kicks": "Processed_aug_Right_Kicks",
        "Processed_Right_Kicks": "Processed_aug_Left_Kicks",
        "Processed_Center_Kicks": "Processed_aug_Center_Kicks"
    }
    
    # Process each folder
    for input_folder_name, output_folder_name in folder_mappings.items():
        # Create full paths
        input_folder = os.path.join(results_folder, input_folder_name)
        output_folder = os.path.join(results_folder, output_folder_name)
        
        # Skip if input folder doesn't exist
        if not os.path.exists(input_folder):
            print(f"Skipping {input_folder_name} - folder not found")
            continue
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        print(f"Processing {input_folder_name} -> {output_folder_name}")
        
        # Process each video in the input folder
        for video_file in os.listdir(input_folder):
            if video_file.endswith(('.mp4', '.avi', '.mov')):
                input_path = os.path.join(input_folder, video_file)
                output_path = os.path.join(output_folder, video_file)
                augment_video(input_path, output_path)

if __name__ == "__main__":
    # Path to the Results folder
    results_folder = "Classified_Clips/Results"
    augment_clips(results_folder)
    print("Augmentation complete!")
