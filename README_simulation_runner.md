# Avail Fusion Simulation Runner

This module provides a streamlined interface for running Avail Fusion staking economy simulations. It encapsulates the simulation setup and execution process from `cold-start-analysis.ipynb` into reusable functions.

## Features

- Clean API for configuring and running simulations
- Flexible parameter configuration via `SimulationConfig` class
- Support for multiple price process models (linear, compound, trend with noise, and Brownian Motion)
- Built-in visualization functions
- Ability to run and compare multiple simulation scenarios with overlaid plots
- Advanced comparison visualization tools for in-depth analysis
- Full access to the underlying cadCAD simulation framework

## Installation

No additional installation is required beyond the base project dependencies. The simulation runner works with the existing Avail Fusion codebase.

## Usage

### Basic Usage

```python
import simulation_runner as sim

# Run a simulation with default parameters
results = sim.run_simulation()

# Visualize results
sim.plot_simulation_results(results)
```

### Custom Configuration

```python
# Create a custom configuration
config = sim.SimulationConfig(
    # Simulation timeframe
    simulation_days=365,  # 1 year
    
    # Initial prices
    avl_initial_price=0.1,
    eth_initial_price=3000,
    btc_initial_price=80000,
    
    # Price process
    price_process_type='compound',
    avl_price_growth=0.5,  # 50% annual growth
    
    # Yield targets
    target_avl_yield=0.15,  # 15% APY for AVL stakers
    target_eth_yield=0.035, # 3.5% APY for ETH stakers
    
    # Agent parameters
    initial_tvl=1_000_000,  # $1M initial TVL
    restaking=1.0,  # 100% restaking
)

# Run simulation with custom config
results = sim.run_simulation(config)
```

### Using Brownian Motion Price Process

The simulation runner now supports a Brownian Motion ('BM') price process type for more realistic price modeling of all assets (AVL, ETH, BTC, and LENS):

```python
# Create a configuration using Brownian Motion for all assets
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
    price_traj_type='convex',      # 'convex', 'concave', or 'none'
    minimum_price=0.05,            # Minimum possible price
    maximum_price=0.5,             # Maximum possible price
    target_avg_price=0.2,          # Target average price across simulation
    bm_volatility=1.2,             # Controls randomness (higher = more volatile)
    
    # ETH Brownian Motion parameters
    eth_price_traj_type='concave', # Different trend type for ETH
    eth_minimum_price=1200,        # ETH-specific price floor
    eth_maximum_price=2000,        # ETH-specific price ceiling
    eth_target_avg_price=1600,     # Target average ETH price
    eth_bm_volatility=0.8,         # Lower volatility for ETH
    
    # BTC Brownian Motion parameters
    btc_price_traj_type='none',    # Pure random walk for BTC
    btc_minimum_price=70000,       # BTC-specific price floor
    btc_maximum_price=100000,      # BTC-specific price ceiling  
    btc_target_avg_price=85000,    # Target average BTC price
    btc_bm_volatility=0.6,         # Even lower volatility for BTC
    
    # LENS Brownian Motion parameters (optional)
    lens_price_traj_type='convex',
    lens_minimum_price=0.8,
    lens_maximum_price=1.5,
    lens_target_avg_price=1.1,
    lens_bm_volatility=1.0,
    
    # Other parameters
    restaking=1.0
)

# Run simulation with Brownian Motion price model for all assets
results = sim.run_simulation(config)
```

This allows you to create rich market scenarios with different price movements for each asset, such as:
- A bullish trend for AVL (convex) with high volatility
- A bearish trend for ETH (concave) with medium volatility  
- A random walk for BTC with low volatility
- Different parameter ranges for each asset

### Comparing Multiple Scenarios

The simulation runner now includes built-in support for comparing multiple scenarios with overlaid plots. This makes it easy to visualize the impact of different parameters on the system.

```python
# Base configuration
base_config = sim.SimulationConfig(restaking=1.0)

# Define comparison configurations
comparisons = [
    {'restaking': 0.5},  # 50% restaking
    {'restaking': 0.0}   # 0% restaking
]

# Run comparisons
results = sim.compare_simulations(
    base_config=base_config,
    comparison_configs=comparisons,
    names=["Full_Restaking", "Half_Restaking", "No_Restaking"],
    auto_plot=True  # Automatically plot results
)

# Access individual results
for name, df in results.items():
    print(f"Results for {name}:")
    # Process individual scenario results
```

#### Built-in Comparison Plotting

The `plot_simulation_results` function now accepts either a single DataFrame or a dictionary of scenario DataFrames for direct comparison:

