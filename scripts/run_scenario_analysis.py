"""
Script to run scenario analysis and generate plots for the Avail Fusion economic model.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from model.simulation_runner import run_scenario_analysis, generate_scenario_report
from model.market_scenarios import MARKET_SCENARIOS

def plot_price_paths(results: dict, output_dir: str) -> None:
    """
    Plot price paths for each scenario
    
    Parameters:
    -----------
    results : dict
        Dictionary mapping scenario names to results DataFrames
    output_dir : str
        Directory to save plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn')
    
    # Plot price paths for each scenario
    for scenario, df in results.items():
        plt.figure(figsize=(12, 6))
        
        # Plot AVL price
        plt.plot(df.index, df['AVL_Price'], label='AVL', linewidth=2)
        
        # Plot ETH and BTC prices (normalized to start at 1)
        plt.plot(df.index, df['ETH_Price'] / df['ETH_Price'].iloc[0], 
                label='ETH', linewidth=2, alpha=0.7)
        plt.plot(df.index, df['BTC_Price'] / df['BTC_Price'].iloc[0], 
                label='BTC', linewidth=2, alpha=0.7)
        
        plt.title(f'Price Paths - {scenario}')
        plt.xlabel('Day')
        plt.ylabel('Price (Normalized)')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        plt.savefig(os.path.join(output_dir, f'price_paths_{scenario}.png'))
        plt.close()

def plot_rewards(results: dict, output_dir: str) -> None:
    """
    Plot rewards for each scenario
    
    Parameters:
    -----------
    results : dict
        Dictionary mapping scenario names to results DataFrames
    output_dir : str
        Directory to save plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn')
    
    # Plot rewards for each scenario
    for scenario, df in results.items():
        plt.figure(figsize=(12, 6))
        
        # Plot staking and liquidity rewards
        plt.plot(df.index, df['Staking_Rewards'].cumsum(), 
                label='Staking Rewards', linewidth=2)
        plt.plot(df.index, df['Liquidity_Rewards'].cumsum(), 
                label='Liquidity Rewards', linewidth=2)
        
        plt.title(f'Cumulative Rewards - {scenario}')
        plt.xlabel('Day')
        plt.ylabel('AVL Tokens')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        plt.savefig(os.path.join(output_dir, f'rewards_{scenario}.png'))
        plt.close()

def plot_usd_rewards(results: dict, output_dir: str) -> None:
    """
    Plot USD value of rewards for each scenario
    
    Parameters:
    -----------
    results : dict
        Dictionary mapping scenario names to results DataFrames
    output_dir : str
        Directory to save plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn')
    
    # Plot USD rewards for each scenario
    for scenario, df in results.items():
        plt.figure(figsize=(12, 6))
        
        # Plot USD value of rewards
        plt.plot(df.index, df['USD_Rewards'].cumsum(), 
                label='USD Value of Rewards', linewidth=2)
        
        plt.title(f'Cumulative USD Value of Rewards - {scenario}')
        plt.xlabel('Day')
        plt.ylabel('USD')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        plt.savefig(os.path.join(output_dir, f'usd_rewards_{scenario}.png'))
        plt.close()

def plot_scenario_comparison(results: dict, output_dir: str) -> None:
    """
    Plot comparison of key metrics across scenarios
    
    Parameters:
    -----------
    results : dict
        Dictionary mapping scenario names to results DataFrames
    output_dir : str
        Directory to save plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn')
    
    # Calculate summary statistics
    summary_stats = {}
    for scenario, df in results.items():
        summary_stats[scenario] = {
            'Total Return': df['AVL_Price'].iloc[-1] / df['AVL_Price'].iloc[0] - 1,
            'Total Rewards': df['Total_Rewards'].sum(),
            'USD Rewards': df['USD_Rewards'].sum(),
            'Max Drawdown': (df['AVL_Price'] / df['AVL_Price'].cummax() - 1).min(),
            'Volatility': df['AVL_Return'].std() * np.sqrt(252),
            'Sharpe Ratio': (df['AVL_Return'].mean() * 252) / (df['AVL_Return'].std() * np.sqrt(252))
        }
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_stats).T
    
    # Plot each metric
    for metric in summary_df.columns:
        plt.figure(figsize=(12, 6))
        
        # Sort scenarios by metric value
        sorted_scenarios = summary_df[metric].sort_values()
        
        # Create bar plot
        plt.bar(range(len(sorted_scenarios)), sorted_scenarios.values)
        plt.xticks(range(len(sorted_scenarios)), sorted_scenarios.index, rotation=45, ha='right')
        
        plt.title(f'{metric} by Scenario')
        plt.xlabel('Scenario')
        plt.ylabel(metric)
        plt.grid(True)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot
        plt.savefig(os.path.join(output_dir, f'comparison_{metric.lower().replace(" ", "_")}.png'))
        plt.close()

def main():
    """Main function to run scenario analysis and generate plots"""
    # Create output directories
    output_dir = project_root / 'output'
    plots_dir = output_dir / 'plots'
    os.makedirs(plots_dir, exist_ok=True)
    
    # Run scenario analysis
    print("Running scenario analysis...")
    results = run_scenario_analysis(
        n_periods=365,
        seed=42,
        initial_avl_supply=1_000_000_000,
        reward_rate=0.05,
        staking_ratio=0.5,
        liquidity_ratio=0.3
    )
    
    # Generate report
    print("Generating report...")
    generate_scenario_report(
        results=results,
        output_file=str(output_dir / 'scenario_analysis_report.txt')
    )
    
    # Generate plots
    print("Generating plots...")
    plot_price_paths(results, str(plots_dir / 'price_paths'))
    plot_rewards(results, str(plots_dir / 'rewards'))
    plot_usd_rewards(results, str(plots_dir / 'usd_rewards'))
    plot_scenario_comparison(results, str(plots_dir / 'comparison'))
    
    print("Analysis complete! Results saved to:", output_dir)

if __name__ == '__main__':
    main() 