"""
Enhanced visualization functions for comparing multiple simulation scenarios
in the Avail Fusion simulations.

This module extends the core visualization capabilities to support overlaying
multiple scenarios on the same plots for direct comparison.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from typing import Dict, List, Optional, Union, Any, Tuple

def plot_token_prices_comparison(scenarios: Dict[str, pd.DataFrame], figsize=(12, 6)):
    """
    Plot token price comparison across multiple scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    """
    plt.figure(figsize=figsize)
    
    for scenario_name, df in scenarios.items():
        timesteps = df['timestep'].tolist()
        avl_prices = []
        
        # Extract token prices
        for _, row in df.iterrows():
            # Get first agent to extract AVL price
            agents = row['agents']
            first_agent = next(iter(agents.values()))
            avl_prices.append(first_agent.assets['AVL'].price)
        
        # Plot token price for this scenario
        plt.plot(timesteps, avl_prices, label=scenario_name)
    
    plt.title('AVL Token Price Comparison')
    plt.xlabel('Day')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_security_comparison(scenarios: Dict[str, pd.DataFrame], figsize=(12, 6)):
    """
    Plot total security (TVL) comparison across multiple scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    """
    plt.figure(figsize=figsize)
    
    for scenario_name, df in scenarios.items():
        plt.plot(df['timestep'], df['total_security'], label=scenario_name)
    
    plt.title('Total Security (TVL) Comparison')
    plt.xlabel('Day')
    plt.ylabel('Total Security (USD)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_yields_comparison(scenarios: Dict[str, pd.DataFrame], figsize=(16, 10)):
    """
    Plot yield comparison for each agent type across multiple scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    """
    # Create a 2x2 grid of subplots
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()
    
    # Agent types to analyze
    agent_types = ['avl_maxi', 'eth_maxi', 'btc_maxi']
    
    # For each agent type (first 3 subplots)
    for i, agent_type in enumerate(agent_types):
        ax = axes[i]
        
        for scenario_name, df in scenarios.items():
            timesteps = df['timestep'].tolist()
            yields = []
            
            # Extract yields for this agent across timesteps
            for _, row in df.iterrows():
                yield_pcts = row['yield_pcts']
                if agent_type in yield_pcts:
                    yields.append(yield_pcts[agent_type])
                else:
                    yields.append(0)
            
            # Plot this agent's yields for this scenario
            ax.plot(timesteps, yields, label=scenario_name)
        
        ax.set_title(f"{agent_type.replace('_', ' ').title()} Yields")
        ax.set_xlabel("Day")
        ax.set_ylabel("Yield (%)")
        ax.grid(True)
        ax.legend()
    
    # Fourth subplot: Average yield across all agents
    ax = axes[3]
    
    for scenario_name, df in scenarios.items():
        ax.plot(df['timestep'], df['avg_yield'], label=scenario_name)
    
    ax.set_title('Average Yield (All Agents)')
    ax.set_xlabel('Day')
    ax.set_ylabel('Yield (%)')
    ax.grid(True)
    ax.legend()
    
    plt.tight_layout()
    plt.show()
    
    # Plot compounding yields if available
    has_compounding = any('compounding_yield_pcts' in df.columns for df in scenarios.values())
    
    if has_compounding:
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        axes = axes.flatten()
        
        # For each agent type (first 3 subplots)
        for i, agent_type in enumerate(agent_types):
            ax = axes[i]
            
            for scenario_name, df in scenarios.items():
                timesteps = df['timestep'].tolist()
                comp_yields = []
                
                # Extract compounding yields if available
                for _, row in df.iterrows():
                    if 'compounding_yield_pcts' in row and row['compounding_yield_pcts'] and agent_type in row['compounding_yield_pcts']:
                        comp_yields.append(row['compounding_yield_pcts'][agent_type])
                    else:
                        comp_yields.append(0)
                
                if any(y > 0 for y in comp_yields):  # Only plot if there are actual values
                    ax.plot(timesteps, comp_yields, label=f"{scenario_name} (Compounding)")
            
            ax.set_title(f"{agent_type.replace('_', ' ').title()} Compounding Yields")
            ax.set_xlabel("Day")
            ax.set_ylabel("Yield (%)")
            ax.grid(True)
            ax.legend()
        
        # Fourth subplot: Average compounding yield across all agents
        ax = axes[3]
        
        for scenario_name, df in scenarios.items():
            if 'compounding_avg_yield' in df.columns:
                ax.plot(df['timestep'], df['compounding_avg_yield'], label=scenario_name)
        
        ax.set_title('Average Compounding Yield (All Agents)')
        ax.set_xlabel('Day')
        ax.set_ylabel('Yield (%)')
        ax.grid(True)
        ax.legend()
        
        plt.tight_layout()
        plt.show()


def plot_staking_inflation_comparison(scenarios: Dict[str, pd.DataFrame], figsize=(12, 6)):
    """
    Plot staking ratio and inflation rate comparison across multiple scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Plot staking ratios
    for scenario_name, df in scenarios.items():
        ax1.plot(df['timestep'], df['staking_ratio_all'], label=scenario_name)
    
    ax1.set_title('Staking Ratio Comparison')
    ax1.set_xlabel('Day')
    ax1.set_ylabel('Staking Ratio')
    ax1.legend()
    ax1.grid(True)
    
    # Plot inflation rates
    for scenario_name, df in scenarios.items():
        ax2.plot(df['timestep'], df['inflation_rate'], label=scenario_name)
    
    ax2.set_title('Inflation Rate Comparison')
    ax2.set_xlabel('Day')
    ax2.set_ylabel('Inflation Rate')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()


