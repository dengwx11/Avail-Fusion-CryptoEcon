# Avail-Fusion-CryptoEcon
This repository contains a simulation framework for modeling the Avail Fusion staking economy. The simulation uses cadCAD to model the dynamics of staking pools, rewards allocation, and participant behavior.
## 1. Setting Up the Environment
### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- git (to clone the repository)
### Creating a Virtual Environment

```
# Clone the repository
git clone https://github.com/dengwx11/Avail-Fusion-CryptoEcon.git
cd Avail-Fusion-CryptoEcon

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```


### Verifying Installation
To verify that everything is installed correctly, you can run a simple test:
)
```
# Start Python interpreter
python

# Import cadCAD and check version
>>> import cadCAD
>>> cadCAD.__version__
'0.5.3'  # Should match the version in requirements.txt

# Exit Python interpreter
>>> exit()
```

## 2. Configuring Simulation Parameters
The simulation parameters are defined in `config/params.py`. This file contains the `FusionParams` dataclass which controls various aspects of the simulation.
### Key Parameter Categories
#### Pool Configurations
Pool configurations control the deposit/withdrawal behavior for each asset type:
```
# Edit in config/params.py
initial_pool_configs: List[Dict] = default([{
    'AVL': {
        'base_deposit': 5e4,         # Base daily deposit in USD
        'max_extra_deposit': 5e5,    # Maximum additional deposit based on APY
        'deposit_k': 5.0,            # Deposit sigmoid steepness parameter
        'apy_threshold': 0.10,       # Target APY threshold for deposit function
        'base_withdrawal': 5e3,      # Base daily withdrawal in USD
        'max_extra_withdrawal': 3e5, # Maximum additional withdrawal based on APY
        'withdrawal_k': 7.0,         # Withdrawal sigmoid steepness parameter
        'max_cap': float('inf')      # Maximum pool size (USD)
    },
    # Similarly for 'ETH' pool
}])

# BTC pool configuration (activated on BTC activation day)
btc_pool_config: List[Dict] = default([{
    'base_deposit': 1e5,
    # ... other parameters
}])
```
#### Security Budget Replenishment
Control how and when new tokens are added to the security budget for each pool:
```
security_budget_replenishment: List[Dict] = default([
    {
        30: {'AVL': 4e6, 'ETH': 1e6},      # Day 30: Add 4M to AVL pool, 1M to ETH pool
        60: {'AVL': 3e6, 'ETH': 2e6},      # Day 60: Add 3M to AVL pool, 2M to ETH pool
        # ... additional replenishment events
        180: {'AVL': 5e6, 'ETH': 2e6, 'BTC': 3e6}  # Day 180: Include BTC pool
    }
])
```
#### Target Yields
Set the target yields (APY) for each pool at different timesteps:
```
target_yields: List[Dict] = default([
    {
        1: {"AVL": 0.15, "ETH": 0.035, "BTC": 0},  # Initial yields
        50: {"AVL": 0.15, "ETH": 0.1, "BTC": 0}    # Change yields on day 50
    }
])
```
#### Admin Actions
Control admin interventions like pausing/resuming deposits or deleting pools:
```
# Pause deposits for specific pools at specific timesteps
admin_pause_deposits: List[Dict] = default([
    {30: ['ETH']}  # Pause ETH deposits on day 30
])

# Resume deposits
admin_resume_deposits: List[Dict] = default([
    {50: ['ETH']}  # Resume ETH deposits on day 50
])

# Delete pools
admin_delete_pools: List[Dict] = default([
    {100: ['ETH']}  # Delete ETH pool on day 100
])
```
#### Setting BTC Activation Day
The BTC activation day is set in the simulation setup. This controls when the BTC staking pool becomes active:
```
# This would typically be set in the simulation setup
params = FusionParams(
    # ...other parameters...
    btc_activation_day=[180]  # BTC will activate on day 180
)

# ...other code...
security_budget_replenishment: List[Dict] = default([
        {
            ...other replenishment schedule---
            180: {'AVL': 5e6, 'ETH': 2e6, 'BTC': 3e6} 
            # Add AVL rewards to new BTC pool when it's activated.
        }
    ])
```
## 3. Running the Simulation with cold-start-analysis.ipynb
### Starting Jupyter Notebook

Navigate to and open `cold-start-analysis.ipynb`.

### Setting Up the Simulation in the Notebook
The notebook contains a Setup section where you can configure your simulation run. Here's how to set up the key parameters (part of the simulation params could be found in `config/config.py`):
```
# In the Setup cell of cold-start-analysis.ipynb

# Set simulation parameters
RUNS = 1                    # Number of simulation runs
TIMESTEPS = 365             # Number of days to simulate
DELTA_TIME = 1              # Time step in days
MONTE_CARLO_RUNS = 1        # Number of Monte Carlo runs

# Initial TVL estimation
init_tvl_usd = 5e6          # Initial TVL in USD

# Other parameters
constants = {
    "total_supply": 1e9,                  # Total AVL token supply
    "native_staking_ratio": 0.1,          # Initial native staking ratio
    "init_total_fdv": init_total_fdv,     # Total FDV in usd
}

# Create parameter object
from config.params import FusionParams

params = FusionParams(
    constants=[constants],
    avl_price_samples=[avl_price],
    eth_price_samples=[eth_price],
    btc_price_samples=[btc_price],
    lens_price_samples=[lens_price],
    rewards_result=[rewards_result],
    agents=[agents],
    btc_activation_day=[btc_activation_day]
)

# Initialize state
from config.initialize_simulation import initialize_state
initial_state = initialize_state(
    init_total_fdv=init_fdv, 
    constants=constants, 
    rewards_result=rewards_result,
    params=params,
    seed=42
)
```
#### Running the Simulation
After setting up parameters, execute the simulation cell:
```
# Run simulation
model = Model(
    initial_state=initial_conditions,
    state_update_blocks=psub,
    params=params
)

simulation=Simulation(model=model, timesteps=600, runs=1)
experiment = Experiment([simulation])
experiment.engine = Engine(deepcopy=True, backend=Backend.SINGLE_PROCESS)
results  = experiment.run()
```
### Analyzing Results
The notebook contains various cells for analyzing and visualizing simulation results. You can plot metrics like:
* TVL over time
* APY/yields for each asset-maxi agent
* Budget utilization
* Staking ratios
* Token prices and their effects


## Troubleshooting
If you encounter issues:
* Check that all dependencies are installed correctly
* Ensure your Python version is compatible
* Verify that the parameter configurations are valid
* Check for errors in the simulation logs
* Restart the Jupyter kernel if the notebook becomes unresponsive
For specific errors, consult the cadCAD documentation or open an issue in the repository.