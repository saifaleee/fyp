import cv2
import numpy as np

class GoalVisualizer:
    def __init__(self):
        """
        Initialize the goal visualizer
        """
        pass

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
        goalpost_color_threshold = 5

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

def process_video(video_path, output_path, left_label=None, center_label=None, right_label=None, delay=100):
    """
    Process the input video and create visualization
    Args:
        video_path: Path to input video
        output_path: Path to save output video
        left_label: Label for left region
        center_label: Label for center region
        right_label: Label for right region
        delay: Delay between frames in milliseconds (default: 100ms)
    """
    # Initialize goal visualizer
    visualizer = GoalVisualizer()

    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Detect goal and create visualization
        goal_box = visualizer.detect_goal(frame)
        if goal_box is not None:
            frame = visualizer.divide_goal_area(frame, goal_box, left_label, center_label, right_label)

        # Write frame to output video
        out.write(frame)

        # Display frame with delay
        cv2.imshow('Goal Analysis', frame)

        # Wait for 'delay' milliseconds, break if 'q' is pressed
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    # Clean up
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    video_path = "020.mp4"
    output_path = "020_viz.mp4"

    # Process video with labels
    process_video(video_path, output_path, left_label="10%", center_label="20%", right_label="70%", delay=100)
00