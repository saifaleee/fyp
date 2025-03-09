import os
import glob

def rename_files_in_folder(folder_path, direction):
    """
    Rename all video files in the given folder to a standard format.
    
    Args:
        folder_path: Path to the folder containing video files
        direction: The kick direction ('left', 'center', or 'right')
    """
    # Get list of video files
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv']
    video_files = []
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    # Sort files to get consistent numbering
    video_files.sort()
    
    print(f"Found {len(video_files)} video files in {folder_path}")
    
    # Rename files
    for i, old_path in enumerate(video_files, 1):
        # Get file extension
        _, file_extension = os.path.splitext(old_path)
        
        # Create new filename
        new_filename = f"{i:03d}_{direction}{file_extension}"
        new_path = os.path.join(folder_path, new_filename)
        
        # Check if destination file already exists
        if os.path.exists(new_path) and old_path != new_path:
            print(f"Warning: {new_filename} already exists, skipping rename of {os.path.basename(old_path)}")
            continue
        
        # Rename file
        os.rename(old_path, new_path)
        print(f"Renamed: {os.path.basename(old_path)} -> {new_filename}")

def main():
    # Define folders and their corresponding directions
    folders = {
        "Classified_Clips/Left_Kicks": "left",
        "Classified_Clips/Center_Kicks": "center",
        "Classified_Clips/Right_Kicks": "right"
    }
    
    # Process each folder
    for folder_path, direction in folders.items():
        if os.path.exists(folder_path):
            print(f"\nProcessing {direction} kicks folder...")
            rename_files_in_folder(folder_path, direction)
        else:
            print(f"Warning: Folder {folder_path} not found")
    
    print("\nRenaming complete!")

if __name__ == "__main__":
    main()
