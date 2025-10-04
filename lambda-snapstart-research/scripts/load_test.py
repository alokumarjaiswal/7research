import requests
import json
import time
import concurrent.futures
import boto3
import csv
from datetime import datetime
import os

# Configuration
BASELINE_URL = "https://6a6cmeno37.execute-api.us-east-1.amazonaws.com/Prod/predict/baseline"
SNAPSTART_URL = "https://6a6cmeno37.execute-api.us-east-1.amazonaws.com/Prod/predict/snapstart"
REGION = "us-east-1"

# AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)

class LoadTester:
    def __init__(self, output_dir='data'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.results = []
        
    def force_cold_start(self, function_name):
        """Force cold start by updating environment variable"""
        try:
            # Get current config
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            env_vars = response.get('Environment', {}).get('Variables', {})
            
            # Update with timestamp to force new execution environment
            env_vars['FORCE_COLD_START'] = str(time.time())
            
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': env_vars}
            )
            
            # Wait for update to complete
            print(f"Forcing cold start for {function_name}...")
            time.sleep(5)
            
            # Wait for function to be active
            waiter = lambda_client.get_waiter('function_updated')
            waiter.wait(FunctionName=function_name)
            print(f"Cold start forced for {function_name}")
            
        except Exception as e:
            print(f"Error forcing cold start: {e}")
    
    def invoke_function(self, url, function_type, run_id, invocation_id):
        """Single function invocation with detailed metrics"""
        payload = {
            "features": [
                [5.1, 3.5, 1.4, 0.2],
                [6.7, 3.0, 5.2, 2.3],
                [5.9, 3.0, 5.1, 1.8]
            ]
        }
        
        start_time = time.time()
        timestamp = datetime.utcnow().isoformat()
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            end_time = time.time()
            
            client_latency = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                metrics = data.get('metrics', {})
                
                result = {
                    'timestamp': timestamp,
                    'run_id': run_id,
                    'invocation_id': invocation_id,
                    'function_type': function_type,
                    'status_code': response.status_code,
                    'client_latency_ms': round(client_latency, 2),
                    'is_cold_start': metrics.get('is_cold_start', False),
                    'model_load_time_ms': metrics.get('model_load_time_ms', 0),
                    'inference_time_ms': metrics.get('inference_time_ms', 0),
                    'total_handler_time_ms': metrics.get('total_handler_time_ms', 0),
                    'memory_mb': metrics.get('memory_mb', 0),
                    'request_id': metrics.get('request_id', ''),
                    'success': True
                }
            else:
                result = {
                    'timestamp': timestamp,
                    'run_id': run_id,
                    'invocation_id': invocation_id,
                    'function_type': function_type,
                    'status_code': response.status_code,
                    'client_latency_ms': round(client_latency, 2),
                    'error': response.text,
                    'success': False
                }
                
        except Exception as e:
            end_time = time.time()
            client_latency = (end_time - start_time) * 1000
            
            result = {
                'timestamp': timestamp,
                'run_id': run_id,
                'invocation_id': invocation_id,
                'function_type': function_type,
                'client_latency_ms': round(client_latency, 2),
                'error': str(e),
                'success': False
            }
        
        return result
    
    def run_cold_start_test(self, num_iterations=10):
        """Test cold start performance"""
        print(f"\n{'='*70}")
        print("COLD START TEST")
        print(f"{'='*70}")
        print(f"Iterations: {num_iterations}")
        
        for i in range(num_iterations):
            print(f"\n--- Iteration {i+1}/{num_iterations} ---")
            
            # Force cold start for baseline
            self.force_cold_start('ml-inference-baseline')
            result_baseline = self.invoke_function(
                BASELINE_URL, 'baseline', f'cold_start_{i+1}', 1
            )
            self.results.append(result_baseline)
            print(f"Baseline: {result_baseline['client_latency_ms']:.2f}ms "
                  f"(Cold: {result_baseline.get('is_cold_start', 'Unknown')})")
            
            time.sleep(2)
            
            # Force cold start for SnapStart
            self.force_cold_start('ml-inference-snapstart')
            result_snapstart = self.invoke_function(
                SNAPSTART_URL, 'snapstart', f'cold_start_{i+1}', 1
            )
            self.results.append(result_snapstart)
            print(f"SnapStart: {result_snapstart['client_latency_ms']:.2f}ms "
                  f"(Cold: {result_snapstart.get('is_cold_start', 'Unknown')})")
            
            time.sleep(5)  # Wait before next iteration
    
    def run_warm_start_test(self, num_iterations=20):
        """Test warm start performance"""
        print(f"\n{'='*70}")
        print("WARM START TEST")
        print(f"{'='*70}")
        print(f"Iterations: {num_iterations}")
        
        # Prime the functions first
        print("\nPriming functions...")
        self.invoke_function(BASELINE_URL, 'baseline', 'prime', 0)
        time.sleep(1)
        self.invoke_function(SNAPSTART_URL, 'snapstart', 'prime', 0)
        time.sleep(2)
        
        for i in range(num_iterations):
            # Test baseline
            result_baseline = self.invoke_function(
                BASELINE_URL, 'baseline', f'warm_start_{i+1}', 1
            )
            self.results.append(result_baseline)
            
            # Test SnapStart
            result_snapstart = self.invoke_function(
                SNAPSTART_URL, 'snapstart', f'warm_start_{i+1}', 1
            )
            self.results.append(result_snapstart)
            
            if (i + 1) % 5 == 0:
                print(f"Completed {i+1}/{num_iterations} iterations")
            
            time.sleep(0.5)  # Small delay between iterations
    
    def run_concurrency_test(self, concurrency_levels=[1, 5, 10, 20]):
        """Test with different concurrency levels"""
        print(f"\n{'='*70}")
        print("CONCURRENCY TEST")
        print(f"{'='*70}")
        
        for concurrency in concurrency_levels:
            print(f"\n--- Testing Concurrency Level: {concurrency} ---")
            
            # Test baseline
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []
                for i in range(concurrency):
                    future = executor.submit(
                        self.invoke_function,
                        BASELINE_URL, 'baseline', f'concurrency_{concurrency}', i+1
                    )
                    futures.append(future)
                
                baseline_results = [f.result() for f in concurrent.futures.as_completed(futures)]
                self.results.extend(baseline_results)
            
            time.sleep(3)
            
            # Test SnapStart
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []
                for i in range(concurrency):
                    future = executor.submit(
                        self.invoke_function,
                        SNAPSTART_URL, 'snapstart', f'concurrency_{concurrency}', i+1
                    )
                    futures.append(future)
                
                snapstart_results = [f.result() for f in concurrent.futures.as_completed(futures)]
                self.results.extend(snapstart_results)
            
            print(f"Completed concurrency level {concurrency}")
            time.sleep(5)
    
    def save_results(self):
        """Save results to CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'load_test_results_{timestamp}.csv')
        
        if not self.results:
            print("No results to save")
            return
        
        # Get all unique keys from results
        all_keys = set()
        for result in self.results:
            all_keys.update(result.keys())
        
        fieldnames = sorted(list(all_keys))
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"\n{'='*70}")
        print(f"Results saved to: {filename}")
        print(f"Total records: {len(self.results)}")
        print(f"{'='*70}")
        
        return filename

def main():
    print("="*70)
    print("LAMBDA SNAPSTART PERFORMANCE TESTING")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = LoadTester()
    
    # Run tests
    tester.run_cold_start_test(num_iterations=5)
    tester.run_warm_start_test(num_iterations=20)
    tester.run_concurrency_test(concurrency_levels=[1, 5, 10, 15])
    
    # Save results
    tester.save_results()
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nTesting complete!")

if __name__ == "__main__":
    main()
