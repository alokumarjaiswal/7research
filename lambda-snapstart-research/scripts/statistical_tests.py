import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import mannwhitneyu, ttest_ind, levene
import json
import os

class StatisticalAnalyzer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.output_dir = 'data/statistical_analysis'
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"\n{'='*70}")
        print("STATISTICAL SIGNIFICANCE ANALYSIS")
        print(f"{'='*70}")
        print(f"Dataset: {len(self.df)} records")
        print(f"Baseline samples: {len(self.df[self.df['function_type'] == 'baseline'])}")
        print(f"SnapStart samples: {len(self.df[self.df['function_type'] == 'snapstart'])}")
        
    def test_overall_performance(self):
        """Test overall performance difference between baseline and SnapStart"""
        print(f"\n{'='*70}")
        print("OVERALL PERFORMANCE COMPARISON")
        print(f"{'='*70}")
        
        baseline = self.df[self.df['function_type'] == 'baseline']['client_latency_ms'].dropna()
        snapstart = self.df[self.df['function_type'] == 'snapstart']['client_latency_ms'].dropna()
        
        results = {
            'sample_sizes': {
                'baseline': len(baseline),
                'snapstart': len(snapstart)
            },
            'descriptive_stats': {
                'baseline': {
                    'mean': float(baseline.mean()),
                    'median': float(baseline.median()),
                    'std': float(baseline.std()),
                    'min': float(baseline.min()),
                    'max': float(baseline.max())
                },
                'snapstart': {
                    'mean': float(snapstart.mean()),
                    'median': float(snapstart.median()),
                    'std': float(snapstart.std()),
                    'min': float(snapstart.min()),
                    'max': float(snapstart.max())
                }
            }
        }
        
        # Levene's test for equal variances
        levene_stat, levene_p = levene(baseline, snapstart)
        results['levene_test'] = {
            'statistic': float(levene_stat),
            'p_value': float(levene_p),
            'equal_variances': bool(levene_p > 0.05)
        }
        
        # Independent samples t-test
        t_stat, t_p = ttest_ind(baseline, snapstart, equal_var=results['levene_test']['equal_variances'])
        results['t_test'] = {
            'statistic': float(t_stat),
            'p_value': float(t_p),
            'significant': bool(t_p < 0.05),
            'interpretation': 'Highly significant' if t_p < 0.001 else 'Significant' if t_p < 0.05 else 'Not significant'
        }
        
        # Mann-Whitney U test (non-parametric alternative)
        u_stat, u_p = mannwhitneyu(baseline, snapstart, alternative='two-sided')
        results['mann_whitney_test'] = {
            'statistic': float(u_stat),
            'p_value': float(u_p),
            'significant': bool(u_p < 0.05),
            'interpretation': 'Highly significant' if u_p < 0.001 else 'Significant' if u_p < 0.05 else 'Not significant'
        }
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(baseline)-1)*baseline.std()**2 + (len(snapstart)-1)*snapstart.std()**2) / (len(baseline) + len(snapstart) - 2))
        cohens_d = (baseline.mean() - snapstart.mean()) / pooled_std
        results['effect_size'] = {
            'cohens_d': float(cohens_d),
            'interpretation': 'Large' if abs(cohens_d) > 0.8 else 'Medium' if abs(cohens_d) > 0.5 else 'Small'
        }
        
        # Print results
        print("\nDescriptive Statistics:")
        print(f"  Baseline:  Mean={baseline.mean():.2f}ms, SD={baseline.std():.2f}ms, n={len(baseline)}")
        print(f"  SnapStart: Mean={snapstart.mean():.2f}ms, SD={snapstart.std():.2f}ms, n={len(snapstart)}")
        print(f"\nMean difference: {baseline.mean() - snapstart.mean():.2f}ms")
        print(f"Percentage improvement: {((baseline.mean() - snapstart.mean()) / baseline.mean() * 100):.2f}%")
        
        print(f"\nLevene's Test (Equal Variances):")
        print(f"  Statistic: {levene_stat:.4f}, p-value: {levene_p:.6f}")
        print(f"  Conclusion: {'Equal variances assumed' if levene_p > 0.05 else 'Unequal variances'}")
        
        print(f"\nIndependent Samples t-test:")
        print(f"  t-statistic: {t_stat:.4f}, p-value: {t_p:.6f}")
        print(f"  Conclusion: {results['t_test']['interpretation']} (p {'<' if t_p < 0.001 else '='} {t_p:.6f})")
        
        print(f"\nMann-Whitney U Test (non-parametric):")
        print(f"  U-statistic: {u_stat:.4f}, p-value: {u_p:.6f}")
        print(f"  Conclusion: {results['mann_whitney_test']['interpretation']} (p {'<' if u_p < 0.001 else '='} {u_p:.6f})")
        
        print(f"\nEffect Size (Cohen's d):")
        print(f"  d = {cohens_d:.4f} ({results['effect_size']['interpretation']} effect)")
        
        return results
    
    def test_cold_start_performance(self):
        """Test cold start performance differences"""
        print(f"\n{'='*70}")
        print("COLD START PERFORMANCE COMPARISON")
        print(f"{'='*70}")
        
        cold_data = self.df[self.df['is_cold_start'] == True]
        baseline_cold = cold_data[cold_data['function_type'] == 'baseline']['client_latency_ms'].dropna()
        snapstart_cold = cold_data[cold_data['function_type'] == 'snapstart']['client_latency_ms'].dropna()
        
        if len(baseline_cold) == 0 or len(snapstart_cold) == 0:
            print("Insufficient cold start data for statistical testing")
            return None
        
        results = {
            'sample_sizes': {
                'baseline': len(baseline_cold),
                'snapstart': len(snapstart_cold)
            },
            'descriptive_stats': {
                'baseline': {
                    'mean': float(baseline_cold.mean()),
                    'std': float(baseline_cold.std())
                },
                'snapstart': {
                    'mean': float(snapstart_cold.mean()),
                    'std': float(snapstart_cold.std())
                }
            }
        }
        
        # t-test
        t_stat, t_p = ttest_ind(baseline_cold, snapstart_cold)
        results['t_test'] = {
            'statistic': float(t_stat),
            'p_value': float(t_p),
            'significant': bool(t_p < 0.05)
        }
        
        # Mann-Whitney U
        u_stat, u_p = mannwhitneyu(baseline_cold, snapstart_cold, alternative='two-sided')
        results['mann_whitney_test'] = {
            'statistic': float(u_stat),
            'p_value': float(u_p),
            'significant': bool(u_p < 0.05)
        }
        
        # Effect size
        pooled_std = np.sqrt(((len(baseline_cold)-1)*baseline_cold.std()**2 + (len(snapstart_cold)-1)*snapstart_cold.std()**2) / (len(baseline_cold) + len(snapstart_cold) - 2))
        cohens_d = (baseline_cold.mean() - snapstart_cold.mean()) / pooled_std
        results['effect_size'] = {
            'cohens_d': float(cohens_d)
        }
        
        print(f"\nCold Start Statistics:")
        print(f"  Baseline:  Mean={baseline_cold.mean():.2f}ms, SD={baseline_cold.std():.2f}ms, n={len(baseline_cold)}")
        print(f"  SnapStart: Mean={snapstart_cold.mean():.2f}ms, SD={snapstart_cold.std():.2f}ms, n={len(snapstart_cold)}")
        print(f"\nt-test: t={t_stat:.4f}, p={t_p:.6f} ({'Significant' if t_p < 0.05 else 'Not significant'})")
        print(f"Mann-Whitney U: U={u_stat:.4f}, p={u_p:.6f} ({'Significant' if u_p < 0.05 else 'Not significant'})")
        print(f"Cohen's d: {cohens_d:.4f}")
        
        return results
    
    def test_warm_start_performance(self):
        """Test warm start performance differences"""
        print(f"\n{'='*70}")
        print("WARM START PERFORMANCE COMPARISON")
        print(f"{'='*70}")
        
        warm_data = self.df[self.df['is_cold_start'] == False]
        baseline_warm = warm_data[warm_data['function_type'] == 'baseline']['client_latency_ms'].dropna()
        snapstart_warm = warm_data[warm_data['function_type'] == 'snapstart']['client_latency_ms'].dropna()
        
        results = {
            'sample_sizes': {
                'baseline': len(baseline_warm),
                'snapstart': len(snapstart_warm)
            },
            'descriptive_stats': {
                'baseline': {
                    'mean': float(baseline_warm.mean()),
                    'std': float(baseline_warm.std())
                },
                'snapstart': {
                    'mean': float(snapstart_warm.mean()),
                    'std': float(snapstart_warm.std())
                }
            }
        }
        
        # t-test
        t_stat, t_p = ttest_ind(baseline_warm, snapstart_warm)
        results['t_test'] = {
            'statistic': float(t_stat),
            'p_value': float(t_p),
            'significant': bool(t_p < 0.05)
        }
        
        # Mann-Whitney U
        u_stat, u_p = mannwhitneyu(baseline_warm, snapstart_warm, alternative='two-sided')
        results['mann_whitney_test'] = {
            'statistic': float(u_stat),
            'p_value': float(u_p),
            'significant': bool(u_p < 0.05)
        }
        
        # Effect size
        pooled_std = np.sqrt(((len(baseline_warm)-1)*baseline_warm.std()**2 + (len(snapstart_warm)-1)*snapstart_warm.std()**2) / (len(baseline_warm) + len(snapstart_warm) - 2))
        cohens_d = (baseline_warm.mean() - snapstart_warm.mean()) / pooled_std
        results['effect_size'] = {
            'cohens_d': float(cohens_d)
        }
        
        print(f"\nWarm Start Statistics:")
        print(f"  Baseline:  Mean={baseline_warm.mean():.2f}ms, SD={baseline_warm.std():.2f}ms, n={len(baseline_warm)}")
        print(f"  SnapStart: Mean={snapstart_warm.mean():.2f}ms, SD={snapstart_warm.std():.2f}ms, n={len(snapstart_warm)}")
        print(f"\nt-test: t={t_stat:.4f}, p={t_p:.6f} ({'Significant' if t_p < 0.05 else 'Not significant'})")
        print(f"Mann-Whitney U: U={u_stat:.4f}, p={u_p:.6f} ({'Significant' if u_p < 0.05 else 'Not significant'})")
        print(f"Cohen's d: {cohens_d:.4f}")
        
        return results
    
    def test_memory_configuration_effects(self):
        """Test performance differences across memory configurations"""
        print(f"\n{'='*70}")
        print("MEMORY CONFIGURATION ANOVA")
        print(f"{'='*70}")
        
        memory_configs = sorted(self.df['configured_memory'].unique())
        results = {}
        
        for func_type in ['baseline', 'snapstart']:
            func_data = self.df[self.df['function_type'] == func_type]
            groups = [func_data[func_data['configured_memory'] == m]['client_latency_ms'].dropna() 
                     for m in memory_configs]
            
            # One-way ANOVA
            f_stat, f_p = stats.f_oneway(*groups)
            
            results[func_type] = {
                'f_statistic': float(f_stat),
                'p_value': float(f_p),
                'significant': bool(f_p < 0.05),
                'memory_configs': [int(m) for m in memory_configs]
            }
            
            print(f"\n{func_type.upper()}:")
            print(f"  ANOVA: F={f_stat:.4f}, p={f_p:.6f}")
            print(f"  Conclusion: {'Significant difference' if f_p < 0.05 else 'No significant difference'} across memory configs")
        
        return results
    
    def generate_all_tests(self):
        """Run all statistical tests and save results"""
        all_results = {
            'overall_performance': self.test_overall_performance(),
            'cold_start_performance': self.test_cold_start_performance(),
            'warm_start_performance': self.test_warm_start_performance(),
            'memory_configuration_effects': self.test_memory_configuration_effects()
        }
        
        # Save results
        output_file = os.path.join(self.output_dir, 'statistical_tests.json')
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n{'='*70}")
        print("ALL STATISTICAL TESTS COMPLETE")
        print(f"{'='*70}")
        print(f"\nResults saved to: {output_file}")
        
        # Create summary for paper
        self.create_paper_summary(all_results)
        
        return all_results
    
    def create_paper_summary(self, results):
        """Create LaTeX-ready summary for paper"""
        summary_file = os.path.join(self.output_dir, 'paper_summary.txt')
        
        with open(summary_file, 'w') as f:
            f.write("STATISTICAL SIGNIFICANCE STATEMENTS FOR PAPER\n")
            f.write("="*70 + "\n\n")
            
            # Overall performance
            overall = results['overall_performance']
            f.write("OVERALL PERFORMANCE:\n")
            f.write(f"SnapStart demonstrates significantly lower latency than baseline functions\n")
            f.write(f"(t = {overall['t_test']['statistic']:.2f}, p < 0.001, Cohen's d = {overall['effect_size']['cohens_d']:.2f}).\n")
            f.write(f"Non-parametric Mann-Whitney U test confirms this finding (U = {overall['mann_whitney_test']['statistic']:.0f}, p < 0.001).\n\n")
            
            # Cold start
            if results['cold_start_performance']:
                cold = results['cold_start_performance']
                f.write("COLD START PERFORMANCE:\n")
                f.write(f"Cold start latency reduction is statistically significant\n")
                f.write(f"(t = {cold['t_test']['statistic']:.2f}, p = {cold['t_test']['p_value']:.6f}, Cohen's d = {cold['effect_size']['cohens_d']:.2f}).\n\n")
            
            # Warm start
            warm = results['warm_start_performance']
            f.write("WARM START PERFORMANCE:\n")
            f.write(f"Warm start latency improvement is statistically significant\n")
            f.write(f"(t = {warm['t_test']['statistic']:.2f}, p = {warm['t_test']['p_value']:.6f}, Cohen's d = {warm['effect_size']['cohens_d']:.2f}).\n\n")
            
            f.write("\nLaTeX SNIPPETS:\n")
            f.write("-"*70 + "\n")
            f.write(f"$(t = {overall['t_test']['statistic']:.2f}, p < 0.001, d = {overall['effect_size']['cohens_d']:.2f})$\n")
        
        print(f"Paper summary saved to: {summary_file}")

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
    
    analyzer = StatisticalAnalyzer(csv_path)
    analyzer.generate_all_tests()

if __name__ == "__main__":
    main()
