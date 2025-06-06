#!/usr/bin/env python3
"""
Avail Fusion Simulation Runner

This script provides a streamlined interface for running Avail Fusion staking economy simulations.
It encapsulates the setup and execution process from cold-start-analysis.ipynb into reusable functions.

Usage:
    import simulation_runner as sim
    results = sim.run_simulation(restaking=True, simulation_days=365)
    # Then analyze results in your notebook
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.io as pio
from typing import Dict, List, Tuple, Optional, Union, Any

# Add the project root to Python's import path if it's not already there
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import simulation components
from radcad import Model, Simulation, Experiment
from radcad.engine import Engine, Backend

from config.params import FusionParams
from config.initialize_simulation import initialize_state
from config.psub import psub
from config.config import TIMESTEPS, DELTA_TIME

from model.agents_class import AgentStake
from model.rewards import calculate_reward_allocation
from model.stochastic_processes import (
    create_linear_price_growth,
    create_compound_price_growth,
    create_trend_with_noise_price,
    create_stochastic_avail_price_process,
    plot_price
)
from scripts.market_scenarios import MARKET_SCENARIOS

try:
    from real_data_fetcher import fetch
except ImportError:
    print("Warning: real_data_fetcher module not found, using simulated data only")


class SimulationConfig:
    """Configuration class for Avail Fusion simulation parameters"""
    
    def __init__(
        self,
        # Simulation timeframe
        simulation_days: int = 365*2,
        delta_time: float = DELTA_TIME,
        
        # Initial prices
        avl_initial_price: float = 0.05,
        eth_initial_price: float = 2500,
        btc_initial_price: float = 100000,
        lens_initial_price: float = 1.0,
        
        # Price process parameters
        price_process_type: str = 'linear',  # 'linear', 'compound', 'trend_with_noise', 'BM', or 'market_scenario'
        avl_price_growth: float = 0.5,       # Annual growth rate (e.g., 0.5 for 50% growth)
        eth_price_growth: float = 0.0,
        btc_price_growth: float = 0.0,
        lens_price_growth: float = 0.0,
        price_volatility: float = 0.2,       # For 'trend_with_noise' process
        
        # Market scenario parameters
        market_scenario: str = None,         # Name of market scenario to use
        scenario_correlation: float = 0.7,   # Correlation between assets in scenario
        scenario_volatility: float = 0.2,    # Base volatility for scenario
        scenario_drift: float = 0.0,         # Base drift for scenario
        regime_changes: List[Dict] = None,   # List of regime change events
        
        # Brownian Motion specific parameters for AVL
        price_traj_type: str = 'convex',    # 'convex', 'concave', or 'none' for BM process
        minimum_price: float = None,        # Minimum price for BM process
        maximum_price: float = None,        # Maximum price for BM process
        target_avg_price: float = None,     # Target average price for BM process
        bm_volatility: float = 1.0,         # Volatility parameter for BM process
        
        # Brownian Motion specific parameters for ETH
        eth_price_traj_type: str = 'convex',
        eth_minimum_price: float = None,
        eth_maximum_price: float = None,
        eth_target_avg_price: float = None,
        eth_bm_volatility: float = 1.0,
        
        # Brownian Motion specific parameters for BTC
        btc_price_traj_type: str = 'convex',
        btc_minimum_price: float = None,
        btc_maximum_price: float = None,
        btc_target_avg_price: float = None,
        btc_bm_volatility: float = 1.0,
        
        # Brownian Motion specific parameters for LENS
        lens_price_traj_type: str = 'convex',
        lens_minimum_price: float = None,
        lens_maximum_price: float = None,
        lens_target_avg_price: float = None,
        lens_bm_volatility: float = 1.0,
        
        # Tokenomics parameters
        total_supply: float = 10_000_000_000,  # 10 billion AVL tokens
        native_staking_ratio: float = 0.5,     # Initial staking ratio
        
        # Yield targets
        target_avl_yield: float = 0.15,     # 15% APY target for AVL stakers
        target_eth_yield: float = 0.035,    # 3.5% APY target for ETH stakers
        target_btc_yield: float = 0.05,     # 5% APY target for BTC stakers
        
        # Agent parameters
        initial_tvl: float = 10,     # $10 initial TVL for cold start
        initial_agent_composition: Dict[str, float] = None,  # Asset allocation
        restaking: float = 1.0,             # Restaking percentage (0-1)
        
        # AVL Boosting parameters
        avl_boosting_enabled: bool = True,  # Enable/disable AVL boosting
        avl_lock_period_multipliers: Dict[int, float] = None,  # Lock period multipliers
        avl_pool_share_multipliers: Dict[float, float] = None,  # Pool share multipliers
        avl_lock_preferences: Dict[str, int] = None,  # Agent lock preferences
        
        # Inflation parameters
        inflation_decay: float = 0.05,
        target_staking_rate: float = 0.5,
        min_inflation_rate: float = 0.01,
        max_inflation_rate: float = 0.05,
        
        # BTC activation
        btc_activation_day: int = 180,
        
        # Security budget
        initial_security_budget: float = 30e9,  # 30 billion AVL tokens for security budget
        
        # Random seed
        seed: int = 42,

        # Market scenarios
        market_scenarios: List[str] = None,
        market_scenario_correlation: float = 0.7,
        market_scenario_volatility: float = 0.2,
        market_scenario_drift: float = 0.0,
        market_scenario_regime_changes: List[Dict] = None,

    ):
        """Initialize simulation configuration with default or custom parameters"""
        # Store all parameters as instance attributes
        self.simulation_days = simulation_days
        self.delta_time = delta_time
        
        # Store initial prices
        self.avl_initial_price = avl_initial_price
        self.eth_initial_price = eth_initial_price
        self.btc_initial_price = btc_initial_price
        self.lens_initial_price = lens_initial_price
        
        # Store price process parameters
        self.price_process_type = price_process_type
        self.avl_price_growth = avl_price_growth
        self.eth_price_growth = eth_price_growth
        self.btc_price_growth = btc_price_growth
        self.lens_price_growth = lens_price_growth
        self.price_volatility = price_volatility
        
        # Store market scenario parameters
        self.market_scenario = market_scenario
        self.scenario_correlation = scenario_correlation
        self.scenario_volatility = scenario_volatility
        self.scenario_drift = scenario_drift
        self.regime_changes = regime_changes or []
        
        # Store Brownian Motion parameters
        self.price_traj_type = price_traj_type
        self.minimum_price = minimum_price
        self.maximum_price = maximum_price
        self.target_avg_price = target_avg_price
        self.bm_volatility = bm_volatility
        
        # Store ETH BM parameters
        self.eth_price_traj_type = eth_price_traj_type
        self.eth_minimum_price = eth_minimum_price
        self.eth_maximum_price = eth_maximum_price
        self.eth_target_avg_price = eth_target_avg_price
        self.eth_bm_volatility = eth_bm_volatility
        
        # Store BTC BM parameters
        self.btc_price_traj_type = btc_price_traj_type
        self.btc_minimum_price = btc_minimum_price
        self.btc_maximum_price = btc_maximum_price
        self.btc_target_avg_price = btc_target_avg_price
        self.btc_bm_volatility = btc_bm_volatility
        
        # Store LENS BM parameters
        self.lens_price_traj_type = lens_price_traj_type
        self.lens_minimum_price = lens_minimum_price
        self.lens_maximum_price = lens_maximum_price
        self.lens_target_avg_price = lens_target_avg_price
        self.lens_bm_volatility = lens_bm_volatility
        
        # Store tokenomics parameters
        self.total_supply = total_supply
        self.native_staking_ratio = native_staking_ratio
        
        # Store yield targets
        self.target_avl_yield = target_avl_yield
        self.target_eth_yield = target_eth_yield
        self.target_btc_yield = target_btc_yield
        
        # Store agent parameters
        self.initial_tvl = initial_tvl
        self.initial_agent_composition = initial_agent_composition or {
            'AVL': 0.4,
            'ETH': 0.4,
            'BTC': 0.2
        }
        self.restaking = restaking
        
        # Store AVL boosting parameters
        self.avl_boosting_enabled = avl_boosting_enabled
        self.avl_lock_period_multipliers = avl_lock_period_multipliers or {
            0: 1.0,
            30: 1.05,
            60: 1.1,
            180: 1.5
        }
        self.avl_pool_share_multipliers = avl_pool_share_multipliers or {
            0.01: 1.1
        }
        self.avl_lock_preferences = avl_lock_preferences or {
            'avl_maxi': 180,
            'eth_maxi': 0,
            'btc_maxi': 0
        }
        
        # Store inflation parameters
        self.inflation_decay = inflation_decay
        self.target_staking_rate = target_staking_rate
        self.min_inflation_rate = min_inflation_rate
        self.max_inflation_rate = max_inflation_rate
        
        # Store BTC activation
        self.btc_activation_day = btc_activation_day
        
        # Store security budget
        self.initial_security_budget = initial_security_budget
        
        # Store random seed
        self.seed = seed

        # Store market scenarios
        self.market_scenarios = market_scenarios
        self.market_scenario_correlation = market_scenario_correlation
        self.market_scenario_volatility = market_scenario_volatility
        self.market_scenario_drift = market_scenario_drift
        self.market_scenario_regime_changes = market_scenario_regime_changes


def generate_price_process(
    config: SimulationConfig,
) -> Tuple[List[float], List[float], List[float], List[float]]:
    """Generate price processes for all assets based on configuration"""
    # Set random seed for reproducibility
    np.random.seed(config.seed)
    
    # Calculate number of timesteps
    n_timesteps = int(config.simulation_days / config.delta_time)
    
    # If using market scenario, generate correlated price paths
    if config.price_process_type == 'market_scenario' and config.market_scenario:
        from scripts.market_scenarios import generate_price_paths
        
        # Get price paths for the specified scenario
        avl_prices, eth_prices, btc_prices, lens_prices = generate_price_paths(
            n_periods=n_timesteps,
            initial_prices=config.initial_prices,
            annual_returns=config.annual_returns,
            annual_volatilities=config.annual_volatilities,
            correlation_matrix=config.correlation_matrix,
            regime_changes=config.regime_changes,
            seed=config.seed
        )
        
    else:
        # Generate individual price processes based on configuration
        if config.price_process_type == 'linear':
            avl_prices = create_linear_price_growth(
                starting_price=config.avl_initial_price,
                annual_increase_pct=config.avl_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            eth_prices = create_linear_price_growth(
                starting_price=config.eth_initial_price,
                annual_increase_pct=config.eth_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            btc_prices = create_linear_price_growth(
                starting_price=config.btc_initial_price,
                annual_increase_pct=config.btc_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            lens_prices = create_linear_price_growth(
                starting_price=config.lens_initial_price,
                annual_increase_pct=config.lens_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            
        elif config.price_process_type == 'compound':
            avl_prices = create_compound_price_growth(
                starting_price=config.avl_initial_price,
                annual_growth_rate=config.avl_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            eth_prices = create_compound_price_growth(
                starting_price=config.eth_initial_price,
                annual_growth_rate=config.eth_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            btc_prices = create_compound_price_growth(
                starting_price=config.btc_initial_price,
                annual_growth_rate=config.btc_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            lens_prices = create_compound_price_growth(
                starting_price=config.lens_initial_price,
                annual_growth_rate=config.lens_price_growth,
                timesteps=n_timesteps,
                dt=config.delta_time
            )
            
        elif config.price_process_type == 'trend_with_noise':
            avl_prices = create_trend_with_noise_price(
                starting_price=config.avl_initial_price,
                annual_trend_pct=config.avl_price_growth,
                volatility=config.price_volatility,
                timesteps=n_timesteps,
                dt=config.delta_time,
                seed=config.seed
            )
            eth_prices = create_trend_with_noise_price(
                starting_price=config.eth_initial_price,
                annual_trend_pct=config.eth_price_growth,
                volatility=config.price_volatility,
                timesteps=n_timesteps,
                dt=config.delta_time,
                seed=config.seed + 1
            )
            btc_prices = create_trend_with_noise_price(
                starting_price=config.btc_initial_price,
                annual_trend_pct=config.btc_price_growth,
                volatility=config.price_volatility,
                timesteps=n_timesteps,
                dt=config.delta_time,
                seed=config.seed + 2
            )
            lens_prices = create_trend_with_noise_price(
                starting_price=config.lens_initial_price,
                annual_trend_pct=config.lens_price_growth,
                volatility=config.price_volatility,
                timesteps=n_timesteps,
                dt=config.delta_time,
                seed=config.seed + 3
            )
            
        else:  # Brownian Motion
            avl_prices = create_stochastic_avail_price_process(
                timesteps=n_timesteps,
                dt=config.delta_time,
                rng=np.random.default_rng(config.seed),
                price_traj_type=config.price_traj_type,
                minimum_avl_price=config.minimum_price,
                target_avg=config.target_avg_price,
                maximum_avl_price=config.maximum_price,
                volatility=config.bm_volatility
            )
            eth_prices = create_stochastic_avail_price_process(
                timesteps=n_timesteps,
                dt=config.delta_time,
                rng=np.random.default_rng(config.seed + 1),
                price_traj_type=config.eth_price_traj_type,
                minimum_avl_price=config.eth_minimum_price,
                target_avg=config.eth_target_avg_price,
                maximum_avl_price=config.eth_maximum_price,
                volatility=config.eth_bm_volatility
            )
            btc_prices = create_stochastic_avail_price_process(
                timesteps=n_timesteps,
                dt=config.delta_time,
                rng=np.random.default_rng(config.seed + 2),
                price_traj_type=config.btc_price_traj_type,
                minimum_avl_price=config.btc_minimum_price,
                target_avg=config.btc_target_avg_price,
                maximum_avl_price=config.btc_maximum_price,
                volatility=config.btc_bm_volatility
            )
            lens_prices = create_stochastic_avail_price_process(
                timesteps=n_timesteps,
                dt=config.delta_time,
                rng=np.random.default_rng(config.seed + 3),
                price_traj_type=config.lens_price_traj_type,
                minimum_avl_price=config.lens_minimum_price,
                target_avg=config.lens_target_avg_price,
                maximum_avl_price=config.lens_maximum_price,
                volatility=config.lens_bm_volatility
            )
    
    return avl_prices, eth_prices, btc_prices, lens_prices


def prepare_simulation(
    config: SimulationConfig
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """Prepare simulation parameters based on configuration
    
    Args:
        config: Simulation configuration
        
    Returns:
        Tuple of (constants, initial_state, simulation_params)
    """
    # Generate price processes
    avl_price_samples, eth_price_samples, btc_price_samples, lens_price_samples = generate_price_process(config)
    
    # Calculate initial FDV (Fully Diluted Valuation)
    init_total_fdv = config.total_supply * config.avl_initial_price
    
    # Create constants dictionary
    constants = {
        "total_supply": config.total_supply,
        "init_total_fdv": init_total_fdv,
        "native_staking_ratio": config.native_staking_ratio,
    }
    
    # Create agent configuration
    agents = AgentStake.create_maxi_agents(
        target_composition=config.initial_agent_composition,
        total_tvl=config.initial_tvl,
        avl_price=config.avl_initial_price,
        eth_price=config.eth_initial_price,
        btc_price=config.btc_initial_price,
        restake_pcts={
            'avl_maxi': config.restaking,
            'eth_maxi': config.restaking,
            'btc_maxi': config.restaking
        },
        avl_lock_preferences=config.avl_lock_preferences
    )
    
    # Calculate initial rewards allocation
    rewards_result = calculate_reward_allocation(
        constants=constants,
        avl_price=config.avl_initial_price,
        total_tvl=config.initial_tvl,
        avl_stake_pct=config.initial_agent_composition.get('AVL', 0),
        target_avl_yield=config.target_avl_yield,
        target_eth_yield=config.target_eth_yield
    )
    
    # Create simulation parameters
    sim_params = FusionParams(
        constants=[constants],
        avl_price_samples=[avl_price_samples],
        eth_price_samples=[eth_price_samples],
        btc_price_samples=[btc_price_samples],
        lens_price_samples=[lens_price_samples],
        rewards_result=[rewards_result],
        agents=[agents],
        btc_activation_day=[config.btc_activation_day],
        
        # Inflation parameters
        inflation_decay=[config.inflation_decay],
        target_staking_rate=[config.target_staking_rate],
        min_inflation_rate=[config.min_inflation_rate],
        max_inflation_rate=[config.max_inflation_rate],
        
        # AVL Boosting parameters
        avl_boosting_enabled=[config.avl_boosting_enabled],
        avl_lock_period_multipliers=[config.avl_lock_period_multipliers],
        avl_pool_share_multipliers=[config.avl_pool_share_multipliers],
        
        # Yield targets
        target_yields=[{
            1: {"AVL": config.target_avl_yield, "ETH": config.target_eth_yield, "BTC": 0},
            config.btc_activation_day: {"AVL": config.target_avl_yield, "ETH": config.target_eth_yield, "BTC": config.target_btc_yield}
        }]
    ).__dict__
    
    # Initialize state
    initial_state = initialize_state(
        init_total_fdv=init_total_fdv,
        constants=constants,
        rewards_result=rewards_result,
        params=sim_params,
        restaking=config.restaking,
        seed=config.seed
    )
    
    return constants, initial_state, sim_params


def run_simulation(
    config: Optional[SimulationConfig] = None,
    **kwargs
) -> pd.DataFrame:
    """Run the Avail Fusion simulation with specified parameters
    
    Args:
        config: Simulation configuration object
        **kwargs: Override configuration parameters
        
    Returns:
        DataFrame with simulation results
    """
    # Create configuration if not provided
    if config is None:
        config = SimulationConfig(**kwargs)
    else:
        # Update config with any provided kwargs
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    # Prepare simulation
    constants, initial_state, sim_params = prepare_simulation(config)
    
    # Create model
    model = Model(
        initial_state=initial_state,
        state_update_blocks=psub,
        params=sim_params
    )
    
    # Configure and run simulation
    simulation = Simulation(
        model=model,
        timesteps=config.simulation_days,
        runs=1
    )
    
    experiment = Experiment([simulation])
    experiment.engine = Engine(deepcopy=True, backend=Backend.SINGLE_PROCESS)
    
    # Run experiment
    print(f"Running Avail Fusion simulation for {config.simulation_days} days...")
    results = experiment.run()
    df = pd.DataFrame(results)
    
    print("Simulation complete!")
    return df


def compare_simulations(
    base_config: SimulationConfig,
    comparison_configs: List[Dict[str, Any]],
    names: List[str] = None
) -> Dict[str, pd.DataFrame]:
    """Run multiple simulations for comparison
    
    Args:
        base_config: Base simulation configuration
        comparison_configs: List of parameter overrides for each comparison
        names: List of names for each simulation
        
    Returns:
        Dictionary mapping simulation names to result DataFrames
    """
    if names is None:
        names = [f"Simulation_{i}" for i in range(len(comparison_configs) + 1)]
    else:
        if len(names) != len(comparison_configs) + 1:
            raise ValueError("Number of names must match number of simulations (base + comparisons)")
    
    results = {}
    
    # Run base simulation
    print(f"Running {names[0]} (base simulation)...")
    results[names[0]] = run_simulation(config=base_config)
    
    # Run comparison simulations
    for i, (params, name) in enumerate(zip(comparison_configs, names[1:])):
        print(f"Running {name} (comparison {i+1}/{len(comparison_configs)})...")
        # Create a copy of the base config and update with comparison params
        config_copy = SimulationConfig(
            **{attr: getattr(base_config, attr) for attr in dir(base_config) 
               if not attr.startswith('_') and not callable(getattr(base_config, attr))}
        )
        
        # Update config with comparison parameters
        for key, value in params.items():
            setattr(config_copy, key, value)
        
        # Run simulation with updated config
        results[name] = run_simulation(config=config_copy)
    
    return results


def plot_simulation_results(df: pd.DataFrame, metrics: List[str] = None):
    """Plot key metrics from simulation results
    
    Args:
        df: Simulation results DataFrame
        metrics: List of metrics to plot
    """
    # Import visualization functions
    import visualizations
    
    # Default metrics to plot if none provided
    if metrics is None:
        metrics = ['token_price', 'total_security', 'yield_pct', 'staking_ratio',
                   'asset_tvl', 'pool_rewards_spent', 'staked_token_balances']
    
    # Create plots based on requested metrics
    for metric in metrics:
        if metric == 'token_price':
            # Extract token prices
            timesteps = df['timestep'].tolist()
            avl_prices = []
            
            for _, row in df.iterrows():
                # Get first agent to extract AVL price
                agents = row['agents']
                first_agent = next(iter(agents.values()))
                avl_prices.append(first_agent.assets['AVL'].price)
            
            # Plot token price
            plt.figure(figsize=(10, 6))
            plt.plot(timesteps, avl_prices)
            plt.title('AVL Token Price')
            plt.xlabel('Day')
            plt.ylabel('Price (USD)')
            plt.grid(True)
            plt.show()
        
        elif metric == 'total_security':
            # Plot total security (TVL)
            fig = visualizations.plot_total_security(df)
            pio.show(fig)

        elif metric == 'yield_pct':
            # Plot yields
            print("####### Yields #######")
            fig = visualizations.plot_yield_pct(df)
            pio.show(fig)
        
        elif metric == 'staking_ratio':
            # Plot staking ratios
            fig = visualizations.plot_staking_ratio_inflation_rate(df)
            pio.show(fig)
        
        elif metric == 'asset_tvl':
            # Plot asset TVL breakdown
            fig = visualizations.plot_asset_tvl_stacked(df)
            pio.show(fig)

        elif metric == 'pool_rewards_spent':
            # Plot pool rewards spent
            fig = visualizations.plot_pool_rewards_spent(df)
            pio.show(fig)

        elif metric == 'staked_token_balances':
            # Plot staked token balances
            fig = visualizations.plot_staked_token_balances(df)
            pio.show(fig)


def run_all_market_scenarios(
    base_config: SimulationConfig,
    metrics: List[str] = None,
    names: List[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Run simulations for all market scenarios defined in MARKET_SCENARIOS.
    
    Args:
        base_config: Base simulation configuration
        metrics: List of metrics to plot. If None, plots all available metrics.
        
    Returns:
        Dictionary mapping scenario names to their simulation results
    """
    # Create comparison configs for each market scenario
    comparison_configs = []
    scenario_names = []
    
    for scenario_name, scenario_params in MARKET_SCENARIOS.items():
        config = {
            'price_process_type': 'market_scenario',
            'market_scenario': scenario_name,
            'initial_prices': scenario_params.get('initial_prices', 0.7),
            'annual_returns': scenario_params.get('annual_returns', 0.2),
            'annual_volatilities': scenario_params.get('annual_volatilities', 0.2),
            'correlation_matrix': scenario_params.get('correlation_matrix', 0.7),
            'regime_changes': scenario_params.get('regime_changes', None)
        }
        
        if 'regime_changes' in scenario_params:
            config['regime_changes'] = scenario_params['regime_changes']
            
        comparison_configs.append(config)
        scenario_names.append(scenario_name)
    
    # Use provided names or default to scenario names
    if names is None:
        names = scenario_names
    else:
        names += scenario_names

    
    # Run comparison simulations
    results = compare_simulations(
        base_config=base_config,
        comparison_configs=comparison_configs,
        names=names
    )
    
    
    return results


# Example usage in notebook:
if __name__ == "__main__":
    # Simple example of running a simulation
    config = SimulationConfig(
        simulation_days=365*2,
        avl_initial_price=0.1,
        eth_initial_price=3000,
        restaking=1.0
    )
    
    results = run_simulation(config)
    plot_simulation_results(results) 