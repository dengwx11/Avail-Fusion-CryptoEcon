"""
Helper functions for integrating scenario analysis plots into existing notebooks.

This module provides drop-in functions that can be easily added to your existing
generate_report() function in price_dynamics_analysis.ipynb
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import warnings
warnings.filterwarnings('ignore')


def generate_scenario_comparison_plots(simulation_results: Dict[str, pd.DataFrame],
                                     show_plots: bool = True,
                                     save_plots: bool = False,
                                     output_prefix: str = "scenario_comparison") -> Dict[str, Any]:
    """
    Generate the two specific comparison plots requested:
    1. Scatterplot of AVL tokens vs USD rewards (portfolio = marker shape, scenario = color)
    2. Grouped barplot of return ratios (portfolio and scenario grouping)
    
    This function can be directly called from your notebook's generate_report() function.
    
    Args:
        simulation_results: Dictionary mapping scenario names to DataFrame results
        show_plots: Whether to display the plots (True for notebooks)
        save_plots: Whether to save plots to files
        output_prefix: Prefix for saved plot filenames
        
    Returns:
        Dictionary containing the analysis data and figure objects
    """
    
    print("📊 Generating Scenario Comparison Plots")
    print("="*50)
    
    # Extract final metrics for analysis
    analysis_data = []
    final_day = 365  # Analyze after 1 year
    
    for scenario_name, df in simulation_results.items():
        # Get final timestep data
        if len(df) == 0:
            continue
            
        final_data = df[df['timestep'] <= final_day].iloc[-1]
        agents = final_data['agents']
        
        # Extract metrics for each agent/portfolio type
        for agent_name, agent in agents.items():
            if not agent:
                continue
                
            # Calculate metrics
            avl_tokens = agent.accu_rewards_avl
            avl_price = agent.assets['AVL'].price
            usd_rewards = avl_tokens * avl_price
            
            # Approximate initial TVL (final TVL minus accumulated rewards)
            initial_tvl = agent.total_tvl - usd_rewards
            return_ratio = (usd_rewards / initial_tvl * 100) if initial_tvl > 0 else 0
            
            # Portfolio type from agent name
            portfolio_type = agent_name.replace('_maxi', '').upper()
            
            analysis_data.append({
                'scenario': scenario_name,
                'portfolio': portfolio_type, 
                'agent_name': agent_name,
                'avl_tokens': avl_tokens,
                'usd_rewards': usd_rewards,
                'return_ratio': return_ratio,
                'avl_price': avl_price
            })
    
    if not analysis_data:
        print("❌ No data available for plotting")
        return {}
        
    analysis_df = pd.DataFrame(analysis_data)
    
    # Create the two requested plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # =============================================================================
    # PLOT 1: SCATTERPLOT - AVL Tokens vs USD Rewards
    # Different portfolios = different marker shapes
    # Different scenarios = different colors
    # =============================================================================
    
    # Define marker styles for portfolios
    portfolio_markers = {
        'AVL': 'o',      # Circle
        'ETH': 's',      # Square
        'BTC': '^'       # Triangle
    }
    
    # Define colors for scenarios
    scenarios = analysis_df['scenario'].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(scenarios)))
    scenario_colors = dict(zip(scenarios, colors))
    
    # Create scatterplot
    for portfolio in analysis_df['portfolio'].unique():
        for scenario in scenarios:
            subset = analysis_df[
                (analysis_df['portfolio'] == portfolio) & 
                (analysis_df['scenario'] == scenario)
            ]
            
            if not subset.empty:
                ax1.scatter(
                    subset['avl_tokens'], 
                    subset['usd_rewards'],
                    marker=portfolio_markers.get(portfolio, 'o'),
                    color=scenario_colors[scenario],
                    s=120,  # Marker size
                    alpha=0.8,
                    edgecolors='black',
                    linewidth=1,
                    label=f'{portfolio}-{scenario}' if portfolio == list(analysis_df['portfolio'].unique())[0] else ""
                )
    
    # Customize scatterplot
    ax1.set_xlabel('Accumulated AVL Tokens', fontsize=12, fontweight='bold')
    ax1.set_ylabel('USD Value of Rewards', fontsize=12, fontweight='bold') 
    ax1.set_title('Portfolio Performance: AVL Tokens vs USD Rewards\n(Marker = Portfolio Type, Color = Scenario)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3)
    ax1.ticklabel_format(style='scientific', axis='both', scilimits=(0,0))
    
    # Create custom legend for scatterplot
    legend_elements = []
    
    # Add portfolio markers to legend
    for portfolio, marker in portfolio_markers.items():
        if portfolio in analysis_df['portfolio'].unique():
            legend_elements.append(
                plt.Line2D([0], [0], marker=marker, color='gray', linestyle='None', 
                          markersize=10, label=f'{portfolio} Portfolio')
            )
    
    # Add scenario colors to legend
    for scenario, color in scenario_colors.items():
        legend_elements.append(
            plt.Line2D([0], [0], marker='o', color=color, linestyle='None',
                      markersize=10, label=scenario)
        )
    
    ax1.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))
    
    # =============================================================================
    # PLOT 2: GROUPED BARPLOT - Return Ratios by Portfolio and Scenario  
    # =============================================================================
    
    # Create pivot table for grouped bar plot
    pivot_df = analysis_df.pivot(index='portfolio', columns='scenario', values='return_ratio')
    
    # Plot grouped bars
    x = np.arange(len(pivot_df.index))  # Portfolio positions
    width = 0.8 / len(pivot_df.columns)  # Bar width
    
    # Create bars for each scenario
    for i, scenario in enumerate(pivot_df.columns):
        values = pivot_df[scenario].values
        bars = ax2.bar(
            x + i * width - width * (len(pivot_df.columns) - 1) / 2, 
            values, 
            width, 
            label=scenario, 
            alpha=0.8,
            color=scenario_colors.get(scenario, f'C{i}')
        )
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            if not np.isnan(height):
                ax2.text(
                    bar.get_x() + bar.get_width()/2., 
                    height + height*0.01,
                    f'{height:.1f}%',
                    ha='center', va='bottom', 
                    fontsize=10, fontweight='bold'
                )
    
    # Customize barplot
    ax2.set_xlabel('Portfolio Type', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Return Ratio (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Return Ratios After 1 Year\nby Portfolio Type and Scenario', 
                 fontsize=14, fontweight='bold', pad=20)
    ax2.set_xticks(x)
    ax2.set_xticklabels(pivot_df.index)
    ax2.legend(title='Scenarios', loc='upper left', bbox_to_anchor=(1.02, 1))
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_ylim(bottom=0)
    
    # Overall figure title
    fig.suptitle('Scenario Analysis: Portfolio Performance Comparison', 
                fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    
    # Save plots if requested
    if save_plots:
        plt.savefig(f'{output_prefix}_comparison_plots.png', 
                   dpi=300, bbox_inches='tight')
        print(f"✅ Plots saved as '{output_prefix}_comparison_plots.png'")
    
    # Show plots if requested
    if show_plots:
        plt.show()
    
    # Print summary statistics
    print(f"\n📈 SUMMARY STATISTICS:")
    print("="*50)
    
    summary_stats = analysis_df.groupby(['scenario', 'portfolio']).agg({
        'avl_tokens': 'mean',
        'usd_rewards': 'mean',
        'return_ratio': 'mean'
    }).round(2)
    
    for scenario in analysis_df['scenario'].unique():
        scenario_data = analysis_df[analysis_df['scenario'] == scenario]
        print(f"\n{scenario}:")
        for portfolio in scenario_data['portfolio'].unique():
            portfolio_data = scenario_data[scenario_data['portfolio'] == portfolio]
            if not portfolio_data.empty:
                row = portfolio_data.iloc[0]
                print(f"  {portfolio}: {row['avl_tokens']:,.0f} AVL → ${row['usd_rewards']:,.0f} USD ({row['return_ratio']:.1f}% return)")
    
    return {
        'analysis_data': analysis_df,
        'summary_stats': summary_stats,
        'figure': fig
    }


def quick_scenario_plots(results_dict: Dict[str, pd.DataFrame]) -> None:
    """
    Quick function to generate both plots in one call.
    Perfect for dropping into existing generate_report() functions.
    
    Usage in your notebook:
    ```python
    from notebook_integration_helper import quick_scenario_plots
    
    def generate_report(results):
        # ... your existing code ...
        
        # Add these two lines to get the comparison plots:
        quick_scenario_plots(results)
    ```
    """
    generate_scenario_comparison_plots(
        simulation_results=results_dict,
        show_plots=True,
        save_plots=True,
        output_prefix="notebook_scenario_analysis"
    )


# Example usage function that demonstrates the integration
def example_integration_with_existing_report():
    """
    Example showing how to integrate with existing generate_report() function
    """
    
    def generate_report(results):
        """
        This is what your existing generate_report() function might look like
        with the new plotting functions integrated
        """
        
        print("📊 Generating Comprehensive Report")
        print("="*50)
        
        # Your existing analysis code here...
        # ...
        
        # Add the new comparison plots at the end:
        print("\n🎯 Generating Scenario Comparison Plots...")
        comparison_analysis = generate_scenario_comparison_plots(
            simulation_results=results,
            show_plots=True,
            save_plots=True,
            output_prefix="report_scenario_comparison"
        )
        
        print("\n✅ Report generation complete!")
        
        return comparison_analysis
    
    # This is just an example - you would call this with your actual results
    print("This is an example of how to integrate the plotting functions")
    print("into your existing generate_report() function in your notebook.") 