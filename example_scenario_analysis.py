#!/usr/bin/env python3
"""
Example script demonstrating how to use the scenario analysis plotting functions
to compare simulation results across different scenarios and portfolio types.

This script shows how to:
1. Run multiple simulation scenarios
2. Generate comparison plots (scatterplot and barplot)
3. Create a comprehensive analysis report
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.simulation_runner import SimulationConfig, compare_simulations
from visualizations.scenario_analysis_plots import (
    plot_rewards_scatterplot,
    plot_return_ratio_barplot,
    plot_scenario_comparison_dashboard,
    generate_comparison_report
)

def run_scenario_analysis_example():
    """
    Example function showing how to generate and compare multiple scenarios
    """
    print("🚀 Running Scenario Analysis Example")
    print("="*60)
    
    # Define base configuration
    base_config = SimulationConfig(
        simulation_days=365,  # 1 year simulation
        
        # Base scenario: Normal market conditions
        avl_initial_price=0.1,
        eth_initial_price=3000,
        btc_initial_price=30000,
        
        # Linear price growth
        price_process_type='linear',
        avl_price_growth=0.3,  # 30% annual growth
        eth_price_growth=0.1,  # 10% annual growth
        btc_price_growth=0.05, # 5% annual growth
        
        # Portfolio settings
        initial_tvl=1_000_000,  # $1M initial TVL
        initial_agent_composition={'AVL': 0.4, 'ETH': 0.5, 'BTC': 0.1},
        restaking=1.0,  # 100% restaking
        
        # Boosting enabled
        avl_boosting_enabled=True,
        
        seed=42
    )
    
    # Define comparison scenarios
    comparison_configs = [
        # Scenario 2: Bear market (negative growth)
        {
            'avl_price_growth': -0.2,   # -20% annual decline
            'eth_price_growth': -0.1,   # -10% annual decline
            'btc_price_growth': -0.05,  # -5% annual decline
            'seed': 42
        },
        
        # Scenario 3: High volatility with trend
        {
            'price_process_type': 'trend_with_noise',
            'price_volatility': 0.5,    # 50% volatility
            'avl_price_growth': 0.5,    # 50% annual growth
            'eth_price_growth': 0.2,    # 20% annual growth
            'btc_price_growth': 0.1,    # 10% annual growth
            'seed': 42
        },
        
        # Scenario 4: Different portfolio composition (AVL-heavy)
        {
            'initial_agent_composition': {'AVL': 0.7, 'ETH': 0.2, 'BTC': 0.1},
            'avl_price_growth': 0.3,
            'eth_price_growth': 0.1,
            'btc_price_growth': 0.05,
            'seed': 42
        },
        
        # Scenario 5: No boosting
        {
            'avl_boosting_enabled': False,
            'avl_price_growth': 0.3,
            'eth_price_growth': 0.1,
            'btc_price_growth': 0.05,
            'seed': 42
        }
    ]
    
    # Define scenario names
    scenario_names = [
        "Base_Bull_Market",
        "Bear_Market", 
        "High_Volatility",
        "AVL_Heavy_Portfolio",
        "No_Boosting"
    ]
    
    print(f"Running {len(scenario_names)} simulation scenarios...")
    
    # Run all simulations
    results = compare_simulations(
        base_config=base_config,
        comparison_configs=comparison_configs,
        names=scenario_names
    )
    
    print(f"\n✅ All simulations completed!")
    print(f"Scenarios run: {list(results.keys())}")
    
    # Generate comparison plots
    print(f"\n📊 Generating comparison plots...")
    
    # 1. Individual plots
    print("Creating rewards scatterplot...")
    fig1 = plot_rewards_scatterplot(results, final_day=365)
    
    print("Creating return ratio barplot...")
    fig2 = plot_return_ratio_barplot(results, final_day=365)
    
    print("Creating comprehensive dashboard...")
    fig3 = plot_scenario_comparison_dashboard(results, final_day=365)
    
    # 2. Generate comprehensive report
    print(f"\n📋 Generating comprehensive analysis report...")
    report = generate_comparison_report(
        simulation_results=results,
        final_day=365,
        output_dir="scenario_analysis_results"
    )
    
    return results, report

def create_custom_scenario_comparison():
    """
    Example of creating a more targeted comparison focused on specific aspects
    """
    print("\n🎯 Creating Custom Scenario Comparison")
    print("="*60)
    
    # Focus on different boosting configurations
    base_config = SimulationConfig(
        simulation_days=365,
        avl_initial_price=0.1,
        price_process_type='linear',
        avl_price_growth=0.2,  # 20% annual growth
        initial_tvl=500_000,   # $500K initial TVL
        restaking=1.0,
        seed=42
    )
    
    # Different boosting scenarios
    boosting_scenarios = [
        # Standard boosting
        {
            'avl_boosting_enabled': True,
            'avl_lock_period_multipliers': {0: 1.0, 30: 1.05, 60: 1.1, 180: 1.5},
            'avl_pool_share_multipliers': {0.01: 1.1}
        },
        
        # Higher boosting rewards
        {
            'avl_boosting_enabled': True,
            'avl_lock_period_multipliers': {0: 1.0, 30: 1.1, 60: 1.2, 180: 2.0},
            'avl_pool_share_multipliers': {0.01: 1.2, 0.05: 1.5}
        },
        
        # No boosting
        {
            'avl_boosting_enabled': False
        }
    ]
    
    boosting_names = [
        "Standard_Boosting",
        "Enhanced_Boosting", 
        "No_Boosting"
    ]
    
    # Run boosting comparison
    boosting_results = compare_simulations(
        base_config=base_config,
        comparison_configs=boosting_scenarios,
        names=boosting_names
    )
    
    # Create focused analysis
    print("Generating boosting comparison plots...")
    
    # Custom plots focusing on the impact of boosting
    fig1 = plot_rewards_scatterplot(
        boosting_results, 
        final_day=365,
        save_path="boosting_rewards_comparison.png"
    )
    
    fig2 = plot_return_ratio_barplot(
        boosting_results,
        final_day=365, 
        save_path="boosting_returns_comparison.png"
    )
    
    return boosting_results

def analyze_specific_portfolios():
    """
    Example focusing on specific portfolio configurations mentioned by user:
    - 10% AVL / 90% ETH portfolio
    - 80% AVL / 20% BTC portfolio
    """
    print("\n👤 Analyzing Specific User Portfolios")
    print("="*60)
    
    base_config = SimulationConfig(
        simulation_days=365,
        avl_initial_price=0.1,
        eth_initial_price=3000,
        btc_initial_price=30000,
        price_process_type='linear',
        avl_price_growth=0.25,  # 25% annual growth
        eth_price_growth=0.15,  # 15% annual growth  
        btc_price_growth=0.08,  # 8% annual growth
        initial_tvl=1_000_000,
        restaking=1.0,
        avl_boosting_enabled=True,
        seed=42
    )
    
    # Specific portfolio configurations
    portfolio_scenarios = [
        # Scenario 1: Conservative ETH-heavy portfolio
        {
            'initial_agent_composition': {'AVL': 0.1, 'ETH': 0.9, 'BTC': 0.0}
        },
        
        # Scenario 2: Aggressive AVL-heavy portfolio  
        {
            'initial_agent_composition': {'AVL': 0.8, 'ETH': 0.0, 'BTC': 0.2}
        },
        
        # Scenario 3: Balanced portfolio
        {
            'initial_agent_composition': {'AVL': 0.33, 'ETH': 0.33, 'BTC': 0.34}
        }
    ]
    
    portfolio_names = [
        "Conservative_ETH_Heavy",    # 10% AVL / 90% ETH
        "Aggressive_AVL_Heavy",      # 80% AVL / 20% BTC  
        "Balanced_Portfolio"         # Equal distribution
    ]
    
    # Run portfolio analysis
    portfolio_results = compare_simulations(
        base_config=base_config,
        comparison_configs=portfolio_scenarios,
        names=portfolio_names
    )
    
    # Generate targeted analysis report
    portfolio_report = generate_comparison_report(
        simulation_results=portfolio_results,
        final_day=365,
        output_dir="portfolio_analysis_results"
    )
    
    return portfolio_results, portfolio_report

if __name__ == "__main__":
    """
    Main execution - run all examples
    """
    try:
        # Example 1: General scenario analysis
        print("🔥 SCENARIO ANALYSIS DEMONSTRATION")
        print("="*80)
        
        # Run main scenario analysis
        main_results, main_report = run_scenario_analysis_example()
        
        # Run boosting comparison  
        boosting_results = create_custom_scenario_comparison()
        
        # Run specific portfolio analysis
        portfolio_results, portfolio_report = analyze_specific_portfolios()
        
        print(f"\n🎉 ALL ANALYSES COMPLETED!")
        print("="*80)
        print("Generated files:")
        print("- scenario_analysis_results/ (main scenario comparison)")
        print("- portfolio_analysis_results/ (specific portfolio analysis)")
        print("- boosting_rewards_comparison.png")
        print("- boosting_returns_comparison.png")
        
        print(f"\n📈 Key insights:")
        print("1. Compare how different market conditions affect portfolio returns")
        print("2. Analyze the impact of AVL boosting mechanisms") 
        print("3. Evaluate specific portfolio allocations (10% AVL/90% ETH vs 80% AVL/20% BTC)")
        print("4. Use the scatterplots to see reward efficiency")
        print("5. Use the barplots to compare return ratios across scenarios")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc() 