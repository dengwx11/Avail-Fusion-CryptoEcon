"""
Simulation Configuration Parameters

This module defines the configuration parameters for simulation runs.
"""

import numpy as np
from config.config import TIMESTEPS, DELTA_TIME

# Extend the main config with simulation-specific parameters
SIM_TIMESTEPS = 730  # 2 years of daily timesteps
SIM_DELTA_TIME = 1   # 1 day per timestep

# Price volatility analysis configuration
VOLATILITY_ANALYSIS = {
    'base_avl_price': 0.1,            # Base AVL price
    'pct_changes': np.arange(-0.9, 2.01, 0.1),  # -90% to +200% in 10% increments
    'strike_days': [100, 200, 500],    # Days to apply price shocks
    'post_shock_analysis_days': 30,    # Days to analyze after shock
}

# Run configuration
MONTE_CARLO_RUNS = 5                  # Number of Monte Carlo runs
RNG_SEED = 42                         # Seed for reproducibility

# Pool configuration for volatility analysis
POOL_CONFIG = {
    'AVL': {
        'target_yield': 0.15,         # 15% target yield
        'initial_budget_share': 0.7,  # 70% of initial budget
    },
    'ETH': {
        'target_yield': 0.035,        # 3.5% target yield
        'initial_budget_share': 0.3,  # 30% of initial budget
    },
    'BTC': {
        'target_yield': 0.02,         # 2% target yield
        'initial_budget_share': 0.0,  # Activated later
        'activation_day': 180,        # BTC pool activation day
    }
}

# TVL response model parameters
TVL_RESPONSE = {
    'price_elasticity': {
        'increase': 0.5,              # TVL increases with sqrt of price increases
        'decrease': 1.2,              # TVL decreases faster than price decreases
    },
    'panic_threshold': -0.5,          # >50% price drop may trigger panic
    'panic_withdrawal_rate': 0.1,     # 10% daily withdrawal during panic
    'growth_cap_days': 30,            # Caps growth effect after 30 days
}

# Visualization settings
VISUALIZATION = {
    'color_schemes': {
        'price_changes': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', 
                         '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850'],
        'tvl': 'viridis',
        'budget': 'plasma',
        'panic': 'YlOrRd',
    },
    'plot_dpi': 300,
    'file_formats': ['png', 'pdf'],
}

def get_replenishment_schedule():
    """Return the security budget replenishment schedule"""
    schedule = {
        30: {'AVL': 4e6, 'ETH': 1e7},
        60: {'AVL': 10e6, 'ETH': 2e7},
        90: {'AVL': 3e6, 'ETH': 2e7},
        120: {'AVL': 13e6, 'ETH': 2e7},
        150: {'AVL': 13e6, 'ETH': 12e6},
        180: {'AVL': 15e6, 'ETH': 2e6, 'BTC': 9e7},
        210: {'AVL': 5e6, 'ETH': 12e6, 'BTC': 3e6},
        240: {'AVL': 25e6, 'ETH': 2e6, 'BTC': 3e6},
        270: {'AVL': 15e6, 'ETH': 12e6, 'BTC': 3e6},
        300: {'AVL': 38e6, 'ETH': 2e6, 'BTC': 3e6},
        330: {'AVL': 18e6, 'ETH': 12e6, 'BTC': 3e6},
        360: {'AVL': 38e6, 'ETH': 2e6, 'BTC': 3e6},
        390: {'AVL': 18e6, 'ETH': 12e6, 'BTC': 3e6},
        420: {'AVL': 38e6, 'ETH': 2e6, 'BTC': 3e6},
        450: {'AVL': 18e6, 'ETH': 12e6, 'BTC': 3e6},
        480: {'AVL': 28e6, 'ETH': 2e6, 'BTC': 3e6},
        510: {'AVL': 38e6, 'ETH': 12e6, 'BTC': 3e6},
        540: {'AVL': 38e6, 'ETH': 2e6, 'BTC': 3e6}
    }
    return schedule 