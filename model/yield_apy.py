from dataclasses import dataclass
from config.config import DELTA_TIME



def policy_calc_yields(params, step, h, s):
    """Calculate yields with target yield enforcement"""
    agents = s['agents']
    
    yield_pcts = {}
    total_rewards_usd = 0.0
    
    for agent_name, agent in agents.items():
        
        yield_pct = agent.current_yield * 100      
        yield_pcts[agent_name] = yield_pct
        total_rewards_usd += agent.current_yield * agent.total_tvl
    
    # Calculate average yield across all agents
    avg_yield = (total_rewards_usd / s['total_security'] * 100) if s['total_security'] > 0 else 0.0
    
    return {
        "yield_pcts": yield_pcts,
        "avg_yield": avg_yield
    }

