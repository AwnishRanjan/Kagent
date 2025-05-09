#!/usr/bin/env python3
"""
Script to train a simple anomaly detection model for testing
"""

import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

def generate_sample_data():
    """Generate synthetic data for anomaly detection"""
    # Normal data distribution
    normal_data = np.random.normal(50, 10, (1000, 4))
    
    # Anomalous data (with higher values)
    anomalous_data = np.random.normal(90, 5, (100, 4))
    
    # Combine data
    training_data = np.vstack((normal_data, anomalous_data))
    
    print(f"Generated {len(training_data)} training samples")
    print(f"Normal samples: {len(normal_data)}")
    print(f"Anomalous samples: {len(anomalous_data)}")
    
    return training_data

def train_model():
    """Train and save an anomaly detection model"""
    print("Generating training data...")
    training_data = generate_sample_data()
    
    print("Training model...")
    # Initialize and train the model
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,  # 10% of data is assumed to be anomalous
        random_state=42
    )
    model.fit(training_data)
    
    # Save the model
    model_path = "model.joblib"
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")
    
    return model_path

if __name__ == "__main__":
    print("Starting model training for Kagent test...")
    model_path = train_model()
    print("Training completed successfully.") 