# AVL Boosting Mechanism

## Overview

The AVL Boosting Mechanism is a sophisticated reward enhancement system that incentivizes longer-term staking and larger stake commitments in the AVL pool. It provides multipliers to base rewards based on two key factors:

1. **Lock Period Multipliers**: Rewards increase based on how long tokens are locked
2. **Pool Share Multipliers**: Rewards increase based on the percentage of the total AVL pool owned

## Key Features

### 🔒 Lock Period System
- **Flexible Lock Periods**: Support for multiple lock durations (0, 30, 60, 180 days)
- **Automatic Locking**: Restaked rewards are automatically locked based on agent preferences
- **Unlock Processing**: Tokens automatically unlock after their lock period expires
- **Weighted Multipliers**: Different portions of a stake can have different lock periods

### 📊 Pool Share Rewards
- **Proportional Bonuses**: Larger stakes receive higher multipliers
- **Tiered System**: Multiple threshold levels for different bonus tiers
- **Dynamic Calculation**: Share percentages recalculated each timestep

### 🔄 Automatic Restaking
- **Lock Preference Integration**: Restaked rewards automatically locked per agent preference
- **Compounding Benefits**: Locked restaked rewards earn boosted returns
- **Flexible Configuration**: Different agents can have different lock preferences

## Configuration Parameters

### Lock Period Multipliers
```python
avl_lock_period_multipliers = {
    0: 1.0,    # No lock: 1.0x multiplier (base rate)
    30: 1.05,  # 30-day lock: 1.05x multiplier (+5% boost)
    60: 1.1,   # 60-day lock: 1.1x multiplier (+10% boost)
    180: 1.5   # 180-day lock: 1.5x multiplier (+50% boost)
}
```

### Pool Share Multipliers
```python
avl_pool_share_multipliers = {
    0.01: 1.1,  # 1% pool share: 1.1x multiplier (+10% boost)
    0.1: 2.5    # 10% pool share: 2.5x multiplier (+150% boost)
}
```

### Agent Lock Preferences
```python
avl_lock_preferences = {
    'avl_maxi': 180,  # AVL maximalists prefer 180-day locks
    'eth_maxi': 0,    # ETH maximalists don't lock AVL
    'btc_maxi': 0     # BTC maximalists don't lock AVL
}
```

## Mathematical Model

### Combined Multiplier Calculation

The total boost multiplier for an agent is calculated as:

```
Total_Multiplier = Lock_Multiplier × Share_Multiplier
```

#### Lock Multiplier (Weighted Average)
```
Lock_Multiplier = Σ(Amount_i × Multiplier_i) / Total_Amount

Where:
- Amount_i = Amount locked for period i
- Multiplier_i = Multiplier for lock period i
- Total_Amount = Total AVL balance for the agent
```

#### Share Multiplier (Tiered)
```
Share_Multiplier = Highest applicable tier multiplier

Where:
- Share_Percentage = (Agent_AVL_Balance / Total_Pool_AVL_Balance) × 100
- Applied multiplier = highest tier where Share_Percentage ≥ threshold
```

### Example Calculation

**Agent State:**
- Total AVL Balance: 1,000,000 AVL
- Unlocked: 200,000 AVL (multiplier: 1.0x)
- Locked 60 days: 300,000 AVL (multiplier: 1.1x)
- Locked 180 days: 500,000 AVL (multiplier: 1.5x)
- Pool Share: 5% (qualifies for 1.1x share multiplier)

**Lock Multiplier:**
```
Lock_Multiplier = (200,000×1.0 + 300,000×1.1 + 500,000×1.5) / 1,000,000
                = (200,000 + 330,000 + 750,000) / 1,000,000
                = 1,280,000 / 1,000,000
                = 1.28x
```

**Share Multiplier:**
```
Share_Percentage = 5% ≥ 1% threshold
Share_Multiplier = 1.1x
```

**Total Multiplier:**
```
Total_Multiplier = 1.28 × 1.1 = 1.408x (+40.8% boost)
```

## Implementation Details

### Core Classes

#### `LockedStake`
```python
@dataclass
class LockedStake:
    amount: float              # Amount of tokens locked
    lock_period_days: int      # Lock period in days
    lock_start_timestep: int   # When lock started
    unlock_timestep: int       # When tokens unlock
```

#### `AssetAllocation` (Enhanced)
```python
@dataclass
class AssetAllocation:
    # ... existing fields ...
    locked_stakes: List[LockedStake] = field(default_factory=list)
    
    @property
    def locked_balance(self) -> float:
        """Get total locked balance"""
    
    @property
    def unlocked_balance(self) -> float:
        """Get unlocked balance"""
```

