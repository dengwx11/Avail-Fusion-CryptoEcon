#!/usr/bin/env python3
"""
Standalone script to generate the two comparison plots requested:
1. Scatterplot of AVL tokens vs USD rewards (portfolio types as markers, scenarios as colors)
2. Grouped barplot of return ratios (portfolio types and scenarios)

This script works with the output of analyze_multiple_scenarios from the notebook.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the plotting functions
from visualizations.notebook_plots import (
    plot_avl_tokens_vs_usd_rewards_scatter,
    plot_return_ratio_grouped_barplot,
    create_combined_analysis_plots
)

# Copy the notebook analysis functions here for standalone use
import pandas as pd
import numpy as np

def analyze_user_portfolio(df, allocations, initial_deposit=100):
    """
    Analyze how a user with specified allocations would perform based on simulation results.
    Only uses the last substep for each timestep in the analysis.
    
    Args:
        df: DataFrame with simulation results including timestep and substep
        allocations: Dictionary mapping allocation names to asset allocation dictionaries
        initial_deposit: Initial deposit amount in USD
        
    Returns:
        DataFrame with performance metrics for each allocation
    """
    # Filter to get only the last substep for each timestep
    last_substeps = df.groupby('timestep')['substep'].max().reset_index()
    filtered_df = pd.merge(df, last_substeps, on=['timestep', 'substep'])
    
    # Sort by timestep to ensure chronological order
    filtered_df = filtered_df.sort_values('timestep')
    
    results = []
    
    # Get data for day 1 and day 365 (or the last available day)
    day1 = filtered_df[filtered_df['timestep'] == 1].iloc[0] if 1 in filtered_df['timestep'].values else filtered_df.iloc[0]
    last_day = filtered_df[filtered_df['timestep'] == 365].iloc[0] if 365 in filtered_df['timestep'].values else filtered_df.iloc[-1]
    
    # Get prices on day 1
    day1_prices = {
        'AVL': day1['agents']['avl_maxi'].assets['AVL'].price,
        'ETH': day1['agents']['eth_maxi'].assets['ETH'].price,
        'BTC': day1['agents']['btc_maxi'].assets['BTC'].price if 'BTC' in day1['agents']['btc_maxi'].assets else 0
    }
    
    # Get prices on last day
    last_day_prices = {
        'AVL': last_day['agents']['avl_maxi'].assets['AVL'].price,
        'ETH': last_day['agents']['eth_maxi'].assets['ETH'].price,
        'BTC': last_day['agents']['btc_maxi'].assets['BTC'].price if 'BTC' in last_day['agents']['btc_maxi'].assets else 0
    }
    
    # Process each allocation strategy
    for allocation_name, allocation in allocations.items():
        # Calculate initial token amounts
        initial_tokens = {}
        for asset, alloc_pct in allocation.items():
            if day1_prices[asset] > 0:
                initial_tokens[asset] = (initial_deposit * alloc_pct) / day1_prices[asset]
            else:
                initial_tokens[asset] = 0
        
        # Track rewards and token balances over time
        avl_rewards = 0
        token_balances = initial_tokens.copy()
        day_counter = 0  # To track actual days (some timesteps might be missing)
        
        # Process each timestep to track compounding
        for _, row in filtered_df.iterrows():
            timestep = row['timestep']
            if timestep <= 1:
                continue  # Skip initial timestep
            
            day_counter += 1
            
            # Get yield percentages for this timestep
            yields = {}
            for asset in allocation.keys():
                agent_key = f"{asset.lower()}_maxi"
                if agent_key in row['yield_pcts']:
                    yields[asset] = row['yield_pcts'][agent_key]/100
                else:
                    yields[asset] = 0
            
            # Calculate daily rewards in AVL tokens
            for asset, balance in token_balances.items():
                agent_key = f"{asset.lower()}_maxi"
                # Skip if no data for this asset
                if agent_key not in row['agents']:
                    continue
                    
                # Get price for this asset and AVL
                asset_price = row['agents'][agent_key].assets[asset].price
                avl_price = row['agents']['avl_maxi'].assets['AVL'].price
                
                # Calculate daily yield in USD, then convert to AVL
                # Using actual daily yield (annual yield / 365)
                daily_yield_usd = (balance * asset_price * yields[asset]) / 365
                daily_yield_avl = daily_yield_usd / avl_price if avl_price > 0 else 0
                
                # Accumulate AVL rewards
                avl_rewards += daily_yield_avl
            
            # Reinvest rewards into AVL tokens
            token_balances['AVL'] += avl_rewards
            avl_rewards = 0  # Reset after reinvesting
        
        # Calculate final values
        final_value_usd = sum(token_balances[asset] * last_day_prices[asset] for asset in token_balances)
        
        # Calculate AVL rewards value in USD (final AVL balance - initial AVL balance)
        initial_avl = initial_tokens.get('AVL', 0)
        rewards_avl = token_balances['AVL'] - initial_avl
        rewards_usd = rewards_avl * last_day_prices['AVL']
        
        # Calculate initial portfolio value for accurate return ratio
        initial_value_usd = sum(initial_tokens[asset] * day1_prices[asset] for asset in initial_tokens)
        
        # Calculate average yield from the simulation data
        avg_portfolio_yield = 0
        for asset, alloc_pct in allocation.items():
            agent_key = f"{asset.lower()}_maxi"
            
            # Get all yields for this agent throughout the simulation
            asset_yields = []
            for _, r in filtered_df.iterrows():
                if agent_key in r['yield_pcts']:
                    asset_yields.append(r['yield_pcts'][agent_key])
            
            # Calculate average yield for this asset if data exists
            if asset_yields:
                avg_asset_yield = sum(asset_yields) / len(asset_yields)
                avg_portfolio_yield += avg_asset_yield * alloc_pct
        
        # Calculate return ratio (considering price appreciation and staking rewards)
        return_ratio = (rewards_usd + final_value_usd - initial_deposit) / initial_deposit 
        
        # Store results
        results.append({
            'Allocation': allocation_name,
            'Rewards (AVL)': rewards_avl,
            'Rewards (USD)': rewards_usd,
            'Avg Yield': avg_portfolio_yield,
            'Initial Value (USD)': initial_value_usd, 
            'Final Staked Value (USD)': final_value_usd,
            'Return Ratio (Rewards/Initial)': return_ratio,
        })
    
    return pd.DataFrame(results)

def analyze_multiple_scenarios(scenarios, allocations, initial_deposit=100):
    """
    Analyze user portfolios across multiple scenarios.
    
    Args:
        scenarios: Dictionary mapping scenario names to DataFrames
        allocations: Dictionary mapping allocation names to asset allocation dictionaries
        initial_deposit: Initial deposit amount in USD
        
    Returns:
        DataFrame with results for all scenarios and allocations
    """
    all_results = []
    
    for scenario_name, df in scenarios.items():
        # Analyze this scenario
        scenario_results = analyze_user_portfolio(df, allocations, initial_deposit)
        
        # Add scenario name to results
        scenario_results['Scenario'] = scenario_name
        
        # Add to combined results
        all_results.append(scenario_results)
    
    # Combine all results
    return pd.concat(all_results, ignore_index=True)

def generate_comparison_plots(
    scenarios_dict,
    allocations_dict=None,
    initial_deposit=100,
    save_plots=True,
    show_plots=True,
    output_dir="comparison_plots"
):
    """
    Generate the two requested comparison plots.
    
    Args:
        scenarios_dict: Dictionary mapping scenario names to simulation DataFrames
        allocations_dict: Dictionary of portfolio allocations (uses default if None)
        initial_deposit: Initial deposit amount in USD
        save_plots: Whether to save plots to files
        show_plots: Whether to display plots
        output_dir: Directory to save plots
    
    Returns:
        Dictionary containing the analysis results and figure objects
    """
    
    # Default allocations if not provided
    if allocations_dict is None:
        allocations_dict = {
            '10% AVL, 90% ETH': {'AVL': 0.1, 'ETH': 0.9, 'BTC': 0},
            '80% AVL, 20% BTC': {'AVL': 0.8, 'ETH': 0, 'BTC': 0.2}
        }
    
    print("🔍 Analyzing Multiple Scenarios...")
    print("="*60)
    print(f"Scenarios: {list(scenarios_dict.keys())}")
    print(f"Portfolio Types: {list(allocations_dict.keys())}")
    print(f"Initial Deposit: ${initial_deposit}")
    
    # Analyze all scenarios
    analysis_results = analyze_multiple_scenarios(
        scenarios_dict, 
        allocations_dict, 
        initial_deposit
    )
    
    print(f"\n📊 Analysis Complete! Found {len(analysis_results)} scenario-portfolio combinations")
    
    # Generate the plots
    figures = create_combined_analysis_plots(
        analysis_results,
        save_plots=save_plots,
        output_dir=output_dir,
        show_plots=show_plots
    )
    
    # Print summary
    print(f"\n📋 SUMMARY OF RESULTS:")
    print("="*60)
    for _, row in analysis_results.iterrows():
        print(f"{row['Scenario']} | {row['Allocation']}:")
        print(f"  - Rewards: {row['Rewards (AVL)']:.1f} AVL (${row['Rewards (USD)']:.1f})")
        print(f"  - Return Ratio: {row['Return Ratio (Rewards/Initial)']*100:.1f}%")
        print()
    
    return {
        'analysis_results': analysis_results,
        'figures': figures
    }

if __name__ == "__main__":
    """
    Example usage - you can modify this section for your specific scenarios
    """
    print("📈 Comparison Plot Generator")
    print("="*60)
    print("This script generates two comparison plots:")
    print("1. Scatterplot: AVL Tokens vs USD Rewards (portfolios as markers, scenarios as colors)")
    print("2. Barplot: Return Ratios by Portfolio and Scenario")
    print("\nTo use this script:")
    print("1. Define your scenarios dictionary with simulation DataFrames")
    print("2. Define your allocations dictionary (or use defaults)")
    print("3. Call generate_comparison_plots(scenarios, allocations)")
    print("\nExample:")
    print("scenarios = {'Scenario1': df1, 'Scenario2': df2}")
    print("allocations = {'10% AVL, 90% ETH': {'AVL': 0.1, 'ETH': 0.9, 'BTC': 0}}")
    print("results = generate_comparison_plots(scenarios, allocations)") 