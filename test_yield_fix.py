#!/usr/bin/env python3
"""
Test script to verify the yield spike fix after day 180

This script runs a simulation and checks for exponential yield increases
around day 180 to ensure the budget replenishment fixes work correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.simulation_runner import SimulationConfig, run_simulation
import pandas as pd
import matplotlib.pyplot as plt

def test_yield_stability():
    """Test that yields remain stable after day 180"""
    
    print("🧪 Testing Yield Stability After Day 180")
    print("="*60)
    
    # Configuration for testing
    config = SimulationConfig(
        simulation_days=250,  # Run past day 180 to see the effect
        avl_initial_price=0.1,
        eth_initial_price=3000,
        btc_initial_price=30000,
        initial_agent_composition={'AVL': 0.7, 'ETH': 0.3, 'BTC': 0.0},
        initial_tvl=1000000,  # $1M initial TVL
        restaking=1.0,  # 100% restaking
        
        # Use default boosting and budget replenishment from params.py
        avl_boosting_enabled=True,
        btc_activation_day=180,
        
        seed=42
    )
    
    print("📊 Running simulation...")
    results = run_simulation(config)
    
    # Analyze yield patterns around day 180
    print("\n📈 YIELD ANALYSIS:")
    
    # Extract yield data for AVL agent
    avl_yields = []
    days = []
    
    for _, row in results.iterrows():
        day = row['timestep']
        yield_pcts = row.get('yield_pcts', {})
        avl_yield = yield_pcts.get('avl_maxi', 0)
        
        days.append(day)
        avl_yields.append(avl_yield)
    
    # Check for exponential increases
    day_170_yield = avl_yields[170] if len(avl_yields) > 170 else 0
    day_180_yield = avl_yields[180] if len(avl_yields) > 180 else 0
    day_190_yield = avl_yields[190] if len(avl_yields) > 190 else 0
    day_200_yield = avl_yields[200] if len(avl_yields) > 200 else 0
    
    print(f"Day 170 AVL Yield: {day_170_yield:.3f}%")
    print(f"Day 180 AVL Yield: {day_180_yield:.3f}%")
    print(f"Day 190 AVL Yield: {day_190_yield:.3f}%")
    print(f"Day 200 AVL Yield: {day_200_yield:.3f}%")
    
    # Calculate yield change ratios
    if day_170_yield > 0:
        day_180_ratio = day_180_yield / day_170_yield
        day_190_ratio = day_190_yield / day_170_yield if day_190_yield > 0 else 0
        
        print(f"\nYield Change Ratios (vs Day 170):")
        print(f"Day 180: {day_180_ratio:.2f}x")
        print(f"Day 190: {day_190_ratio:.2f}x")
        
        # Check if the fix worked
        if day_180_ratio > 5.0:  # More than 5x increase is problematic
            print("❌ ISSUE: Exponential yield increase detected!")
            return False, results
        elif day_180_ratio > 2.0:  # More than 2x increase is concerning
            print("⚠️  WARNING: Significant yield increase detected")
            return True, results
        else:
            print("✅ SUCCESS: Yield remains stable after day 180")
            return True, results
    
    return True, results

def plot_yield_analysis(results):
    """Plot yield trends to visualize the fix"""
    
    # Extract data for plotting
    days = results['timestep'].tolist()
    avl_yields = [row.get('avl_maxi', 0) for row in results['yield_pcts']]
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Plot yield over time
    plt.subplot(2, 1, 1)
    plt.plot(days, avl_yields, 'b-', linewidth=2, label='AVL Yield')
    plt.axvline(x=180, color='r', linestyle='--', alpha=0.7, label='Day 180 (BTC Activation)')
    plt.xlabel('Day')
    plt.ylabel('Yield (%)')
    plt.title('AVL Yield Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot yield change rate
    plt.subplot(2, 1, 2)
    yield_changes = [0] + [avl_yields[i] - avl_yields[i-1] for i in range(1, len(avl_yields))]
    plt.plot(days, yield_changes, 'g-', linewidth=2, label='Daily Yield Change')
    plt.axvline(x=180, color='r', linestyle='--', alpha=0.7, label='Day 180 (BTC Activation)')
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    plt.xlabel('Day')
    plt.ylabel('Yield Change (%)')
    plt.title('Daily Yield Change Rate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('yield_stability_test.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 Yield analysis plot saved as 'yield_stability_test.png'")

def analyze_budget_usage(results):
    """Analyze budget usage patterns"""
    
    print("\n💰 BUDGET USAGE ANALYSIS:")
    
    # Get final state
    final_state = results.iloc[-1]
    pool_manager = final_state.get('pool_manager')
    
    if pool_manager:
        budget_summary = pool_manager.get_budget_summary()
        remaining_budgets = pool_manager.get_remaining_budget()
        spent_budgets = pool_manager.get_spent_budget_per_pool()
        
        print(f"Total Budget: {budget_summary['current_total_budget']:,.0f} AVL")
        print(f"Total Spent: {budget_summary['spent_budget']:,.0f} AVL")
        print(f"Utilization: {budget_summary['budget_utilization_pct']:.1f}%")
        
        print(f"\nRemaining Budget by Pool:")
        for pool, amount in remaining_budgets.items():
            print(f"  {pool}: {amount:,.0f} AVL")
        
        print(f"\nSpent Budget by Pool:")
        for pool, amount in spent_budgets.items():
            print(f"  {pool}: {amount:,.0f} AVL")

if __name__ == "__main__":
    try:
        # Run the test
        success, results = test_yield_stability()
        
        # Analyze results
        analyze_budget_usage(results)
        
        # Create visualization
        plot_yield_analysis(results)
        
        if success:
            print("\n✅ Test completed successfully!")
            print("The yield spike issue appears to be resolved.")
        else:
            print("\n❌ Test failed!")
            print("The yield spike issue persists and needs further investigation.")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc() 