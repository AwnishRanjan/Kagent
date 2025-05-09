"""
Model training utility for the Kubernetes Predictor.

This script trains an Isolation Forest model for anomaly detection on Kubernetes metrics
and saves it to a file to be used by the KubernetesPredictor.
"""

import os
import numpy as np
import pandas as pd
import logging
import joblib
import argparse
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

def generate_sample_data(n_samples=1000, n_features=5):
    """
    Generate synthetic training data for the model.
    
    In a real-world scenario, this would be replaced with historical metrics
    from your Kubernetes clusters.
    
    Args:
        n_samples: Number of samples to generate
        n_features: Number of features (CPU, memory, disk pressure, etc.)
        
    Returns:
        DataFrame with synthetic data
    """
    # Generate normal data (most of the data)
    normal_data = np.random.normal(50, 15, size=(int(n_samples * 0.9), n_features))
    normal_data = np.clip(normal_data, 0, 100)  # Clip values to 0-100 range
    
    # Generate anomaly data (outliers)
    anomaly_data = np.random.normal(80, 10, size=(int(n_samples * 0.1), n_features))
    anomaly_data = np.clip(anomaly_data, 0, 100)
    
    # Combine data
    data = np.vstack([normal_data, anomaly_data])
    
    # Create dataframe
    feature_names = [
        'cpu_usage',
        'memory_usage',
        'disk_pressure',
        'memory_pressure',
        'pid_pressure'
    ]
    
    # Ensure we only use the needed features
    feature_names = feature_names[:n_features]
    
    df = pd.DataFrame(data, columns=feature_names)
    
    return df

def train_and_save_model(output_path=None, contamination=0.1):
    """
    Train an Isolation Forest model and save it to a file.
    
    Args:
        output_path: Path to save the model
        contamination: Expected proportion of anomalies in the data
    """
    if output_path is None:
        output_path = os.path.expanduser("~/.kagent/models/predictor_model.joblib")
    else:
        # Convert to absolute path if needed
        output_path = os.path.abspath(output_path)
    
    logger.info(f"Will save model to: {output_path}")
    
    # Create directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate sample data (replace with real data in production)
    logger.info("Generating sample training data")
    df = generate_sample_data()
    
    # Create and fit scaler
    logger.info("Fitting StandardScaler")
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)
    
    # Create and fit Isolation Forest
    logger.info(f"Training Isolation Forest model with contamination={contamination}")
    model = IsolationForest(
        n_estimators=100,
        max_samples='auto',
        contamination=contamination,
        random_state=42
    )
    model.fit(scaled_data)
    
    # Save model and scaler
    logger.info(f"Saving model to {output_path}")
    joblib.dump(
        {
            "model": model,
            "scaler": scaler,
            "feature_names": df.columns.tolist()
        },
        output_path
    )
    
    logger.info("Model training and saving complete")
    return output_path

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Train and save an Isolation Forest model for Kubernetes metrics anomaly detection")
    parser.add_argument("--output-path", type=str, help="Path to save the model file")
    parser.add_argument("--contamination", type=float, default=0.1, help="Expected proportion of anomalies in the data (default: 0.1)")
    args = parser.parse_args()
    
    # Train and save the model
    output_path = train_and_save_model(args.output_path, args.contamination)
    print(f"Model saved to: {output_path}") 