#!/usr/bin/env python3
"""
AVL Price Volatility Impact Analysis

This script analyzes the impact of AVL price volatility on system metrics:
1. Tests price changes from -90% to +200% in 10% increments
2. Simulates price shocks on days 100, 200, and 500
3. Tracks TVL and rewards budget to identify potential panic withdrawals
"""

# Add at the beginning of your notebook to make imports work
import sys
import os

# Get the absolute path to the project root directory (one level up from notebooks)
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))

# Add the project root to Python's import path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor
from itertools import product

# Import project modules
from model.stochastic_processes import create_price_with_volatility_strike, create_price_with_multiple_volatility_strikes
from model.cold_start import policy_cold_start_staking
from config.config import TIMESTEPS, DELTA_TIME
from config.initialize_simulation import initialize_state

# Import the simulation configuration
from experiments.simulation_configuration import (
    SIM_TIMESTEPS, 
    SIM_DELTA_TIME,
    VOLATILITY_ANALYSIS,
    POOL_CONFIG,
    TVL_RESPONSE,
    VISUALIZATION,
    get_replenishment_schedule
)

# Set plot style
plt.style.use('ggplot')
sns.set_palette("viridis")

# Extract configuration parameters
PCT_CHANGES = VOLATILITY_ANALYSIS['pct_changes']
STRIKE_DAYS = VOLATILITY_ANALYSIS['strike_days']
BASE_PRICE = VOLATILITY_ANALYSIS['base_avl_price']
SIMULATION_DAYS = SIM_TIMESTEPS

def generate_price_scenarios():
    """Generate all price scenarios for testing"""
    scenarios = []
    
    # Generate scenarios for each day and percentage change
    for day in STRIKE_DAYS:
        for pct_change in PCT_CHANGES:
            # Create unique scenario ID
            scenario_id = f"day{day}_pct{int(pct_change*100)}"
            
            # Generate price series with volatility strike
            price_series = create_price_with_volatility_strike(
                timesteps=SIMULATION_DAYS,
                dt=SIM_DELTA_TIME,
                base_price=BASE_PRICE,
                strike_timestep=day,
                pct_change=pct_change
            )
            
            # Add to scenarios list
            scenarios.append({
                'id': scenario_id,
                'strike_day': day,
                'pct_change': pct_change,
                'price_series': price_series
            })
    
    return scenarios

