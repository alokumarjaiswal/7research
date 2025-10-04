import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class PerformanceAnalyzer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.output_dir = 'data/analysis'
        os.makedirs(self.output_dir, exist_ok=True)
        
    def structural_decomposition(self):
        """Analyze structural components of latency"""
        print("\n" + "="*70)
        print("STRUCTURAL DECOMPOSITION ANALYSIS")
        print("="*70)
        
        results = {}
        
        for func_type in ['baseline', 'snapstart']:
            cold = self.df[(self.df['function_type'] == func_type) & (self.df['is_cold_start'] == True)]
            warm = self.df[(self.df['function_type'] == func_type) & (self.df['is_cold_start'] == False)]
            
            if len(cold) > 0 and len(warm) > 0:
                results[func_type] = {
                    'cold_start': {
                        'total_latency': {
                            'mean': float(cold['client_latency_ms'].mean()),
                            'std': float(cold['client_latency_ms'].std()),
                            'median': float(cold['client_latency_ms'].median())
                        },
                        'model_load_time': {
                            'mean': float(cold['model_load_time_ms'].mean()),
                            'std': float(cold['model_load_time_ms'].std())
                        },
                        'inference_time': {
                            'mean': float(cold['inference_time_ms'].mean()),
                            'std': float(cold['inference_time_ms'].std())
                        },
                        'handler_time': {
                            'mean': float(cold['total_handler_time_ms'].mean()),
                            'std': float(cold['total_handler_time_ms'].std())
                        },
                        'network_overhead': {
                            'mean': float(cold['client_latency_ms'].mean() - cold['total_handler_time_ms'].mean())
                        }
                    },
                    'warm_start': {
                        'total_latency': {
                            'mean': float(warm['client_latency_ms'].mean()),
                            'std': float(warm['client_latency_ms'].std()),
                            'median': float(warm['client_latency_ms'].median()),
                            'p95': float(warm['client_latency_ms'].quantile(0.95)),
                            'p99': float(warm['client_latency_ms'].quantile(0.99))
                        },
                        'inference_time': {
                            'mean': float(warm['inference_time_ms'].mean()),
                            'std': float(warm['inference_time_ms'].std())
                        },
                        'handler_time': {
                            'mean': float(warm['total_handler_time_ms'].mean()),
                            'std': float(warm['total_handler_time_ms'].std())
                        },
                        'network_overhead': {
                            'mean': float(warm['client_latency_ms'].mean() - warm['total_handler_time_ms'].mean())
                        }
                    }
                }
        
        # Print results
        for func_type, metrics in results.items():
            print(f"\n{func_type.upper()}:")
            print(f"  Cold Start Components:")
            print(f"    Model Load: {metrics['cold_start']['model_load_time']['mean']:.2f}ms")
            print(f"    Inference: {metrics['cold_start']['inference_time']['mean']:.2f}ms")
            print(f"    Handler Total: {metrics['cold_start']['handler_time']['mean']:.2f}ms")
            print(f"    Network Overhead: {metrics['cold_start']['network_overhead']['mean']:.2f}ms")
            print(f"    Total Latency: {metrics['cold_start']['total_latency']['mean']:.2f}ms")
            
            print(f"  Warm Start Components:")
            print(f"    Inference: {metrics['warm_start']['inference_time']['mean']:.2f}ms")
            print(f"    Handler Total: {metrics['warm_start']['handler_time']['mean']:.2f}ms")
            print(f"    Network Overhead: {metrics['warm_start']['network_overhead']['mean']:.2f}ms")
            print(f"    Total Latency: {metrics['warm_start']['total_latency']['mean']:.2f}ms (P95: {metrics['warm_start']['total_latency']['p95']:.2f}ms)")
        
        # Save to JSON
        output_file = os.path.join(self.output_dir, 'structural_decomposition.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def slo_analysis(self, slo_targets=[100, 500, 1000, 2000, 5000]):
        """Analyze SLO compliance at different thresholds"""
        print("\n" + "="*70)
        print("SLO-AWARE OPTIMIZATION ANALYSIS")
        print("="*70)
        
        results = {}
        
        for slo_ms in slo_targets:
            results[f'{slo_ms}ms'] = {}
            
            for func_type in ['baseline', 'snapstart']:
                func_data = self.df[self.df['function_type'] == func_type]
                total_requests = len(func_data)
                
                # Requests meeting SLO
                meeting_slo = len(func_data[func_data['client_latency_ms'] <= slo_ms])
                slo_compliance = (meeting_slo / total_requests) * 100
                
                # Cold start SLO compliance
                cold_data = func_data[func_data['is_cold_start'] == True]
                cold_meeting_slo = len(cold_data[cold_data['client_latency_ms'] <= slo_ms])
                cold_slo_compliance = (cold_meeting_slo / len(cold_data)) * 100 if len(cold_data) > 0 else 0
                
                # Warm start SLO compliance
                warm_data = func_data[func_data['is_cold_start'] == False]
                warm_meeting_slo = len(warm_data[warm_data['client_latency_ms'] <= slo_ms])
                warm_slo_compliance = (warm_meeting_slo / len(warm_data)) * 100 if len(warm_data) > 0 else 0
                
                results[f'{slo_ms}ms'][func_type] = {
                    'overall_compliance': float(slo_compliance),
                    'cold_start_compliance': float(cold_slo_compliance),
                    'warm_start_compliance': float(warm_slo_compliance),
                    'requests_meeting_slo': int(meeting_slo),
                    'total_requests': int(total_requests)
                }
            
            print(f"\nSLO Target: {slo_ms}ms")
            for func_type in ['baseline', 'snapstart']:
                data = results[f'{slo_ms}ms'][func_type]
                print(f"  {func_type}: {data['overall_compliance']:.1f}% compliance "
                      f"({data['requests_meeting_slo']}/{data['total_requests']} requests)")
                print(f"    Cold: {data['cold_start_compliance']:.1f}%, Warm: {data['warm_start_compliance']:.1f}%")
        
        # Save to JSON
        output_file = os.path.join(self.output_dir, 'slo_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def cost_efficiency_analysis(self):
        """Analyze cost efficiency (invocation cost + duration cost)"""
        print("\n" + "="*70)
        print("COST-EFFICIENCY ANALYSIS")
        print("="*70)
        
        # AWS Lambda pricing (us-east-1, as of 2025)
        # Request cost: $0.20 per 1M requests
        # Duration cost: $0.0000166667 per GB-second
        
        REQUEST_COST = 0.20 / 1_000_000  # per request
        DURATION_COST_PER_GB_SEC = 0.0000166667
        MEMORY_GB = 1024 / 1024  # 1GB
        
        results = {}
        
        for func_type in ['baseline', 'snapstart']:
            func_data = self.df[self.df['function_type'] == func_type]
            
            # Calculate costs
            num_requests = len(func_data)
            total_request_cost = num_requests * REQUEST_COST
            
            # Duration cost (convert ms to seconds)
            total_duration_sec = func_data['total_handler_time_ms'].sum() / 1000
            total_duration_cost = total_duration_sec * MEMORY_GB * DURATION_COST_PER_GB_SEC
            
            total_cost = total_request_cost + total_duration_cost
            avg_latency = func_data['client_latency_ms'].mean()
            
            # Cost per request
            cost_per_request = total_cost / num_requests if num_requests > 0 else 0
            
            results[func_type] = {
                'num_requests': int(num_requests),
                'total_request_cost': float(total_request_cost),
                'total_duration_cost': float(total_duration_cost),
                'total_cost': float(total_cost),
                'cost_per_request': float(cost_per_request),
                'avg_latency_ms': float(avg_latency),
                'cost_efficiency_ratio': float(cost_per_request / avg_latency if avg_latency > 0 else 0)
            }
        
        # Compare
        baseline_cost = results['baseline']['total_cost']
        snapstart_cost = results['snapstart']['total_cost']
        cost_savings = ((baseline_cost - snapstart_cost) / baseline_cost) * 100 if baseline_cost > 0 else 0
        
        print(f"\nBASELINE:")
        print(f"  Total cost: ${results['baseline']['total_cost']:.6f}")
        print(f"  Cost per request: ${results['baseline']['cost_per_request']:.8f}")
        print(f"  Avg latency: {results['baseline']['avg_latency_ms']:.2f}ms")
        
        print(f"\nSNAPSTART:")
        print(f"  Total cost: ${results['snapstart']['total_cost']:.6f}")
        print(f"  Cost per request: ${results['snapstart']['cost_per_request']:.8f}")
        print(f"  Avg latency: {results['snapstart']['avg_latency_ms']:.2f}ms")
        
        print(f"\nCost Savings: {cost_savings:.2f}%")
        
        # Save to JSON
        output_file = os.path.join(self.output_dir, 'cost_efficiency.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def generate_summary_report(self):
        """Generate comprehensive summary for research paper"""
        print("\n" + "="*70)
        print("GENERATING COMPREHENSIVE SUMMARY REPORT")
        print("="*70)
        
        report = {
            'metadata': {
                'total_invocations': len(self.df),
                'baseline_invocations': len(self.df[self.df['function_type'] == 'baseline']),
                'snapstart_invocations': len(self.df[self.df['function_type'] == 'snapstart']),
                'cold_starts': len(self.df[self.df['is_cold_start'] == True]),
                'warm_starts': len(self.df[self.df['is_cold_start'] == False]),
                'memory_size_mb': int(self.df['memory_mb'].iloc[0]),
                'runtime': 'python3.12'
            },
            'structural_decomposition': self.structural_decomposition(),
            'slo_analysis': self.slo_analysis(),
            'cost_efficiency': self.cost_efficiency_analysis()
        }
        
        # Save comprehensive report
        output_file = os.path.join(self.output_dir, 'comprehensive_report.json')
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*70}")
        print(f"Comprehensive report saved to: {output_file}")
        print(f"{'='*70}")
        
        return report

def main():
    # Find the most recent CSV file
    data_dir = 'data'
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in data directory!")
        return
    
    # Use most recent file
    latest_file = sorted(csv_files)[-1]
    csv_path = os.path.join(data_dir, latest_file)
    
    print(f"Analyzing: {csv_path}")
    
    analyzer = PerformanceAnalyzer(csv_path)
    analyzer.generate_summary_report()

if __name__ == "__main__":
    main()
