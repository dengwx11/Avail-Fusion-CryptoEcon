from dataclasses import dataclass, field
from model.utils import default
from typing import List, Callable, Dict
from model.agents_class import AgentStake


from config.config import COLD_START_DURATION_TIMESTEPS



@dataclass
class FusionParams:
    """Dynamic simulation parameters with dependency injection"""
    
    # External dependencies
    avl_price_samples: List[float]
    eth_price_samples: List[float]
    rewards_result: Dict
    agents: List[AgentStake]
    
    # Price processes
    avl_price_process: List[Callable[[int, int], float]] = field(init=False)
    eth_price_process: List[Callable[[int, int], float]] = field(init=False)
    
    # Inflation parameters
    inflation_rate: List[float] = field(init=False)
    AVL_reward_pct: List[float] = field(init=False)
    ETH_reward_pct: List[float] = field(init=False)
    
    # Policy parameters
    inflation_decay: List[float] = default([0.05])
    target_staking_rate: List[float] = default([0.5])
    min_inflation_rate: List[float] = default([0.01])
    max_inflation_rate: List[float] = default([0.05])
    
    # Cold start parameters
    COLD_START_DURATION_TIMESTEPS: List[int] = default([365])
    NEW_AVAIL_DEPOSIT_DAILY_FACTOR_DOLLAR: List[float] = default([1e6])
    NEW_ETH_DEPOSIT_DAILY_FACTOR_DOLLAR: List[float] = default([5e6])
    COLD_START_BOOST_FACTOR: List[float] = default([1.0])

    def __post_init__(self):
        """Initialize derived parameters"""
        # Price processes
        self.avl_price_process = [
            lambda run, timestep: self.avl_price_samples[timestep % len(self.avl_price_samples)]
        ]
        self.eth_price_process = [
            lambda run, timestep: self.eth_price_samples[timestep % len(self.eth_price_samples)]
        ]
        
        # Reward allocation
        self.inflation_rate = [self.rewards_result["init_inflation_rate"]]
        self.AVL_reward_pct = [self.rewards_result["avl_rewards_pct"]]
        self.ETH_reward_pct = [1 - self.rewards_result["avl_rewards_pct"]]

