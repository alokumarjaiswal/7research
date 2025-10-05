import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set style for academic publications
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 11

class CostPerformanceVisualizer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.output_dir = 'data/visualizations'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # AWS Lambda pricing (as of 2025)
        self.request_cost = 0.20 / 1_000_000  # $0.20 per 1M requests
        self.duration_cost_per_gb_sec = 0.0000166667  # $ per GB-second
        
    def calculate_costs(self):
        """Calculate costs for each configuration"""
        results = {}
        
        memory_configs = sorted(self.df['configured_memory'].unique())
        
        for memory_mb in memory_configs:
            memory_data = self.df[self.df['configured_memory'] == memory_mb]
            
            for func_type in ['baseline', 'snapstart']:
                func_data = memory_data[memory_data['function_type'] == func_type]
                
                if len(func_data) == 0:
                    continue
                
                # Calculate average execution time (convert ms to seconds)
                avg_duration_sec = func_data['client_latency_ms'].mean() / 1000
                
                # Calculate cost per invocation
                memory_gb = memory_mb / 1024
                duration_cost = self.duration_cost_per_gb_sec * memory_gb * avg_duration_sec
                total_cost_per_invocation = self.request_cost + duration_cost
                
                # Calculate cost per 1000 invocations
                cost_per_1000 = total_cost_per_invocation * 1000
                
                # Get performance metrics
                mean_latency = func_data['client_latency_ms'].mean()
                p95_latency = func_data['client_latency_ms'].quantile(0.95)
                
                key = f"{func_type}_{memory_mb}MB"
                results[key] = {
                    'function_type': func_type,
                    'memory_mb': memory_mb,
                    'cost_per_1000': cost_per_1000,
                    'mean_latency_ms': mean_latency,
                    'p95_latency_ms': p95_latency,
                    'invocations': len(func_data)
                }
        
        return results
    
    def create_scatter_plot(self):
        """Figure 6: Cost-Performance Trade-off Scatter Plot"""
        print("\nCreating Figure 6: Cost-Performance Trade-off...")
        
        costs = self.calculate_costs()
        
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Separate data by function type
        baseline_data = {k: v for k, v in costs.items() if v['function_type'] == 'baseline'}
        snapstart_data = {k: v for k, v in costs.items() if v['function_type'] == 'snapstart'}
        
        # Plot baseline points
        baseline_costs = [v['cost_per_1000'] for v in baseline_data.values()]
        baseline_latencies = [v['mean_latency_ms'] for v in baseline_data.values()]
        baseline_memories = [v['memory_mb'] for v in baseline_data.values()]
        
        for i, (cost, latency, mem) in enumerate(zip(baseline_costs, baseline_latencies, baseline_memories)):
            ax.scatter(cost, latency, s=300, color='#d62728', marker='o', 
                      edgecolors='black', linewidths=2, alpha=0.7, zorder=5)
            ax.annotate(f'Baseline\n{mem}MB', xy=(cost, latency), 
                       xytext=(10, -15), textcoords='offset points',
                       fontsize=9, ha='left', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#d62728', 
                                alpha=0.2, edgecolor='none'))
        
        # Plot SnapStart points
        snapstart_costs = [v['cost_per_1000'] for v in snapstart_data.values()]
        snapstart_latencies = [v['mean_latency_ms'] for v in snapstart_data.values()]
        snapstart_memories = [v['memory_mb'] for v in snapstart_data.values()]
        
        for i, (cost, latency, mem) in enumerate(zip(snapstart_costs, snapstart_latencies, snapstart_memories)):
            ax.scatter(cost, latency, s=300, color='#2ca02c', marker='s', 
                      edgecolors='black', linewidths=2, alpha=0.7, zorder=5)
            ax.annotate(f'SnapStart\n{mem}MB', xy=(cost, latency), 
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=9, ha='left', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#2ca02c', 
                                alpha=0.2, edgecolor='none'))
        
        # Draw arrows showing improvement direction
        for mem in sorted(set(baseline_memories) & set(snapstart_memories)):
            baseline_point = next((v for v in baseline_data.values() if v['memory_mb'] == mem), None)
            snapstart_point = next((v for v in snapstart_data.values() if v['memory_mb'] == mem), None)
            
            if baseline_point and snapstart_point:
                ax.annotate('', xy=(snapstart_point['cost_per_1000'], snapstart_point['mean_latency_ms']),
                           xytext=(baseline_point['cost_per_1000'], baseline_point['mean_latency_ms']),
                           arrowprops=dict(arrowstyle='->', lw=1.5, color='gray', 
                                         alpha=0.5, linestyle='--'))
        
        # Add ideal direction indicator
        ax.annotate('Better\n(Lower cost & latency)', xy=(0.05, 0.05), xycoords='axes fraction',
                   fontsize=10, ha='left', va='bottom', color='green', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.3))
        
        ax.set_xlabel('Cost per 1,000 Invocations ($)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Mean Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_title('Cost-Performance Trade-off Analysis:\nBaseline vs SnapStart Across Memory Configurations', 
                     fontsize=14, fontweight='bold', pad=20)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#d62728', 
                      markersize=12, label='Baseline', markeredgecolor='black', markeredgewidth=2),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='#2ca02c', 
                      markersize=12, label='SnapStart', markeredgecolor='black', markeredgewidth=2)
        ]
        ax.legend(handles=legend_elements, loc='upper right', frameon=True, 
                 shadow=True, fontsize=11, title='Function Type', title_fontsize=12)
        
        ax.grid(alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig6_cost_performance_tradeoff.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
        
    def create_pareto_frontier_plot(self):
        """Figure 7: Pareto Frontier Analysis"""
        print("\nCreating Figure 7: Pareto Frontier...")
        
        costs = self.calculate_costs()
        
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Prepare data
        all_points = []
        for key, data in costs.items():
            all_points.append({
                'name': key,
                'type': data['function_type'],
                'memory': data['memory_mb'],
                'cost': data['cost_per_1000'],
                'latency': data['mean_latency_ms']
            })
        
        # Sort by cost
        all_points.sort(key=lambda x: x['cost'])
        
        # Find Pareto frontier
        pareto_points = []
        min_latency = float('inf')
        
        for point in all_points:
            if point['latency'] < min_latency:
                pareto_points.append(point)
                min_latency = point['latency']
        
        # Plot all points
        for point in all_points:
            color = '#2ca02c' if point['type'] == 'snapstart' else '#d62728'
            marker = 's' if point['type'] == 'snapstart' else 'o'
            alpha = 1.0 if point in pareto_points else 0.3
            size = 300 if point in pareto_points else 150
            
            ax.scatter(point['cost'], point['latency'], s=size, color=color, 
                      marker=marker, edgecolors='black', linewidths=2 if point in pareto_points else 1, 
                      alpha=alpha, zorder=5 if point in pareto_points else 3)
            
            if point in pareto_points:
                ax.annotate(f"{point['memory']}MB", xy=(point['cost'], point['latency']), 
                           xytext=(10, -10), textcoords='offset points',
                           fontsize=9, ha='left', fontweight='bold')
        
        # Draw Pareto frontier line
        if len(pareto_points) > 1:
            pareto_costs = [p['cost'] for p in pareto_points]
            pareto_latencies = [p['latency'] for p in pareto_points]
            ax.plot(pareto_costs, pareto_latencies, 'g--', linewidth=2.5, 
                   label='Pareto Frontier', alpha=0.7, zorder=4)
        
        ax.set_xlabel('Cost per 1,000 Invocations ($)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Mean Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_title('Pareto Frontier Analysis:\nOptimal Cost-Performance Configurations', 
                     fontsize=14, fontweight='bold', pad=20)
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#d62728', 
                      markersize=10, label='Baseline', markeredgecolor='black', markeredgewidth=2),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='#2ca02c', 
                      markersize=10, label='SnapStart', markeredgecolor='black', markeredgewidth=2),
            plt.Line2D([0], [0], color='green', linewidth=2.5, linestyle='--', 
                      label='Pareto Frontier')
        ]
        ax.legend(handles=legend_elements, loc='upper right', frameon=True, 
                 shadow=True, fontsize=10)
        
        ax.grid(alpha=0.3, linestyle='--')
        
        # Add annotation about Pareto optimality
        ax.text(0.05, 0.95, 'Points on the frontier represent\noptimal cost-performance trade-offs',
               transform=ax.transAxes, fontsize=9, va='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig7_pareto_frontier.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
        
    def create_cost_breakdown_chart(self):
        """Figure 8: Cost Component Breakdown"""
        print("\nCreating Figure 8: Cost Breakdown...")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        memory_configs = [512, 1024, 2048]
        
        for ax, func_type, color in [(ax1, 'baseline', '#d62728'), (ax2, 'snapstart', '#2ca02c')]:
            request_costs = []
            duration_costs = []
            
            for memory_mb in memory_configs:
                func_data = self.df[(self.df['configured_memory'] == memory_mb) & 
                                   (self.df['function_type'] == func_type)]
                
                if len(func_data) == 0:
                    request_costs.append(0)
                    duration_costs.append(0)
                    continue
                
                avg_duration_sec = func_data['client_latency_ms'].mean() / 1000
                memory_gb = memory_mb / 1024
                
                req_cost = self.request_cost * 1000
                dur_cost = self.duration_cost_per_gb_sec * memory_gb * avg_duration_sec * 1000
                
                request_costs.append(req_cost)
                duration_costs.append(dur_cost)
            
            x = np.arange(len(memory_configs))
            width = 0.5
            
            bars1 = ax.bar(x, request_costs, width, label='Request Cost', 
                          color='lightblue', edgecolor='black', linewidth=1.5)
            bars2 = ax.bar(x, duration_costs, width, bottom=request_costs, 
                          label='Duration Cost', color=color, alpha=0.7, 
                          edgecolor='black', linewidth=1.5)
            
            ax.set_xlabel('Memory Configuration (MB)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Cost per 1,000 Invocations ($)', fontsize=11, fontweight='bold')
            ax.set_title(f'{func_type.capitalize()}', fontsize=12, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([f'{m}MB' for m in memory_configs])
            ax.legend(loc='upper left', frameon=True, shadow=True)
            ax.grid(axis='y', alpha=0.3)
            
            # Add total cost labels
            for i, (r, d) in enumerate(zip(request_costs, duration_costs)):
                total = r + d
                ax.text(i, total, f'${total:.4f}', ha='center', va='bottom', 
                       fontsize=9, fontweight='bold')
        
        fig.suptitle('Cost Component Breakdown by Memory Configuration', 
                    fontsize=14, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'fig8_cost_breakdown.png')
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {filename}")
    
    def generate_all_figures(self):
        """Generate all cost-performance figures"""
        print(f"\n{'='*70}")
        print("CREATING COST-PERFORMANCE VISUALIZATIONS")
        print(f"{'='*70}")
        
        self.create_scatter_plot()
        self.create_pareto_frontier_plot()
        self.create_cost_breakdown_chart()
        
        print(f"\n{'='*70}")
        print("ALL COST-PERFORMANCE FIGURES COMPLETE")
        print(f"{'='*70}")
        print("\nGenerated Figures:")
        print("  6. fig6_cost_performance_tradeoff.png")
        print("  7. fig7_pareto_frontier.png")
        print("  8. fig8_cost_breakdown.png")

def main():
    # Find the most recent comprehensive test CSV
    data_dir = 'data'
    csv_files = [f for f in os.listdir(data_dir) if f.startswith('comprehensive_test_') and f.endswith('.csv')]
    
    if not csv_files:
        print("No comprehensive test CSV files found!")
        return
    
    latest_file = sorted(csv_files)[-1]
    csv_path = os.path.join(data_dir, latest_file)
    
    print(f"Creating cost-performance visualizations from: {csv_path}")
    
    visualizer = CostPerformanceVisualizer(csv_path)
    visualizer.generate_all_figures()

if __name__ == "__main__":
    main()