```python
# Plot results from multiple scenarios on the same graphs
sim.plot_simulation_results(results)
```

This will automatically create comparison plots for key metrics like token price, total security (TVL), agent yields, and staking ratios.

### Enhanced Comparison Visualization

For more advanced comparison analysis, you can use the specialized comparison plots module:

```python
import visualizations.comparison_plots as comp_plots

# Create a comprehensive dashboard comparing all scenarios
comp_plots.plot_comparison_dashboard(results)

# Compare yields across scenarios
comp_plots.plot_yields_comparison(results)

# Compare accumulated rewards
comp_plots.plot_rewards_comparison(results)

# Compare asset-specific TVL
comp_plots.plot_asset_tvl_comparison(results, asset='AVL')
comp_plots.plot_asset_tvl_comparison(results, asset='ETH')

# Compare staking ratios and inflation rates
comp_plots.plot_staking_inflation_comparison(results)
```

These specialized functions provide more detailed and customized visualizations for in-depth analysis of the differences between scenarios.

## Multi-Factor Comparison Study

You can conduct complex comparison studies with multiple varying factors:

```python
# Base configuration
base_config = sim.SimulationConfig(
    simulation_days=365,
    avl_initial_price=0.1,
    restaking=1.0
)

# Define multiple comparison configurations
comparisons = [
    # No restaking
    {'restaking': 0.0},
    
    # Partial restaking
    {'restaking': 0.5},
    
    # Different asset composition
    {'initial_agent_composition': {'AVL': 0.7, 'ETH': 0.3, 'BTC': 0.0}},
    
    # Higher yield targets
    {'target_avl_yield': 0.2, 'target_eth_yield': 0.05}
]

# Define scenario names
names = ["Baseline", "No_Restaking", "50pct_Restaking", 
         "Higher_AVL_Allocation", "Higher_Yield_Targets"]

# Run all simulations and compare
results = sim.compare_simulations(
    base_config=base_config,
    comparison_configs=comparisons,
    names=names
)

# Create comprehensive dashboard visualization
comp_plots.plot_comparison_dashboard(results)
```

## Configuration Parameters

The `SimulationConfig` class accepts the following parameters:

### Simulation Timeframe
- `simulation_days`: Number of days to simulate (default: 365)
- `delta_time`: Time step size in years (default: DELTA_TIME from config)

### Initial Prices
- `avl_initial_price`: Initial AVL token price (default: 0.1)
- `eth_initial_price`: Initial ETH price (default: 3000)
- `btc_initial_price`: Initial BTC price (default: 80000)
- `lens_initial_price`: Initial LENS price (default: 1.0)

### Price Process Parameters
- `price_process_type`: Type of price process model ('linear', 'compound', 'trend_with_noise', or 'BM')
- `avl_price_growth`: Annual growth rate for AVL price (default: 0.5)
- `eth_price_growth`: Annual growth rate for ETH price (default: 0.0)
- `btc_price_growth`: Annual growth rate for BTC price (default: 0.0)
- `lens_price_growth`: Annual growth rate for LENS price (default: 0.0)
- `price_volatility`: Volatility parameter for 'trend_with_noise' process (default: 0.2)

### Brownian Motion Parameters
- `price_traj_type`: Trajectory type for BM process ('convex', 'concave', or 'none') (default: 'convex')
- `minimum_price`: Minimum possible price in BM process (default: 50% of initial price)
- `maximum_price`: Maximum possible price in BM process (default: 200% of initial price)
- `target_avg_price`: Target average price across the simulation (default: initial price)
- `bm_volatility`: Volatility parameter for BM process (higher = more randomness) (default: 1.0)

### Tokenomics Parameters
- `total_supply`: Total AVL token supply (default: 10 billion)
- `native_staking_ratio`: Initial staking ratio (default: 0.5)

### Yield Targets
- `target_avl_yield`: Target yield for AVL stakers (default: 0.15)
- `target_eth_yield`: Target yield for ETH stakers (default: 0.035)
- `target_btc_yield`: Target yield for BTC stakers (default: 0.05)

### Agent Parameters
- `initial_tvl`: Initial total value locked (default: $1M)
- `initial_agent_composition`: Asset allocation for agents (default: {'AVL': 0.33, 'ETH': 0.67, 'BTC': 0.0})
- `restaking`: Restaking percentage (default: 1.0)

### Inflation Parameters
- `inflation_decay`: Inflation decay parameter (default: 0.05)
- `target_staking_rate`: Target staking rate (default: 0.5)
- `min_inflation_rate`: Minimum inflation rate (default: 0.01)
- `max_inflation_rate`: Maximum inflation rate (default: 0.05)