def run_simulation(scenario):
    """
    Run a simulation with the given price scenario
    This is a simplified version that models expected system behavior
    """
    # Initialize metrics tracking
    metrics = {
        'day': [],
        'avl_price': [],
        'total_tvl': [],
        'avl_tvl': [],
        'eth_tvl': [],
        'btc_tvl': [],
        'avl_budget': [],
        'eth_budget': [],
        'btc_budget': [],
        'panic_withdrawal': []
    }
    
    # Simulation parameters
    initial_tvl = 10e6  # $10M initial TVL
    initial_avl_share = POOL_CONFIG['AVL']['initial_budget_share']
    initial_eth_share = POOL_CONFIG['ETH']['initial_budget_share']
    initial_btc_share = POOL_CONFIG['BTC']['initial_budget_share']
    initial_budget = 30e6  # 30M AVL initial budget
    btc_activation_day = POOL_CONFIG['BTC']['activation_day']
    
    # Replenishment schedule
    replenishment_schedule = get_replenishment_schedule()
    
    # Track previous TVL to detect panic withdrawals
    prev_tvl = initial_tvl
    
    for day in range(SIMULATION_DAYS + 1):
        # Get price for this day
        avl_price = scenario['price_series'][day]
        
        # Calculate price ratio compared to initial price
        price_ratio = avl_price / scenario['price_series'][0]
        
        # BTC activation occurs on BTC activation day
        btc_active = day >= btc_activation_day
        
        # TVL changes differently before and after the price shock
        if day < scenario['strike_day']:
            # Normal growth before shock
            tvl_factor = price_ratio ** TVL_RESPONSE['price_elasticity']['increase'] if price_ratio > 1 else price_ratio ** TVL_RESPONSE['price_elasticity']['decrease']
            total_tvl = initial_tvl * (1 + 0.002 * day) * tvl_factor  # Slight natural growth
            
            # Share distribution
            if btc_active:
                avl_share = 0.6
                eth_share = 0.3
                btc_share = 0.1
            else:
                avl_share = 0.7
                eth_share = 0.3
                btc_share = 0.0
                
        else:
            # After shock
            # Calculate impact based on shock magnitude
            days_since_shock = day - scenario['strike_day']
            
            if scenario['pct_change'] < TVL_RESPONSE['panic_threshold']:  # If price dropped >50%
                # Exponential TVL decay model for large drops (panic withdrawals)
                decay_rate = min(TVL_RESPONSE['panic_withdrawal_rate'], abs(scenario['pct_change']) * 0.1)
                impact_factor = (1 - decay_rate) ** days_since_shock
                
                # Extreme price drops cause compositional shifts
                if scenario['pct_change'] < -0.7:  # >70% drop
                    avl_share = max(0.2, 0.6 - days_since_shock * 0.01)  # AVL share drops
                    eth_share = min(0.7, 0.3 + days_since_shock * 0.01)  # ETH share rises
                    btc_share = 0.1 if btc_active else 0.0
                else:
                    # Less extreme shifts
                    avl_share = max(0.4, 0.6 - days_since_shock * 0.005)
                    eth_share = min(0.5, 0.3 + days_since_shock * 0.005)
                    btc_share = 0.1 if btc_active else 0.0
                    
            elif scenario['pct_change'] > 0.5:  # If price increased >50%
                # Growth model for price increases (inflows)
                growth_rate = min(0.05, scenario['pct_change'] * 0.05)  # Up to 5% daily growth
                impact_factor = (1 + growth_rate) ** min(days_since_shock, TVL_RESPONSE['growth_cap_days'])
                
                # Price increases attract more AVL staking
                avl_share = min(0.8, 0.6 + days_since_shock * 0.005)
                eth_share = max(0.1, 0.3 - days_since_shock * 0.003)
                btc_share = 0.1 if btc_active else 0.0
            else:
                # Moderate changes have less dramatic effects
                impact_factor = 1.0 + scenario['pct_change'] * 0.2
                avl_share = 0.6
                eth_share = 0.3
                btc_share = 0.1 if btc_active else 0.0
            
            # Apply the impact to TVL
            total_tvl = prev_tvl * impact_factor
            
        # Calculate component TVLs
        avl_tvl = total_tvl * avl_share
        eth_tvl = total_tvl * eth_share
        btc_tvl = total_tvl * btc_share
        
        # Rewards budget calculations
        # Budget depletes based on TVL and target yields
        avl_yield = POOL_CONFIG['AVL']['target_yield']
        eth_yield = POOL_CONFIG['ETH']['target_yield']
        btc_yield = POOL_CONFIG['BTC']['target_yield']
        
        # Daily reward consumption rate (yearly yield / 365)
        avl_daily_reward = avl_tvl * avl_yield / 365
        eth_daily_reward = eth_tvl * eth_yield / 365
        btc_daily_reward = btc_tvl * btc_yield / 365
        
        # Budget replenishment based on schedule
        avl_replenishment = 0
        eth_replenishment = 0
        btc_replenishment = 0
        
        if day in replenishment_schedule:
            replenishment = replenishment_schedule[day]
            if 'AVL' in replenishment:
                avl_replenishment = replenishment['AVL']
            if 'ETH' in replenishment:
                eth_replenishment = replenishment['ETH']
            if 'BTC' in replenishment and btc_active:
                btc_replenishment = replenishment['BTC']
        
        # Update budgets
        if day == 0:
            # Initialize budgets
            avl_budget = initial_budget * initial_avl_share
            eth_budget = initial_budget * initial_eth_share
            btc_budget = 0
        else:
            # Update budgets with consumption and replenishment
            avl_budget = metrics['avl_budget'][-1] - avl_daily_reward + avl_replenishment
            eth_budget = metrics['eth_budget'][-1] - eth_daily_reward + eth_replenishment
            btc_budget = (metrics['btc_budget'][-1] if btc_active else 0) - (btc_daily_reward if btc_active else 0) + btc_replenishment
        
        # Check for panic withdrawals
        # Panic withdrawal defined as TVL dropping more than 5% in a day due to price changes
        tvl_change_pct = (total_tvl - prev_tvl) / prev_tvl if prev_tvl > 0 else 0
        panic_withdrawal = 1 if tvl_change_pct < -0.05 and day > scenario['strike_day'] else 0
        
        # Store metrics
        metrics['day'].append(day)
        metrics['avl_price'].append(avl_price)
        metrics['total_tvl'].append(total_tvl)
        metrics['avl_tvl'].append(avl_tvl)
        metrics['eth_tvl'].append(eth_tvl)
        metrics['btc_tvl'].append(btc_tvl)
        metrics['avl_budget'].append(avl_budget)
        metrics['eth_budget'].append(eth_budget)
        metrics['btc_budget'].append(btc_budget)
        metrics['panic_withdrawal'].append(panic_withdrawal)
        
        # Update previous TVL for next iteration
        prev_tvl = total_tvl
    
    # Create DataFrame from metrics
    df = pd.DataFrame(metrics)
    
    # Add scenario information
    df['scenario_id'] = scenario['id']
    df['strike_day'] = scenario['strike_day']
    df['pct_change'] = scenario['pct_change']
    
    return df

