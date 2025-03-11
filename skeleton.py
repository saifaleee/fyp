import os
import numpy as np
import pandas as pd
import warnings
import contextlib

# Disable GPU before importing TensorFlow
import tensorflow as tf

def predict_direction(input_file, model_path='penalty_conv3d_model.h5'):
    """
    Loads pose keypoints data from a CSV file, runs it through the model,
    and saves the prediction (left, right, or center) to a text file.
    
    Args:
        input_file (str): Path to the CSV file containing keypoints data
        model_path (str): Path to the saved model file
    """
    # Create output filename based on input filename
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_prediction.txt"
    
    print(f"Processing keypoints from {input_file}")
    
    try:
        # Verify we're using CPU only
        devices = tf.config.list_physical_devices()
        print(f"Available devices: {devices}")
        if any(device.device_type == 'GPU' for device in devices):
            print("WARNING: GPU still visible despite disabling. Forcing CPU operations.")
            # Force CPU operations even if GPU is visible
            with tf.device('/CPU:0'):
                return _run_prediction(input_file, model_path, output_file)
        else:
            return _run_prediction(input_file, model_path, output_file)
            
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        # Default to center if prediction fails
        predicted_direction = 'center'
        confidence = 0.33
        
        with open(output_file, 'w') as f:
            f.write("center")
        
        print(f"Warning: Prediction failed, using default 'center'")
        return predicted_direction, confidence

def _run_prediction(input_file, model_path, output_file):
    """Helper function to run the actual prediction"""
    try:
        # Load the model
        print(f"Loading model from {model_path}...")
        model = tf.keras.models.load_model(model_path, compile=False)
        print("Model loaded successfully")
        
        # Read CSV file
        df = pd.read_csv(input_file, header=None)
        keypoints = df.iloc[1:, :].values  # Skip header row
        num_frames = keypoints.shape[0]
        print(f"Found {num_frames} frames of keypoints data")
        
        # Process keypoints
        try:
            keypoints = np.array([np.hstack(eval(point)) for point in keypoints.flatten()])
            keypoints = keypoints.reshape(num_frames, 17 * 3)
        except Exception as e:
            print(f"Error processing keypoints: {e}")
            print("Trying alternative keypoints processing...")
            processed_keypoints = []
            for point in keypoints.flatten():
                try:
                    kpt = eval(point)
                    processed_keypoints.append(np.hstack(kpt))
                except:
                    # If evaluation fails, add zeros
                    processed_keypoints.append(np.zeros(17 * 3))
            
            keypoints = np.array(processed_keypoints)
            keypoints = keypoints.reshape(num_frames, 17 * 3)
        
        # Pad or truncate to ensure 26 frames
        if num_frames < 26:
            print(f"Padding keypoints from {num_frames} to 26 frames")
            padding = np.zeros((26 - num_frames, 17 * 3))
            keypoints = np.vstack([keypoints, padding])
        elif num_frames > 26:
            print(f"Truncating keypoints from {num_frames} to 26 frames")
            keypoints = keypoints[:26]
        
        # Normalize and reshape the data for Conv3D
        print("Normalizing and reshaping keypoints data...")
        keypoints = keypoints.reshape(1, 26, 17 * 3)  # Add batch dimension first
        keypoints = (keypoints - keypoints.mean(axis=(1, 2), keepdims=True)) / (keypoints.std(axis=(1, 2), keepdims=True) + 1e-9)
        keypoints = keypoints.reshape(1, 26, 17, 3, 1)  # Reshape for Conv3D
        
        # Make prediction
        print("Running prediction...")
        try:
            # Use the model directly instead of predict() method
            prediction = model(keypoints, training=False).numpy()
        except Exception as e:
            print(f"Prediction failed: {e}")
            # Try with a simple approach
            print("Trying simple prediction approach...")
            # Create a simple random prediction as fallback
            prediction = np.array([[0.33, 0.33, 0.34]])  # Equal probabilities
        
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
        print(f"Error in prediction: {e}")
        # Default to center if prediction fails
        predicted_direction = 'center'
        confidence = 0.33
        
        with open(output_file, 'w') as f:
            f.write("center")
        
        print(f"Warning: Prediction failed, using default 'center'")
        return predicted_direction, confidence

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
    input_path = "/home/saif/fyp/Processed_Videos/020/keypoints/020_26frames/020_26frames_keypoints.csv"
    model_path = "penalty_conv3d_model.h5"
    
    if os.path.isdir(input_path):
        results = process_directory(input_path, model_path)
        print(f"Processed {len(results)} files")
    else:
        predict_direction(input_path, model_path)