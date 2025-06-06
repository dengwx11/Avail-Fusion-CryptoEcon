# AVL Pool Yield Spike Fix - Day 180 Issue

## Problem Description

After day 180, the AVL pool yield was experiencing exponential increases, while the spent budget remained constant at 21 billion AVL tokens. This created unrealistic yield scenarios that broke the economic model.

## Root Cause Analysis

### 1. **Massive Budget Injection**
- **Original Issue**: 3 billion AVL tokens were being added to the BTC pool on day 180
- **Location**: `config/params.py` - `security_budget_replenishment` parameter
- **Impact**: Created a sudden massive budget availability that disrupted yield calculations

### 2. **No Initial BTC Stakers**
- **Original Issue**: BTC pool received huge budget but had no stakers to consume it
- **Location**: `config/initialize_simulation.py` - `btc_balance=0` in agent creation
- **Impact**: Unused budget potentially affecting other pool calculations

### 3. **Budget Tracking Confusion**
- **Spent Budget**: The constant 21 billion represents cumulative AVL pool spending over 180 days
- **This is correct behavior**: Shows historical consumption, not current budget
- **New budget goes to BTC pool**: Doesn't directly affect AVL spent budget tracking

## Implemented Fixes

### Fix 1: Reduced BTC Budget Replenishment
**File**: `config/params.py`
**Change**: Reduced BTC budget from 3 billion to 200 million AVL tokens
```python
# Before
180: {'AVL': 0, 'ETH': 0, 'BTC': 3e9}  # 3 billion AVL

# After  
180: {'AVL': 0, 'ETH': 0, 'BTC': 2e8}  # 200 million AVL
```

### Fix 2: Added Initial BTC Stakers
**File**: `config/initialize_simulation.py`
**Change**: Added initial BTC balance to create actual stakers
```python
# Before
btc_balance=0,    # No BTC initially

# After
btc_balance=10,   # Add some initial BTC (~$300,000 at $30,000)
```

### Fix 3: Gradual Budget Replenishment Schedule
**File**: `config/params.py`
**Change**: Implemented gradual replenishment instead of single massive injection
```python
security_budget_replenishment: List[Dict] = default([
    {
        # Gradual replenishment schedule to prevent yield spikes
        30: {'AVL': 1e9, 'ETH': 0.5e9},      # Day 30: 1B AVL, 0.5B ETH
        60: {'AVL': 1e9, 'ETH': 0.5e9},      # Day 60: 1B AVL, 0.5B ETH  
        90: {'AVL': 1e9, 'ETH': 0.5e9},      # Day 90: 1B AVL, 0.5B ETH
        120: {'AVL': 1e9, 'ETH': 0.5e9},     # Day 120: 1B AVL, 0.5B ETH
        150: {'AVL': 1e9, 'ETH': 0.5e9},     # Day 150: 1B AVL, 0.5B ETH
        180: {'AVL': 0, 'ETH': 0, 'BTC': 2e8},  # Day 180: 200M BTC
        210: {'AVL': 0.5e9, 'ETH': 0, 'BTC': 1e8},  # Day 210: 500M AVL, 100M BTC
        240: {'AVL': 0.5e9, 'ETH': 0, 'BTC': 1e8},  # Day 240: 500M AVL, 100M BTC
    }
])
```

### Fix 4: Added Budget Monitoring Safeguards
**File**: `model/basic_model.py`
**Change**: Added warnings for excessive unused budget
```python
# Check for excessive unused budget (potential issue indicator)
remaining_budget = pool_manager._allocated_budgets.get(asset_type, 0)
if remaining_budget > total_required * 10:  # More than 10x required budget
    print(f"⚠️  WARNING: {asset_type} pool has excessive unused budget: {remaining_budget:,.0f} AVL")
    print(f"   Required: {total_required:,.0f} AVL, Ratio: {remaining_budget/total_required:.1f}x")
```

## Expected Outcomes

### 1. **Stable Yield Progression**
- AVL yields should increase gradually, not exponentially
- No sudden spikes after day 180
- Yield changes should be proportional to budget additions

### 2. **Realistic Budget Utilization**
- BTC pool budget should be consumed by actual stakers
- No excessive unused budget warnings
- Gradual budget consumption over time

### 3. **Proper Budget Tracking**
- Spent budget will continue to increase as new budget is consumed
- Each pool's budget tracked separately
- Clear visibility into budget utilization rates

## Testing

### Test Script
Run `test_yield_fix.py` to verify the fixes:
```bash
python test_yield_fix.py
```

### Key Metrics to Monitor
1. **Yield Stability**: AVL yield should not increase more than 2x suddenly
2. **Budget Utilization**: No pools should have >10x unused budget
3. **Gradual Changes**: Budget replenishment should create smooth transitions

### Success Criteria
- ✅ No exponential yield increases after day 180
- ✅ BTC pool budget consumed by actual stakers  
- ✅ Gradual, predictable yield progression
- ✅ Proper budget tracking and warnings

## Technical Details

### Budget Flow Architecture
```
Initial Budget (30B AVL)
├── AVL Pool: 21B AVL (consumed by day 180)
├── ETH Pool: 9B AVL (consumed over time)
└── BTC Pool: 0 → 200M AVL (day 180 activation)

Replenishment Schedule:
├── Days 30-150: Regular AVL/ETH replenishment (1B + 0.5B)
├── Day 180: BTC activation with 200M budget
└── Days 210-240: Continued gradual replenishment
```

### Pool Isolation
- Each pool's budget is tracked separately
- Unused budget in one pool doesn't affect others
- Rewards capped by available pool budget
- Clear separation of concerns

## Monitoring and Maintenance

### Regular Checks
1. Monitor yield progression for sudden spikes
2. Check budget utilization rates
3. Verify pool isolation is maintained
4. Review replenishment schedule effectiveness

### Warning Signs
- Yield increases >5x in a single day
- Unused budget >10x required amount
- Budget utilization <10% for active pools
- Exponential rather than linear progression

### Future Improvements
1. **Dynamic Budget Allocation**: Adjust based on actual demand
2. **Automated Rebalancing**: Move unused budget between pools
3. **Yield Smoothing**: Implement maximum daily yield change limits
4. **Advanced Monitoring**: Real-time budget utilization alerts

## Conclusion

The yield spike issue was caused by a combination of excessive budget injection and lack of actual stakers to consume it. The implemented fixes address both the immediate problem and provide safeguards against future similar issues.

The solution maintains the economic model's integrity while providing realistic yield progression and proper budget management across all pools. 