#### `AgentStake` (Enhanced)
```python
@dataclass
class AgentStake:
    # ... existing fields ...
    id: str = ""                        # Agent identifier
    avl_lock_preference: int = 0        # Preferred lock period
    
    def calculate_avl_boost_multiplier(self, ...):
        """Calculate combined boost multiplier"""
    
    def lock_avl_tokens(self, amount, lock_period, timestep):
        """Lock AVL tokens for specified period"""
    
    def process_avl_unlocks(self, timestep):
        """Process any unlocked stakes"""
```

### Policy Functions

#### `policy_tune_rewards_allocation`
- Processes unlocks at start of each timestep
- Calculates boost multipliers for each agent
- Applies boosted rewards based on combined multipliers
- Logs detailed boosting information

#### `policy_handle_rewards_restaking`
- Automatically locks restaked rewards based on agent preferences
- Tracks lock information in restaking logs

## Usage Examples

### Basic Configuration
```python
from scripts.simulation_runner import SimulationConfig, run_simulation

config = SimulationConfig(
    simulation_days=365,
    avl_boosting_enabled=True,
    avl_lock_period_multipliers={0: 1.0, 30: 1.05, 60: 1.1, 180: 1.5},
    avl_pool_share_multipliers={0.01: 1.1, 0.1: 2.5},
    avl_lock_preferences={'avl_maxi': 180, 'eth_maxi': 0, 'btc_maxi': 0}
)

results = run_simulation(config)
```

### Analyzing Results
```python
# Get final state
final_state = results.iloc[-1]
avl_agent = final_state['agents']['avl_maxi']

# Check lock distribution
print(f"Lock Distribution: {avl_agent.get_avl_lock_distribution()}")
print(f"Unlocked Balance: {avl_agent.assets['AVL'].unlocked_balance:,.2f} AVL")
print(f"Locked Balance: {avl_agent.assets['AVL'].locked_balance:,.2f} AVL")
print(f"Annual Rewards: {avl_agent.curr_annual_rewards_avl:,.2f} AVL")
```

### Testing the Mechanism
```python
# Run the test script
python test_boosting.py
```

## Benefits and Incentives

### For Stakers
1. **Higher Yields**: Earn up to 50% more rewards with 180-day locks
2. **Compounding Benefits**: Restaked rewards automatically locked for continued boosts
3. **Flexible Options**: Choose lock periods that match investment timeline
4. **Pool Share Rewards**: Larger stakes earn additional multipliers

### For the Protocol
1. **Reduced Selling Pressure**: Locked tokens can't be immediately sold
2. **Increased Commitment**: Longer locks demonstrate long-term belief
3. **Stable TVL**: Locked tokens provide predictable liquidity
4. **Whale Incentives**: Large holders get additional rewards for their commitment

## Security Considerations

### Lock Period Validation
- Lock periods must match predefined options
- Unlock timestamps calculated deterministically
- No early unlock mechanisms (by design)

### Balance Tracking
- Separate tracking of locked vs unlocked balances
- Automatic unlock processing prevents stuck tokens
- Comprehensive validation of lock/unlock operations

### Multiplier Bounds
- Multipliers have reasonable upper bounds
- Share calculations use total pool balance for accuracy
- Boost calculations are deterministic and auditable

## Future Enhancements

### Potential Features
1. **Dynamic Lock Periods**: Adjust multipliers based on market conditions
2. **Partial Unlocks**: Allow partial early unlocks with penalties
3. **Lock Extensions**: Allow extending existing locks for additional rewards
4. **Cross-Asset Boosts**: Apply AVL lock benefits to other asset rewards

### Governance Integration
1. **Voting Power**: Locked tokens could provide enhanced governance rights
2. **Proposal Bonuses**: Lock holders get priority in governance proposals
3. **Parameter Updates**: Community governance of multiplier parameters

## Monitoring and Analytics

### Key Metrics
- Total locked vs unlocked AVL
- Distribution of lock periods
- Average boost multipliers
- Lock/unlock flow rates
- Yield enhancement effectiveness

### Logging Output
The system provides detailed logging including:
- Daily unlock processing
- Boost multiplier calculations
- Lock distribution changes
- Reward allocation details
- Restaking with lock information

## Conclusion

The AVL Boosting Mechanism provides a sophisticated and flexible system for incentivizing long-term staking commitment while rewarding larger stakeholders. Through its combination of lock period and pool share multipliers, it creates a compelling value proposition for serious AVL stakers while supporting the protocol's stability and growth objectives. 