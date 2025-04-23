#!/usr/bin/env python3
"""
Example Brownian Motion Simulation

This script demonstrates how to use the Brownian Motion price process
in the Avail Fusion simulation runner to model more realistic price movements
for all assets (AVL, ETH, BTC, and LENS).
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to Python's import path if it's not already there
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import simulation runner
import simulation_runner as sim
import visualizations.comparison_plots as comp_plots

def run_basic_bm_simulation():
    """Run a basic simulation with Brownian Motion price process for all assets"""
    print("Running basic simulation with Brownian Motion price process for all assets...")
    
    # Create configuration with Brownian Motion
    config = sim.SimulationConfig(
        # Basic simulation parameters
        simulation_days=365,
        
        # Initial prices
        avl_initial_price=0.1,
        eth_initial_price=1500,
        btc_initial_price=80000,
        lens_initial_price=1.0,
        
        # Use Brownian Motion price process
        price_process_type='BM',
        
        # AVL Brownian Motion parameters
        price_traj_type='convex',      # 'convex' trajectory (increasing)
        minimum_price=0.05,            # Minimum possible price
        maximum_price=0.5,             # Maximum possible price
        target_avg_price=0.2,          # Target average price
        bm_volatility=1.2,             # Higher volatility for more randomness
        
        # ETH Brownian Motion parameters
        eth_price_traj_type='convex',
        eth_minimum_price=1200,
        eth_maximum_price=2000,
        eth_target_avg_price=1600,
        eth_bm_volatility=0.8,
        
        # BTC Brownian Motion parameters
        btc_price_traj_type='convex',
        btc_minimum_price=70000,
        btc_maximum_price=100000,
        btc_target_avg_price=85000,
        btc_bm_volatility=0.6,
        
        # LENS Brownian Motion parameters
        lens_price_traj_type='none',   # Pure Brownian motion
        lens_minimum_price=0.8,
        lens_maximum_price=1.5,
        lens_target_avg_price=1.1,
        lens_bm_volatility=1.5,
        
        # Other parameters
        restaking=1.0
    )
    
    # Run simulation
    results = sim.run_simulation(config)
    
    # Plot results
    sim.plot_simulation_results(results)
    
    # Extract and plot just the asset prices for a better view of the Brownian Motion
    plot_asset_price_trajectories(results)
    
    return results

def compare_bm_trajectory_types():
    """Compare different trajectory types for Brownian Motion"""
    print("Comparing different trajectory types for Brownian Motion...")
    
    # Base configuration with common parameters
    base_config = sim.SimulationConfig(
        simulation_days=365,
        avl_initial_price=0.1,
        price_process_type='BM',
        minimum_price=0.05,
        maximum_price=0.5,
        target_avg_price=0.2,
        bm_volatility=1.0,
        
        # Use the same parameters for other assets
        eth_price_traj_type='convex',
        eth_bm_volatility=1.0,
        
        btc_price_traj_type='convex',
        btc_bm_volatility=1.0,
        
        lens_price_traj_type='convex',
        lens_bm_volatility=1.0
    )
    
    # Define comparison configurations for different trajectory types
    comparisons = [
        {'price_traj_type': 'concave'},  # Concave trajectory (decreasing)
        {'price_traj_type': 'none'}      # No trajectory (pure Brownian)
    ]
    
    # Run comparisons
    results = sim.compare_simulations(
        base_config=base_config,
        comparison_configs=comparisons,
        names=["Convex_Trajectory", "Concave_Trajectory", "Pure_Brownian"]
    )
    
    # Plot comparison results
    compare_price_trajectories(results)
    
    # Plot other comparison metrics
    comp_plots.plot_comparison_dashboard(results)
    
    return results

def multi_asset_bm_simulation():
    """
    Demo of different Brownian Motion configurations for each asset
    
    This example shows how to configure different price trajectory types
    and volatility levels for each asset.
    """
    print("Running multi-asset Brownian Motion simulation...")
    
    # Create configuration with different settings for each asset
    config = sim.SimulationConfig(
        # Basic simulation parameters
        simulation_days=365,
        
        # Initial prices
        avl_initial_price=0.1,
        eth_initial_price=1500,
        btc_initial_price=80000,
        lens_initial_price=1.0,
        
        # Use Brownian Motion price process
        price_process_type='BM',
        
        # AVL: Convex (generally increasing) with high volatility
        price_traj_type='convex',
        minimum_price=0.05,
        maximum_price=0.3,
        target_avg_price=0.15,
        bm_volatility=1.5,
        
        # ETH: Concave (generally decreasing) with medium volatility
        eth_price_traj_type='concave',
        eth_minimum_price=1000,
        eth_maximum_price=2000,
        eth_target_avg_price=1500,
        eth_bm_volatility=1.0,
        
        # BTC: No trend (pure Brownian) with low volatility
        btc_price_traj_type='none',
        btc_minimum_price=75000,
        btc_maximum_price=90000,
        btc_target_avg_price=82000,
        btc_bm_volatility=0.5,
        
        # LENS: Convex with extreme volatility
        lens_price_traj_type='convex',
        lens_minimum_price=0.5,
        lens_maximum_price=3.0,
        lens_target_avg_price=1.2,
        lens_bm_volatility=2.0,
        
        # Other parameters
        restaking=1.0,
        initial_agent_composition={'AVL': 0.25, 'ETH': 0.25, 'BTC': 0.25, 'LENS': 0.25}  # Equal allocation
    )
    
    # Run simulation
    results = sim.run_simulation(config)
    
    # Plot results
    sim.plot_simulation_results(results)
    
    # Plot all asset price trajectories
    plot_asset_price_trajectories(results)
    
    return results

def compare_eth_btc_volatility():
    """Compare volatility effects on ETH and BTC prices"""
    print("Comparing different volatility levels for ETH and BTC...")
    
    # Base configuration
    base_config = sim.SimulationConfig(
        simulation_days=365,
        price_process_type='BM',
        
        # ETH with low volatility
        eth_price_traj_type='none',
        eth_bm_volatility=0.5,
        
        # BTC with low volatility
        btc_price_traj_type='none',
        btc_bm_volatility=0.5
    )
    
    # Define comparison configurations
    comparisons = [
        # Medium volatility for both
        {
            'eth_bm_volatility': 1.0,
            'btc_bm_volatility': 1.0
        },
        # High volatility for both
        {
            'eth_bm_volatility': 2.0,
            'btc_bm_volatility': 2.0
        }
    ]
    
    # Run comparisons
    results = sim.compare_simulations(
        base_config=base_config,
        comparison_configs=comparisons,
        names=["Low_Volatility", "Medium_Volatility", "High_Volatility"]
    )
    
    # Plot comparative results
    compare_eth_btc_prices(results)
    
    return results

def market_scenario_simulation():
    """
    Simulate a realistic market scenario with correlated asset movements
    
    This example creates a market scenario where:
    - BTC has a generally bullish trend (convex)
    - ETH follows with slightly more volatility
    - AVL has high growth potential but also high volatility
    - LENS is relatively stable
    """
    print("Running market scenario simulation...")
    
    # Create configuration
    config = sim.SimulationConfig(
        # Simulation for 2 years
        simulation_days=730,
        
        # Initial prices
        avl_initial_price=0.1,
        eth_initial_price=1800,
        btc_initial_price=45000,
        lens_initial_price=1.0,
        
        # Use Brownian Motion price process
        price_process_type='BM',
        
        # AVL: High growth potential with high volatility
        price_traj_type='convex',
        minimum_price=0.05,
        maximum_price=1.0,
        target_avg_price=0.3,
        bm_volatility=1.8,
        
        # ETH: Moderate growth with medium-high volatility
        eth_price_traj_type='convex',
        eth_minimum_price=1500,
        eth_maximum_price=6000,
        eth_target_avg_price=3000,
        eth_bm_volatility=1.4,
        
        # BTC: Steady growth with medium volatility
        btc_price_traj_type='convex',
        btc_minimum_price=40000,
        btc_maximum_price=150000,
        btc_target_avg_price=80000,
        btc_bm_volatility=1.0,
        
        # LENS: Stable with low volatility
        lens_price_traj_type='none',
        lens_minimum_price=0.8,
        lens_maximum_price=1.2,
        lens_target_avg_price=1.0,
        lens_bm_volatility=0.3,
        
        # Other parameters
        restaking=1.0,
        initial_agent_composition={'AVL': 0.2, 'ETH': 0.3, 'BTC': 0.4, 'LENS': 0.1}
    )
    
    # Run simulation
    results = sim.run_simulation(config)
    
    # Plot results
    sim.plot_simulation_results(results)
    
    # Plot all asset price trajectories
    plot_asset_price_trajectories(results, normalize=True)
    
    return results

def plot_asset_price_trajectories(df, normalize=False):
    """Extract and plot price trajectories for all assets from simulation results"""
    # Extract timesteps
    timesteps = df['timestep'].tolist()
    
    # Initialize empty price lists
    avl_prices = []
    eth_prices = []
    btc_prices = []
    lens_prices = []
    
    # Extract prices for each asset
    for _, row in df.iterrows():
        # Get first agent to extract prices
        agents = row['agents']
        first_agent = next(iter(agents.values()))
        
        # Append prices
        avl_prices.append(first_agent.assets['AVL'].price)
        eth_prices.append(first_agent.assets['ETH'].price)
        btc_prices.append(first_agent.assets['BTC'].price)
        
        # Check if LENS exists in the assets
        if 'LENS' in first_agent.assets:
            lens_prices.append(first_agent.assets['LENS'].price)
    
    # Normalize prices if requested (to show relative changes)
    if normalize:
        avl_prices = [p / avl_prices[0] for p in avl_prices]
        eth_prices = [p / eth_prices[0] for p in eth_prices]
        btc_prices = [p / btc_prices[0] for p in btc_prices]
        if lens_prices:
            lens_prices = [p / lens_prices[0] for p in lens_prices]
        
        ylabel = 'Relative Price (normalized to initial = 1.0)'
        title = 'Normalized Asset Price Trajectories (Brownian Motion)'
    else:
        ylabel = 'Price (USD)'
        title = 'Asset Price Trajectories (Brownian Motion)'
    
    # Create plot with subplots
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    
    # AVL plot
    axs[0, 0].plot(timesteps, avl_prices, linewidth=2, color='blue')
    axs[0, 0].set_title('AVL Price')
    axs[0, 0].set_xlabel('Day')
    axs[0, 0].set_ylabel(ylabel)
    axs[0, 0].grid(True, alpha=0.3)
    
    # ETH plot
    axs[0, 1].plot(timesteps, eth_prices, linewidth=2, color='green')
    axs[0, 1].set_title('ETH Price')
    axs[0, 1].set_xlabel('Day')
    axs[0, 1].set_ylabel(ylabel)
    axs[0, 1].grid(True, alpha=0.3)
    
    # BTC plot
    axs[1, 0].plot(timesteps, btc_prices, linewidth=2, color='orange')
    axs[1, 0].set_title('BTC Price')
    axs[1, 0].set_xlabel('Day')
    axs[1, 0].set_ylabel(ylabel)
    axs[1, 0].grid(True, alpha=0.3)
    
    # LENS plot (if available)
    if lens_prices:
        axs[1, 1].plot(timesteps, lens_prices, linewidth=2, color='purple')
        axs[1, 1].set_title('LENS Price')
        axs[1, 1].set_xlabel('Day')
        axs[1, 1].set_ylabel(ylabel)
        axs[1, 1].grid(True, alpha=0.3)
    else:
        axs[1, 1].set_visible(False)
    
    # Add overall title
    fig.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
    
    # Create a combined plot on a single axis
    plt.figure(figsize=(14, 8))
    
    # Plot all assets on the same chart
    plt.plot(timesteps, avl_prices, linewidth=2, label='AVL')
    plt.plot(timesteps, eth_prices, linewidth=2, label='ETH')
    plt.plot(timesteps, btc_prices, linewidth=2, label='BTC')
    if lens_prices:
        plt.plot(timesteps, lens_prices, linewidth=2, label='LENS')
    
    plt.title(f'Combined {title}')
    plt.xlabel('Day')
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def compare_price_trajectories(results_dict):
    """Compare price trajectories from multiple simulations"""
    plt.figure(figsize=(14, 8))
    
    for name, df in results_dict.items():
        # Extract token prices
        timesteps = df['timestep'].tolist()
        avl_prices = []
        
        for _, row in df.iterrows():
            # Get first agent to extract AVL price
            agents = row['agents']
            first_agent = next(iter(agents.values()))
            avl_prices.append(first_agent.assets['AVL'].price)
        
        # Plot token price for this scenario
        plt.plot(timesteps, avl_prices, linewidth=2, label=name)
    
    plt.title('Comparison of AVL Token Price Trajectories')
    plt.xlabel('Day')
    plt.ylabel('Price (USD)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def compare_eth_btc_prices(results_dict):
    """Compare ETH and BTC price trajectories across different volatility settings"""
    # Create plot with subplots
    fig, axs = plt.subplots(1, 2, figsize=(16, 6))
    
    # For each scenario
    for name, df in results_dict.items():
        # Extract timesteps
        timesteps = df['timestep'].tolist()
        eth_prices = []
        btc_prices = []
        
        # Extract prices
        for _, row in df.iterrows():
            agents = row['agents']
            first_agent = next(iter(agents.values()))
            eth_prices.append(first_agent.assets['ETH'].price)
            btc_prices.append(first_agent.assets['BTC'].price)
        
        # Plot ETH prices
        axs[0].plot(timesteps, eth_prices, linewidth=2, label=name)
        
        # Plot BTC prices
        axs[1].plot(timesteps, btc_prices, linewidth=2, label=name)
    
    # Set titles and labels
    axs[0].set_title('ETH Price Comparison')
    axs[0].set_xlabel('Day')
    axs[0].set_ylabel('Price (USD)')
    axs[0].grid(True, alpha=0.3)
    axs[0].legend()
    
    axs[1].set_title('BTC Price Comparison')
    axs[1].set_xlabel('Day')
    axs[1].set_ylabel('Price (USD)')
    axs[1].grid(True, alpha=0.3)
    axs[1].legend()
    
    plt.tight_layout()
    plt.show()

def compare_staking_ratios():
    """Compare staking ratios across different simulation scenarios"""
    print("Comparing staking ratios across different simulation scenarios...")
    
    # Base configuration
    base_config = sim.SimulationConfig(
        simulation_days=365,
        avl_initial_price=0.1,
        price_process_type='BM',  # Use Brownian Motion for more realistic price movements
        price_traj_type='convex',
        minimum_price=0.05,
        maximum_price=0.3,
        target_avg_price=0.15,
        bm_volatility=0.8,
        restaking=1.0,  # 100% restaking
        initial_agent_composition={'AVL': 0.4, 'ETH': 0.6, 'BTC': 0.0}
    )
    
    # Define comparison configurations
    comparisons = [
        # No restaking
        {'restaking': 0.0},
        
        # Different asset composition
        {'initial_agent_composition': {'AVL': 0.6, 'ETH': 0.4, 'BTC': 0.0}}
    ]
    
    # Run simulations
    results = sim.compare_simulations(
        base_config=base_config,
        comparison_configs=comparisons,
        names=["Base_100pct_Restake", "No_Restake", "Higher_AVL_Ratio"]
    )
    
    # Plot AVL staking ratio comparison
    comp_plots.plot_avl_staking_ratio_comparison(results)
    
    # Plot asset staking ratio comparison for ETH
    comp_plots.plot_asset_staking_ratio_comparison(results, asset='ETH')
    
    # Show the comprehensive dashboard with the new AVL staking ratio plot
    comp_plots.plot_comparison_dashboard(results)
    
    return results

if __name__ == "__main__":
    # Run one of the example functions
    # You can comment/uncomment based on which example you want to run
    
    # Basic BM simulation for all assets
    run_basic_bm_simulation()
    
    # Compare different trajectory types
    # compare_bm_trajectory_types()
    
    # Multi-asset BM simulation with different configurations
    # multi_asset_bm_simulation()
    
    # Compare ETH and BTC volatility levels
    # compare_eth_btc_volatility()
    
    # Market scenario simulation
    # market_scenario_simulation()
    
    # Compare staking ratios across different scenarios
    # compare_staking_ratios() 