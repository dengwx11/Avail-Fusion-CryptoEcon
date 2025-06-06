"""
Notebook-specific plotting functions for scenario and portfolio analysis.

This module provides plotting functions that work directly with the output
of the analyze_multiple_scenarios function from the price_dynamics_analysis notebook.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from typing import Dict, List, Optional, Tuple


def plot_avl_tokens_vs_usd_rewards_scatter(
    analysis_results: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 8),
    save_path: Optional[str] = None,
    title: str = "AVL Tokens vs USD Rewards After 1 Year"
) -> plt.Figure:
    """
    Create a scatterplot showing AVL tokens vs USD value of rewards after 1 year,
    with different portfolios shown by marker shapes and scenarios shown by colors.
    
    Args:
        analysis_results: DataFrame from analyze_multiple_scenarios function with columns:
                         'Scenario', 'Allocation', 'Rewards (AVL)', 'Rewards (USD)', etc.
        figsize: Figure size as (width, height)
        save_path: Optional path to save the plot
        title: Plot title
    
    Returns:
        matplotlib Figure object
    """
    if analysis_results.empty:
        print("No data available for plotting")
        return None
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Define marker styles for different portfolios/allocations
    allocations = analysis_results['Allocation'].unique()
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']  # Circle, Square, Triangle, etc.
    allocation_markers = {alloc: markers[i % len(markers)] for i, alloc in enumerate(allocations)}
    
    # Define colors for different scenarios
    scenarios = analysis_results['Scenario'].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(scenarios)))
    scenario_colors = {scenario: colors[i] for i, scenario in enumerate(scenarios)}
    
    # Create scatter plot for each allocation-scenario combination
    for allocation in allocations:
        for scenario in scenarios:
            subset = analysis_results[
                (analysis_results['Allocation'] == allocation) & 
                (analysis_results['Scenario'] == scenario)
            ]
            
            if not subset.empty:
                ax.scatter(
                    subset['Rewards (AVL)'], 
                    subset['Rewards (USD)'],
                    marker=allocation_markers[allocation],
                    color=scenario_colors[scenario],
                    s=120,  # Size of markers
                    alpha=0.8,
                    label=f'{allocation} - {scenario}',
                    edgecolors='black',
                    linewidth=1
                )
    
    # Customize the plot
    ax.set_xlabel('Accumulated AVL Tokens', fontsize=12, fontweight='bold')
    ax.set_ylabel('USD Value of Rewards', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Create custom legend - combine both portfolio types and scenarios in one legend
    legend_handles = []
    
    # Add portfolio type handles (marker shapes)
    legend_handles.append(plt.Line2D([0], [0], marker='', color='white', 
                                   linestyle='None', label='Portfolio Types:', 
                                   markeredgecolor='white'))
    for allocation, marker in allocation_markers.items():
        legend_handles.append(
            plt.Line2D([0], [0], marker=marker, color='gray', 
                      linestyle='None', markersize=10, label=f'  {allocation}',
                      markeredgecolor='black', markeredgewidth=1)
        )
    
    # Add a separator
    legend_handles.append(plt.Line2D([0], [0], marker='', color='white', 
                                   linestyle='None', label=' ', 
                                   markeredgecolor='white'))
    
    # Add scenario handles (colors)
    legend_handles.append(plt.Line2D([0], [0], marker='', color='white', 
                                   linestyle='None', label='Scenarios:', 
                                   markeredgecolor='white'))
    for scenario, color in scenario_colors.items():
        legend_handles.append(
            plt.Line2D([0], [0], marker='o', color=color, 
                      linestyle='None', markersize=10, label=f'  {scenario}',
                      markeredgecolor='black', markeredgewidth=1)
        )
    
    # Create single combined legend
    ax.legend(handles=legend_handles, 
             loc='upper left', bbox_to_anchor=(1.02, 1.0),
             fontsize=10, frameon=True, fancybox=True, shadow=True)
    
    # Format axes with thousand separators
    ax.ticklabel_format(style='plain', axis='both')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Add annotations for each point showing the exact values
    for _, row in analysis_results.iterrows():
        ax.annotate(
            f'{row["Allocation"].split(",")[0]}',  # Show first part of allocation name
            (row['Rewards (AVL)'], row['Rewards (USD)']),
            xytext=(5, 5), textcoords='offset points',
            fontsize=8, alpha=0.7
        )
    
    # Adjust layout to prevent legend cutoff
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Scatterplot saved to {save_path}")
    
    return fig


def plot_return_ratio_grouped_barplot(
    analysis_results: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 8),
    save_path: Optional[str] = None,
    title: str = "Return Ratios After 1 Year by Portfolio and Scenario"
) -> plt.Figure:
    """
    Create a grouped barplot showing return ratios for different portfolios and scenarios.
    
    Args:
        analysis_results: DataFrame from analyze_multiple_scenarios function
        figsize: Figure size as (width, height)
        save_path: Optional path to save the plot
        title: Plot title
    
    Returns:
        matplotlib Figure object
    """
    if analysis_results.empty:
        print("No data available for plotting")
        return None
    
    # Create a copy and convert return ratio to percentage
    plot_data = analysis_results.copy()
    plot_data['Return Ratio (%)'] = plot_data['Return Ratio (Rewards/Initial)'] * 100
    
    # Create pivot table - GROUP BY SCENARIOS (scenarios on x-axis, portfolios as bars)
    pivot_df = plot_data.pivot(index='Scenario', columns='Allocation', values='Return Ratio (%)')
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create grouped bar plot
    x = np.arange(len(pivot_df.index))  # Scenario positions (x-axis groups)
    width = 0.8 / len(pivot_df.columns)  # Width of bars
    
    # Define colors for portfolios (portfolios are now the different colored bars)
    portfolios = pivot_df.columns
    colors = plt.cm.Set1(np.linspace(0, 1, len(portfolios)))
    portfolio_colors = {portfolio: colors[i] for i, portfolio in enumerate(portfolios)}
    
    # Plot bars for each portfolio
    for i, portfolio in enumerate(pivot_df.columns):
        values = pivot_df[portfolio].values
        bars = ax.bar(
            x + i * width - width * (len(pivot_df.columns) - 1) / 2, 
            values, 
            width, 
            label=portfolio, 
            alpha=0.8,
            color=portfolio_colors[portfolio],
            edgecolor='black',
            linewidth=0.5
        )
        
        # Add value labels on top of bars
        for j, bar in enumerate(bars):
            height = bar.get_height()
            if not np.isnan(height):
                # Position labels above positive bars, below negative bars
                if height >= 0:
                    label_y = height + max(abs(values)) * 0.01
                    va = 'bottom'
                else:
                    label_y = height - max(abs(values)) * 0.01
                    va = 'top'
                
                ax.text(
                    bar.get_x() + bar.get_width()/2., 
                    label_y,
                    f'{height:.1f}%',
                    ha='center', va=va, 
                    fontsize=10, fontweight='bold'
                )
    
    # Customize the plot
    ax.set_xlabel('Scenario', fontsize=12, fontweight='bold')
    ax.set_ylabel('Return Ratio (%)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Set x-axis labels (scenarios)
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_df.index, fontsize=10, rotation=45, ha='right')
    
    # Add legend for portfolios
    ax.legend(title='Portfolio Types', loc='upper left', bbox_to_anchor=(1.02, 1),
             fontsize=10, title_fontsize=11)
    
    # Add grid
    ax.grid(True, alpha=0.3, axis='y')
    
    # Format y-axis with percentage (allow negative values)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # Add horizontal line at 0% for reference (important for negative values)
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
    
    # Adjust y-axis limits to show all data with some padding
    y_min, y_max = ax.get_ylim()
    y_range = y_max - y_min
    ax.set_ylim(y_min - y_range * 0.05, y_max + y_range * 0.05)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Barplot saved to {save_path}")
    
    return fig


def create_combined_analysis_plots(
    analysis_results: pd.DataFrame,
    save_plots: bool = True,
    output_dir: str = "analysis_plots",
    show_plots: bool = True
) -> Dict[str, plt.Figure]:
    """
    Create both requested plots from analysis results and optionally save them.
    
    Args:
        analysis_results: DataFrame from analyze_multiple_scenarios function
        save_plots: Whether to save the plots to files
        output_dir: Directory to save plots
        show_plots: Whether to display the plots
    
    Returns:
        Dictionary containing both figure objects
    """
    import os
    
    if save_plots:
        os.makedirs(output_dir, exist_ok=True)
    
    print("🎨 Creating Analysis Plots...")
    print("="*50)
    
    # Create scatterplot
    print("📊 Generating scatterplot: AVL Tokens vs USD Rewards...")
    scatter_save_path = f"{output_dir}/avl_tokens_vs_usd_rewards_scatter.png" if save_plots else None
    fig1 = plot_avl_tokens_vs_usd_rewards_scatter(
        analysis_results,
        save_path=scatter_save_path
    )
    
    # Create barplot  
    print("📊 Generating barplot: Return Ratios by Portfolio and Scenario...")
    bar_save_path = f"{output_dir}/return_ratio_grouped_barplot.png" if save_plots else None
    fig2 = plot_return_ratio_grouped_barplot(
        analysis_results,
        save_path=bar_save_path
    )
    
    if show_plots:
        plt.show()
    
    print(f"\n✅ Analysis plots completed!")
    if save_plots:
        print(f"📁 Plots saved to '{output_dir}' directory")
    
    return {
        'scatterplot': fig1,
        'barplot': fig2
    }


# Integration function for notebook usage
def generate_comparison_plots_from_notebook_data(
    scenarios: Dict[str, pd.DataFrame],
    allocations: Dict[str, Dict[str, float]],
    initial_deposit: float = 100,
    save_plots: bool = True,
    show_plots: bool = True
) -> Dict[str, plt.Figure]:
    """
    Complete workflow: analyze scenarios and generate comparison plots.
    
    This function integrates with the existing notebook functions to:
    1. Analyze multiple scenarios using analyze_multiple_scenarios
    2. Generate the two requested comparison plots
    
    Args:
        scenarios: Dictionary mapping scenario names to simulation DataFrames
        allocations: Dictionary mapping allocation names to asset allocation dictionaries
        initial_deposit: Initial deposit amount in USD
        save_plots: Whether to save plots
        show_plots: Whether to display plots
    
    Returns:
        Dictionary containing figure objects
    """
    # Import the analysis function from the notebook (assuming it's available)
    # You'll need to run the notebook cells first or import these functions
    
    print("🔍 Analyzing multiple scenarios...")
    
    # Note: You'll need to have the analyze_multiple_scenarios function available
    # This would typically be done by running the notebook cells first
    try:
        from notebooks.price_dynamics_analysis import analyze_multiple_scenarios
        analysis_results = analyze_multiple_scenarios(scenarios, allocations, initial_deposit)
    except ImportError:
        print("⚠️  Note: Please ensure analyze_multiple_scenarios function is available")
        print("   Run the notebook cells first or define the function in your environment")
        return None
    
    # Generate plots
    return create_combined_analysis_plots(
        analysis_results,
        save_plots=save_plots,
        show_plots=show_plots
    ) 