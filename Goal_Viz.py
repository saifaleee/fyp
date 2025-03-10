import cv2
import numpy as np
from GoalkeeperAnimation import GoalkeeperAnimator

class GoalVisualizer:

    def __init__(self):
        """
        Initialize the goal visualizer
        """
        self.goalkeeper = GoalkeeperAnimator(animations_folder="Fbx Animations")

    def cieluv(self, img, target):
        """
        Compute color distance in the CIELUV space
        """
        img = img.astype('int')
        aR, aG, aB = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        bR, bG, bB = target
        rmean = ((aR + bR) / 2).astype('int')
        r2 = np.square(aR - bR)
        g2 = np.square(aG - bG)
        b2 = np.square(aB - bB)
        result = (((512 + rmean) * r2) >> 8) + 4 * g2 + (((767 - rmean) * b2) >> 8)
        result = result.astype('float64')
        result -= result.min()
        result /= result.max()
        result *= 255
        return result.astype('uint8')

    def detect_goal(self, frame):
        """
        Detect goal posts in the frame using advanced color distance and line detection
        """
        # Define goalpost color and threshold
        goalpost_color = (220, 220, 220)
        goalpost_color_threshold = 3

        # Detect goalpost color
        goalpost = self.cieluv(frame, goalpost_color) < goalpost_color_threshold
        img_goalpost = goalpost.astype(bool).astype('uint8') * 255

        # Apply morphological operations
        kernel = np.ones((7, 7), np.uint8)
        img_goalpost = cv2.morphologyEx(img_goalpost, cv2.MORPH_CLOSE, kernel)

        # Find contours of potential goalposts
        contours, _ = cv2.findContours(img_goalpost, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Variables to store goal post coordinates
        goal_box = None
        max_area = 0

        for contour in contours:
            # Get the bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            # Filter based on aspect ratio and area
            aspect_ratio = float(w) / h if h != 0 else 0
            if area > 1000 and aspect_ratio > 1.2:  # Adjust these values based on your videos
                if area > max_area:
                    max_area = area
                    goal_box = (x, y, x + w, y + h)

        return goal_box

    def divide_goal_area(self, frame, goal_box, left_label=None, center_label=None, right_label=None):
        """
        Divide the goal area into three equal regions and add labels if provided
        """
        if goal_box is None:
            return frame

        x1, y1, x2, y2 = goal_box
        total_width = x2 - x1

        # Calculate equal region widths
        region_width = total_width // 3

        # Draw goal post lines and region boundaries
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
        cv2.line(frame, (x1 + region_width, y1), (x1 + region_width, y2), (255, 255, 255), 2)
        cv2.line(frame, (x1 + 2 * region_width, y1), (x1 + 2 * region_width, y2), (255, 255, 255), 2)

        # Add labels to the regions if provided
        if left_label:
            cv2.putText(frame, left_label, (x1 + 10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        if center_label:
            cv2.putText(frame, center_label, (x1 + region_width + 10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        if right_label:
            cv2.putText(frame, right_label, (x1 + 2 * region_width + 10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return frame

def process_video(video_path, output_path, prediction, delay=100):
    """
    Process video with goalkeeper animation based on prediction
    Args:
        prediction: 'left', 'center', or 'right'
    """
    visualizer = GoalVisualizer()
    
    # Get total frames in the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Set animation with total frames, 50% speed, and 25% lower position
    visualizer.goalkeeper.set_animation(
        prediction, 
        total_frames,
        animation_speed=0.50,  # Play only 50% of the animation
        y_offset_percentage=0.3  # Position 25% lower
    )
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Detect goal and create visualization
        goal_box = visualizer.detect_goal(frame)
        if goal_box is not None:
            # Add goal visualization
            frame = visualizer.divide_goal_area(frame, goal_box)
            # Overlay goalkeeper animation
            frame = visualizer.goalkeeper.overlay_frame(frame, goal_box)
            
        out.write(frame)
        cv2.imshow('Goal Analysis', frame)
        
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test with each direction
    videos = [
        ("020.mp4", "020_viz.mp4", "right")
    ]
    
    for video_path, output_path, prediction in videos:
        print(f"Processing {video_path} with {prediction} prediction...")
        process_video(video_path, output_path, prediction, delay=150)