def analyze_results(all_results):
    """Analyze simulation results and create plots"""
    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Create a Figure with subplots for each strike day
    fig, axes = plt.subplots(3, 2, figsize=(18, 16))
    fig.suptitle("Impact of AVL Price Volatility on System Metrics", fontsize=20)
    
    # Create a colormap for visualizing price changes
    colors = VISUALIZATION['color_schemes']['price_changes']
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=len(PCT_CHANGES))
    
    # Define custom normalization for color mapping
    norm = plt.Normalize(-0.9, 2.0)
    
    for i, day in enumerate(STRIKE_DAYS):
        # Filter results for this strike day
        day_results = all_results[all_results['strike_day'] == day]
        
        # Group by percentage change and get final metrics
        grouped = day_results.groupby(['pct_change', 'day']).agg({
            'total_tvl': 'mean',
            'avl_budget': 'mean',
            'panic_withdrawal': 'sum'
        }).reset_index()
        
        # Find days with panic withdrawals
        panic_days = grouped[grouped['panic_withdrawal'] > 0]
        
        # Plot TVL impact
        ax1 = axes[i, 0]
        for pct in PCT_CHANGES:
            subset = grouped[grouped['pct_change'] == pct]
            color = cmap(norm(pct))
            ax1.plot(subset['day'], subset['total_tvl'] / 1e6, color=color, 
                     label=f"{int(pct*100)}%" if i == 0 else "")
            
            # Mark the strike day
            ax1.axvline(x=day, color='black', linestyle='--', alpha=0.3)
            
        ax1.set_title(f"TVL Impact (Strike Day {day})")
        ax1.set_xlabel("Simulation Day")
        ax1.set_ylabel("Total TVL (Millions $)")
        ax1.grid(True, alpha=0.3)
        
        # Plot Budget impact
        ax2 = axes[i, 1]
        for pct in PCT_CHANGES:
            subset = grouped[grouped['pct_change'] == pct]
            color = cmap(norm(pct))
            ax2.plot(subset['day'], subset['avl_budget'] / 1e6, color=color)
            
            # Mark the strike day
            ax2.axvline(x=day, color='black', linestyle='--', alpha=0.3)
        
        ax2.set_title(f"AVL Rewards Budget (Strike Day {day})")
        ax2.set_xlabel("Simulation Day")
        ax2.set_ylabel("AVL Budget (Millions tokens)")
        ax2.grid(True, alpha=0.3)
    
    # Add a color bar for percentage changes
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), orientation='horizontal', pad=0.01, aspect=40)
    cbar.set_label("AVL Price Change %", fontsize=14)
    
    # Add legend to first plot only (to avoid duplication)
    # Format with 5 columns to save space
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=5, fontsize=10)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save the figure
    plt.savefig("results/avl_price_volatility_analysis.png", dpi=VISUALIZATION['plot_dpi'], bbox_inches='tight')
    if 'pdf' in VISUALIZATION['file_formats']:
        plt.savefig("results/avl_price_volatility_analysis.pdf", bbox_inches='tight')
    plt.close(fig)
    
    # Create a heatmap of panic withdrawal likelihood
    fig2, axes2 = plt.subplots(1, 3, figsize=(20, 6))
    fig2.suptitle("Likelihood of Panic Withdrawals by Price Change Scenario", fontsize=16)
    
    for i, day in enumerate(STRIKE_DAYS):
        # Filter results for this strike day
        day_results = all_results[all_results['strike_day'] == day]
        
        # Create a pivot table of panic withdrawal counts
        pivot = day_results.pivot_table(
            index='pct_change', 
            columns='day',
            values='panic_withdrawal',
            aggfunc='sum'
        )
        
        # Create a binary version where any panic = 1
        pivot_binary = (pivot > 0).astype(int)
        
        # Compute total panic days per scenario
        total_panic_days = pivot_binary.sum(axis=1)
        
        # Plot as a heatmap for the period after strike
        post_strike_days = 30  # Look at 30 days after strike
        
        # Make sure we have sufficient columns to avoid indexing errors
        if day + post_strike_days <= pivot.shape[1]:
            sns.heatmap(
                pivot.iloc[:, day:day+post_strike_days],
                ax=axes2[i],
                cmap=VISUALIZATION['color_schemes']['panic'],
                cbar_kws={'label': 'Panic withdrawal events'}
            )
        else:
            # If we don't have enough days after strike, adjust the range
            end_col = min(day + post_strike_days, pivot.shape[1])
            sns.heatmap(
                pivot.iloc[:, day:end_col],
                ax=axes2[i],
                cmap=VISUALIZATION['color_schemes']['panic'],
                cbar_kws={'label': 'Panic withdrawal events'}
            )
            
        axes2[i].set_title(f"Panic Withdrawals (Strike Day {day})")
        axes2[i].set_xlabel("Days after strike")
        axes2[i].set_ylabel("Price change %")
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("results/avl_panic_withdrawal_heatmap.png", dpi=VISUALIZATION['plot_dpi'], bbox_inches='tight')
    if 'pdf' in VISUALIZATION['file_formats']:
        plt.savefig("results/avl_panic_withdrawal_heatmap.pdf", bbox_inches='tight')
    
    # Create summary metrics table
    summary = pd.DataFrame(columns=[
        'strike_day',
        'pct_change',
        'final_tvl',
        'tvl_pct_change',
        'final_budget',
        'budget_consumed_pct',
        'panic_days'
    ])
    
    for day in STRIKE_DAYS:
        for pct in PCT_CHANGES:
            scenario = all_results[(all_results['strike_day'] == day) & 
                                 (all_results['pct_change'] == pct)]
            
            if not scenario.empty:
                initial_tvl = scenario[scenario['day'] == 0]['total_tvl'].values[0]
                final_tvl = scenario[scenario['day'] == SIMULATION_DAYS]['total_tvl'].values[0]
                
                initial_budget = scenario[scenario['day'] == 0]['avl_budget'].values[0]
                final_budget = scenario[scenario['day'] == SIMULATION_DAYS]['avl_budget'].values[0]
                
                panic_count = scenario['panic_withdrawal'].sum()
                
                summary = summary.append({
                    'strike_day': day,
                    'pct_change': pct,
                    'final_tvl': final_tvl,
                    'tvl_pct_change': (final_tvl - initial_tvl) / initial_tvl * 100,
                    'final_budget': final_budget,
                    'budget_consumed_pct': (initial_budget - final_budget) / initial_budget * 100 if initial_budget > 0 else 0,
                    'panic_days': panic_count
                }, ignore_index=True)
    
    # Save summary to CSV
    summary.to_csv("results/avl_volatility_summary.csv", index=False)
    
    # Create summary plots
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    
    for day in STRIKE_DAYS:
        day_summary = summary[summary['strike_day'] == day]
        ax3.plot(day_summary['pct_change'] * 100, day_summary['tvl_pct_change'], 
                 marker='o', label=f"Strike Day {day}")
        
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax3.axvline(x=0, color='black', linestyle='--', alpha=0.5)
    ax3.set_xlabel("AVL Price Change %")
    ax3.set_ylabel("Final TVL Change %")
    ax3.set_title("Final TVL Change vs. Price Shock Magnitude")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("results/avl_tvl_vs_price_shock.png", dpi=VISUALIZATION['plot_dpi'], bbox_inches='tight')
    
    return summary

