from typing import Dict

def calc_inflation_rate(
        staking_ratio,
        inflation_decay = 0.05,
        target_staking_rate = 0.5,
        min_inflation_rate = 0.01,
        max_inflation_rate = 0.05):
    
    d = inflation_decay
    x_ideal = target_staking_rate
    I_0 = min_inflation_rate
    i_ideal = max_inflation_rate/x_ideal

    I_left = I_0 + staking_ratio* (i_ideal - I_0/x_ideal)
    I_right = I_0 +(i_ideal*x_ideal - I_0) * (2** ((x_ideal-staking_ratio)/d))
    return min(I_left, I_right)

def calculate_reward_allocation(
    constants: Dict,
    avl_price: float,
    total_tvl: float,
    avl_stake_pct: float,
    target_avl_yield: float,
    target_eth_yield: float
) -> Dict:
    """Calculate reward allocation with proportional capping when exceeding limits"""
    # 1. Calculate base inflation parameters
    init_inflation_rate = calc_inflation_rate(
        staking_ratio=constants["native_staking_ratio"],
    )
    total_inflation_rewards_in_avl = constants["total_supply"] * init_inflation_rate
    total_inflation_rewards_usd = total_inflation_rewards_in_avl * avl_price

    # 2. Calculate initial reward requirements
    avl_rewards = (avl_stake_pct * total_tvl) * target_avl_yield
    eth_rewards = ((1 - avl_stake_pct) * total_tvl) * target_eth_yield
    total_required = avl_rewards + eth_rewards

    # 3. Determine AVL reward ratio before any capping
    avl_ratio = avl_rewards / (total_required + 1e-9)  # Prevent division by zero

    # 4. Calculate potential fusion allocation
    fusion_pct = total_required / (total_inflation_rewards_usd + 1e-9)
    print(f"fusion_pct: {fusion_pct}")
    capped = fusion_pct > constants["upper_rewards_to_fusion_pct"]

    # 5. Apply fusion cap if needed
    if capped:
        max_allowed = total_inflation_rewards_usd * constants["upper_rewards_to_fusion_pct"]
        # Scale rewards proportionally
        avl_rewards = avl_ratio * max_allowed
        eth_rewards = max_allowed - avl_rewards
        total_required = max_allowed
        fusion_pct = constants["upper_rewards_to_fusion_pct"]

    return {
        "init_inflation_rate": init_inflation_rate,
        "fusion_allocation_pct": fusion_pct,
        "avl_rewards_pct": avl_ratio,
        "total_inflation_rewards_in_avl": total_inflation_rewards_in_avl,
        "total_inflation_rewards_usd": total_inflation_rewards_usd,
        "required_rewards": total_required,
        "avl_rewards": avl_rewards,
        "eth_rewards": eth_rewards,
        "capped": capped
    }