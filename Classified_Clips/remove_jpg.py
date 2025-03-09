import os
import glob

def remove_jpg_files(directory):
    """
    Remove all .jpg files from the given directory and its subdirectories.
    
    Args:
        directory: Path to the directory to clean
    
    Returns:
        int: Number of files removed
    """
    count = 0
    
    # Find all .jpg files in the directory and subdirectories
    jpg_files = glob.glob(os.path.join(directory, "**/*.jpg"), recursive=True)
    
    # Remove each file
    for file_path in jpg_files:
        try:
            os.remove(file_path)
            count += 1
            if count % 100 == 0:  # Print progress every 100 files
                print(f"Removed {count} files so far...")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
    
    return count

def main():
    keypoints_dir = "Classified_Clips/Keypoints"
    
    if not os.path.exists(keypoints_dir):
        print(f"Error: Directory '{keypoints_dir}' not found")
        return
    
    print(f"Scanning for .jpg files in {keypoints_dir}...")
    removed_count = remove_jpg_files(keypoints_dir)
    
    print(f"\nOperation complete! Removed {removed_count} .jpg files")

if __name__ == "__main__":
    main()
