import os
import json
import cv2
import pandas as pd
from mmpose.apis import MMPoseInferencer
from mmpose.utils import register_all_modules

register_all_modules()


class Infer3D:
    def __init__(self, device='cuda'):
        self.inferencer = MMPoseInferencer(pose3d='human3d', device=device)

    def infer_frame(self, frame, frame_idx, output_folder, return_vis=False, save_vis=False):
        """
        Infer keypoints on a single frame.
        """
        result_generator = self.inferencer(frame, return_vis=return_vis)
        result = next(result_generator)  # Get the result for this frame

        # Access the predictions for the current frame
        predictions = result.get('predictions', [])[0]  # Get the first frame's prediction
        keypoints = predictions[0].get('keypoints', None)  # Assuming you want the first set of keypoints
        
        visualization = result.get('visualization', [None])[0] 

        # Save visualization if needed
        if save_vis and visualization is not None:
            vis_path = os.path.join(output_folder, f"frame_{frame_idx:04d}.jpg")
            cv2.imwrite(vis_path, cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR))

        return predictions

    def process_video(self, video_path, output_base_folder, return_vis=True, save_vis=False):
        """
        Process a single video and save its keypoints.
        """
        # Create output folder structure
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_output_folder = os.path.join(output_base_folder, video_name)
        os.makedirs(video_output_folder, exist_ok=True)

        # Extract frames and process
        cap = cv2.VideoCapture(video_path)
        frame_idx = 0
        keypoints_list = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Infer on the frame
            predictions = self.infer_frame(
                frame, frame_idx, video_output_folder, return_vis=return_vis, save_vis=save_vis
            )

            # Process keypoints
            frame_keypoints = []
            if predictions and isinstance(predictions, list) and len(predictions) > 0:
                keypoints = predictions[0].get('keypoints', None)
                if keypoints is not None:
                    frame_keypoints = keypoints[:17]  # Ensure only 17 keypoints are added
                else:
                    print(f"Warning: No keypoints detected for frame {frame_idx} in {video_name}")
            else:
                print(f"Warning: No predictions returned for frame {frame_idx} in {video_name}")

            keypoints_list.append(frame_keypoints)
            frame_idx += 1

        cap.release()

        # Save keypoints
        json_path = os.path.join(video_output_folder, f"{video_name}_keypoints.json")
        csv_path = os.path.join(video_output_folder, f"{video_name}_keypoints.csv")

        with open(json_path, 'w') as f:
            json.dump(keypoints_list, f, indent=4)

        df = pd.DataFrame(keypoints_list)
        df.to_csv(csv_path, index=False)

        print(f"Processed {video_name}: Saved keypoints to {video_output_folder}")
        return video_output_folder

def process_all_videos(input_folder, output_base_folder, return_vis=True, save_vis=False):
    """
    Process all videos in the input folder and its subfolders.
    """
    infer3d = Infer3D()
    processed_folders = []

    # Process each video in the folder
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mov')):
                video_path = os.path.join(root, file)
                # Create corresponding output folder structure
                rel_path = os.path.relpath(root, input_folder)
                video_output_base = os.path.join(output_base_folder, rel_path)
                os.makedirs(video_output_base, exist_ok=True)
                
                output_folder = infer3d.process_video(
                    video_path, 
                    video_output_base,
                    return_vis=return_vis,
                    save_vis=save_vis
                )
                processed_folders.append(output_folder)

    return processed_folders

def main():
    # Example usage
    input_folder = "Results"  # Your Results folder containing all processed videos
    output_base_folder = "Keypoints"  # Where keypoint data will be saved
    
    processed_folders = process_all_videos(
        input_folder=input_folder,
        output_base_folder=output_base_folder,
        return_vis=True,
        save_vis=True
    )
    
    print(f"Processing complete! Processed {len(processed_folders)} videos.")

if __name__ == "__main__":
    main()
