from dataclasses import dataclass, field
from model.utils import default
from typing import List, Callable, Dict
from model.agents_class import AgentStake


from config.config import COLD_START_DURATION_TIMESTEPS



@dataclass
class FusionParams:
    """Dynamic simulation parameters with dependency injection for multiple runs"""
    
    ### External dependencies (list of dictionaries for multiple runs) ###
    constants: List[Dict]
    avl_price_samples: List[List[float]]  # Price samples per run
    eth_price_samples: List[List[float]]  # Price samples per run
    btc_price_samples: List[List[float]]  # Price samples per run
    lens_price_samples: List[List[float]]  # Price samples per run
    rewards_result: List[Dict]
    agents: List[AgentStake]
    btc_activation_day: List[int]

    ### Derived parameters (initialized in post_init) ###
    native_staking_ratio: List[float] = field(init=False)
    avl_price_process: List[Callable[[int, int], float]] = field(init=False)
    eth_price_process: List[Callable[[int, int], float]] = field(init=False)

    ### ADMIN: fusion pallete ###
    target_yields: List[Dict] = default([
        {1: {"AVL": 0.15, "ETH": 0.035, "BTC": 0}, 50: {"AVL": 0.15, "ETH": 0.035, "BTC": 0},
         180: {"AVL": 0.15, "ETH": 0.035, "BTC": 0.02}}  # BTC target yield
    ])
    # Security budget replenishment schedule
    # Dictionary mapping timestep to pool-specific token allocations
    security_budget_replenishment: List[Dict] = default([
        {
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
    ])
    # Admin actions to pause deposits or delete pools
    # admin_pause_deposits: List[Dict] = default([
    #     {30: ['ETH']} 
    # ]) # remain APY

    # admin_resume_deposits: List[Dict] = default([
    #     {50: ['ETH']} 
    # ])

    # admin_delete_pools: List[Dict] = default([
    #     {100: ['ETH']} 
    # ]) # APY = 0%


    ### Inflation function parameters (Polkadot) ###
    inflation_decay: List[float] = default([0.05])
    target_staking_rate: List[float] = default([0.5])
    min_inflation_rate: List[float] = default([0.01])
    max_inflation_rate: List[float] = default([0.05])

    ### After cold start, no more new tokens are added ###
    COLD_START_DURATION_TIMESTEPS: List[int] = default([365])
    COLD_START_BOOST_FACTOR: List[float] = default([1])


    ### Pool Manager config ###
    # BTC pool configuration - will be used when BTC is activated
    btc_pool_config: List[Dict] = default([{
        'base_deposit': 1e5,
        'max_extra_deposit': 4e5,
        'deposit_k': 6.0,
        'apy_threshold': 0.02,  # 2%
        'base_withdrawal': 8e3,
        'max_extra_withdrawal': 2e5,
        'withdrawal_k': 9.0,
        'max_cap': float('inf')
    }])

    # Initial pool configurations during cold start
    initial_pool_configs: List[Dict] = default([{
        'AVL': {
            'base_deposit': 5e4,
            'max_extra_deposit': 5e5,
            'deposit_k': 5.0,
            'apy_threshold': 0.15,
            'base_withdrawal': 5e3,
            'max_extra_withdrawal': 3e5,
            'withdrawal_k': 7.0,
            'max_cap': float('inf')
        },
        'ETH': {
            'base_deposit': 3e4,
            'max_extra_deposit': 5e4,
            'deposit_k': 8.0,
            'apy_threshold': 0.035,
            'base_withdrawal': 1e4,
            'max_extra_withdrawal': 3e4,
            'withdrawal_k': 10.0,
            'max_cap': 100e6 # in USD
        }
    }])
    
    # Post-cold-start pool configurations (applied after cold start period ends)
    post_cold_start_pool_configs: List[Dict] = default([{
        'AVL': {
            'base_deposit': 2e4,  # Reduced base deposit after cold start
            'max_extra_deposit': 3e5,  # Reduced max extra deposit
            'deposit_k': 7.0,     # Higher sensitivity (steeper curve)
            'apy_threshold': 0.12, # Adjusted APY threshold
            'base_withdrawal': 2e4, # Increased base withdrawal
            'max_extra_withdrawal': 4e5, # Increased max extra withdrawal
            'withdrawal_k': 8.0,   # Higher sensitivity for withdrawals
            'max_cap': float('inf')
        },
        'ETH': {
            'base_deposit': 1.5e4, # Reduced base deposit
            'max_extra_deposit': 3e4, # Reduced max extra deposit
            'deposit_k': 10.0,     # Higher sensitivity
            'apy_threshold': 0.03, # Slightly lower APY threshold
            'base_withdrawal': 1.5e4, # Increased base withdrawal
            'max_extra_withdrawal': 5e4, # Increased max extra withdrawal
            'withdrawal_k': 12.0,   # Higher sensitivity for withdrawals
            'max_cap': 120e6 # Slightly increased cap
        },
        'BTC': {
            'base_deposit': 1e4,    # Adjusted from BTC pool config
            'max_extra_deposit': 2e5, # Reduced from original
            'deposit_k': 8.0,        # Increased sensitivity
            'apy_threshold': 0.015,  # Lower APY threshold
            'base_withdrawal': 1e4,   # Increased base withdrawal
            'max_extra_withdrawal': 2.5e5, # Increased max withdrawal
            'withdrawal_k': 10.0,     # Higher sensitivity
            'max_cap': float('inf')
        }
    }])

    def __post_init__(self):
        """Initialize derived parameters for multiple runs"""
        # Price processes with run-specific indexing
        self.avl_price_process = [
            lambda timestep: self.avl_price_samples[run][timestep % len(self.avl_price_samples[run])]
            for run in range(len(self.avl_price_samples))
        ]
        self.eth_price_process = [
            lambda timestep: self.eth_price_samples[run][timestep % len(self.eth_price_samples[run])]
            for run in range(len(self.eth_price_samples))
        ]

        self.btc_price_process = [
            lambda timestep: self.btc_price_samples[run][timestep % len(self.btc_price_samples[run])]
            for run in range(len(self.btc_price_samples))
        ]

        self.lens_price_process = [
            lambda timestep: self.lens_price_samples[run][timestep % len(self.lens_price_samples[run])]
            for run in range(len(self.lens_price_samples))
        ]

        # Native staking ratio from constants
        self.native_staking_ratio = [constant["native_staking_ratio"] for constant in self.constants]

        self.target_yields[0][self.btc_activation_day[0]] = {"AVL": 0.15, "ETH": 0.035, "BTC": 0.05}
