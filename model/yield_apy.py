from dataclasses import dataclass




def policy_calc_yields(params, step, h, s):
    """Calculate yields based on agent rewards and TVL"""
    agents = s['agents']
    
    yield_pcts = {}
    total_rewards_usd = 0.0
    total_tvl = 0.0
    
    for agent_name, agent in agents.items():
        # Get annual rewards in USD
        rewards_avl = agent.curr_annual_rewards_avl
        avl_price = agent.assets['AVL'].price
        rewards_usd = rewards_avl * avl_price
        
        # Get total value locked in USD
        tvl = agent.total_tvl
        
        # Calculate yield percentage
        if tvl > 0:
            yield_pct = (rewards_usd / tvl) * 100
        else:
            yield_pct = 0.0  # Default for new agents
            
        yield_pcts[agent_name] = yield_pct
        total_rewards_usd += rewards_usd
        total_tvl += tvl
    
    # Calculate average yield across all agents
    avg_yield = (total_rewards_usd / total_tvl * 100) if total_tvl > 0 else 0.0
    
    return {
        "yield_pcts": yield_pcts,
        "avg_yield": avg_yield
    }

