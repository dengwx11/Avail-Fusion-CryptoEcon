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
    rewards_result: List[Dict]
    agents: List[AgentStake]
    
    # Derived parameters (initialized in post_init)
    native_staking_ratio: List[float] = field(init=False)
    avl_price_process: List[Callable[[int, int], float]] = field(init=False)
    eth_price_process: List[Callable[[int, int], float]] = field(init=False)
    inflation_rate: List[float] = field(init=False)

    # Policy parameters with list-based defaults
    inflation_decay: List[float] = default([0.05])
    target_staking_rate: List[float] = default([0.5])
    min_inflation_rate: List[float] = default([0.01])
    max_inflation_rate: List[float] = default([0.05])
    COLD_START_DURATION_TIMESTEPS: List[int] = default([365])
    NEW_AVAIL_DEPOSIT_DAILY_FACTOR_DOLLAR: List[float] = default([1e3])
    NEW_ETH_DEPOSIT_DAILY_FACTOR_DOLLAR: List[float] = default([5e3])
    COLD_START_BOOST_FACTOR: List[float] = default([1.0])

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

        # Inflation rate from rewards results
        self.inflation_rate = [result["init_inflation_rate"] for result in self.rewards_result]
        
        # Native staking ratio from constants
        self.native_staking_ratio = [constant["native_staking_ratio"] for constant in self.constants]
