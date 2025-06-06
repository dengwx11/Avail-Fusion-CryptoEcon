"""
Simulation runner for Avail Fusion economic model.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scripts.market_scenarios import get_scenario_prices, MARKET_SCENARIOS

def run_simulation(
    scenario_name: str,
    n_periods: int = 365,
    seed: int = 42,
    initial_avl_supply: float = 10_000_000_000,
    initial_eth_price: float = 2500.0,
    initial_btc_price: float = 100000.0,
    initial_avl_price: float = 0.05,
    reward_rate: float = 0.05,
    staking_ratio: float = 0.5,
    liquidity_ratio: float = 0.3,
    market_impact: float = 0.1,
    correlation: float = 0.6,
    volatility: float = 0.5,
    drift: float = 0.0,
    regime_changes: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Run a simulation with the specified market scenario
    
    Parameters:
    -----------
    scenario_name : str
        Name of the market scenario to run
    n_periods : int
        Number of periods to simulate
    seed : int
        Random seed for reproducibility
    initial_avl_supply : float
        Initial AVL token supply
    initial_eth_price : float
        Initial ETH price in USD
    initial_btc_price : float
        Initial BTC price in USD
    initial_avl_price : float
        Initial AVL price in USD
    reward_rate : float
        Annual reward rate for staking
    staking_ratio : float
        Ratio of AVL tokens staked
    liquidity_ratio : float
        Ratio of AVL tokens in liquidity pools
    market_impact : float
        Market impact parameter for price dynamics
    correlation : float
        Correlation between AVL and ETH/BTC prices
    volatility : float
        Volatility of price movements
    drift : float
        Drift term for price dynamics
    regime_changes : dict
        Dictionary specifying regime changes
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing simulation results
    """
    # Get price paths for the scenario
    avl_prices, eth_prices, btc_prices = get_scenario_prices(
        scenario_name=scenario_name,
        n_periods=n_periods,
        seed=seed
    )
    
    # Create price DataFrame
    prices_df = pd.DataFrame({
        'AVL': avl_prices,
        'ETH': eth_prices,
        'BTC': btc_prices
    })
    
    # Calculate returns
    returns_df = prices_df.pct_change().fillna(0)
    
    # Calculate staking rewards
    daily_reward_rate = (1 + reward_rate) ** (1/365) - 1
    staking_rewards = initial_avl_supply * staking_ratio * daily_reward_rate
    
    # Calculate liquidity rewards
    liquidity_rewards = initial_avl_supply * liquidity_ratio * daily_reward_rate
    
    # Calculate total rewards
    total_rewards = staking_rewards + liquidity_rewards
    
    # Calculate USD value of rewards
    usd_rewards = total_rewards * prices_df['AVL']
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'AVL_Price': prices_df['AVL'],
        'ETH_Price': prices_df['ETH'],
        'BTC_Price': prices_df['BTC'],
        'AVL_Return': returns_df['AVL'],
        'ETH_Return': returns_df['ETH'],
        'BTC_Return': returns_df['BTC'],
        'Staking_Rewards': staking_rewards,
        'Liquidity_Rewards': liquidity_rewards,
        'Total_Rewards': total_rewards,
        'USD_Rewards': usd_rewards
    })
    
    return results_df

def run_scenario_analysis(
    scenario_names: Optional[List[str]] = None,
    n_periods: int = 365,
    seed: int = 42,
    **kwargs
) -> Dict[str, pd.DataFrame]:
    """
    Run multiple market scenarios and return results
    
    Parameters:
    -----------
    scenario_names : List[str]
        List of scenario names to run. If None, runs all scenarios.
    n_periods : int
        Number of periods to simulate
    seed : int
        Random seed for reproducibility
    **kwargs : dict
        Additional parameters to pass to run_simulation
        
    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary mapping scenario names to results DataFrames
    """
    if scenario_names is None:
        scenario_names = list(MARKET_SCENARIOS.keys())
    
    results = {}
    for scenario in scenario_names:
        results[scenario] = run_simulation(
            scenario_name=scenario,
            n_periods=n_periods,
            seed=seed,
            **kwargs
        )
    
    return results

def generate_scenario_report(
    results: Dict[str, pd.DataFrame],
    output_file: Optional[str] = None
) -> None:
    """
    Generate a report comparing results across scenarios
    
    Parameters:
    -----------
    results : Dict[str, pd.DataFrame]
        Dictionary mapping scenario names to results DataFrames
    output_file : str
        Path to save the report. If None, prints to console.
    """
    # Calculate summary statistics for each scenario
    summary_stats = {}
    for scenario, df in results.items():
        summary_stats[scenario] = {
            'Final_AVL_Price': df['AVL_Price'].iloc[-1],
            'AVL_Return': df['AVL_Price'].iloc[-1] / df['AVL_Price'].iloc[0] - 1,
            'Total_Rewards': df['Total_Rewards'].sum(),
            'USD_Rewards': df['USD_Rewards'].sum(),
            'Max_Drawdown': (df['AVL_Price'] / df['AVL_Price'].cummax() - 1).min(),
            'Volatility': df['AVL_Return'].std() * np.sqrt(252),
            'Sharpe_Ratio': (df['AVL_Return'].mean() * 252) / (df['AVL_Return'].std() * np.sqrt(252))
        }
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_stats).T
    
    # Format the report
    report = f"Scenario Analysis Report\n{'='*50}\n\n"
    
    # Add summary statistics
    report += "Summary Statistics:\n"
    report += summary_df.to_string()
    report += "\n\n"
    
    # Add scenario descriptions
    report += "Scenario Descriptions:\n"
    for scenario in results.keys():
        report += f"\n{scenario}:\n"
        report += f"- Initial AVL Price: ${results[scenario]['AVL_Price'].iloc[0]:.4f}\n"
        report += f"- Final AVL Price: ${results[scenario]['AVL_Price'].iloc[-1]:.4f}\n"
        report += f"- Total Return: {summary_df.loc[scenario, 'AVL_Return']:.2%}\n"
        report += f"- Total Rewards: {summary_df.loc[scenario, 'Total_Rewards']:,.0f} AVL\n"
        report += f"- USD Value of Rewards: ${summary_df.loc[scenario, 'USD_Rewards']:,.2f}\n"
        report += f"- Max Drawdown: {summary_df.loc[scenario, 'Max_Drawdown']:.2%}\n"
        report += f"- Annualized Volatility: {summary_df.loc[scenario, 'Volatility']:.2%}\n"
        report += f"- Sharpe Ratio: {summary_df.loc[scenario, 'Sharpe_Ratio']:.2f}\n"
    
    # Save or print the report
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
    else:
        print(report) 