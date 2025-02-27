from dataclasses import dataclass, field
from model.utils import default
from typing import List, Callable, Dict
from model.agents_class import AgentStake


from config.config import COLD_START_DURATION_TIMESTEPS



@dataclass
class FusionParams:
    """Dynamic simulation parameters with dependency injection for multiple runs"""
    
    # External dependencies (list of dictionaries for multiple runs)
    constants: List[Dict]
    avl_price_samples: List[List[float]]  # Price samples per run
    eth_price_samples: List[List[float]]  # Price samples per run
    btc_price_samples: List[List[float]]  # Price samples per run
    lens_price_samples: List[List[float]]  # Price samples per run
    rewards_result: List[Dict]
    agents: List[AgentStake]
    btc_activation_day: List[int]

    # Derived parameters (initialized in post_init)
    native_staking_ratio: List[float] = field(init=False)
    avl_price_process: List[Callable[[int, int], float]] = field(init=False)
    eth_price_process: List[Callable[[int, int], float]] = field(init=False)
    inflation_rate: List[float] = field(init=False)

    # ADMIN: fusion pallete
    fusion_palette_avl_token: List[Dict] = default([
        {1: {'AVL': 30e6, 'ETH': 10e6, 'BTC': 0}}  # Added BTC allocation
        
    ])
    target_yields: List[Dict] = default([
        {1: {"AVL": 0.15, "ETH": 0.035, "BTC": 0}}  # BTC target yield
    ])

    # ADD BTC staking pool
    # Security percentages before BTC activation - list of dicts
    security_pct_before_btc: List[Dict] = default([
        {'AVL': 1, 'ETH': 0 , 'BTC': 0}
    ])
    # Security percentages after BTC activation - list of dicts 
    security_pct_after_btc: List[Dict] = default([
        {'AVL': 0.5, 'ETH': 0.2, 'BTC': 0.3}
    ])
    
    # Policy parameters with list-based defaults
    inflation_decay: List[float] = default([0.05])
    target_staking_rate: List[float] = default([0.5])
    min_inflation_rate: List[float] = default([0.01])
    max_inflation_rate: List[float] = default([0.05])
    # TODO: add comments on cold start duration
    COLD_START_DURATION_TIMESTEPS: List[int] = default([365])
    NEW_DEPOSIT_DAILY_FACTOR_DOLLAR: List[Dict] = default([{'AVL': 3e4, 'ETH': 2e4, 'BTC': 5e5}])
    COLD_START_BOOST_FACTOR: List[float] = default([1])

    # New parameter for security budget replenishment schedule
    # Dictionary mapping timestep to amount of new tokens to add
    security_budget_replenishment: List[Dict] = default([
        {30: 5e6, 60: 5e6, 90: 5e6, 120: 5e6, 150: 5e6, 180: 10e6}  # Example schedule
    ])

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

        # Inflation rate from rewards results
        self.inflation_rate = [result["init_inflation_rate"] for result in self.rewards_result]
        
        # Native staking ratio from constants
        self.native_staking_ratio = [constant["native_staking_ratio"] for constant in self.constants]

        self.fusion_palette_avl_token[0][self.btc_activation_day[0]] = {'AVL': 0, 'ETH': 5e6, 'BTC': 15e6}
        self.target_yields[0][self.btc_activation_day[0]] = {"AVL": 0.15, "ETH": 0.035, "BTC": 0.05}
