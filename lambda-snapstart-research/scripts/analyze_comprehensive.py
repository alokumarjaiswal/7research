import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class ComprehensiveAnalyzer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.output_dir = 'data/comprehensive_analysis'
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"\n{'='*70}")
        print("COMPREHENSIVE DATASET ANALYSIS")
        print(f"{'='*70}")
        print(f"Total records: {len(self.df)}")
        print(f"Date range: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")
        
    def memory_configuration_analysis(self):
        """Analyze performance across memory configurations"""
        print(f"\n{'='*70}")
        print("MEMORY CONFIGURATION ANALYSIS")
        print(f"{'='*70}")
        
        results = {}
        memory_sizes = self.df['configured_memory'].unique()
        
        for memory_mb in sorted(memory_sizes):
            memory_data = self.df[self.df['configured_memory'] == memory_mb]
            
            print(f"\n{memory_mb}MB Configuration:")
            print(f"  Total invocations: {len(memory_data)}")
            
            results[f'{memory_mb}MB'] = {}
            
            for func_type in ['baseline', 'snapstart']:
                func_data = memory_data[memory_data['function_type'] == func_type]
                
                if len(func_data) == 0:
                    continue
                
                # Separate cold and warm starts
                cold = func_data[func_data['is_cold_start'] == True]
                warm = func_data[func_data['is_cold_start'] == False]
                
                func_results = {
                    'total_invocations': len(func_data),
                    'cold_starts': {
                        'count': len(cold),
                        'mean_latency_ms': float(cold['client_latency_ms'].mean()) if len(cold) > 0 else 0,
                        'median_latency_ms': float(cold['client_latency_ms'].median()) if len(cold) > 0 else 0,
                        'std_latency_ms': float(cold['client_latency_ms'].std()) if len(cold) > 0 else 0,
                        'min_latency_ms': float(cold['client_latency_ms'].min()) if len(cold) > 0 else 0,
                        'max_latency_ms': float(cold['client_latency_ms'].max()) if len(cold) > 0 else 0
                    },
                    'warm_starts': {
                        'count': len(warm),
                        'mean_latency_ms': float(warm['client_latency_ms'].mean()) if len(warm) > 0 else 0,
                        'median_latency_ms': float(warm['client_latency_ms'].median()) if len(warm) > 0 else 0,
                        'p50_ms': float(warm['client_latency_ms'].quantile(0.50)) if len(warm) > 0 else 0,
                        'p90_ms': float(warm['client_latency_ms'].quantile(0.90)) if len(warm) > 0 else 0,
                        'p95_ms': float(warm['client_latency_ms'].quantile(0.95)) if len(warm) > 0 else 0,
                        'p99_ms': float(warm['client_latency_ms'].quantile(0.99)) if len(warm) > 0 else 0,
                        'std_latency_ms': float(warm['client_latency_ms'].std()) if len(warm) > 0 else 0
                    }
                }
                
                results[f'{memory_mb}MB'][func_type] = func_results
                
                print(f"\n  {func_type.upper()}:")
                print(f"    Cold Starts: {func_results['cold_starts']['count']}")
                print(f"      Mean: {func_results['cold_starts']['mean_latency_ms']:.2f}ms")
                print(f"      Std Dev: {func_results['cold_starts']['std_latency_ms']:.2f}ms")
                print(f"    Warm Starts: {func_results['warm_starts']['count']}")
                print(f"      Mean: {func_results['warm_starts']['mean_latency_ms']:.2f}ms")
                print(f"      P95: {func_results['warm_starts']['p95_ms']:.2f}ms")
        
        # Calculate improvement percentages
        print(f"\n{'='*70}")
        print("SNAPSTART IMPROVEMENT BY MEMORY SIZE")
        print(f"{'='*70}")
        
        for memory_mb in sorted(memory_sizes):
            if f'{memory_mb}MB' not in results:
                continue
            
            baseline = results[f'{memory_mb}MB'].get('baseline', {})
            snapstart = results[f'{memory_mb}MB'].get('snapstart', {})
            
            if baseline and snapstart:
                cold_baseline = baseline['cold_starts']['mean_latency_ms']
                cold_snapstart = snapstart['cold_starts']['mean_latency_ms']
                
                if cold_baseline > 0:
                    improvement = ((cold_baseline - cold_snapstart) / cold_baseline) * 100
                    print(f"\n{memory_mb}MB - Cold Start Improvement: {improvement:.2f}%")
                    print(f"  Baseline: {cold_baseline:.2f}ms → SnapStart: {cold_snapstart:.2f}ms")
                    print(f"  Reduction: {cold_baseline - cold_snapstart:.2f}ms")
        
        # Save results
        output_file = os.path.join(self.output_dir, 'memory_configuration_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def sustained_load_analysis(self):
        """Analyze sustained load test results"""
        print(f"\n{'='*70}")
        print("SUSTAINED LOAD ANALYSIS")
        print(f"{'='*70}")
        
        sustained_data = self.df[self.df['run_id'].str.contains('sustained', na=False)]
        
        if len(sustained_data) == 0:
            print("No sustained load data found")
            return {}
        
        print(f"\nTotal sustained load invocations: {len(sustained_data)}")
        
        results = {}
        
        for func_type in ['baseline', 'snapstart']:
            func_data = sustained_data[sustained_data['function_type'] == func_type]
            
            if len(func_data) == 0:
                continue
            
            # Calculate statistics
            results[func_type] = {
                'invocations': len(func_data),
                'mean_latency_ms': float(func_data['client_latency_ms'].mean()),
                'median_latency_ms': float(func_data['client_latency_ms'].median()),
                'std_latency_ms': float(func_data['client_latency_ms'].std()),
                'min_latency_ms': float(func_data['client_latency_ms'].min()),
                'max_latency_ms': float(func_data['client_latency_ms'].max()),
                'p50_ms': float(func_data['client_latency_ms'].quantile(0.50)),
                'p90_ms': float(func_data['client_latency_ms'].quantile(0.90)),
                'p95_ms': float(func_data['client_latency_ms'].quantile(0.95)),
                'p99_ms': float(func_data['client_latency_ms'].quantile(0.99))
            }
            
            print(f"\n{func_type.upper()}:")
            print(f"  Invocations: {results[func_type]['invocations']}")
            print(f"  Mean latency: {results[func_type]['mean_latency_ms']:.2f}ms")
            print(f"  Median latency: {results[func_type]['median_latency_ms']:.2f}ms")
            print(f"  Std Dev: {results[func_type]['std_latency_ms']:.2f}ms")
            print(f"  P50: {results[func_type]['p50_ms']:.2f}ms")
            print(f"  P90: {results[func_type]['p90_ms']:.2f}ms")
            print(f"  P95: {results[func_type]['p95_ms']:.2f}ms")
            print(f"  P99: {results[func_type]['p99_ms']:.2f}ms")
        
        # Save results
        output_file = os.path.join(self.output_dir, 'sustained_load_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return results
    
    def statistical_summary(self):
        """Generate statistical summary for research paper"""
        print(f"\n{'='*70}")
        print("STATISTICAL SUMMARY FOR RESEARCH PAPER")
        print(f"{'='*70}")
        
        summary = {
            'dataset_overview': {
                'total_invocations': len(self.df),
                'baseline_invocations': len(self.df[self.df['function_type'] == 'baseline']),
                'snapstart_invocations': len(self.df[self.df['function_type'] == 'snapstart']),
                'memory_configurations_tested': sorted(self.df['configured_memory'].unique().tolist()),
                'cold_starts_total': len(self.df[self.df['is_cold_start'] == True]),
                'warm_starts_total': len(self.df[self.df['is_cold_start'] == False])
            }
        }
        
        print("\nDataset Overview:")
        for key, value in summary['dataset_overview'].items():
            print(f"  {key}: {value}")
        
        # Overall performance comparison
        baseline_all = self.df[self.df['function_type'] == 'baseline']
        snapstart_all = self.df[self.df['function_type'] == 'snapstart']
        
        summary['overall_performance'] = {
            'baseline': {
                'mean_latency_ms': float(baseline_all['client_latency_ms'].mean()),
                'median_latency_ms': float(baseline_all['client_latency_ms'].median()),
                'p95_latency_ms': float(baseline_all['client_latency_ms'].quantile(0.95))
            },
            'snapstart': {
                'mean_latency_ms': float(snapstart_all['client_latency_ms'].mean()),
                'median_latency_ms': float(snapstart_all['client_latency_ms'].median()),
                'p95_latency_ms': float(snapstart_all['client_latency_ms'].quantile(0.95))
            }
        }
        
        baseline_mean = summary['overall_performance']['baseline']['mean_latency_ms']
        snapstart_mean = summary['overall_performance']['snapstart']['mean_latency_ms']
        overall_improvement = ((baseline_mean - snapstart_mean) / baseline_mean) * 100
        
        print(f"\nOverall Performance:")
        print(f"  Baseline mean: {baseline_mean:.2f}ms")
        print(f"  SnapStart mean: {snapstart_mean:.2f}ms")
        print(f"  Improvement: {overall_improvement:.2f}%")
        
        # Save comprehensive summary
        output_file = os.path.join(self.output_dir, 'statistical_summary.json')
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nSaved to: {output_file}")
        
        return summary
    
    def generate_all_analyses(self):
        """Run all analyses"""
        self.memory_configuration_analysis()
        self.sustained_load_analysis()
        self.statistical_summary()
        
        print(f"\n{'='*70}")
        print("ALL ANALYSES COMPLETE")
        print(f"{'='*70}")
        print(f"\nOutput directory: {self.output_dir}")
        print("\nFiles generated:")
        print("  - memory_configuration_analysis.json")
        print("  - sustained_load_analysis.json")
        print("  - statistical_summary.json")
        print("\nReady for research paper writing!")

def main():
    # Find the most recent comprehensive test CSV
    data_dir = 'data'
    csv_files = [f for f in os.listdir(data_dir) if f.startswith('comprehensive_test_') and f.endswith('.csv')]
    
    if not csv_files:
        print("No comprehensive test CSV files found!")
        return
    
    latest_file = sorted(csv_files)[-1]
    csv_path = os.path.join(data_dir, latest_file)
    
    print(f"Analyzing: {csv_path}")
    
    analyzer = ComprehensiveAnalyzer(csv_path)
    analyzer.generate_all_analyses()

if __name__ == "__main__":
    main()
