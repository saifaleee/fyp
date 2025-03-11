import cv2
import numpy as np
import os

class GoalkeeperAnimator:
    def __init__(self, animations_folder="Fbx Animations"):
        """
        Initialize goalkeeper animator with PNG sequences
        animations_folder should contain:
        - dive_left/
        - dive_center/
        - dive_right/
        Each folder containing PNG sequence of the animation
        """
        # Print current working directory to debug
        print(f"[DEBUG] GoalkeeperAnimator: Initializing with folder '{animations_folder}'")
        print(f"[DEBUG] Current working directory: {os.getcwd()}")
        
        # Check if the animations folder exists
        if not os.path.exists(animations_folder):
            print(f"[ERROR] Animations folder '{animations_folder}' not found!")
            print(f"[ERROR] Full path: {os.path.abspath(animations_folder)}")
        else:
            print(f"[DEBUG] Found animations folder: {os.path.abspath(animations_folder)}")
            # List contents of the folder
            print(f"[DEBUG] Contents of {animations_folder}:")
            for item in os.listdir(animations_folder):
                item_path = os.path.join(animations_folder, item)
                if os.path.isdir(item_path):
                    print(f"[DEBUG]   - {item}/ (directory with {len(os.listdir(item_path))} files)")
                else:
                    print(f"[DEBUG]   - {item} (file)")
        
        print(f"[DEBUG] Loading animations from {animations_folder}...")
        self.animations = {
            'left': self._load_animation(os.path.join(animations_folder, 'dive_left')),
            'center': self._load_animation(os.path.join(animations_folder, 'dive_center')),
            'right': self._load_animation(os.path.join(animations_folder, 'dive_right'))
        }
        print(f"[DEBUG] Loaded animations: left({len(self.animations['left'])}), center({len(self.animations['center'])}), right({len(self.animations['right'])})")
        
        self.current_animation = None
        self.current_frame = 0
        self.total_video_frames = 0
        self.current_video_frame = 0
        self.animation_speed = 0.60  # Play only 50% of the animation
        self.y_offset_percentage = 0.30  # Move animation 25% lower
        print(f"[DEBUG] GoalkeeperAnimator initialized successfully")
    
    def _load_animation(self, folder_path):
        """Load PNG sequence from folder"""
        print(f"[DEBUG] Loading animation from: {folder_path}")
        frames = []
        if not os.path.exists(folder_path):
            print(f"[WARNING] Animation folder not found: {folder_path}")
            return frames

        # List all files in the folder to debug
        print(f"[DEBUG] Contents of {folder_path}:")
        file_count = 0
        for file in sorted(os.listdir(folder_path)):
            file_path = os.path.join(folder_path, file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            print(f"[DEBUG]   - {file} ({file_size:.1f} KB)")
            file_count += 1
            if file_count > 10:
                print(f"[DEBUG]   ... and {len(os.listdir(folder_path)) - 10} more files")
                break
            
            # Check if it's a PNG with correct case
            if file.lower().endswith('.png'):
                img_path = os.path.join(folder_path, file)
                print(f"[DEBUG] Attempting to load image: {file}")
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    print(f"[DEBUG]    Successfully loaded image: {file} (shape: {img.shape})")
                    frames.append(img)
                else:
                    print(f"[ERROR]    Failed to load image: {file}")
        
        if not frames:
            print(f"[WARNING] No PNG files found in {folder_path}")
            # Check for case sensitivity issues
            png_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.PNG'))]
            if png_files:
                print(f"[DEBUG]  However, found these potential PNG files: {png_files}")
                print(f"[DEBUG]  Check file extensions - they should be lowercase .png")
        else:
            print(f"[DEBUG] Loaded {len(frames)} animation frames from {folder_path}")
            
        return frames

    def set_animation(self, direction, total_video_frames=None, animation_speed=0.5, y_offset_percentage=0.25):
        """
        Set current animation based on prediction and video length
        
        Args:
            direction: 'left', 'center', or 'right'
            total_video_frames: Total number of frames in the video
            animation_speed: Speed factor (0.5 = play 50% of animation)
            y_offset_percentage: How much lower to position the animation (0.25 = 25% lower)
        """
        print(f"[DEBUG] Setting animation to '{direction}' with {total_video_frames} frames")
        if direction not in self.animations:
            print(f"[WARNING] Unknown direction '{direction}'. Using 'center'")
            direction = 'center'
            
        self.current_animation = self.animations[direction]
        self.current_frame = 0
        self.current_video_frame = 0
        self.animation_speed = animation_speed
        self.y_offset_percentage = y_offset_percentage
        
        # Set total video frames if provided
        if total_video_frames is not None:
            self.total_video_frames = total_video_frames
            print(f"[DEBUG] Animation will play at {animation_speed*100}% speed over {total_video_frames} video frames")
            print(f"[DEBUG] Animation will be positioned {y_offset_percentage*100}% lower")
        
        print(f"[DEBUG] Set animation to '{direction}' ({len(self.current_animation)} frames)")
    
    def overlay_frame(self, background, goal_box):
        """
        Overlay current animation frame on background, with adjusted position and speed
        """
        if (self.current_animation is None or 
            not self.current_animation or 
            self.current_video_frame >= self.total_video_frames):
            if self.current_video_frame >= self.total_video_frames:
                print(f"[DEBUG] Reached end of animation: frame {self.current_video_frame}/{self.total_video_frames}")
            return background
            
        # Calculate which animation frame to use based on video progress and speed
        if self.total_video_frames > 0 and len(self.current_animation) > 0:
            # Map video frame index to animation frame index with speed adjustment
            animation_progress = (self.current_video_frame / self.total_video_frames) * self.animation_speed
            frame_idx = min(int(animation_progress * len(self.current_animation)), 
                           len(self.current_animation) - 1)
            
            # Print debug info every 5 frames
            if self.current_video_frame % 5 == 0:
                print(f"[DEBUG] Overlay frame {self.current_video_frame}/{self.total_video_frames}, " 
                      f"animation frame {frame_idx}/{len(self.current_animation)-1}, "
                      f"progress: {animation_progress:.2f}")
                
            anim_frame = self.current_animation[frame_idx]
        else:
            # Fallback to sequential playback if total_video_frames not set
            if self.current_frame >= len(self.current_animation):
                print(f"[DEBUG] Reached end of sequential animation: frame {self.current_frame}/{len(self.current_animation)}")
                return background
            anim_frame = self.current_animation[self.current_frame]
            print(f"[DEBUG] Sequential overlay: frame {self.current_frame}/{len(self.current_animation)-1}")
            self.current_frame += 1
        
        # Calculate goalkeeper position relative to goal
        x1, y1, x2, y2 = goal_box
        goal_center_x = (x1 + x2) // 2
        goal_bottom = y2
        
        # Scale animation to match goal size
        goal_width = x2 - x1
        scale_factor = goal_width / anim_frame.shape[1]
        scaled_width = int(anim_frame.shape[1] * scale_factor)
        scaled_height = int(anim_frame.shape[0] * scale_factor)
        
        try:
            print(f"[DEBUG] Scaling animation: {anim_frame.shape} -> ({scaled_width}, {scaled_height})")
            scaled_frame = cv2.resize(anim_frame, (scaled_width, scaled_height))
            print(f"[DEBUG] Scaling successful")
        except Exception as e:
            print(f"[ERROR] Error scaling animation: {e}")
            self.current_video_frame += 1
            return background
        
        # Calculate position to place goalkeeper with Y-offset
        gk_x = goal_center_x - scaled_width // 2
        
        # Apply the Y-offset (25% lower)
        y_offset = int(scaled_height * self.y_offset_percentage)
        gk_y = goal_bottom - scaled_height + y_offset
        
        print(f"[DEBUG] Positioning at ({gk_x}, {gk_y}) with goal box {goal_box}")
        
        # Ensure coordinates are within image bounds
        if gk_y < 0:
            print(f"[DEBUG] Y-coordinate out of bounds, adjusting...")
            scaled_frame = scaled_frame[-gk_y:, :]
            gk_y = 0
        if gk_x < 0:
            print(f"[DEBUG] X-coordinate out of bounds, adjusting...")
            scaled_frame = scaled_frame[:, -gk_x:]
            gk_x = 0
            
        # Clip dimensions to fit within background
        if gk_y + scaled_frame.shape[0] > background.shape[0]:
            print(f"[DEBUG] Frame extends beyond bottom of background, clipping...")
            scaled_frame = scaled_frame[:background.shape[0] - gk_y, :]
        if gk_x + scaled_frame.shape[1] > background.shape[1]:
            print(f"[DEBUG] Frame extends beyond right of background, clipping...")
            scaled_frame = scaled_frame[:, :background.shape[1] - gk_x]
        
        # Overlay animation frame with alpha channel
        try:
            print(f"[DEBUG] Overlaying frame with shape {scaled_frame.shape} at ({gk_x}, {gk_y})")
            if scaled_frame.shape[2] == 4:  # With alpha channel
                alpha = scaled_frame[:, :, 3] / 255.0
                for c in range(3):
                    background[gk_y:gk_y+scaled_frame.shape[0], gk_x:gk_x+scaled_frame.shape[1], c] = \
                        (1 - alpha) * background[gk_y:gk_y+scaled_frame.shape[0], gk_x:gk_x+scaled_frame.shape[1], c] + \
                        alpha * scaled_frame[:, :, c]
                print(f"[DEBUG] Overlay successful")
            else:
                print(f"[WARNING] Frame has no alpha channel, shape: {scaled_frame.shape}")
        except Exception as e:
            print(f"[ERROR] Error overlaying animation: {e}")
        
        # Increment video frame counter
        self.current_video_frame += 1
        return background 