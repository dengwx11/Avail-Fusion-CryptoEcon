from dataclasses import dataclass, field
from typing import List, NamedTuple, Tuple, Dict

from config.config import DELTA_TIME

# Type alias for agent allocation percentages
# with length of number of agents
# for example, [0.25, 0.25, 0.5] means 25% of full pool is staked by agent 1, 25% by agent 2, and 50% by agent 3
AgentComposition_TVL = List[float]


@dataclass
class LockedStake:
    """Represents a locked stake with lock period and unlock timestamp"""
    amount: float  # Amount of tokens locked
    lock_period_days: int  # Lock period in days
    lock_start_timestep: int  # Timestep when lock started
    unlock_timestep: int  # Timestep when tokens unlock
    
    def is_unlocked(self, current_timestep: int) -> bool:
        """Check if the locked stake is now unlocked"""
        return current_timestep >= self.unlock_timestep


@dataclass
class AssetAllocation:
    """Stores allocation details for a single asset"""
    pct: float  # Allocation percentage (0-1)
    balance: float  # Token balance
    price: float  # USD price per token
    
    # AVL-specific locking mechanism
    locked_stakes: List[LockedStake] = field(default_factory=list)  # List of locked stakes
    
    @property
    def tvl(self) -> float:
        """Calculate TVL in USD for this asset"""
        return self.balance * self.price
    
    @property
    def locked_balance(self) -> float:
        """Get total locked balance"""
        return sum(stake.amount for stake in self.locked_stakes)
    
    @property
    def unlocked_balance(self) -> float:
        """Get unlocked balance"""
        return self.balance - self.locked_balance
    
    def add_locked_stake(self, amount: float, lock_period_days: int, current_timestep: int):
        """Add a new locked stake"""
        if amount <= 0:
            return
            
        unlock_timestep = current_timestep + lock_period_days
        locked_stake = LockedStake(
            amount=amount,
            lock_period_days=lock_period_days,
            lock_start_timestep=current_timestep,
            unlock_timestep=unlock_timestep
        )
        self.locked_stakes.append(locked_stake)
    
    def process_unlocks(self, current_timestep: int) -> float:
        """Process any unlocked stakes and return the amount unlocked"""
        unlocked_amount = 0.0
        remaining_stakes = []
        
        for stake in self.locked_stakes:
            if stake.is_unlocked(current_timestep):
                unlocked_amount += stake.amount
            else:
                remaining_stakes.append(stake)
        
        self.locked_stakes = remaining_stakes
        return unlocked_amount
    
    def get_lock_period_distribution(self) -> Dict[int, float]:
        """Get distribution of locked amounts by lock period"""
        distribution = {}
        for stake in self.locked_stakes:
            period = stake.lock_period_days
            distribution[period] = distribution.get(period, 0) + stake.amount
        return distribution

