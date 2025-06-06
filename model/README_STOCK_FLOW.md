# Stock-Flow Consistent Model for Staking Flows

## Overview

This README explains the implementation of a stock-flow consistent model for simulating staking inflows and outflows in the Avail Fusion CryptoEcon model. The model is designed to realistically capture how staking behavior responds to:

- **Price Dynamics**: How token price changes affect staking decisions
- **Market Sentiment**: General market mood (bullish/bearish)
- **Yield Attractiveness**: How APY affects deposit and withdrawal decisions
- **Liquidity Constraints**: How TVL impacts flow dynamics

The model has been fully integrated into the simulation framework, replacing the previous sigmoid-based approach.

## Key Components

The stock-flow model consists of the following key components:

1. **`StakingFlowModel` Class**: Core implementation of the stock-flow consistent model (in `model/stock_flow_model.py`)
2. **`PoolManager` Class**: Enhanced to use the stock-flow model (in `model/pool_management.py`) 
3. **`policy_cold_start_staking` Function**: Updated to process flows using the stock-flow approach (in `model/cold_start.py`)

## How It Works

The stock-flow model calculates deposit and withdrawal flows using these key calculations:

1. **Price Momentum**:
   - Calculates the normalized price change between current and previous price
   - Uses a sigmoid function to keep momentum values between -1 and 1
   - Rising prices create positive momentum (encouraging deposits)
   - Falling prices create negative momentum (encouraging withdrawals)

2. **Effective APY**:
   - Adjusts the perceived APY based on market conditions
   - In bullish markets, even lower APYs seem attractive
   - In bearish markets, higher APYs are needed to attract stakers

3. **Liquidity Constraints**:
   - Models how TVL affects flow dynamics
   - Small pools (<$1M) have more volatile flows
   - Large pools (>$1B) have reduced sensitivity to price changes

4. **Inflow Calculation**:
   - Base inflow rate (e.g., 1% of TVL daily)
   - Adjusted by price momentum (positive momentum increases inflows)
   - Adjusted by APY differential (higher than threshold APY increases inflows)
   - Adjusted by market sentiment (positive sentiment increases inflows)

5. **Outflow Calculation**:
   - Base outflow rate (e.g., 0.5% of TVL daily)
   - Adjusted by inverse price momentum (negative momentum increases outflows)
   - Adjusted by inverse APY differential (lower than threshold APY increases outflows)
   - Adjusted by inverse market sentiment (negative sentiment increases outflows)

## Usage

The stock-flow model is now the default model for calculating staking flows. To configure it for your simulation:

1. **Set Pool Configuration**:
   ```python
   POOL_CONFIG = {
       'AVL': {
           'price_sensitivity': 0.5,        # Sensitivity to price changes (0-1)
           'apy_sensitivity': 10.0,         # Sensitivity to APY differentials (0-20)
           'momentum_factor': 2.0,          # How much momentum affects flows (0-3)
           'liquidity_factor': 0.8,         # Impact of TVL on flow dynamics (0-1)
           'base_inflow_rate': 0.01,        # 1% daily base inflow
           'base_outflow_rate': 0.005,      # 0.5% daily base outflow
           'apy_threshold': 0.10,           # 10% APY threshold for attractiveness
       }
   }
   ```

2. **Run a Price Shock Experiment**:
   ```python
   # Create price scenarios
   base_scenario = {
       'AVL': create_price_scenario(days, 1.0, volatility=0.01)
   }
   shock_scenario = {
       'AVL': create_price_shock_scenario(days, 1.0, shock_day=90, shock_size=-0.4)
   }
   
   # Run simulations
   base_results = run_stock_flow_experiment(price_process=base_scenario)
   shock_results = run_stock_flow_experiment(price_process=shock_scenario)
   
   # Compare results
   scenarios = {
       "Base Scenario": base_results,
       "Price Shock": shock_results
   }
   comp_plots.plot_total_value_locked_comparison(scenarios)
   ```

## Configuration Parameters

### Market Behavior Parameters

- **`price_sensitivity`**: How much price changes affect flows (0-1)
  - Higher values mean staking/unstaking are more responsive to price changes
  - Lower values mean behavior is less tied to price movements

