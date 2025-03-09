import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model

def predict_direction(input_file, model_path='penalty_conv3d_model.h5'):
    """
    Loads pose keypoints data from a CSV file, runs it through the model,
    and saves the prediction (left, right, or center) to a text file.
    
    Args:
        input_file (str): Path to the CSV file containing keypoints data
        model_path (str): Path to the saved model file
    """
    # Load the model
    model = load_model(model_path)
    
    # Create output filename based on input filename
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_prediction.txt"
    
    # Load and process keypoints data
    try:
        # Read CSV file
        df = pd.read_csv(input_file, header=None)
        keypoints = df.iloc[1:, :].values  # Skip header row
        num_frames = keypoints.shape[0]
        
        # Process keypoints similar to training data
        keypoints = np.array([np.hstack(eval(point)) for point in keypoints.flatten()])
        keypoints = keypoints.reshape(num_frames, 17 * 3)
        
        # Pad or truncate to ensure 26 frames
        if num_frames < 26:
            padding = np.zeros((26 - num_frames, 17 * 3))
            keypoints = np.vstack([keypoints, padding])
        elif num_frames > 26:
            keypoints = keypoints[:26]
        
        # Normalize and reshape the data for Conv3D
        keypoints = keypoints.reshape(1, 26, 17 * 3)  # Add batch dimension first
        keypoints = (keypoints - keypoints.mean(axis=(1, 2), keepdims=True)) / (keypoints.std(axis=(1, 2), keepdims=True) + 1e-9)
        keypoints = keypoints.reshape(1, 26, 17, 3, 1)  # Reshape for Conv3D
        
        # Make prediction
        prediction = model.predict(keypoints)
        class_index = np.argmax(prediction[0])
        
        # Map index to class label
        class_mapping = {0: 'center', 1: 'left', 2: 'right'}
        predicted_direction = class_mapping[class_index]
        confidence = prediction[0][class_index]
        
        # Save prediction to text file
        with open(output_file, 'w') as f:
            f.write(f"{predicted_direction}")
        
        print(f"Prediction saved to {output_file}: {predicted_direction} (confidence: {confidence:.2f})")
        return predicted_direction, confidence
        
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        with open(output_file, 'w') as f:
            f.write("Error in prediction")
        return None, None

def process_directory(directory_path, model_path='penalty_conv3d_model.h5'):
    """
    Process all CSV files in a directory
    
    Args:
        directory_path (str): Path to directory containing CSV files
        model_path (str): Path to the saved model file
    """
    results = {}
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('_keypoints.csv'):
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}...")
                direction, confidence = predict_direction(file_path, model_path)
                results[file] = {'direction': direction, 'confidence': confidence}
    
    return results

if __name__ == "__main__":
    # Define parameters directly
    input_path = "/home/saif/fyp/Processed_Videos/020/keypoints/020_26frames/020_26frames_keypoints.csv"  # Change this to your input file or directory
    model_path = "penalty_conv3d_model.h5"
    
    if os.path.isdir(input_path):
        results = process_directory(input_path, model_path)
        print(f"Processed {len(results)} files")
    else:
        predict_direction(input_path, model_path)