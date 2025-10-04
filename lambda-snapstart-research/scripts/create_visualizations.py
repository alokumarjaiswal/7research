import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import os
import json

# Set style for academic publications
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.2)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']

class ResearchVisualizer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.output_dir = 'data/visualizations'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load comprehensive analysis data
        self.analysis_dir = 'data/comprehensive_analysis'
        
        print(f"\n{'='*70}")
        print("CREATING RESEARCH PAPER VISUALIZATIONS")
        print(f"{'='*70}")
        print(f"Dataset: {len(self.df)} records")
        
    def plot_cold_start_comparison(self):
        """Figure 1: Cold Start Latency by Memory Configuration"""
        print("\nCreating Figure 1: Cold Start Comparison...")
        
        # Filter cold starts only
        cold_data = self.df[self.df['is_cold_start'] == True].copy()
        
        if len(cold_data) == 0:
            print("No cold start data found")
            return
        
        # Group by memory and function type
        grouped = cold_data.groupby(['configured_memory', 'function_type'])['client_latency_ms'].agg(['mean', 'std']).reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Bar positions
        memory_sizes = sorted(grouped['configured_memory'].unique())
        x = np.arange(len(memory_sizes))
        width = 0.35
        
        # Separate baseline and snapstart
        baseline_means = []
        baseline_stds = []
        snapstart_means = []
        snapstart_stds = []
        
        for mem in memory_sizes:
            baseline_row = grouped[(grouped['configured_memory'] == mem) & (grouped['function_type'] == 'baseline')]
            snapstart_row = grouped[(grouped['configured_memory'] == mem) & (grouped['function_type'] == 'snapstart')]
            
            baseline_means.append(baseline_row['mean'].values[0] if len(baseline_row) > 0 else 0)
            baseline_stds.append(baseline_row['std'].values[0] if len(baseline_row) > 0 else 0)
            snapstart_means.append(snapstart_row['mean'].values[0] if len(snapstart_row) > 0 else 0)
            snapstart_stds.append(snapstart_row['std'].values[0] if len(snapstart_row) > 0 else 0)
        
        # Create bars
        bars1 = ax.bar(x - width/2, baseline_means, width, label='Baseline', 
                       color='#d62728', alpha=0.8, yerr=baseline_stds, capsize=5)
        bars2 = ax.bar(x + width/2, snapstart_means, width, label='SnapStart',
                       color='#2ca02c', alpha=0.8, yerr=snapstart_stds, capsize=5)
        
        # Customization
        ax.set_xlabel('Memory Configuration (MB)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Cold Start Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_title('Cold Start Performance: Baseline vs SnapStart\nAcross Memory Configurations', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([f'{int(m)}MB' for m in memory_sizes])
        ax.legend(loc='upper right', frameon=True, shadow=True)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}ms',
                           ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig1_cold_start_comparison.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
        
    def plot_percentile_comparison(self):
        """Figure 2: Performance Percentiles (Warm Starts)"""
        print("\nCreating Figure 2: Performance Percentiles...")
        
        warm_data = self.df[self.df['is_cold_start'] == False].copy()
        
        if len(warm_data) == 0:
            print("No warm start data found")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        percentiles = [50, 75, 90, 95, 99]
        baseline_vals = [warm_data[warm_data['function_type'] == 'baseline']['client_latency_ms'].quantile(p/100) for p in percentiles]
        snapstart_vals = [warm_data[warm_data['function_type'] == 'snapstart']['client_latency_ms'].quantile(p/100) for p in percentiles]
        
        x = np.arange(len(percentiles))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, baseline_vals, width, label='Baseline', 
                       color='#d62728', alpha=0.8)
        bars2 = ax.bar(x + width/2, snapstart_vals, width, label='SnapStart',
                       color='#2ca02c', alpha=0.8)
        
        ax.set_xlabel('Percentile', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_title('Warm Start Latency Distribution\nPercentile Comparison', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([f'P{p}' for p in percentiles])
        ax.legend(loc='upper left', frameon=True, shadow=True)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig2_percentile_comparison.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
        
    def plot_sustained_load_timeline(self):
        """Figure 3: Sustained Load Performance Over Time"""
        print("\nCreating Figure 3: Sustained Load Timeline...")
        
        sustained_data = self.df[self.df['run_id'].str.contains('sustained', na=False)].copy()
        
        if len(sustained_data) == 0:
            print("No sustained load data found")
            return
        
        # Sort by invocation_id
        sustained_data = sustained_data.sort_values('invocation_id')
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        baseline_data = sustained_data[sustained_data['function_type'] == 'baseline']
        snapstart_data = sustained_data[sustained_data['function_type'] == 'snapstart']
        
        ax.plot(baseline_data['invocation_id'], baseline_data['client_latency_ms'],
                label='Baseline', color='#d62728', alpha=0.6, linewidth=1.5)
        ax.plot(snapstart_data['invocation_id'], snapstart_data['client_latency_ms'],
                label='SnapStart', color='#2ca02c', alpha=0.6, linewidth=1.5)
        
        # Add rolling average
        if len(baseline_data) > 5:
            baseline_rolling = baseline_data['client_latency_ms'].rolling(window=5).mean()
            ax.plot(baseline_data['invocation_id'], baseline_rolling,
                    color='#d62728', linewidth=2.5, linestyle='--', alpha=0.9)
        
        if len(snapstart_data) > 5:
            snapstart_rolling = snapstart_data['client_latency_ms'].rolling(window=5).mean()
            ax.plot(snapstart_data['invocation_id'], snapstart_rolling,
                    color='#2ca02c', linewidth=2.5, linestyle='--', alpha=0.9)
        
        ax.set_xlabel('Invocation Number', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_title('Sustained Load Performance Over Time\n(10-minute test, dashed lines show 5-point moving average)', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', frameon=True, shadow=True)
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig3_sustained_load_timeline.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
        
    def plot_memory_impact_boxplot(self):
        """Figure 4: Latency Distribution by Memory Configuration"""
        print("\nCreating Figure 4: Memory Impact Box Plot...")
        
        warm_data = self.df[self.df['is_cold_start'] == False].copy()
        
        if len(warm_data) == 0:
            print("No warm start data found")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
        
        # Baseline
        baseline_data = warm_data[warm_data['function_type'] == 'baseline']
        memory_sizes_baseline = sorted(baseline_data['configured_memory'].unique())
        data_baseline = [baseline_data[baseline_data['configured_memory'] == m]['client_latency_ms'].values 
                         for m in memory_sizes_baseline]
        
        bp1 = axes[0].boxplot(data_baseline, labels=[f'{int(m)}MB' for m in memory_sizes_baseline],
                              patch_artist=True, medianprops=dict(color='red', linewidth=2))
        for patch in bp1['boxes']:
            patch.set_facecolor('#d62728')
            patch.set_alpha(0.6)
        
        axes[0].set_xlabel('Memory Configuration', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        axes[0].set_title('Baseline', fontsize=13, fontweight='bold')
        axes[0].grid(axis='y', alpha=0.3)
        
        # SnapStart
        snapstart_data = warm_data[warm_data['function_type'] == 'snapstart']
        memory_sizes_snapstart = sorted(snapstart_data['configured_memory'].unique())
        data_snapstart = [snapstart_data[snapstart_data['configured_memory'] == m]['client_latency_ms'].values 
                          for m in memory_sizes_snapstart]
        
        bp2 = axes[1].boxplot(data_snapstart, labels=[f'{int(m)}MB' for m in memory_sizes_snapstart],
                              patch_artist=True, medianprops=dict(color='red', linewidth=2))
        for patch in bp2['boxes']:
            patch.set_facecolor('#2ca02c')
            patch.set_alpha(0.6)
        
        axes[1].set_xlabel('Memory Configuration', fontsize=12, fontweight='bold')
        axes[1].set_title('SnapStart', fontsize=13, fontweight='bold')
        axes[1].grid(axis='y', alpha=0.3)
        
        fig.suptitle('Warm Start Latency Distribution by Memory Configuration', 
                     fontsize=14, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig4_memory_impact_boxplot.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
        
    def plot_improvement_summary(self):
        """Figure 5: Overall Performance Improvement Summary"""
        print("\nCreating Figure 5: Improvement Summary...")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = ['Cold Starts\n(512MB)', 'Cold Starts\n(1024MB)', 'Cold Starts\n(2048MB)',
                     'Warm Starts\n(All)', 'Sustained Load\n(P95)', 'Overall\n(Mean)']
        
        # Calculate improvements
        cold_512 = self.df[(self.df['is_cold_start'] == True) & (self.df['configured_memory'] == 512)]
        cold_1024 = self.df[(self.df['is_cold_start'] == True) & (self.df['configured_memory'] == 1024)]
        cold_2048 = self.df[(self.df['is_cold_start'] == True) & (self.df['configured_memory'] == 2048)]
        warm_all = self.df[self.df['is_cold_start'] == False]
        sustained = self.df[self.df['run_id'].str.contains('sustained', na=False)]
        
        improvements = []
        
        # Cold 512MB
        if len(cold_512) > 0:
            b = cold_512[cold_512['function_type'] == 'baseline']['client_latency_ms'].mean()
            s = cold_512[cold_512['function_type'] == 'snapstart']['client_latency_ms'].mean()
            improvements.append(((b - s) / b * 100) if b > 0 and s > 0 else 0)
        else:
            improvements.append(0)
        
        # Cold 1024MB
        if len(cold_1024) > 0:
            b = cold_1024[cold_1024['function_type'] == 'baseline']['client_latency_ms'].mean()
            s = cold_1024[cold_1024['function_type'] == 'snapstart']['client_latency_ms'].mean()
            improvements.append(((b - s) / b * 100) if b > 0 and s > 0 else 100)
        else:
            improvements.append(0)
        
        # Cold 2048MB
        if len(cold_2048) > 0:
            b = cold_2048[cold_2048['function_type'] == 'baseline']['client_latency_ms'].mean()
            s = cold_2048[cold_2048['function_type'] == 'snapstart']['client_latency_ms'].mean()
            improvements.append(((b - s) / b * 100) if b > 0 and s > 0 else 100)
        else:
            improvements.append(0)
        
        # Warm all
        b = warm_all[warm_all['function_type'] == 'baseline']['client_latency_ms'].mean()
        s = warm_all[warm_all['function_type'] == 'snapstart']['client_latency_ms'].mean()
        improvements.append(((b - s) / b * 100) if b > 0 else 0)
        
        # Sustained P95
        if len(sustained) > 0:
            b = sustained[sustained['function_type'] == 'baseline']['client_latency_ms'].quantile(0.95)
            s = sustained[sustained['function_type'] == 'snapstart']['client_latency_ms'].quantile(0.95)
            improvements.append(((b - s) / b * 100) if b > 0 else 0)
        else:
            improvements.append(0)
        
        # Overall
        b = self.df[self.df['function_type'] == 'baseline']['client_latency_ms'].mean()
        s = self.df[self.df['function_type'] == 'snapstart']['client_latency_ms'].mean()
        improvements.append(((b - s) / b * 100) if b > 0 else 0)
        
        colors = ['#2ca02c' if x > 0 else '#d62728' for x in improvements]
        bars = ax.bar(range(len(categories)), improvements, color=colors, alpha=0.8)
        
        ax.set_ylabel('Performance Improvement (%)', fontsize=12, fontweight='bold')
        ax.set_title('SnapStart Performance Improvement Summary\nAcross Different Scenarios', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=0, ha='center')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, improvements)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.1f}%',
                   ha='center', va='bottom' if height > 0 else 'top', 
                   fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig5_improvement_summary.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
        
    def generate_all_figures(self):
        """Generate all figures for research paper"""
        self.plot_cold_start_comparison()
        self.plot_percentile_comparison()
        self.plot_sustained_load_timeline()
        self.plot_memory_impact_boxplot()
        self.plot_improvement_summary()
        
        print(f"\n{'='*70}")
        print("ALL VISUALIZATIONS COMPLETE")
        print(f"{'='*70}")
        print(f"\nOutput directory: {self.output_dir}")
        print("\nGenerated Figures:")
        print("  1. fig1_cold_start_comparison.png")
        print("  2. fig2_percentile_comparison.png")
        print("  3. fig3_sustained_load_timeline.png")
        print("  4. fig4_memory_impact_boxplot.png")
        print("  5. fig5_improvement_summary.png")
        print("\nAll figures ready for research paper!")

def main():
    # Find the most recent comprehensive test CSV
    data_dir = 'data'
    csv_files = [f for f in os.listdir(data_dir) if f.startswith('comprehensive_test_') and f.endswith('.csv')]
    
    if not csv_files:
        print("No comprehensive test CSV files found!")
        return
    
    latest_file = sorted(csv_files)[-1]
    csv_path = os.path.join(data_dir, latest_file)
    
    print(f"Creating visualizations from: {csv_path}")
    
    visualizer = ResearchVisualizer(csv_path)
    visualizer.generate_all_figures()

if __name__ == "__main__":
    main()
