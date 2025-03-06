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
    init_inflation_rate = calc_inflation_rate(
        staking_ratio=constants["native_staking_ratio"],
    )
    total_inflation_rewards_in_avl = constants["total_supply"] * init_inflation_rate
    total_inflation_rewards_usd = total_inflation_rewards_in_avl * avl_price


    return {
        "init_inflation_rate": init_inflation_rate,
        "total_inflation_rewards_in_avl": total_inflation_rewards_in_avl,
        "total_inflation_rewards_usd": total_inflation_rewards_usd,
    }