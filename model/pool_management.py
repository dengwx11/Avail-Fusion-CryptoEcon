import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class PoolManager:
    """
    Manages staking pools with shared security budget allocation
    and controls deposit/withdrawal flows using sigmoid functions.
    """
    # Total shared security budget (in AVL tokens)
    total_budget: float
    
    # Pool configuration
    pools: Dict[str, Dict] = field(default_factory=dict)
    
    # Internal state
    _allocated_budgets: Dict[str, float] = field(default_factory=dict)
    _paused_deposits: Set[str] = field(default_factory=set)
    _deleted_pools: Set[str] = field(default_factory=set)
    _cap_paused_deposits: Set[str] = field(default_factory=set)
    
    # Budget tracking
    _initial_budget: float = field(default=0.0)
    _spent_budget: float = field(default=0.0)
    _spent_budget_per_pool: Dict[str, float] = field(default_factory=dict)
    
    # Track pools with zero yield due to budget depletion
    _zero_yield_pools: Set[str] = field(default_factory=set)
    
    # New attribute for deleted pool reason
    _deleted_pool_reason: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default pool parameters and budget tracking"""
        # Store initial budget for reference
        self._initial_budget = self.total_budget
        
        # Track pools with zero yield due to budget depletion
        self._zero_yield_pools = set()
        
        # Default parameters for each pool type
        default_params = {
            'AVL': {
                'base_deposit': 5e4,
                'max_extra_deposit': 1e5,
                'deposit_k': 5.0, # sensitivity of deposit flow to APY
                'apy_threshold': 0.10,  # 10%
                'base_withdrawal': 5e3,
                'max_extra_withdrawal': 1e5,
                'withdrawal_k': 7.0, # sensitivity of withdrawal flow to APY
                'max_cap': float('inf')
            },
            'ETH': {
                'base_deposit': 5e4,
                'max_extra_deposit': 5e5,
                'deposit_k': 8.0,
                'apy_threshold': 0.03,  # 3%
                'base_withdrawal': 5e3,
                'max_extra_withdrawal': 1.5e5,
                'withdrawal_k': 10.0,
                'max_cap': float('inf')
            }
            # ,'BTC': {
            #     'base_deposit': 1e5,
            #     'max_extra_deposit': 4e5,
            #     'deposit_k': 6.0,
            #     'apy_threshold': 0.02,  # 2%
            #     'base_withdrawal': 8e3,
            #     'max_extra_withdrawal': 2e5,
            #     'withdrawal_k': 9.0,
            #     'max_cap': float('inf')
            # }
        }
        
        # Initialize pools with default parameters if not provided
        for pool_type, default_config in default_params.items():
            if pool_type not in self.pools:
                self.pools[pool_type] = default_config
            else:
                # Apply defaults for missing parameters
                for param, value in default_config.items():
                    if param not in self.pools[pool_type]:
                        self.pools[pool_type][param] = value
            
            # Initialize allocated budget to zero
            self._allocated_budgets[pool_type] = 0.0
            
            # Initialize spent budget per pool to zero
            self._spent_budget_per_pool[pool_type] = 0.0
    
    def allocate_budget(self, allocations: Dict[str, float]):
        """
        Allocate budget to pools based on specified percentages.
        
        Args:
            allocations: Dict mapping pool types to allocation percentages (0-1)
        """
        # Validate allocations sum to approximately 1
        allocation_sum = sum(allocations.values())
        if not (0.99 <= allocation_sum <= 1.01):
            raise ValueError(f"Allocations must sum to 1.0 (got {allocation_sum})")
        
        # Update allocated budgets
        for pool_type, allocation_pct in allocations.items():
            if pool_type in self._deleted_pools:
                continue  # Skip deleted pools
                
            self._allocated_budgets[pool_type] = self.total_budget * allocation_pct
    
    def pause_deposits(self, pool_type: str, due_to_cap=False):
        """
        Pause deposits for a specific pool
        
        Args:
            pool_type: Type of pool to pause
            due_to_cap: Whether pause is due to hitting max cap
        """
        self._paused_deposits.add(pool_type)
        if due_to_cap:
            self._cap_paused_deposits.add(pool_type)
    
    def resume_deposits(self, pool_type: str):
        """Resume deposits for a specific pool"""
        if pool_type in self._paused_deposits:
            self._paused_deposits.remove(pool_type)
        if pool_type in self._cap_paused_deposits:
            self._cap_paused_deposits.remove(pool_type)
    
    def delete_pool(self, pool_type: str):
        """
        Mark a pool as deleted, which will stop all deposits
        and gradually drain all funds through withdrawals.
        
        Args:
            pool_type: Type of pool (AVL, ETH, BTC)
        """
        if pool_type not in self._deleted_pools:
            self._deleted_pools.add(pool_type)
            # Also pause deposits for deleted pools
            self.pause_deposits(pool_type)
            # Set special flag for deletion to distinguish from regular pauses
            self._deleted_pool_reason = getattr(self, '_deleted_pool_reason', {})
            self._deleted_pool_reason[pool_type] = "ADMIN_DELETED"
            
            print(f"Pool {pool_type} marked as deleted by admin action")
            
        # Return any remaining allocated budget to the unallocated pool
        remaining_budget = self._allocated_budgets.get(pool_type, 0)
        if remaining_budget > 0:
            self._allocated_budgets[pool_type] = 0
            # Note: We're not redistributing the budget automatically
            print(f"Returned {remaining_budget:,.2f} AVL from deleted {pool_type} pool to unallocated budget")
    
    def calculate_flows(self, pool_type: str, current_apy: float, current_tvl: float = 0) -> Dict[str, float]:
        """
        Calculate deposit and withdrawal flows based on current APY.
        
        Args:
            pool_type: Type of pool (AVL, ETH, BTC)
            current_apy: Current APY for this pool
            current_tvl: Current TVL for the pool
            
        Returns:
            Dict with 'deposit' and 'withdrawal' amounts in USD
        """
        # For deleted pools, stop all deposits and accelerate withdrawals
        if pool_type in self._deleted_pools:
            # For deleted pools, rapidly withdraw funds (30% per day)
            accelerated_withdrawal = current_tvl * 0.3
            print(f"  DELETED POOL: {pool_type} - accelerated withdrawal of ${accelerated_withdrawal:,.2f}")
            return {'deposit': 0.0, 'withdrawal': accelerated_withdrawal}
        
        # Check if pool has zero yield due to budget depletion
        budget_depleted = hasattr(self, '_zero_yield_pools') and pool_type in self._zero_yield_pools
        
        pool_config = self.pools.get(pool_type, {})
        
        # Calculate deposit flow (sigmoid function)
        deposit_k = pool_config.get('deposit_k', 5.0)
        base_deposit = pool_config.get('base_deposit', 0.0)
        max_extra_deposit = pool_config.get('max_extra_deposit', 1e6)
        apy_threshold = pool_config.get('apy_threshold', 0.05)
        
        # Sigmoid function for deposits
        sigmoid_factor = 1.0 / (1.0 + np.exp(-deposit_k * (current_apy - apy_threshold)))
        deposit_flow = base_deposit + max_extra_deposit * sigmoid_factor
        
        # If deposits are paused or budget is depleted, set to zero
        if pool_type in self._paused_deposits or budget_depleted:
            deposit_flow = 0.0
            
        # Calculate withdrawal flow (inverse sigmoid)
        withdrawal_k = pool_config.get('withdrawal_k', 7.0)
        base_withdrawal = pool_config.get('base_withdrawal', 0.0)
        max_extra_withdrawal = pool_config.get('max_extra_withdrawal', 5e5)
        
        # Sigmoid function for withdrawals (inverse relation to APY)
        sigmoid_factor = 1.0 / (1.0 + np.exp(-withdrawal_k * (apy_threshold - current_apy)))
        withdrawal_flow = base_withdrawal + max_extra_withdrawal * sigmoid_factor
        
        # If budget is depleted, increase withdrawals dramatically
        if budget_depleted:
            # Apply a rapid 30-day decay factor (withdraw ~10-15% per day)
            panic_withdrawal = current_tvl * 0.15
            withdrawal_flow = max(withdrawal_flow, panic_withdrawal)
            print(f"  ALERT: {pool_type} pool has depleted budget - rapid withdrawals in progress")
        
        return {
            'deposit': deposit_flow,
            'withdrawal': withdrawal_flow
        }
    
    def check_cap_status(self, pool_type: str, current_tvl: float) -> bool:
        """Check if pool has reached maximum cap and manage deposits accordingly"""
        max_cap = self.pools.get(pool_type, {}).get('max_cap', float('inf'))
        
        # If TVL is at or above cap, pause deposits
        if current_tvl >= max_cap:
            self.pause_deposits(pool_type, due_to_cap=True)
            return True
        
        # If TVL is below cap and deposits were paused due to cap, resume them
        elif pool_type in self._cap_paused_deposits and current_tvl < max_cap * 0.95:
            # Only resume if this pool was paused due to cap
            self.resume_deposits(pool_type)
            return False
        
        return pool_type in self._paused_deposits
    
    def get_pool_rewards(self, pool_type: str, required_amount: float) -> float:
        """
        Get rewards allocation for a pool, limited by available budget.
        
        Args:
            pool_type: Type of pool (AVL, ETH, BTC)
            required_amount: Required reward amount
            
        Returns:
            Actual reward amount (may be capped by budget)
        """
        if pool_type in self._deleted_pools:
            return 0.0
            
        available_budget = self._allocated_budgets.get(pool_type, 0.0)
        
        # Cap rewards at available budget
        actual_rewards = min(required_amount, available_budget)
        
        # Update remaining budget
        self._allocated_budgets[pool_type] -= actual_rewards
        
        # Track spent budget
        self._spent_budget += actual_rewards
        
        # Track spent budget per pool
        if pool_type not in self._spent_budget_per_pool:
            self._spent_budget_per_pool[pool_type] = 0.0
        self._spent_budget_per_pool[pool_type] += actual_rewards
        
        return actual_rewards
    
    def get_spent_budget_per_pool(self) -> Dict[str, float]:
        """Get spent budget for each pool"""
        return self._spent_budget_per_pool.copy()
    
    def get_remaining_budget(self) -> Dict[str, float]:
        """Get remaining budget for each pool"""
        return self._allocated_budgets.copy()
    
    def get_total_remaining_budget(self) -> float:
        """Get total remaining budget across all pools"""
        return sum(self._allocated_budgets.values())
    
    def get_budget_summary(self) -> Dict[str, float]:
        """Get summary of budget allocation and usage"""
        return {
            'initial_budget': self._initial_budget,
            'current_total_budget': self.total_budget,
            'allocated_budget': sum(self._allocated_budgets.values()),
            'spent_budget': self._spent_budget,
            'spent_budget_per_pool': self._spent_budget_per_pool.copy(),
            'unallocated_budget': self.total_budget - sum(self._allocated_budgets.values()),
            'budget_utilization_pct': (self._spent_budget / self._initial_budget * 100) 
                                     if self._initial_budget > 0 else 0.0
        }
    
    def get_active_pools(self) -> List[str]:
        """Get list of active (non-deleted) pools"""
        # Only include pools that are both defined and not deleted
        return [pool for pool in self.pools.keys() 
                if pool not in self._deleted_pools]
    
    def is_pool_active(self, pool_type: str) -> bool:
        """
        Check if a pool exists, is not deleted, and accepts deposits
        
        Args:
            pool_type: Type of pool to check
            
        Returns:
            True if pool exists, is not deleted, and accepts deposits
        """
        return (pool_type in self.pools and 
                pool_type not in self._deleted_pools and
                pool_type not in self._paused_deposits) 