import requests
import json
import time
import concurrent.futures
import boto3
import csv
from datetime import datetime
import os

# Configuration
BASELINE_URL = "https://fqtvzqi6ah.execute-api.us-east-1.amazonaws.com/Prod/predict/baseline"
SNAPSTART_URL = "https://fqtvzqi6ah.execute-api.us-east-1.amazonaws.com/Prod/predict/snapstart"
REGION = "us-east-1"

# AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)

class ComprehensiveLoadTester:
    def __init__(self, output_dir='data'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.results = []
        
    def update_memory_configuration(self, function_name, memory_mb):
        """Update Lambda function memory configuration"""
        try:
            print(f"\nUpdating {function_name} to {memory_mb}MB memory...")
            
            response = lambda_client.update_function_configuration(
                FunctionName=function_name,
                MemorySize=memory_mb
            )
            
            # Wait for update to complete
            waiter = lambda_client.get_waiter('function_updated')
            waiter.wait(FunctionName=function_name)
            
            print(f"✓ Memory updated to {memory_mb}MB")
            time.sleep(5)  # Extra buffer for propagation
            
            return True
            
        except Exception as e:
            print(f"✗ Error updating memory: {e}")
            return False
    
    def force_cold_start(self, function_name):
        """Force cold start by updating environment variable"""
        try:
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            env_vars = response.get('Environment', {}).get('Variables', {})
            
            # Update with timestamp to force new execution environment
            env_vars['FORCE_COLD_START'] = str(time.time())
            
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': env_vars}
            )
            
            # Wait for update to complete
            waiter = lambda_client.get_waiter('function_updated')
            waiter.wait(FunctionName=function_name)
            
            time.sleep(3)
            
        except Exception as e:
            print(f"Error forcing cold start: {e}")
    
    def invoke_function(self, url, function_type, run_id, invocation_id, memory_mb):
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
                    'memory_mb': memory_mb,
                    'configured_memory': memory_mb,
                    'status_code': response.status_code,
                    'client_latency_ms': round(client_latency, 2),
                    'is_cold_start': metrics.get('is_cold_start', False),
                    'model_load_time_ms': metrics.get('model_load_time_ms', 0),
                    'inference_time_ms': metrics.get('inference_time_ms', 0),
                    'total_handler_time_ms': metrics.get('total_handler_time_ms', 0),
                    'request_id': metrics.get('request_id', ''),
                    'success': True
                }
            else:
                result = {
                    'timestamp': timestamp,
                    'run_id': run_id,
                    'invocation_id': invocation_id,
                    'function_type': function_type,
                    'memory_mb': memory_mb,
                    'configured_memory': memory_mb,
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
                'memory_mb': memory_mb,
                'configured_memory': memory_mb,
                'client_latency_ms': round(client_latency, 2),
                'error': str(e),
                'success': False
            }
        
        return result
    
    def test_memory_configuration(self, memory_mb, iterations_cold=10, iterations_warm=30):
        """Test both functions at a specific memory configuration"""
        print(f"\n{'='*70}")
        print(f"TESTING MEMORY CONFIGURATION: {memory_mb}MB")
        print(f"{'='*70}")
        
        # Update baseline function memory
        if not self.update_memory_configuration('ml-inference-baseline', memory_mb):
            return
        
        # Update SnapStart function memory (requires republish)
        if not self.update_memory_configuration('ml-inference-snapstart', memory_mb):
            return
        
        # For SnapStart, we need to publish a new version
        try:
            print("Publishing new version for SnapStart...")
            lambda_client.publish_version(FunctionName='ml-inference-snapstart')
            time.sleep(5)
        except Exception as e:
            print(f"Error publishing version: {e}")
        
        # Cold Start Tests
        print(f"\n--- Cold Start Tests ({iterations_cold} iterations) ---")
        for i in range(iterations_cold):
            print(f"Cold start iteration {i+1}/{iterations_cold}")
            
            # Force cold start for baseline
            self.force_cold_start('ml-inference-baseline')
            result_baseline = self.invoke_function(
                BASELINE_URL, 'baseline', f'cold_{memory_mb}mb_{i+1}', 1, memory_mb
            )
            self.results.append(result_baseline)
            print(f"  Baseline: {result_baseline['client_latency_ms']:.2f}ms")
            
            time.sleep(2)
            
            # Force cold start for SnapStart
            self.force_cold_start('ml-inference-snapstart')
            result_snapstart = self.invoke_function(
                SNAPSTART_URL, 'snapstart', f'cold_{memory_mb}mb_{i+1}', 1, memory_mb
            )
            self.results.append(result_snapstart)
            print(f"  SnapStart: {result_snapstart['client_latency_ms']:.2f}ms")
            
            time.sleep(5)
        
        # Warm Start Tests
        print(f"\n--- Warm Start Tests ({iterations_warm} iterations) ---")
        
        # Prime the functions
        print("Priming functions...")
        self.invoke_function(BASELINE_URL, 'baseline', 'prime', 0, memory_mb)
        time.sleep(1)
        self.invoke_function(SNAPSTART_URL, 'snapstart', 'prime', 0, memory_mb)
        time.sleep(2)
        
        for i in range(iterations_warm):
            # Test baseline
            result_baseline = self.invoke_function(
                BASELINE_URL, 'baseline', f'warm_{memory_mb}mb_{i+1}', 1, memory_mb
            )
            self.results.append(result_baseline)
            
            # Test SnapStart
            result_snapstart = self.invoke_function(
                SNAPSTART_URL, 'snapstart', f'warm_{memory_mb}mb_{i+1}', 1, memory_mb
            )
            self.results.append(result_snapstart)
            
            if (i + 1) % 10 == 0:
                print(f"Completed {i+1}/{iterations_warm} warm iterations")
            
            time.sleep(0.5)
        
        print(f"\n✓ Completed testing for {memory_mb}MB configuration")
    
    def test_sustained_load(self, duration_minutes=10, rate_per_minute=20):
        """Run sustained load test to measure performance over time"""
        print(f"\n{'='*70}")
        print(f"SUSTAINED LOAD TEST")
        print(f"Duration: {duration_minutes} minutes, Rate: {rate_per_minute}/min")
        print(f"{'='*70}")
        
        end_time = time.time() + (duration_minutes * 60)
        iteration = 0
        
        while time.time() < end_time:
            iteration += 1
            
            # Alternate between functions
            result_baseline = self.invoke_function(
                BASELINE_URL, 'baseline', f'sustained_{iteration}', iteration, 1024
            )
            self.results.append(result_baseline)
            
            result_snapstart = self.invoke_function(
                SNAPSTART_URL, 'snapstart', f'sustained_{iteration}', iteration, 1024
            )
            self.results.append(result_snapstart)
            
            # Rate limiting
            time.sleep(60 / rate_per_minute)
            
            if iteration % 10 == 0:
                elapsed = (time.time() - (end_time - duration_minutes * 60)) / 60
                print(f"Sustained test: {elapsed:.1f}/{duration_minutes} min, {iteration} iterations")
        
        print(f"✓ Completed sustained load test: {iteration} total iterations")
    
    def save_results(self):
        """Save results to CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'comprehensive_test_{timestamp}.csv')
        
        if not self.results:
            print("No results to save")
            return
        
        # Get all unique keys
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
    print("COMPREHENSIVE LAMBDA SNAPSTART PERFORMANCE TESTING")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis comprehensive test will:")
    print("  1. Test multiple memory configurations (512MB, 1024MB, 2048MB)")
    print("  2. Collect 10 cold starts + 30 warm starts per config")
    print("  3. Run a 10-minute sustained load test")
    print(f"\nEstimated duration: 60-90 minutes")
    print("="*70)
    
    confirm = input("\nProceed with comprehensive testing? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Testing cancelled.")
        return
    
    tester = ComprehensiveLoadTester()
    
    # Test different memory configurations
    memory_configs = [512, 1024, 2048]
    
    for memory_mb in memory_configs:
        tester.test_memory_configuration(
            memory_mb=memory_mb,
            iterations_cold=10,
            iterations_warm=30
        )
        time.sleep(10)  # Buffer between memory configs
    
    # Sustained load test (at 1024MB)
    tester.update_memory_configuration('ml-inference-baseline', 1024)
    tester.update_memory_configuration('ml-inference-snapstart', 1024)
    tester.test_sustained_load(duration_minutes=10, rate_per_minute=20)
    
    # Save all results
    tester.save_results()
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✓ Comprehensive testing complete!")
    print("  Next steps:")
    print("  1. Run: python scripts/analyze_results.py")
    print("  2. Run: python scripts/cloudwatch_queries.py")
    print("  3. Ready for research paper writing!")

if __name__ == "__main__":
    main()