@dataclass
class AgentStake:
    """Manages asset allocations and auto-updates percentages on changes"""
    assets: Dict[str, AssetAllocation]  # Asset symbol to allocation mapping
    curr_annual_rewards_avl: float = 0.0  # Current annual rewards in AVL tokens
    accu_rewards_avl: float = 0.0  # Accumulated rewards in AVL tokens
    restake_pct: float = 0.0  # Percentage of rewards to restake (0.0-1.0)
    
    # AVL boosting attributes
    id: str = ""  # Agent identifier for tracking
    avl_lock_preference: int = 0  # Preferred lock period in days (0 = no lock)

    def __post_init__(self):
        self._update_percentages()
    
    def _update_percentages(self):
        """Recalculate allocation percentages based on current TVL"""
        total_tvl = sum(asset.tvl for asset in self.assets.values())
        
        # Handle zero TVL edge case
        if total_tvl <= 0:
            for asset in self.assets.values():
                asset.pct = 0.0
            return

        # Update percentages based on TVL ratios
        for asset in self.assets.values():
            asset.pct = asset.tvl / total_tvl

    def update_asset(self, symbol: str, balance: float = None, price: float = None):
        """Update either balance or price of an asset and recalculate percentages"""
        asset = self.assets.get(symbol)
        if not asset:
            raise ValueError(f"Asset {symbol} not found in allocations")

        if balance is not None:
            asset.balance = balance
        if price is not None:
            asset.price = price
            
        self._update_percentages()

    def lock_avl_tokens(self, amount: float, lock_period_days: int, current_timestep: int):
        """Lock AVL tokens for a specified period"""
        if 'AVL' not in self.assets:
            raise ValueError("Agent does not have AVL asset")
        
        avl_asset = self.assets['AVL']
        
        # Check if enough unlocked balance is available
        if amount > avl_asset.unlocked_balance:
            raise ValueError(f"Insufficient unlocked AVL balance. Available: {avl_asset.unlocked_balance}, Requested: {amount}")
        
        # Add the locked stake
        avl_asset.add_locked_stake(amount, lock_period_days, current_timestep)
    
    def process_avl_unlocks(self, current_timestep: int) -> float:
        """Process any AVL unlocks and return the amount unlocked"""
        if 'AVL' not in self.assets:
            return 0.0
        
        return self.assets['AVL'].process_unlocks(current_timestep)
    
    def get_avl_lock_distribution(self) -> Dict[int, float]:
        """Get distribution of locked AVL amounts by lock period"""
        if 'AVL' not in self.assets:
            return {}
        
        return self.assets['AVL'].get_lock_period_distribution()
    
    def calculate_avl_boost_multiplier(self, total_avl_pool_balance: float, 
                                     lock_multipliers: Dict[int, float],
                                     share_multipliers: Dict[float, float]) -> float:
        """
        Calculate the boost multiplier for AVL rewards based on lock periods and pool share.
        
        Args:
            total_avl_pool_balance: Total AVL balance in the pool
            lock_multipliers: Dictionary mapping lock periods to multipliers
            share_multipliers: Dictionary mapping share percentages to multipliers
            
        Returns:
            Combined boost multiplier
        """
        if 'AVL' not in self.assets or self.assets['AVL'].balance <= 0:
            return 1.0
        
        avl_asset = self.assets['AVL']
        
        # Calculate weighted average lock period multiplier
        lock_distribution = avl_asset.get_lock_period_distribution()
        total_locked = sum(lock_distribution.values())
        unlocked_amount = avl_asset.unlocked_balance
        
        # Calculate weighted lock multiplier
        weighted_lock_multiplier = 0.0
        
        # Add unlocked portion with base multiplier
        if unlocked_amount > 0:
            base_multiplier = lock_multipliers.get(0, 1.0)
            weighted_lock_multiplier += (unlocked_amount / avl_asset.balance) * base_multiplier
        
        # Add locked portions with their respective multipliers
        for lock_period, amount in lock_distribution.items():
            if amount > 0:
                period_multiplier = lock_multipliers.get(lock_period, 1.0)
                weighted_lock_multiplier += (amount / avl_asset.balance) * period_multiplier
        
        # Calculate pool share multiplier
        if total_avl_pool_balance > 0:
            share_percentage = (avl_asset.balance / total_avl_pool_balance) * 100
            
            # Find the appropriate share multiplier (use the highest applicable tier)
            share_multiplier = 1.0
            for threshold, multiplier in sorted(share_multipliers.items()):
                if share_percentage >= threshold:
                    share_multiplier = multiplier
        else:
            share_multiplier = 1.0
        
        # Combine multipliers (multiplicative)
        combined_multiplier = weighted_lock_multiplier * share_multiplier
        
        return combined_multiplier

        
    @property
    def total_tvl(self) -> float:
        """Get combined TVL of all assets in USD"""
        return sum(asset.tvl for asset in self.assets.values())


    def add_rewards(self, avl_amount: float):
        """Add AVL token rewards to the agent
        
        Args:
            avl_amount: Annual rewards in AVL tokens
            
        The method sets the current annual rewards and also accumulates
        the non-restaked portion into accu_rewards_avl.
        """
        # Update the current annual rewards amount
        self.curr_annual_rewards_avl = avl_amount
        
        # Convert to daily rewards for this timestep
        timesteps_per_year = 365 / DELTA_TIME
        
        # Add non-restaked rewards to accumulated rewards
        self.accu_rewards_avl += avl_amount/timesteps_per_year

    def restake_accumulated_rewards(self, current_timestep: int = 0) -> float:
        """
        Restake rewards based on restake_pct.
        Returns the amount of AVL tokens that were restaked.
        
        If restake_pct > 0, current annual rewards are converted to daily rewards
        and that portion is automatically restaked.
        
        For AVL agents, restaked rewards can be automatically locked based on lock preference.
        """
        # Convert annual rewards to daily rewards for this timestep
        timesteps_per_year = 365 / DELTA_TIME
        daily_rewards = self.curr_annual_rewards_avl / timesteps_per_year
        
        # Calculate amount to restake from daily rewards
        amount_to_restake = daily_rewards * self.restake_pct
        
        if amount_to_restake <= 0:
            return 0.0
            
        # Add restaked amount to AVL balance
        self.assets['AVL'].balance += amount_to_restake
        
        # If this is an AVL agent and has a lock preference, lock the restaked rewards
        if 'AVL' in self.assets and self.avl_lock_preference > 0:
            try:
                self.lock_avl_tokens(amount_to_restake, self.avl_lock_preference, current_timestep)
            except ValueError:
                # If locking fails, just add to unlocked balance (already done above)
                pass
        
        # We don't subtract from accu_rewards_avl since we're taking directly from the daily flow
        # The remaining rewards are still accumulated via add_rewards method
        
        # Update asset percentages
        self._update_percentages()
        
        return amount_to_restake

    @property
    def annual_rewards_usd(self) -> float:
        """Calculate USD value of current annual rewards"""
        return self.curr_annual_rewards_avl * self.assets["AVL"].price
    
    @property
    def current_yield(self) -> float:
        """Calculate yield as rewards USD / agent's current TVL"""
        return self.annual_rewards_usd / self.total_tvl if self.total_tvl > 0 else 0.0

    @classmethod
    def create_maxi_agents(
        cls,
        target_composition: Dict[str, float],
        total_tvl: float,
        avl_price: float = 0.1,
        eth_price: float = 3000,
        btc_price: float = 30000,
        restake_pcts: Dict[str, float] = None,
        avl_lock_preferences: Dict[str, int] = None
    ) -> Dict[str, 'AgentStake']:
        """Class method to create maxi agents based on target composition with restaking and locking"""
        # Calculate required balances
        balances = cls.calculate_required_balances(
            target_composition,
            total_tvl,
            avl_price,
            eth_price,
            btc_price
        )
        
        # Default restake percentages if not provided
        if restake_pcts is None:
            restake_pcts = {
                'avl_maxi': 1,  # 80% restake for AVL maxis
                'eth_maxi': 1,  # 30% restake for ETH maxis
                'btc_maxi': 1   # 20% restake for BTC maxis
            }
        
        # Default lock preferences if not provided
        if avl_lock_preferences is None:
            avl_lock_preferences = {
                'avl_maxi': 180,  # AVL maxis prefer 180-day locks for maximum boost
                'eth_maxi': 0,    # ETH maxis don't lock AVL
                'btc_maxi': 0     # BTC maxis don't lock AVL
            }
        
        return {
            'avl_maxi': cls(
                id='avl_maxi',
                assets={
                    'AVL': AssetAllocation(pct=1.0, balance=balances['AVL'], price=avl_price),
                    'ETH': AssetAllocation(pct=0.0, balance=0, price=eth_price),
                    'BTC': AssetAllocation(pct=0.0, balance=0, price=btc_price)
                }, 
                restake_pct=restake_pcts.get('avl_maxi', 0.8),
                avl_lock_preference=avl_lock_preferences.get('avl_maxi', 180)
            ),
            'eth_maxi': cls(
                id='eth_maxi',
                assets={
                    'AVL': AssetAllocation(pct=0.0, balance=0, price=avl_price),
                    'ETH': AssetAllocation(pct=1.0, balance=balances['ETH'], price=eth_price),
                    'BTC': AssetAllocation(pct=0.0, balance=0, price=btc_price)
                }, 
                restake_pct=restake_pcts.get('eth_maxi', 0.3),
                avl_lock_preference=avl_lock_preferences.get('eth_maxi', 0)
            ),
            'btc_maxi': cls(
                id='btc_maxi',
                assets={
                    'AVL': AssetAllocation(pct=0.0, balance=0, price=avl_price),
                    'ETH': AssetAllocation(pct=0.0, balance=0, price=eth_price),
                    'BTC': AssetAllocation(pct=1.0, balance=balances['BTC'], price=btc_price)
                }, 
                restake_pct=restake_pcts.get('btc_maxi', 0.2),
                avl_lock_preference=avl_lock_preferences.get('btc_maxi', 0)
            )
        }

    @staticmethod
    def calculate_required_balances(
        target_composition: Dict[str, float],
        total_tvl: float,
        avl_price: float = 0.1,
        eth_price: float = 3000,
        btc_price: float = 30000
    ) -> Dict[str, float]:
        """Static method to calculate required balances"""
        sum_percent = sum(target_composition.values())
        if not (0.99 <= sum_percent <= 1.01):
            raise ValueError("Target composition must sum to 1 (±0.01 tolerance)")

        avl_usd = total_tvl * target_composition.get('AVL', 0)
        eth_usd = total_tvl * target_composition.get('ETH', 0)
        btc_usd = total_tvl * target_composition.get('BTC', 0)

        return {
            'AVL': avl_usd / avl_price if avl_price > 0 else 0,
            'ETH': eth_usd / eth_price if eth_price > 0 else 0,
            'BTC': btc_usd / btc_price if btc_price > 0 else 0
        }

    @staticmethod
    def update_agent_prices(
        agents: Dict[str, 'AgentStake'],
        avl_price: float = None,
        eth_price: float = None,
        btc_price: float = None
    ) -> None:
        """Update prices for all assets across all agents
        
        Args:
            agents: Dictionary of AgentStake instances
            *_price: New price values (None leaves unchanged)
        """
        # Update AVL price if provided
        if avl_price is not None:
            for agent in agents.values():
                agent.assets['AVL'].price = avl_price
                agent._update_percentages()
        
        # Update ETH price if provided
        if eth_price is not None:
            for agent in agents.values():
                agent.assets['ETH'].price = eth_price
                agent._update_percentages()
        
        # Update BTC price if provided
        if btc_price is not None:
            for agent in agents.values():
                agent.assets['BTC'].price = btc_price
                agent._update_percentages()

    @staticmethod
    def total_combined_tvl(agents: Dict[str, 'AgentStake']) -> float:
        """Calculate combined TVL across all agents"""
        return sum(agent.total_tvl for agent in agents.values())

    @staticmethod
    def calculate_agent_tvl_shares(agents: Dict[str, 'AgentStake']) -> Dict[str, float]:
        """Calculate each agent's TVL percentage of total combined TVL"""
        total_tvl = AgentStake.total_combined_tvl(agents)
        
        if total_tvl <= 0:
            return {name: 0.0 for name in agents.keys()}
        
        return {
            name: agent.total_tvl / total_tvl
            for name, agent in agents.items()
        }