### BTC Activation
- `btc_activation_day`: Day when BTC pool is activated (default: 180)

### Security Budget
- `initial_security_budget`: Initial security budget in AVL tokens (default: 30 billion)

### Random Seed
- `seed`: Random seed for reproducibility (default: 42)

### Brownian Motion Parameters for AVL
- `price_traj_type`: Trajectory type for BM process ('convex', 'concave', or 'none') (default: 'convex')
- `minimum_price`: Minimum possible price in BM process (default: 50% of initial price)
- `maximum_price`: Maximum possible price in BM process (default: 200% of initial price)
- `target_avg_price`: Target average price across the simulation (default: initial price)
- `bm_volatility`: Volatility parameter for BM process (higher = more randomness) (default: 1.0)

### Brownian Motion Parameters for ETH
- `eth_price_traj_type`: Trajectory type for ETH BM process (default: 'convex')
- `eth_minimum_price`: Minimum possible ETH price (default: 50% of initial ETH price)
- `eth_maximum_price`: Maximum possible ETH price (default: 200% of initial ETH price)
- `eth_target_avg_price`: Target average ETH price (default: initial ETH price)
- `eth_bm_volatility`: Volatility parameter for ETH price (default: 1.0)

### Brownian Motion Parameters for BTC
- `btc_price_traj_type`: Trajectory type for BTC BM process (default: 'convex')
- `btc_minimum_price`: Minimum possible BTC price (default: 50% of initial BTC price)
- `btc_maximum_price`: Maximum possible BTC price (default: 200% of initial BTC price)
- `btc_target_avg_price`: Target average BTC price (default: initial BTC price)
- `btc_bm_volatility`: Volatility parameter for BTC price (default: 1.0)

### Brownian Motion Parameters for LENS
- `lens_price_traj_type`: Trajectory type for LENS BM process (default: 'convex')
- `lens_minimum_price`: Minimum possible LENS price (default: 50% of initial LENS price)
- `lens_maximum_price`: Maximum possible LENS price (default: 200% of initial LENS price)
- `lens_target_avg_price`: Target average LENS price (default: initial LENS price)
- `lens_bm_volatility`: Volatility parameter for LENS price (default: 1.0)

## Available Comparison Plot Functions

The `visualizations.comparison_plots` module includes the following specialized functions for comparing multiple scenarios:

1. `plot_token_prices_comparison`: Compare token prices across scenarios
2. `plot_security_comparison`: Compare TVL across scenarios
3. `plot_yields_comparison`: Compare yields for each agent type
4. `plot_staking_inflation_comparison`: Compare staking ratios and inflation rates
5. `plot_tvl_asset_distribution`: Compare asset distribution within each scenario
6. `plot_asset_tvl_comparison`: Compare specific asset TVL across scenarios
7. `plot_rewards_comparison`: Compare accumulated rewards by agent type
8. `plot_comparison_dashboard`: Create a comprehensive dashboard of key metrics
9. `plot_avl_staking_ratio_comparison`: Compare AVL staking ratio to Fusion across scenarios
10. `plot_asset_staking_ratio_comparison`: Compare staking ratio for a specific asset across scenarios

### Analyzing Asset Staking Ratios

The new staking ratio comparison functions allow you to analyze how different assets are staked within the Fusion ecosystem across various simulation scenarios:

```python
# Compare AVL staking ratio to Fusion across scenarios
comp_plots.plot_avl_staking_ratio_comparison(results)

# Compare staking ratio for a specific asset across scenarios
comp_plots.plot_asset_staking_ratio_comparison(results, asset='ETH')
comp_plots.plot_asset_staking_ratio_comparison(results, asset='BTC')
```

These functions are particularly useful for understanding how different parameters (like restaking percentages, price trajectories, or yield targets) affect the contribution of each asset to the overall security of the Fusion ecosystem.

## Example Notebook

See `avail_fusion_simulation.ipynb` for a comprehensive example of using the simulation runner for various analyses, including comparison studies.

## Example Script

The `example_simulation.py` file provides sample code for:
- Running basic simulations
- Comparing restaking scenarios with overlaid plots
- Running multi-scenario comparisons
- Configuring and running advanced simulations

## Advanced Usage

The simulation runner is built on top of the cadCAD framework and the existing Avail Fusion simulation codebase. Advanced users can access the underlying components for further customization:

```python
from config.psub import psub  # State update blocks
from config.params import FusionParams  # Parameter structure
from model.agents_class import AgentStake  # Agent model
from model.stochastic_processes import create_linear_price_growth  # Price process models
```