def main():
    """Main execution function"""
    print(f"{'='*80}")
    print("AVL PRICE VOLATILITY IMPACT ANALYSIS")
    print(f"{'='*80}")
    
    # Create results directory
    os.makedirs("results", exist_ok=True)
    
    # Generate scenarios
    print("\n1. Generating price scenarios...")
    scenarios = generate_price_scenarios()
    print(f"   Created {len(scenarios)} price scenarios")
    
    # Run simulations
    print("\n2. Running simulations...")
    results = []
    
    # For demonstration, we'll use sequential processing
    # In practice, you could use multiprocessing
    for i, scenario in enumerate(scenarios):
        print(f"   Processing scenario {i+1}/{len(scenarios)}: {scenario['id']}")
        scenario_results = run_simulation(scenario)
        results.append(scenario_results)
    
    # Combine all results
    all_results = pd.concat(results)
    
    # Save raw results
    all_results.to_csv("results/all_simulation_results.csv", index=False)
    print("   Raw simulation results saved to results/all_simulation_results.csv")
    
    # Analyze and plot results
    print("\n3. Analyzing results and creating plots...")
    summary = analyze_results(all_results)
    
    print("\nAnalysis complete!")
    print("Results saved to the 'results' directory:")
    print("- avl_price_volatility_analysis.png/.pdf")
    print("- avl_panic_withdrawal_heatmap.png/.pdf")
    print("- avl_volatility_summary.csv")
    print("- avl_tvl_vs_price_shock.png")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 