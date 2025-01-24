import os
import shutil

def organize_videos():
    # Define paths for main directory and output folders
    main_directory = os.getcwd()  # Get current working directory
    left_kicks_folder = os.path.join(main_directory, "Left_Kicks")
    center_kicks_folder = os.path.join(main_directory, "Center_Kicks")
    right_kicks_folder = os.path.join(main_directory, "Right_Kicks")

    # Create the output folders if they don't exist
    os.makedirs(left_kicks_folder, exist_ok=True)
    os.makedirs(center_kicks_folder, exist_ok=True)
    os.makedirs(right_kicks_folder, exist_ok=True)

    # Iterate through folders 1, 2, and 3
    for folder in ["1", "2", "3"]:
        sub_folder_path = os.path.join(main_directory, folder)

        # Process videos from 'left' sub-folder
        left_videos = os.path.join(sub_folder_path, "left")
        rename_and_move_videos(left_videos, left_kicks_folder, "left")

        # Process videos from 'center' sub-folder
        center_videos = os.path.join(sub_folder_path, "center")
        rename_and_move_videos(center_videos, center_kicks_folder, "center")

        # Process videos from 'right' sub-folder
        right_videos = os.path.join(sub_folder_path, "right")
        rename_and_move_videos(right_videos, right_kicks_folder, "right")

    print("Videos organized successfully!")

def rename_and_move_videos(source_folder, destination_folder, prefix):
    if not os.path.exists(source_folder):
        print(f"Source folder does not exist: {source_folder}")
        return

    # Get all files already in the destination folder
    existing_files = os.listdir(destination_folder)
    counter = len(existing_files) + 1  # Start numbering based on existing files

    for file_name in os.listdir(source_folder):
        if file_name.endswith(".mp4"):  # Only process video files
            source_path = os.path.join(source_folder, file_name)

            # Generate unique name to avoid collisions
            while True:
                new_name = f"{counter:03d}_{prefix}.mp4"  # Example: 001_left.mp4
                destination_path = os.path.join(destination_folder, new_name)
                if not os.path.exists(destination_path):  # Check if name is unique
                    break
                counter += 1

            shutil.move(source_path, destination_path)  # Move and rename file
            counter += 1

if __name__ == "__main__":
    organize_videos()