- **`apy_sensitivity`**: How responsive deposits/withdrawals are to APY (0-20)
  - Higher values mean small changes in APY have large effects
  - Lower values mean APY has less impact on behavior

- **`momentum_factor`**: How much weight price momentum has (0-3)
  - Higher values amplify the effect of recent price trends
  - Lower values reduce the impact of price trends

- **`liquidity_factor`**: Base scaling factor for flow calculations (0-1)
  - Higher values mean more liquidity is available for staking
  - Lower values mean liquidity is more constrained

### Flow Rate Parameters

- **`base_inflow_rate`**: Base daily inflow as percentage of TVL (0-0.05)
  - Represents the natural rate of new deposits in neutral conditions

- **`base_outflow_rate`**: Base daily outflow as percentage of TVL (0-0.05)
  - Represents the natural rate of withdrawals in neutral conditions

- **`apy_threshold`**: APY level considered attractive enough to drive deposits (0-0.2)
  - APY above this threshold increases deposits
  - APY below this threshold increases withdrawals

## Market Sentiment

Market sentiment represents the general mood of the market (bullish or bearish) and is represented as a value from -1 (extremely bearish) to 1 (extremely bullish). It affects:

- How attractive a given APY is perceived
- Base inflow and outflow rates
- Price momentum impact

You can update market sentiment in your simulation parameters:

```python
MARKET_SENTIMENT = {
    0: {  # Initial sentiment (day 0)
        'AVL': 0.8,   # Bullish
        'ETH': 0.2,   # Slightly bullish
        'BTC': 0.1    # Nearly neutral
    },
    90: {  # Update sentiment on day 90
        'AVL': 0.4,
        'ETH': 0.3,
        'BTC': 0.2
    }
}
```

Or programmatically calculate it based on price movements:

```python
def update_sentiment_based_on_price(price_history, window=7):
    # Calculate recent price momentum
    recent_prices = price_history[-window:]
    oldest_price = price_history[-window-1]
    
    # Average price change over the window
    avg_change = np.mean([(price / oldest_price) - 1 for price in recent_prices])
    
    # Map significant price changes to sentiment between -1 and 1
    sentiment = 2 / (1 + np.exp(-10 * avg_change)) - 1
    
    return sentiment
```

## Mathematical Model

### Key Equations

1. **Price Momentum**:
   ```
   momentum = 2.0 / (1.0 + exp(-momentum_factor * price_change_pct)) - 1.0
   ```

2. **Effective APY**:
   ```
   effective_apy = current_apy + (market_sentiment * 0.05)
   ```

3. **Inflow Rate**:
   ```
   inflow_rate = base_inflow + apy_component + price_component + sentiment_component
   ```
   where:
   - `apy_component` increases with (effective_apy - apy_threshold)
   - `price_component = price_sensitivity * price_momentum * 0.05`
   - `sentiment_component = market_sentiment * 0.01`

4. **Outflow Rate**:
   ```
   outflow_rate = base_outflow + apy_outflow_component + price_outflow_component + sentiment_outflow_component
   ```
   where components have inverse relationships to their inflow counterparts.

5. **Deposit Flow**:
   ```
   deposit_flow = inflow_rate * current_tvl
   ```

6. **Withdrawal Flow**:
   ```
   withdrawal_flow = outflow_rate * current_tvl
   ```

## Integration with Visualization Tools

The stock-flow model outputs include:

1. **TVL Over Time**: Track how Total Value Locked changes in response to price dynamics
2. **Staking Ratio**: The percentage of circulating supply that is staked
3. **Deposit and Withdrawal Flows**: Daily flows into and out of the staking pools

These metrics can be visualized using the existing visualization tools:

```python
comp_plots.plot_total_value_locked_comparison(scenarios)
comp_plots.plot_staking_ratio_comparison(scenarios, assets=['AVL'])
```

## Implementation Details

For detailed implementation, refer to these files:

1. `model/stock_flow_model.py`: Core implementation of the model
2. `model/pool_management.py`: Integration with pool management system
3. `model/cold_start.py`: Flow processing in the simulation
4. `experiments/stock_flow_experiment.py`: Example experiment with price shocks 