def plot_tvl_asset_distribution(scenarios: Dict[str, pd.DataFrame], figsize=(14, 10)):
    """
    Plot TVL asset distribution for each scenario.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    """
    num_scenarios = len(scenarios)
    fig, axes = plt.subplots(num_scenarios, 1, figsize=figsize)
    
    # Handle single scenario case
    if num_scenarios == 1:
        axes = [axes]
    
    for i, (scenario_name, df) in enumerate(scenarios.items()):
        ax = axes[i]
        timesteps = df['timestep'].tolist()
        
        # Extract TVL for each asset
        asset_tvl = {'AVL': [], 'ETH': [], 'BTC': []}
        
        for _, row in df.iterrows():
            tvl = row['tvl']
            for asset in asset_tvl.keys():
                asset_tvl[asset].append(tvl.get(asset, 0))
        
        # Plot stacked area chart
        ax.stackplot(timesteps, 
                    asset_tvl['AVL'], 
                    asset_tvl['ETH'], 
                    asset_tvl['BTC'],
                    labels=['AVL', 'ETH', 'BTC'],
                    alpha=0.8)
        
        ax.set_title(f'Asset TVL Breakdown - {scenario_name}')
        ax.set_xlabel('Day')
        ax.set_ylabel('TVL (USD)')
        ax.legend(loc='upper left')
        ax.grid(True)
    
    plt.tight_layout()
    plt.show()


