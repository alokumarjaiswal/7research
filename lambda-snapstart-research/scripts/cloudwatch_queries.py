import boto3
import time
import json
from datetime import datetime, timedelta
import pandas as pd
import os

class CloudWatchAnalyzer:
    def __init__(self, region='us-east-1'):
        self.logs_client = boto3.client('logs', region_name=region)
        self.xray_client = boto3.client('xray', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        self.log_groups = {
            'baseline': '/aws/lambda/ml-inference-baseline',
            'snapstart': '/aws/lambda/ml-inference-snapstart'
        }
        
        self.output_dir = 'data/cloudwatch'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_insights_query(self, log_group, query_string, start_time, end_time):
        """Execute CloudWatch Logs Insights query"""
        try:
            print(f"Running query on {log_group}...")
            
            response = self.logs_client.start_query(
                logGroupName=log_group,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query_string
            )
            
            query_id = response['queryId']
            
            # Poll for results
            while True:
                result = self.logs_client.get_query_results(queryId=query_id)
                status = result['status']
                
                if status == 'Complete':
                    return result['results']
                elif status == 'Failed':
                    print(f"Query failed: {result}")
                    return None
                
                time.sleep(1)
                
        except Exception as e:
            print(f"Error running query: {e}")
            return None
    
    def analyze_cold_starts(self, hours_back=24):
        """Analyze cold start patterns"""
        print("\n" + "="*70)
        print("COLD START ANALYSIS (CloudWatch Logs)")
        print("="*70)
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Query to detect cold starts and measure init duration
        query = """
        filter @type = "REPORT"
        | fields @timestamp, @requestId, @duration, @memorySize, @maxMemoryUsed
        | parse @message /Init Duration: (?<initDuration>.*?) ms/
        | stats 
            count(*) as totalInvocations,
            count(initDuration) as coldStarts,
            avg(initDuration) as avgInitDuration,
            max(initDuration) as maxInitDuration,
            avg(@duration) as avgDuration,
            max(@duration) as maxDuration,
            avg(@maxMemoryUsed) / 1024 / 1024 as avgMemoryUsedMB
        """
        
        results = {}
        for func_type, log_group in self.log_groups.items():
            print(f"\n{func_type.upper()}:")
            result = self.run_insights_query(log_group, query, start_time, end_time)
            
            if result and len(result) > 0:
                data = {item['field']: item['value'] for item in result[0]}
                results[func_type] = data
                
                total = float(data.get('totalInvocations', 0))
                cold = float(data.get('coldStarts', 0))
                cold_pct = (cold / total * 100) if total > 0 else 0
                
                print(f"  Total invocations: {int(total)}")
                print(f"  Cold starts: {int(cold)} ({cold_pct:.1f}%)")
                print(f"  Avg init duration: {data.get('avgInitDuration', 'N/A')} ms")
                print(f"  Max init duration: {data.get('maxInitDuration', 'N/A')} ms")
                print(f"  Avg execution duration: {float(data.get('avgDuration', 0)):.2f} ms")
                print(f"  Max execution duration: {float(data.get('maxDuration', 0)):.2f} ms")
                print(f"  Avg memory used: {float(data.get('avgMemoryUsed', 0)):.2f} MB")
        
        # Save results
        output_file = os.path.join(self.output_dir, 'cold_start_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def analyze_performance_percentiles(self, hours_back=24):
        """Analyze performance percentiles"""
        print("\n" + "="*70)
        print("PERFORMANCE PERCENTILE ANALYSIS")
        print("="*70)
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        query = """
        filter @type = "REPORT"
        | stats 
            count(*) as invocations,
            avg(@duration) as avgDuration,
            min(@duration) as minDuration,
            max(@duration) as maxDuration,
            pct(@duration, 50) as p50Duration,
            pct(@duration, 90) as p90Duration,
            pct(@duration, 95) as p95Duration,
            pct(@duration, 99) as p99Duration,
            avg(@maxMemoryUsed) / 1024 / 1024 as avgMemoryMB,
            max(@maxMemoryUsed) / 1024 / 1024 as maxMemoryMB
        """
        
        results = {}
        for func_type, log_group in self.log_groups.items():
            print(f"\n{func_type.upper()}:")
            result = self.run_insights_query(log_group, query, start_time, end_time)
            
            if result and len(result) > 0:
                data = {item['field']: item['value'] for item in result[0]}
                results[func_type] = data
                
                print(f"  Invocations: {data.get('invocations', 0)}")
                print(f"  Duration (ms):")
                print(f"    Min: {float(data.get('minDuration', 0)):.2f}")
                print(f"    P50: {float(data.get('p50Duration', 0)):.2f}")
                print(f"    P90: {float(data.get('p90Duration', 0)):.2f}")
                print(f"    P95: {float(data.get('p95Duration', 0)):.2f}")
                print(f"    P99: {float(data.get('p99Duration', 0)):.2f}")
                print(f"    Max: {float(data.get('maxDuration', 0)):.2f}")
                print(f"  Memory (MB):")
                print(f"    Avg: {float(data.get('avgMemory', 0)):.2f}")
                print(f"    Max: {float(data.get('maxMemory', 0)):.2f}")
        
        # Save results
        output_file = os.path.join(self.output_dir, 'performance_percentiles.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def analyze_errors(self, hours_back=24):
        """Analyze errors and failures"""
        print("\n" + "="*70)
        print("ERROR ANALYSIS")
        print("="*70)
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        query = """
        fields @message, @timestamp
        | filter @message like /ERROR/ or @message like /Exception/ or @message like /Traceback/
        | stats count() as errorCount
        """
        
        results = {}
        for func_type, log_group in self.log_groups.items():
            print(f"\n{func_type.upper()}:")
            result = self.run_insights_query(log_group, query, start_time, end_time)
            
            if result and len(result) > 0:
                data = {item['field']: item['value'] for item in result[0]}
                results[func_type] = data
                
                total = float(data.get('totalInvocations', 0))
                errors = float(data.get('errors', 0))
                error_rate = (errors / total * 100) if total > 0 else 0
                
                print(f"  Total invocations: {int(total)}")
                print(f"  Errors: {int(errors)} ({error_rate:.2f}%)")
                print(f"  Exceptions: {data.get('exceptions', 0)}")
        
        # Save results
        output_file = os.path.join(self.output_dir, 'error_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def get_xray_traces(self, hours_back=1):
        """Fetch X-Ray trace summaries"""
        print("\n" + "="*70)
        print("X-RAY TRACE ANALYSIS")
        print("="*70)
        
        # X-Ray has strict time window requirements
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        try:
            response = self.xray_client.get_trace_summaries(
                StartTime=start_time,
                EndTime=end_time,
                FilterExpression='annotation.function_name = "ml-inference-baseline" OR annotation.function_name = "ml-inference-snapstart"'
            )
            
            traces = response.get('TraceSummaries', [])
            print(f"\nFound {len(traces)} traces in the last {hours_back} hour(s)")
            
            if traces:
                # Analyze trace data
                durations = [t.get('Duration', 0) for t in traces]
                response_times = [t.get('ResponseTime', 0) for t in traces]
                
                print(f"\nTrace Duration:")
                print(f"  Avg: {sum(durations)/len(durations):.2f}s")
                print(f"  Min: {min(durations):.2f}s")
                print(f"  Max: {max(durations):.2f}s")
                
                print(f"\nResponse Time:")
                print(f"  Avg: {sum(response_times)/len(response_times):.2f}s")
                print(f"  Min: {min(response_times):.2f}s")
                print(f"  Max: {max(response_times):.2f}s")
                
                # Save trace IDs for detailed analysis
                trace_ids = [t['Id'] for t in traces[:10]]  # First 10
                output_file = os.path.join(self.output_dir, 'xray_trace_ids.json')
                with open(output_file, 'w') as f:
                    json.dump({'trace_ids': trace_ids, 'count': len(traces)}, f, indent=2)
                print(f"\nSaved trace IDs to: {output_file}")
                
                return traces
            else:
                print("\nNo X-Ray traces found.")
                print("Note: X-Ray traces may take 1-2 minutes to appear after invocation.")
                
        except Exception as e:
            print(f"Error fetching X-Ray traces: {e}")
            print("This is normal if no recent invocations have been made.")
        
        return []
    
    def generate_monitoring_summary(self):
        """Generate comprehensive monitoring summary"""
        print("\n" + "="*70)
        print("GENERATING COMPREHENSIVE MONITORING SUMMARY")
        print("="*70)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'cold_starts': self.analyze_cold_starts(hours_back=24),
            'performance_percentiles': self.analyze_performance_percentiles(hours_back=24),
            'errors': self.analyze_errors(hours_back=24),
            'xray_traces': len(self.get_xray_traces(hours_back=1))
        }
        
        output_file = os.path.join(self.output_dir, 'monitoring_summary.json')
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*70}")
        print(f"Monitoring summary saved to: {output_file}")
        print(f"{'='*70}")
        
        return summary

def main():
    print("="*70)
    print("CLOUDWATCH LOGS INSIGHTS ANALYSIS")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyzer = CloudWatchAnalyzer()
    analyzer.generate_monitoring_summary()
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nAnalysis complete! Check the data/cloudwatch folder for results.")

if __name__ == "__main__":
    main()
