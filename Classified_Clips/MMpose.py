import os
import json
import cv2
import pandas as pd
import warnings
import threading
import torch
import time
import gc
from mmpose.apis import MMPoseInferencer
from mmpose.utils import register_all_modules

# Suppress specific tkinter warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Initialize threading lock
threading_lock = threading.Lock()

register_all_modules()

class Infer3D:
    def __init__(self, device='cuda'):
        """Initialize with specific threading and warning handling"""
        # Check if CUDA is available
        if device == 'cuda' and not torch.cuda.is_available():
            print("WARNING: CUDA is not available, falling back to CPU")
            device = 'cpu'
        
        # Print device information
        if device == 'cuda':
            gpu_name = torch.cuda.get_device_name(0)
            print(f"\nUsing GPU: {gpu_name}")
            print(f"CUDA Version: {torch.version.cuda}")
            
            # Get available GPU memory
            total_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)  # GB
            free_mem = torch.cuda.memory_reserved(0) / (1024 ** 3)  # GB
            print(f"GPU Memory: {total_mem:.2f} GB total, {free_mem:.2f} GB reserved")
        else:
            print("\nUsing CPU for inference (this will be slower)")
        
        with threading_lock:
            self.inferencer = MMPoseInferencer(pose3d='human3d', device=device)
            
        self.device = device
        
    def infer_frame(self, frame, frame_idx, output_folder, return_vis=False, save_vis=False):
        """
        Infer keypoints on a single frame with better error handling
        """
        try:
            with threading_lock:
                result_generator = self.inferencer(frame, return_vis=return_vis)
                result = next(result_generator)

            # Access the predictions for the current frame
            predictions = result.get('predictions', [])[0]
            
            if save_vis and return_vis:
                visualization = result.get('visualization', [None])[0]
                if visualization is not None:
                    vis_path = os.path.join(output_folder, f"frame_{frame_idx:04d}.jpg")
                    # Use try-except for visualization saving
                    try:
                        cv2.imwrite(vis_path, cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR))
                    except Exception as e:
                        print(f"Warning: Could not save visualization for frame {frame_idx}: {e}")

            return predictions
            
        except Exception as e:
            print(f"Warning: Error processing frame {frame_idx}: {e}")
            return None

    def process_video(self, video_path, output_base_folder, return_vis=True, save_vis=False):
        """Process a single video with improved error handling"""
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_output_folder = os.path.join(output_base_folder, video_name)
        
        # Check if video was already processed
        json_path = os.path.join(video_output_folder, f"{video_name}_keypoints.json")
        if os.path.exists(json_path):
            print(f"Video {video_name} already processed. Skipping.")
            return video_output_folder
            
        os.makedirs(video_output_folder, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return None

        frame_idx = 0
        keypoints_list = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\nProcessing {video_name} ({total_frames} frames)")
        start_time = time.time()
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Show progress with time estimate
                if frame_idx % 5 == 0:  # Update progress every 5 frames
                    elapsed = time.time() - start_time
                    frames_per_second = frame_idx / elapsed if elapsed > 0 else 0
                    remaining_frames = total_frames - frame_idx
                    eta_seconds = remaining_frames / frames_per_second if frames_per_second > 0 else 0
                    
                    minutes, seconds = divmod(eta_seconds, 60)
                    hours, minutes = divmod(minutes, 60)
                    
                    progress = (frame_idx / total_frames) * 100
                    eta_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                    
                    print(f"\rProgress: {progress:.1f}% (Frame {frame_idx}/{total_frames}) | FPS: {frames_per_second:.1f} | ETA: {eta_str}", end="")

                # Infer on the frame
                predictions = self.infer_frame(
                    frame, frame_idx, video_output_folder, return_vis=return_vis, save_vis=save_vis
                )

                # Process keypoints
                frame_keypoints = []
                if predictions and isinstance(predictions, list) and len(predictions) > 0:
                    keypoints = predictions[0].get('keypoints', None)
                    if keypoints is not None:
                        frame_keypoints = keypoints[:17]
                
                keypoints_list.append(frame_keypoints)
                frame_idx += 1
                
                # Clear CUDA cache periodically to prevent memory leaks
                if self.device == 'cuda' and frame_idx % 10 == 0:
                    torch.cuda.empty_cache()

        except Exception as e:
            print(f"\nError processing video {video_name}: {e}")
        finally:
            cap.release()
            total_time = time.time() - start_time
            print(f"\nFinished processing {frame_idx} frames in {total_time:.2f} seconds ({frame_idx/total_time:.1f} FPS)")

        # Save keypoints
        try:
            with open(json_path, 'w') as f:
                json.dump(keypoints_list, f, indent=2)

            csv_path = os.path.join(video_output_folder, f"{video_name}_keypoints.csv")
            df = pd.DataFrame(keypoints_list)
            df.to_csv(csv_path, index=False)

            print(f"Saved keypoints to {video_output_folder}")
            
            # Force garbage collection
            keypoints_list = None
            df = None
            gc.collect()
            if self.device == 'cuda':
                torch.cuda.empty_cache()
                
            return video_output_folder

        except Exception as e:
            print(f"Error saving keypoints for {video_name}: {e}")
            return None

def process_all_videos(input_folder, output_base_folder, return_vis=True, save_vis=False):
    """Process all videos with better progress tracking"""
    infer3d = Infer3D()
    processed_folders = []

    # Get list of videos and check which ones are already processed
    videos = []
    already_processed = []
    
    print("\nScanning for videos...")
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mov')):
                video_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, input_folder)
                video_name = os.path.splitext(file)[0]
                
                # Check if output exists
                video_output_base = os.path.join(output_base_folder, rel_path)
                json_path = os.path.join(video_output_base, video_name, f"{video_name}_keypoints.json")
                
                if os.path.exists(json_path):
                    already_processed.append((root, file))
                else:
                    videos.append((root, file))

    total_new = len(videos)
    total_processed = len(already_processed)
    
    print(f"\nFound {total_new + total_processed} videos:")
    print(f"- {total_new} new videos to process")
    print(f"- {total_processed} already processed")
    
    # Process new videos
    for idx, (root, file) in enumerate(videos, 1):
        print(f"\nProcessing video {idx}/{total_new}: {file}")
        
        video_path = os.path.join(root, file)
        rel_path = os.path.relpath(root, input_folder)
        video_output_base = os.path.join(output_base_folder, rel_path)
        os.makedirs(video_output_base, exist_ok=True)
        
        output_folder = infer3d.process_video(
            video_path, 
            video_output_base,
            return_vis=return_vis,
            save_vis=save_vis
        )
        
        if output_folder:
            processed_folders.append(output_folder)
    
    # Add already processed folders to the list
    for root, file in already_processed:
        rel_path = os.path.relpath(root, input_folder)
        video_name = os.path.splitext(file)[0]
        video_output_folder = os.path.join(output_base_folder, rel_path, video_name)
        processed_folders.append(video_output_folder)

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