def plot_asset_tvl_comparison(scenarios: Dict[str, pd.DataFrame], asset: str = 'AVL', figsize=(12, 6)):
    """
    Plot TVL comparison for a specific asset across scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        asset: Asset to compare ('AVL', 'ETH', or 'BTC')
        figsize: Figure size for the plot
    """
    plt.figure(figsize=figsize)
    
    for scenario_name, df in scenarios.items():
        timesteps = df['timestep'].tolist()
        asset_tvl_values = []
        
        for _, row in df.iterrows():
            tvl = row['tvl']
            asset_tvl_values.append(tvl.get(asset, 0))
        
        plt.plot(timesteps, asset_tvl_values, label=scenario_name)
    
    plt.title(f'{asset} TVL Comparison Across Scenarios')
    plt.xlabel('Day')
    plt.ylabel('TVL (USD)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_rewards_comparison(scenarios: Dict[str, pd.DataFrame], figsize=(12, 10)):
    """
    Plot accumulated rewards comparison across scenarios for each agent type,
    with both token amount and USD value.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    """
    # Create figure with 6 subplots (2 rows, 3 columns)
    fig, axes = plt.subplots(2, 3, figsize=figsize, sharex=True)
    agent_types = ['avl_maxi', 'eth_maxi', 'btc_maxi']
    
    # First row: AVL token accumulated rewards
    for i, agent_type in enumerate(agent_types):
        ax = axes[0, i]
        
        for scenario_name, df in scenarios.items():
            timesteps = df['timestep'].tolist()
            rewards = []
            
            # Extract rewards for this agent across timesteps
            for _, row in df.iterrows():
                agents = row['agents']
                if agent_type in agents:
                    rewards.append(agents[agent_type].accu_rewards_avl)
                else:
                    rewards.append(0)
            
            # Plot this agent's rewards for this scenario
            ax.plot(timesteps, rewards, label=scenario_name)
        
        ax.set_title(f"{agent_type.replace('_', ' ').title()} Rewards (AVL)")
        ax.set_xlabel("Day")
        if i == 0:
            ax.set_ylabel("Accumulated AVL Rewards")
        ax.grid(True)
    
    # Second row: USD value of accumulated rewards
    for i, agent_type in enumerate(agent_types):
        ax = axes[1, i]
        
        for scenario_name, df in scenarios.items():
            timesteps = df['timestep'].tolist()
            rewards_usd = []
            
            # Extract rewards and multiply by AVL price for this agent across timesteps
            for _, row in df.iterrows():
                agents = row['agents']
                if agent_type in agents:
                    # Get accumulated rewards
                    accu_rewards = agents[agent_type].accu_rewards_avl
                    # Get AVL price
                    avl_price = agents[agent_type].assets['AVL'].price
                    # Calculate USD value
                    rewards_usd.append(accu_rewards * avl_price)
                else:
                    rewards_usd.append(0)
            
            # Plot this agent's rewards USD value for this scenario
            ax.plot(timesteps, rewards_usd, label=scenario_name)
        
        ax.set_title(f"{agent_type.replace('_', ' ').title()} Rewards (USD)")
        ax.set_xlabel("Day")
        if i == 0:
            ax.set_ylabel("USD Value of Rewards")
        ax.grid(True)
    
    # Add a legend to the rightmost subplot in each row
    axes[0, -1].legend(loc='upper left', bbox_to_anchor=(1.05, 1))
    
    plt.tight_layout()
    #plt.show()
    
    return fig


def plot_comparison_dashboard(scenarios: Dict[str, pd.DataFrame], figsize=(16, 16)):
    """
    Create a comprehensive dashboard of key metrics for scenario comparison.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    """
    # Create a 4x2 grid of subplots for the dashboard (updated from 3x2)
    fig = plt.figure(figsize=figsize)
    
    # 1. Total Security (TVL)
    ax1 = plt.subplot(4, 2, 1)
    #linestyles = [ 'dotted', 'dashed', 'dashdot', 'solid']
    for i, (scenario_name, df) in enumerate(scenarios.items()):
        ax1.plot(df['timestep'], df['total_security'], label=scenario_name)
    ax1.set_title('Total Security (TVL)')
    ax1.set_xlabel('Day')
    ax1.set_ylabel('USD')
    ax1.legend()
    ax1.grid(True)
    
    # 2. Average Yield
    ax2 = plt.subplot(4, 2, 2)
    for scenario_name, df in scenarios.items():
        ax2.plot(df['timestep'], df['avg_yield'], label=scenario_name)
    ax2.set_title('Average Yield')
    ax2.set_xlabel('Day')
    ax2.set_ylabel('Yield (%)')
    ax2.legend()
    ax2.grid(True)
    
    # 3. Overall Staking Ratio
    ax3 = plt.subplot(4, 2, 3)
    for scenario_name, df in scenarios.items():
        ax3.plot(df['timestep'], df['staking_ratio_all'], label=scenario_name)
    ax3.set_title('Overall Staking Ratio')
    ax3.set_xlabel('Day')
    ax3.set_ylabel('Ratio')
    ax3.legend()
    ax3.grid(True)
    
    # 4. AVL Staking Ratio to Fusion
    ax4 = plt.subplot(4, 2, 4)
    for scenario_name, df in scenarios.items():
        # Extract AVL staking ratio from staking_ratio_fusion dictionary
        avl_staking_ratios = []
        for _, row in df.iterrows():
            staking_ratio_fusion = row['staking_ratio_fusion']
            avl_staking_ratios.append(staking_ratio_fusion.get('AVL', 0))
        
        ax4.plot(df['timestep'], avl_staking_ratios, label=scenario_name)
    ax4.set_title('AVL Staking Ratio to Fusion')
    ax4.set_xlabel('Day')
    ax4.set_ylabel('Ratio')
    ax4.legend()
    ax4.grid(True)
    
    # 5. Inflation Rate
    ax5 = plt.subplot(4, 2, 5)
    for scenario_name, df in scenarios.items():
        ax5.plot(df['timestep'], df['inflation_rate'], label=scenario_name)
    ax5.set_title('Inflation Rate')
    ax5.set_xlabel('Day')
    ax5.set_ylabel('Rate')
    ax5.legend()
    ax5.grid(True)
    
    # 6. AVL TVL
    ax6 = plt.subplot(4, 2, 6)
    for scenario_name, df in scenarios.items():
        avl_tvl = []
        for _, row in df.iterrows():
            tvl = row['tvl']
            avl_tvl.append(tvl.get('AVL', 0))
        ax6.plot(df['timestep'], avl_tvl, label=scenario_name)
    ax6.set_title('AVL TVL')
    ax6.set_xlabel('Day')
    ax6.set_ylabel('USD')
    ax6.legend()
    ax6.grid(True)
    
    # 7. ETH TVL
    ax7 = plt.subplot(4, 2, 7)
    for scenario_name, df in scenarios.items():
        eth_tvl = []
        for _, row in df.iterrows():
            tvl = row['tvl']
            eth_tvl.append(tvl.get('ETH', 0))
        ax7.plot(df['timestep'], eth_tvl, label=scenario_name)
    ax7.set_title('ETH TVL')
    ax7.set_xlabel('Day')
    ax7.set_ylabel('USD')
    ax7.legend()
    ax7.grid(True)
    
    # 8. BTC TVL (if available)
    ax8 = plt.subplot(4, 2, 8)
    for scenario_name, df in scenarios.items():
        btc_tvl = []
        for _, row in df.iterrows():
            tvl = row['tvl']
            btc_tvl.append(tvl.get('BTC', 0))
        ax8.plot(df['timestep'], btc_tvl, label=scenario_name)
    ax8.set_title('BTC TVL')
    ax8.set_xlabel('Day')
    ax8.set_ylabel('USD')
    ax8.legend()
    ax8.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    return fig


def plot_avl_staking_ratio_comparison(scenarios: Dict[str, pd.DataFrame], figsize=(12, 6)):
    """
    Plot AVL staking ratio to Fusion comparison across multiple scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    
    Returns:
        The matplotlib figure object
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Plot overall staking ratios
    for scenario_name, df in scenarios.items():
        ax1.plot(df['timestep'], df['staking_ratio_all'], label=f"{scenario_name} (All)")
    
    ax1.set_title('Overall Staking Ratio')
    ax1.set_xlabel('Day')
    ax1.set_ylabel('Staking Ratio')
    ax1.legend()
    ax1.grid(True)
    
    # Plot AVL staking ratio to Fusion
    for scenario_name, df in scenarios.items():
        # Extract AVL staking ratio from staking_ratio_fusion dictionary
        avl_staking_ratios = []
        for _, row in df.iterrows():
            staking_ratio_fusion = row['staking_ratio_fusion']
            avl_staking_ratios.append(staking_ratio_fusion.get('AVL', 0))
        
        ax2.plot(df['timestep'], avl_staking_ratios, label=scenario_name)
    
    ax2.set_title('AVL Staking Ratio to Fusion')
    ax2.set_xlabel('Day')
    ax2.set_ylabel('Staking Ratio')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    return fig


def plot_asset_staking_ratio_comparison(scenarios: Dict[str, pd.DataFrame], asset='AVL', figsize=(12, 6)):
    """
    Plot staking ratio comparison for a specific asset across multiple scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        asset: Asset to compare ('AVL', 'ETH', or 'BTC')
        figsize: Figure size for the plot
    
    Returns:
        The matplotlib figure object
    """
    plt.figure(figsize=figsize)
    
    for scenario_name, df in scenarios.items():
        # Extract asset-specific staking ratio from staking_ratio_fusion dictionary
        asset_staking_ratios = []
        for _, row in df.iterrows():
            staking_ratio_fusion = row['staking_ratio_fusion']
            asset_staking_ratios.append(staking_ratio_fusion.get(asset, 0))
        
        plt.plot(df['timestep'], asset_staking_ratios, label=scenario_name)
    
    plt.title(f'{asset} Staking Ratio to Fusion')
    plt.xlabel('Day')
    plt.ylabel('Staking Ratio')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    return plt.gcf()


def plot_staked_token_balances_comparison(scenarios: Dict[str, pd.DataFrame], assets: List[str] = None, figsize=(18, 10)):
    """
    Plot staked token balances comparison across scenarios with separate subplot for each asset.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        assets: Optional list of specific assets to compare. If None, all assets will be plotted.
        figsize: Figure size for the plot
    
    Returns:
        Matplotlib figure object
    """
    # Check if staked_token_balances exists in the data
    first_df = next(iter(scenarios.values()))
    if 'staked_token_balances' not in first_df.columns:
        print("Error: 'staked_token_balances' not found in the data.")
        print("This feature requires running a simulation with the updated model that tracks token balances.")
        print("Please update your simulation code and run it again, or use other visualization functions.")
        return None
    
    # Find the first non-empty entry
    first_entry = {}
    for _, row in first_df.iterrows():
        if 'staked_token_balances' in row and row['staked_token_balances']:
            first_entry = row['staked_token_balances']
            break
    
    # If we couldn't find any valid data, show an error
    if not first_entry:
        print("Error: No valid 'staked_token_balances' data found.")
        return None
        
    all_assets = list(first_entry.keys())
    
    # If assets are specified, use those; otherwise use all assets
    assets_to_plot = assets if assets else all_assets
    
    # Filter out any requested assets that don't exist in the data
    assets_to_plot = [asset for asset in assets_to_plot if asset in all_assets]
    
    if not assets_to_plot:
        print(f"Error: None of the requested assets {assets} exist in the data.")
        print(f"Available assets: {all_assets}")
        return None
    
    # Create a figure with a subplot for each asset
    fig, axes = plt.subplots(len(assets_to_plot), 1, figsize=figsize, sharex=True)
    
    # Handle single asset case
    if len(assets_to_plot) == 1:
        axes = [axes]
    
    # Plot each asset in its own subplot
    for i, asset_name in enumerate(assets_to_plot):
        ax = axes[i]
        
        for scenario_name, df in scenarios.items():
            timesteps = df['timestep'].tolist()
            
            # Extract staked token balances for this asset
            balances = []
            for _, row in df.iterrows():
                token_balances = row.get('staked_token_balances', {})
                if token_balances and asset_name in token_balances:
                    balances.append(token_balances[asset_name])
                else:
                    balances.append(0)
            
            # Plot this asset's balances for this scenario
            ax.plot(timesteps, balances, label=scenario_name)
        
        # Set titles and labels
        ax.set_title(f'{asset_name} Staked Token Balance')
        if i == len(assets_to_plot) - 1:  # Only show x-label on bottom subplot
            ax.set_xlabel('Day')
        ax.set_ylabel('Token Amount')
        ax.legend()
        ax.grid(True)
    
    #plt.tight_layout()
    #plt.show()
    
    return fig


def plot_staked_token_balances_dashboard(scenarios: Dict[str, pd.DataFrame], figsize=(18, 12)):
    """
    Create a dashboard view of staked token balances with both the raw balances
    and percentage of total supply for each asset.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        figsize: Figure size for the plot
    
    Returns:
        Matplotlib figure object
    """
    # Check if staked_token_balances exists in the data
    first_df = next(iter(scenarios.values()))
    if 'staked_token_balances' not in first_df.columns:
        print("Error: 'staked_token_balances' not found in the data.")
        print("This feature requires running a simulation with the updated model that tracks token balances.")
        print("Please update your simulation code and run it again, or use other visualization functions.")
        return None
    
    # Find the first non-empty entry
    first_entry = {}
    for _, row in first_df.iterrows():
        if 'staked_token_balances' in row and row['staked_token_balances']:
            first_entry = row['staked_token_balances']
            break
    
    # If we couldn't find any valid data, show an error
    if not first_entry:
        print("Error: No valid 'staked_token_balances' data found.")
        return None
        
    all_assets = list(first_entry.keys())
    
    if not all_assets:
        print("Error: No assets found in the staked_token_balances data.")
        return None
    
    # Create a figure with 2 columns (raw balances and % of total)
    fig, axes = plt.subplots(len(all_assets), 2, figsize=figsize, sharex='col')
    
    # Handle single asset case
    if len(all_assets) == 1:
        axes = axes.reshape(1, 2)
    
    # Get total supply for AVL from constants - assume it's the same across scenarios
    total_avl_supply = 10_000_000_000  # Default fallback
    
    # Try to get the actual total supply from the first scenario
    if 'constants' in first_df.columns:
        for _, row in first_df.iterrows():
            if isinstance(row.get('constants'), dict) and 'total_supply' in row['constants']:
                total_avl_supply = row['constants']['total_supply']
                break
    
    # Plot each asset in its own row
    for i, asset_name in enumerate(all_assets):
        # Raw balances subplot (left column)
        ax1 = axes[i, 0]
        
        for scenario_name, df in scenarios.items():
            timesteps = df['timestep'].tolist()
            
            # Extract staked token balances for this asset
            balances = []
            for _, row in df.iterrows():
                token_balances = row.get('staked_token_balances', {})
                if token_balances and asset_name in token_balances:
                    balances.append(token_balances[asset_name])
                else:
                    balances.append(0)
            
            # Plot this asset's balances for this scenario
            ax1.plot(timesteps, balances, label=scenario_name)
        
        # Set titles and labels for raw balances
        ax1.set_title(f'{asset_name} Staked Token Balance')
        if i == len(all_assets) - 1:  # Only show x-label on bottom row
            ax1.set_xlabel('Day')
        ax1.set_ylabel('Token Amount')
        ax1.legend()
        ax1.grid(True)
        
        # Percentage of total (right column) - only for AVL
        ax2 = axes[i, 1]
        
        for scenario_name, df in scenarios.items():
            timesteps = df['timestep'].tolist()
            
            # Extract staked token balances for this asset and convert to percentage
            percentages = []
            for _, row in df.iterrows():
                token_balances = row.get('staked_token_balances', {})
                if token_balances and asset_name in token_balances:
                    # For AVL, calculate as percentage of total supply
                    if asset_name == 'AVL':
                        percentages.append(token_balances[asset_name] / total_avl_supply * 100)
                    else:
                        # For other assets, just show the raw balance
                        percentages.append(token_balances[asset_name])
                else:
                    percentages.append(0)
            
            # Plot this asset's percentages for this scenario
            ax2.plot(timesteps, percentages, label=scenario_name)
        
        # Set titles and labels for percentages
        if asset_name == 'AVL':
            ax2.set_title(f'{asset_name} Staked (% of Total Supply)')
            ax2.set_ylabel('% of Total Supply')
        else:
            ax2.set_title(f'{asset_name} Staked Token Balance')
            ax2.set_ylabel('Token Amount')
            
        if i == len(all_assets) - 1:  # Only show x-label on bottom row
            ax2.set_xlabel('Day')
        ax2.legend()
        ax2.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    return fig 