"""
Scenario Analysis Visualization Module

This module provides specialized plotting functions for comparing simulation results
across different scenarios and portfolio configurations (user profiles).

The functions are designed to work with simulation data that contains:
- Multiple scenarios (different market conditions, parameters, etc.)
- Multiple portfolio types (different agent/user profiles like avl_maxi, eth_maxi, btc_maxi)
- Accumulated rewards data over time
- Return ratio calculations
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from typing import Dict, List, Optional, Union, Any, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def extract_final_metrics(simulation_results: Dict[str, pd.DataFrame], 
                         final_day: int = 365) -> pd.DataFrame:
    """
    Extract final metrics from simulation results for analysis.
    
    Args:
        simulation_results: Dictionary mapping scenario names to simulation DataFrames
        final_day: The day to extract final metrics from (default: 365 for 1 year)
    
    Returns:
        DataFrame with columns: scenario, portfolio, avl_tokens, usd_rewards, return_ratio
    """
    analysis_data = []
    
    for scenario_name, df in simulation_results.items():
        # Get the final timestep data (closest to final_day)
        final_data = df[df['timestep'] <= final_day].iloc[-1] if len(df) > 0 else None
        
        if final_data is None:
            continue
            
        agents = final_data['agents']
        
        # Extract metrics for each agent (portfolio type)
        for agent_name, agent in agents.items():
            # Skip if agent doesn't exist
            if not agent:
                continue
                
            # Get final accumulated rewards in AVL tokens
            avl_tokens = agent.accu_rewards_avl
            
            # Get USD value of rewards (rewards * AVL price)
            avl_price = agent.assets['AVL'].price
            usd_rewards = avl_tokens * avl_price
            
            # Calculate return ratio (total rewards USD / initial TVL)
            initial_tvl = agent.total_tvl - usd_rewards  # Approximate initial TVL
            return_ratio = (usd_rewards / initial_tvl * 100) if initial_tvl > 0 else 0
            
            # Get agent's primary asset for portfolio classification
            portfolio_type = agent_name.replace('_maxi', '').upper()
            
            analysis_data.append({
                'scenario': scenario_name,
                'portfolio': portfolio_type,
                'agent_name': agent_name,
                'avl_tokens': avl_tokens,
                'usd_rewards': usd_rewards,
                'return_ratio': return_ratio,
                'initial_tvl': initial_tvl,
                'final_tvl': agent.total_tvl,
                'avl_price': avl_price
            })
    
    return pd.DataFrame(analysis_data)


def plot_rewards_scatterplot(simulation_results: Dict[str, pd.DataFrame], 
                            final_day: int = 365,
                            figsize: Tuple[int, int] = (12, 8),
                            save_path: Optional[str] = None) -> plt.Figure:
    """
    Create a scatterplot showing AVL tokens vs USD value of rewards after 1 year,
    with different portfolios shown by marker shapes and scenarios shown by colors.
    
    Args:
        simulation_results: Dictionary mapping scenario names to simulation DataFrames
        final_day: The day to extract final metrics from (default: 365 for 1 year)
        figsize: Figure size as (width, height)
        save_path: Optional path to save the plot
    
    Returns:
        matplotlib Figure object
    """
    # Extract final metrics
    analysis_df = extract_final_metrics(simulation_results, final_day)
    
    if analysis_df.empty:
        print("No data available for plotting")
        return None
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Define marker styles for different portfolios
    portfolio_markers = {
        'AVL': 'o',      # Circle
        'ETH': 's',      # Square  
        'BTC': '^'       # Triangle
    }
    
    # Define colors for different scenarios
    scenarios = analysis_df['scenario'].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(scenarios)))
    scenario_colors = dict(zip(scenarios, colors))
    
    # Create scatter plot for each portfolio-scenario combination
    for portfolio in analysis_df['portfolio'].unique():
        for scenario in scenarios:
            subset = analysis_df[(analysis_df['portfolio'] == portfolio) & 
                               (analysis_df['scenario'] == scenario)]
            
            if not subset.empty:
                ax.scatter(
                    subset['avl_tokens'], 
                    subset['usd_rewards'],
                    marker=portfolio_markers.get(portfolio, 'o'),
                    color=scenario_colors[scenario],
                    s=100,  # Size of markers
                    alpha=0.7,
                    label=f'{portfolio} - {scenario}',
                    edgecolors='black',
                    linewidth=0.5
                )
    
    # Customize the plot
    ax.set_xlabel('Accumulated AVL Tokens', fontsize=12, fontweight='bold')
    ax.set_ylabel('USD Value of Rewards', fontsize=12, fontweight='bold')
    ax.set_title(f'Rewards Comparison After {final_day} Days\nby Portfolio Type and Scenario', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Create custom legend
    # First, create legend for portfolios (marker shapes)
    portfolio_handles = []
    for portfolio, marker in portfolio_markers.items():
        if portfolio in analysis_df['portfolio'].unique():
            portfolio_handles.append(
                plt.Line2D([0], [0], marker=marker, color='gray', 
                          linestyle='None', markersize=8, label=f'{portfolio} Portfolio')
            )
    
    # Create legend for scenarios (colors)
    scenario_handles = []
    for scenario, color in scenario_colors.items():
        scenario_handles.append(
            plt.Line2D([0], [0], marker='o', color=color, 
                      linestyle='None', markersize=8, label=scenario)
        )
    
    # Create two legends
    portfolio_legend = ax.legend(handles=portfolio_handles, title='Portfolio Types', 
                               loc='upper left', bbox_to_anchor=(1.02, 1))
    scenario_legend = ax.legend(handles=scenario_handles, title='Scenarios', 
                              loc='upper left', bbox_to_anchor=(1.02, 0.6))
    
    # Add both legends to the plot
    ax.add_artist(portfolio_legend)
    ax.add_artist(scenario_legend)
    
    # Format axes
    ax.ticklabel_format(style='scientific', axis='both', scilimits=(0,0))
    
    # Adjust layout to prevent legend cutoff
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    
    return fig


def plot_return_ratio_barplot(simulation_results: Dict[str, pd.DataFrame], 
                             final_day: int = 365,
                             figsize: Tuple[int, int] = (12, 8),
                             save_path: Optional[str] = None) -> plt.Figure:
    """
    Create a grouped barplot showing return ratios for different portfolios and scenarios.
    
    Args:
        simulation_results: Dictionary mapping scenario names to simulation DataFrames
        final_day: The day to extract final metrics from (default: 365 for 1 year)
        figsize: Figure size as (width, height)
        save_path: Optional path to save the plot
    
    Returns:
        matplotlib Figure object
    """
    # Extract final metrics
    analysis_df = extract_final_metrics(simulation_results, final_day)
    
    if analysis_df.empty:
        print("No data available for plotting")
        return None
    
    # Create pivot table for easier plotting
    pivot_df = analysis_df.pivot(index='portfolio', columns='scenario', values='return_ratio')
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create grouped bar plot
    x = np.arange(len(pivot_df.index))  # Portfolio positions
    width = 0.8 / len(pivot_df.columns)  # Width of bars
    
    # Plot bars for each scenario
    for i, scenario in enumerate(pivot_df.columns):
        values = pivot_df[scenario].values
        bars = ax.bar(x + i * width - width * (len(pivot_df.columns) - 1) / 2, 
                     values, width, label=scenario, alpha=0.8)
        
        # Add value labels on top of bars
        for j, bar in enumerate(bars):
            height = bar.get_height()
            if not np.isnan(height):
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Customize the plot
    ax.set_xlabel('Portfolio Type', fontsize=12, fontweight='bold')
    ax.set_ylabel('Return Ratio (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Return Ratios After {final_day} Days\nby Portfolio Type and Scenario', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Set x-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_df.index)
    
    # Add legend
    ax.legend(title='Scenarios', loc='upper left', bbox_to_anchor=(1.02, 1))
    
    # Add grid
    ax.grid(True, alpha=0.3, axis='y')
    
    # Set y-axis to start from 0
    ax.set_ylim(bottom=0)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    
    return fig


def plot_scenario_comparison_dashboard(simulation_results: Dict[str, pd.DataFrame], 
                                     final_day: int = 365,
                                     figsize: Tuple[int, int] = (16, 12),
                                     save_path: Optional[str] = None) -> plt.Figure:
    """
    Create a comprehensive dashboard comparing scenarios across multiple metrics.
    
    Args:
        simulation_results: Dictionary mapping scenario names to simulation DataFrames
        final_day: The day to extract final metrics from (default: 365 for 1 year)
        figsize: Figure size as (width, height)
        save_path: Optional path to save the plot
    
    Returns:
        matplotlib Figure object
    """
    # Extract final metrics
    analysis_df = extract_final_metrics(simulation_results, final_day)
    
    if analysis_df.empty:
        print("No data available for plotting")
        return None
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
    
    # 1. Rewards Scatterplot (top-left)
    portfolio_markers = {'AVL': 'o', 'ETH': 's', 'BTC': '^'}
    scenarios = analysis_df['scenario'].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(scenarios)))
    scenario_colors = dict(zip(scenarios, colors))
    
    for portfolio in analysis_df['portfolio'].unique():
        for scenario in scenarios:
            subset = analysis_df[(analysis_df['portfolio'] == portfolio) & 
                               (analysis_df['scenario'] == scenario)]
            
            if not subset.empty:
                ax1.scatter(
                    subset['avl_tokens'], 
                    subset['usd_rewards'],
                    marker=portfolio_markers.get(portfolio, 'o'),
                    color=scenario_colors[scenario],
                    s=80, alpha=0.7,
                    edgecolors='black', linewidth=0.5
                )
    
    ax1.set_xlabel('AVL Tokens')
    ax1.set_ylabel('USD Rewards')
    ax1.set_title('Rewards: AVL Tokens vs USD Value')
    ax1.grid(True, alpha=0.3)
    
    # 2. Return Ratio Barplot (top-right)
    pivot_df = analysis_df.pivot(index='portfolio', columns='scenario', values='return_ratio')
    x = np.arange(len(pivot_df.index))
    width = 0.8 / len(pivot_df.columns)
    
    for i, scenario in enumerate(pivot_df.columns):
        values = pivot_df[scenario].values
        ax2.bar(x + i * width - width * (len(pivot_df.columns) - 1) / 2, 
               values, width, label=scenario, alpha=0.8)
    
    ax2.set_xlabel('Portfolio Type')
    ax2.set_ylabel('Return Ratio (%)')
    ax2.set_title('Return Ratios by Portfolio')
    ax2.set_xticks(x)
    ax2.set_xticklabels(pivot_df.index)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.legend()
    
    # 3. Final TVL Comparison (bottom-left)
    pivot_tvl = analysis_df.pivot(index='portfolio', columns='scenario', values='final_tvl')
    
    for i, scenario in enumerate(pivot_tvl.columns):
        values = pivot_tvl[scenario].values
        ax3.bar(x + i * width - width * (len(pivot_tvl.columns) - 1) / 2, 
               values, width, label=scenario, alpha=0.8)
    
    ax3.set_xlabel('Portfolio Type')
    ax3.set_ylabel('Final TVL (USD)')
    ax3.set_title('Final Total Value Locked')
    ax3.set_xticks(x)
    ax3.set_xticklabels(pivot_tvl.index)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
    
    # 4. Summary Statistics Table (bottom-right)
    ax4.axis('tight')
    ax4.axis('off')
    
    # Create summary statistics
    summary_stats = analysis_df.groupby(['scenario', 'portfolio']).agg({
        'avl_tokens': 'mean',
        'usd_rewards': 'mean', 
        'return_ratio': 'mean'
    }).round(2)
    
    # Create table
    table_data = []
    for (scenario, portfolio), row in summary_stats.iterrows():
        table_data.append([
            scenario, portfolio, 
            f"{row['avl_tokens']:,.0f}",
            f"${row['usd_rewards']:,.0f}",
            f"{row['return_ratio']:.1f}%"
        ])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Scenario', 'Portfolio', 'AVL Tokens', 'USD Rewards', 'Return %'],
                     cellLoc='center',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    ax4.set_title('Summary Statistics', fontweight='bold')
    
    # Overall title
    fig.suptitle(f'Scenario Comparison Dashboard - Day {final_day}', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Dashboard saved to {save_path}")
    
    return fig


def generate_comparison_report(simulation_results: Dict[str, pd.DataFrame], 
                             final_day: int = 365,
                             output_dir: str = "results") -> Dict[str, Any]:
    """
    Generate a comprehensive comparison report with both plots and summary statistics.
    
    Args:
        simulation_results: Dictionary mapping scenario names to simulation DataFrames
        final_day: The day to extract final metrics from (default: 365 for 1 year)
        output_dir: Directory to save output files
    
    Returns:
        Dictionary containing analysis results and figure objects
    """
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract final metrics
    analysis_df = extract_final_metrics(simulation_results, final_day)
    
    if analysis_df.empty:
        print("No data available for analysis")
        return {}
    
    # Generate plots
    print("Generating comparison plots...")
    
    # 1. Rewards scatterplot
    fig1 = plot_rewards_scatterplot(
        simulation_results, final_day, 
        save_path=f"{output_dir}/rewards_scatterplot.png"
    )
    
    # 2. Return ratio barplot
    fig2 = plot_return_ratio_barplot(
        simulation_results, final_day,
        save_path=f"{output_dir}/return_ratio_barplot.png"
    )
    
    # 3. Comprehensive dashboard
    fig3 = plot_scenario_comparison_dashboard(
        simulation_results, final_day,
        save_path=f"{output_dir}/comparison_dashboard.png"
    )
    
    # Generate summary statistics
    print("Generating summary statistics...")
    
    summary_stats = analysis_df.groupby(['scenario', 'portfolio']).agg({
        'avl_tokens': ['mean', 'std'],
        'usd_rewards': ['mean', 'std'],
        'return_ratio': ['mean', 'std'],
        'final_tvl': ['mean', 'std']
    }).round(3)
    
    # Save summary statistics
    summary_stats.to_csv(f"{output_dir}/summary_statistics.csv")
    
    # Save detailed analysis data
    analysis_df.to_csv(f"{output_dir}/detailed_analysis.csv", index=False)
    
    print(f"\nComparison report generated successfully!")
    print(f"Files saved to '{output_dir}' directory:")
    print("- rewards_scatterplot.png")
    print("- return_ratio_barplot.png") 
    print("- comparison_dashboard.png")
    print("- summary_statistics.csv")
    print("- detailed_analysis.csv")
    
    # Display basic statistics
    print(f"\n📊 SUMMARY STATISTICS:")
    print("="*60)
    
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
        'figures': {
            'scatterplot': fig1,
            'barplot': fig2,
            'dashboard': fig3
        }
    } 