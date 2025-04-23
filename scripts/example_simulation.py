#!/usr/bin/env python3
"""
Example script showing how to use the simulation_runner for Avail Fusion simulations.

This script can be run directly or the code can be copied into a Jupyter notebook.
"""

import scripts.simulation_runner as sim
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os

# Add import for the enhanced visualization module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import visualizations.comparison_plots as comp_plots
except ImportError:
    print("Warning: Comparison plots module not found. Will use basic visualization.")

# 1. Basic simulation with default parameters
def run_basic_simulation():
    """Run a basic simulation with default parameters"""
    # Create a simulation with default parameters (365 days, default prices, etc.)
    results = sim.run_simulation()
    
    # Plot some basic results
    sim.plot_simulation_results(results)
    
    return results

# 2. Compare restaking vs non-restaking simulations
def compare_restaking_scenarios():
    """Compare restaking vs non-restaking scenarios with overlaid plots"""
    # Base configuration with restaking enabled
    base_config = sim.SimulationConfig(
        simulation_days=365,
        avl_initial_price=0.1,
        eth_initial_price=3000,
        restaking=1.0,  # 100% restaking
        price_process_type='trend_with_noise',
        avl_price_growth=0.5,  # 50% annual growth
        price_volatility=0.3
    )
    
    # Define comparison configurations
    comparisons = [
        # Non-restaking scenario
        {'restaking': 0.0, 'seed': 42}
    ]
    
    # Run simulations
    results = sim.compare_simulations(
        base_config=base_config,
        comparison_configs=comparisons,
        names=["Restaking_100pct", "Non_Restaking"]
    )
    
    # Use the updated plot_simulation_results function to overlay scenarios
    print("\nPlotting overlaid comparison of restaking scenarios:")
    sim.plot_simulation_results(results)
    
    # If the enhanced visualization module is available, use it for more detailed comparison
    try:
        # Plot comprehensive dashboard
        print("\nPlotting comprehensive comparison dashboard:")
        comp_plots.plot_comparison_dashboard(results)
        
        # Plot detailed yield comparison
        print("\nPlotting detailed yield comparison:")
        comp_plots.plot_yields_comparison(results)
        
        # Plot accumulated rewards comparison
        print("\nPlotting accumulated rewards comparison:")
        comp_plots.plot_rewards_comparison(results)
    except (NameError, ImportError) as e:
        print(f"Enhanced visualization not available: {e}")
    
    return results

# 3. Advanced multi-scenario comparison
def run_multiway_comparison():
    """Run a comparison with multiple scenarios and varying parameters"""
    # Base configuration
    base_config = sim.SimulationConfig(
        # Simulation timeframe
        simulation_days=365,
        
        # Initial prices
        avl_initial_price=0.1,
        eth_initial_price=3000,
        
        # Price process
        price_process_type='linear',
        avl_price_growth=0.3,  # 30% annual growth
        
        # Yield targets
        target_avl_yield=0.15,     # 15% APY target for AVL stakers
        target_eth_yield=0.035,    # 3.5% APY target for ETH stakers
        
        # Agent parameters
        initial_tvl=1_000_000,     # $1M initial TVL
        initial_agent_composition={'AVL': 0.3, 'ETH': 0.7, 'BTC': 0.0},
        restaking=1.0,             # 100% restaking
        
        # Random seed
        seed=42
    )
    
    # Define multiple comparison configurations
    comparisons = [
        # No restaking
        {'restaking': 0.0, 'seed': 42},
        
        # Partial restaking
        {'restaking': 0.5, 'seed': 42},
        
        # Different asset composition
        {'restaking': 1.0, 'initial_agent_composition': {'AVL': 0.7, 'ETH': 0.3, 'BTC': 0.0}, 'seed': 42},
        
        # Higher yield targets
        {'restaking': 1.0, 'target_avl_yield': 0.2, 'target_eth_yield': 0.05, 'seed': 42}
    ]
    
    # Define descriptive names for each scenario
    names = [
        "Baseline", 
        "No Restaking",
        "50% Restaking", 
        "70% AVL Composition",
        "Higher Yield Targets"
    ]
    
    # Run all simulations
    results = sim.compare_simulations(
        base_config=base_config,
        comparison_configs=comparisons,
        names=names
    )
    
    # Use enhanced visualization if available
    try:
        # Plot comprehensive dashboard
        print("\nPlotting comprehensive multi-scenario dashboard:")
        comp_plots.plot_comparison_dashboard(results)
        
        # Plot specific asset TVL comparison
        print("\nComparing TVL for specific assets across scenarios:")
        comp_plots.plot_asset_tvl_comparison(results, asset='AVL')
        comp_plots.plot_asset_tvl_comparison(results, asset='ETH')
    except (NameError, ImportError) as e:
        print(f"Enhanced visualization not available: {e}")
        
        # Fall back to basic visualization
        sim.plot_simulation_results(results)
    
    return results

# 4. Advanced simulation with customized parameters
def run_advanced_simulation():
    """Run a more complex simulation with customized parameters"""
    # Create a custom configuration
    config = sim.SimulationConfig(
        # Simulation timeframe
        simulation_days=730,  # 2 years
        
        # Initial prices
        avl_initial_price=0.08,
        eth_initial_price=3500,
        btc_initial_price=85000,
        
        # Price process
        price_process_type='compound',
        avl_price_growth=1.0,  # 100% annual compound growth
        eth_price_growth=0.2,  # 20% annual compound growth
        btc_price_growth=0.3,  # 30% annual compound growth
        
        # Yield targets
        target_avl_yield=0.18,     # 18% APY target for AVL stakers
        target_eth_yield=0.045,    # 4.5% APY target for ETH stakers
        target_btc_yield=0.06,     # 6% APY target for BTC stakers
        
        # Agent parameters
        initial_tvl=5_000_000,     # $5M initial TVL
        initial_agent_composition={'AVL': 0.2, 'ETH': 0.8, 'BTC': 0.0},
        restaking=0.8,             # 80% restaking
        
        # BTC activation
        btc_activation_day=90,     # Activate BTC after 90 days
        
        # Random seed
        seed=123
    )
    
    # Run the simulation
    results = sim.run_simulation(config)
    
    # Plot results with custom metrics
    sim.plot_simulation_results(
        results, 
        metrics=['token_price', 'total_security', 'yield_pct', 'staking_ratio', 'asset_tvl']
    )
    
    return results

if __name__ == "__main__":
    print("Running basic simulation example...")
    basic_results = run_basic_simulation()
    
    print("\nRunning restaking comparison example with overlaid plots...")
    restaking_results = compare_restaking_scenarios()
    
    print("\nRunning multi-scenario comparison example...")
    multiway_results = run_multiway_comparison()
    
    print("\nRunning advanced simulation example...")
    advanced_results = run_advanced_simulation() 