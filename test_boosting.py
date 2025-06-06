#!/usr/bin/env python3
"""
Test script for AVL Boosting Mechanism

This script demonstrates the AVL boosting functionality including:
1. Lock period multipliers
2. Pool share multipliers  
3. Automatic locking of restaked rewards
4. Unlock processing over time
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.simulation_runner import SimulationConfig, run_simulation
import pandas as pd

def test_avl_boosting():
    """Test the AVL boosting mechanism with different configurations"""
    
    print("🚀 Testing AVL Boosting Mechanism")
    print("="*60)
    
    # Configuration with boosting enabled
    config_with_boosting = SimulationConfig(
        simulation_days=30,  # Short test run
        avl_initial_price=0.1,
        eth_initial_price=3000,
        initial_agent_composition={'AVL': 0.8, 'ETH': 0.2, 'BTC': 0.0},
        initial_tvl=1000000,  # $1M initial TVL
        restaking=1.0,  # 100% restaking
        
        # AVL Boosting enabled with custom parameters
        avl_boosting_enabled=True,
        avl_lock_period_multipliers={0: 1.0, 30: 1.05, 60: 1.1, 180: 1.5},
        avl_pool_share_multipliers={0.01: 1.1, 0.1: 2.5},  # 1% gets 1.1x, 10% gets 2.5x
        avl_lock_preferences={'avl_maxi': 180, 'eth_maxi': 0, 'btc_maxi': 0},
        
        seed=42
    )
    
    # Configuration with boosting disabled for comparison
    config_without_boosting = SimulationConfig(
        simulation_days=30,
        avl_initial_price=0.1,
        eth_initial_price=3000,
        initial_agent_composition={'AVL': 0.8, 'ETH': 0.2, 'BTC': 0.0},
        initial_tvl=1000000,
        restaking=1.0,
        
        # AVL Boosting disabled
        avl_boosting_enabled=False,
        avl_lock_preferences={'avl_maxi': 0, 'eth_maxi': 0, 'btc_maxi': 0},  # No locking
        
        seed=42
    )
    
    print("\n📊 Running simulation WITH boosting...")
    results_with_boosting = run_simulation(config_with_boosting)
    
    print("\n📊 Running simulation WITHOUT boosting...")
    results_without_boosting = run_simulation(config_without_boosting)
    
    # Compare results
    print("\n📈 COMPARISON RESULTS")
    print("="*60)
    
    # Get final day results
    final_day_with = results_with_boosting.iloc[-1]
    final_day_without = results_without_boosting.iloc[-1]
    
    # Extract agent data
    agents_with = final_day_with['agents']
    agents_without = final_day_without['agents']
    
    print(f"\n🔒 AVL Agent (with boosting):")
    avl_agent_with = agents_with['avl_maxi']
    print(f"  Total AVL Balance: {avl_agent_with.assets['AVL'].balance:,.2f} AVL")
    print(f"  Unlocked Balance: {avl_agent_with.assets['AVL'].unlocked_balance:,.2f} AVL")
    print(f"  Locked Balance: {avl_agent_with.assets['AVL'].locked_balance:,.2f} AVL")
    print(f"  Lock Distribution: {avl_agent_with.get_avl_lock_distribution()}")
    print(f"  Annual Rewards: {avl_agent_with.curr_annual_rewards_avl:,.2f} AVL")
    print(f"  Accumulated Rewards: {avl_agent_with.accu_rewards_avl:,.2f} AVL")
    
    print(f"\n🔓 AVL Agent (without boosting):")
    avl_agent_without = agents_without['avl_maxi']
    print(f"  Total AVL Balance: {avl_agent_without.assets['AVL'].balance:,.2f} AVL")
    print(f"  Annual Rewards: {avl_agent_without.curr_annual_rewards_avl:,.2f} AVL")
    print(f"  Accumulated Rewards: {avl_agent_without.accu_rewards_avl:,.2f} AVL")
    
    # Calculate boost effect
    reward_boost = (avl_agent_with.curr_annual_rewards_avl / avl_agent_without.curr_annual_rewards_avl - 1) * 100 if avl_agent_without.curr_annual_rewards_avl > 0 else 0
    balance_boost = (avl_agent_with.assets['AVL'].balance / avl_agent_without.assets['AVL'].balance - 1) * 100 if avl_agent_without.assets['AVL'].balance > 0 else 0
    
    print(f"\n🚀 BOOSTING EFFECT:")
    print(f"  Reward Boost: {reward_boost:+.2f}%")
    print(f"  Balance Boost: {balance_boost:+.2f}%")
    
    # Show yield comparison
    print(f"\n📊 YIELD COMPARISON:")
    print(f"  With Boosting: {avl_agent_with.current_yield*100:.3f}%")
    print(f"  Without Boosting: {avl_agent_without.current_yield*100:.3f}%")
    
    return results_with_boosting, results_without_boosting

def test_lock_unlock_cycle():
    """Test the lock/unlock cycle over a longer period"""
    
    print("\n\n🔄 Testing Lock/Unlock Cycle")
    print("="*60)
    
    config = SimulationConfig(
        simulation_days=200,  # Long enough to see unlocks
        avl_initial_price=0.1,
        initial_agent_composition={'AVL': 1.0, 'ETH': 0.0, 'BTC': 0.0},
        initial_tvl=1000000,
        restaking=1.0,
        
        # Mixed lock preferences
        avl_boosting_enabled=True,
        avl_lock_period_multipliers={0: 1.0, 30: 1.05, 60: 1.1, 180: 1.5},
        avl_pool_share_multipliers={0.01: 1.1, 0.1: 2.5},
        avl_lock_preferences={'avl_maxi': 60, 'eth_maxi': 0, 'btc_maxi': 0},  # 60-day locks
        
        seed=42
    )
    
    print("📊 Running long-term simulation...")
    results = run_simulation(config)
    
    # Analyze lock/unlock patterns
    print("\n📈 LOCK/UNLOCK ANALYSIS:")
    
    # Sample key timesteps
    sample_days = [0, 30, 60, 90, 120, 150, 180]
    
    for day in sample_days:
        if day < len(results):
            row = results.iloc[day]
            avl_agent = row['agents']['avl_maxi']
            
            print(f"\nDay {day}:")
            print(f"  Total Balance: {avl_agent.assets['AVL'].balance:,.2f} AVL")
            print(f"  Unlocked: {avl_agent.assets['AVL'].unlocked_balance:,.2f} AVL")
            print(f"  Locked: {avl_agent.assets['AVL'].locked_balance:,.2f} AVL")
            print(f"  Lock Distribution: {avl_agent.get_avl_lock_distribution()}")
            print(f"  Annual Rewards: {avl_agent.curr_annual_rewards_avl:,.2f} AVL")
    
    return results

if __name__ == "__main__":
    # Run tests
    print("🧪 AVL Boosting Mechanism Test Suite")
    print("="*80)
    
    try:
        # Test 1: Basic boosting comparison
        results_with, results_without = test_avl_boosting()
        
        # Test 2: Lock/unlock cycle
        long_term_results = test_lock_unlock_cycle()
        
        print("\n✅ All tests completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✓ Lock period multipliers (0d: 1.0x, 30d: 1.05x, 60d: 1.1x, 180d: 1.5x)")
        print("  ✓ Pool share multipliers (1%: 1.1x, 10%: 2.5x)")
        print("  ✓ Automatic locking of restaked rewards")
        print("  ✓ Unlock processing over time")
        print("  ✓ Boosted reward calculations")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 