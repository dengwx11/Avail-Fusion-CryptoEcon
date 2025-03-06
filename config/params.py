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
        {1: {"AVL": 0.15, "ETH": 0.035, "BTC": 0}, 50: {"AVL": 0.15, "ETH": 0.1, "BTC": 0}}  # BTC target yield
    ])
    # Security budget replenishment schedule
    # Dictionary mapping timestep to pool-specific token allocations
    security_budget_replenishment: List[Dict] = default([
        {
            30: {'AVL': 4e6, 'ETH': 1e6},
            60: {'AVL': 3e6, 'ETH': 2e6},
            90: {'AVL': 3e6, 'ETH': 2e6},
            120: {'AVL': 3e6, 'ETH': 2e6},
            150: {'AVL': 3e6, 'ETH': 2e6},
            180: {'AVL': 5e6, 'ETH': 2e6, 'BTC': 3e6}
        }
    ])
    # Admin actions to pause deposits or delete pools
    admin_pause_deposits: List[Dict] = default([
        {30: ['ETH']} 
    ])

    admin_resume_deposits: List[Dict] = default([
        {50: ['ETH']} 
    ])

    admin_delete_pools: List[Dict] = default([
        {100: ['ETH']} 
    ])


    ### Policy parameters with list-based defaults ###
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

    # Initial pool configurations
    initial_pool_configs: List[Dict] = default([{
        'AVL': {
            'base_deposit': 5e4,
            'max_extra_deposit': 5e5,
            'deposit_k': 5.0,
            'apy_threshold': 0.10,
            'base_withdrawal': 5e3,
            'max_extra_withdrawal': 3e5,
            'withdrawal_k': 7.0,
            'max_cap': float('inf')
        },
        'ETH': {
            'base_deposit': 3e4,
            'max_extra_deposit': 5e4,
            'deposit_k': 8.0,
            'apy_threshold': 0.03,
            'base_withdrawal': 1e4,
            'max_extra_withdrawal': 3e4,
            'withdrawal_k': 10.0,
            'max_cap': 100e6
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
