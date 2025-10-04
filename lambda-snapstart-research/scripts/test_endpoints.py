import requests
import json
import time

# Updated API endpoints from latest deployment
BASELINE_URL = "https://fqtvzqi6ah.execute-api.us-east-1.amazonaws.com/Prod/predict/baseline"
SNAPSTART_URL = "https://fqtvzqi6ah.execute-api.us-east-1.amazonaws.com/Prod/predict/snapstart"

def test_endpoint(url, name):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    # Test payload (iris flower features)
    payload = {
        "features": [
            [5.1, 3.5, 1.4, 0.2],
            [6.7, 3.0, 5.2, 2.3]
        ]
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Status Code: {response.status_code}")
        print(f"Client-Side Latency: {(end_time - start_time)*1000:.2f} ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ SUCCESS!")
            print(f"\nPredictions: {data['predictions']}")
            print(f"\nPerformance Metrics:")
            for key, value in data['metrics'].items():
                print(f"  - {key}: {value}")
        else:
            print(f"\n✗ ERROR: {response.text}")
            
    except Exception as e:
        print(f"\n✗ EXCEPTION: {str(e)}")

def main():
    print("Testing Lambda SnapStart Research Endpoints")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test baseline first
    test_endpoint(BASELINE_URL, "Baseline (No SnapStart)")
    
    # Wait a moment
    time.sleep(2)
    
    # Test SnapStart
    test_endpoint(SNAPSTART_URL, "SnapStart Enabled")
    
    print(f"\n{'='*60}")
    print("Testing Complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
