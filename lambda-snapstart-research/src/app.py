import json
import os
import time
import joblib
import numpy as np
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch all AWS SDK calls for X-Ray tracing
patch_all()

# Global variables to track cold/warm starts
COLD_START = True
model = None
model_load_time = 0

# This runs during cold start (initialization phase)
def init():
    """Initialize model during cold start"""
    global model, model_load_time, COLD_START
    
    init_start = time.time()
    
    # Load the ML model
    model_path = os.path.join(os.path.dirname(__file__), 'model.joblib')
    model = joblib.load(model_path)
    
    model_load_time = time.time() - init_start
    print(f"Cold start - Model loaded in {model_load_time:.4f} seconds")

# Load model during initialization
if model is None:
    init()

def lambda_handler(event, context):
    """Main Lambda handler function"""
    global COLD_START
    
    handler_start = time.time()
    is_cold_start = COLD_START
    COLD_START = False
    
    try:
        # Parse input
        if isinstance(event, str):
            body = json.loads(event)
        elif 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Get input features (expecting array of features)
        features = body.get('features', [[5.1, 3.5, 1.4, 0.2]])
        
        # Perform inference
        inference_start = time.time()
        X = np.array(features)
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        inference_time = time.time() - inference_start
        
        # Calculate total handler time
        total_handler_time = time.time() - handler_start
        
        # Prepare response with detailed metrics
        response = {
            'predictions': predictions.tolist(),
            'probabilities': probabilities.tolist(),
            'metrics': {
                'is_cold_start': is_cold_start,
                'model_load_time_ms': round(model_load_time * 1000, 2),
                'inference_time_ms': round(inference_time * 1000, 2),
                'total_handler_time_ms': round(total_handler_time * 1000, 2),
                'function_type': os.environ.get('FUNCTION_TYPE', 'unknown'),
                'memory_mb': int(context.memory_limit_in_mb),
                'request_id': context.aws_request_id
            }
        }
        
        # Log metrics for CloudWatch
        print(json.dumps({
            'event': 'inference_complete',
            'cold_start': is_cold_start,
            'inference_time_ms': round(inference_time * 1000, 2),
            'total_time_ms': round(total_handler_time * 1000, 2)
        }))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'metrics': {
                    'is_cold_start': is_cold_start,
                    'function_type': os.environ.get('FUNCTION_TYPE', 'unknown')
                }
            })
        }
