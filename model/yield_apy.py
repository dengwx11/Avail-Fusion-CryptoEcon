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

###########################
# rewards restaking
###########################

def policy_handle_rewards_restaking(params, step, h, s):
    """
    Policy function to handle restaking of rewards for all agents.
    
    This function processes each agent and restakes a portion of their 
    daily rewards (calculated from annual rewards) based on their restake_pct parameter.
    
    The restaking flow works as follows:
    1. Agents receive annual rewards via policy_tune_rewards_allocation
    2. The daily portion of these rewards is calculated (annual/365)
    3. A percentage (restake_pct) of these daily rewards is immediately restaked
    4. The remaining rewards are accumulated for future claiming
    
    Now also tracks compounding yields through two additional state variables:
    - compounding_yield_pcts: Yield percentages accounting for compounding effects
    - compounding_avg_yield: Average compounding yield across all agents
    
    For AVL agents with lock preferences, restaked rewards are automatically locked.
    
    Args:
        params: Simulation parameters
        step: Current step function
        h: History of previous states
        s: Current state
        
    Returns:
        Updated agents dictionary with compounding yield metrics
    """
    agents = s["agents"].copy()
    timestep = s["timestep"]
    
    total_restaked = 0.0
    total_accumulated = 0.0
    
    # Dictionaries to track compounding yields
    compounding_yield_pcts = {}
    total_compounding_rewards_usd = 0.0
    
    # Process each agent for restaking
    for agent_name, agent in agents.items():
        # Restake the appropriate portion of current rewards (pass timestep for locking)
        amount_restaked = agent.restake_accumulated_rewards(current_timestep=timestep)
        total_restaked += amount_restaked
        
        # Track accumulated rewards for reporting
        timesteps_per_year = 365 / DELTA_TIME
        daily_rewards = agent.curr_annual_rewards_avl / timesteps_per_year
        total_accumulated += daily_rewards
        
        # Calculate compounding yield
        avl_price = agent.assets['AVL'].price
        tvl = agent.total_tvl
        accumulated_rewards_usd = agent.accu_rewards_avl * avl_price
        
        # Calculate effective TVL excluding accumulated rewards
        effective_tvl = max(tvl - accumulated_rewards_usd, 1)  # Avoid division by zero
        
        # Calculate compounding yield (effective APY considering accumulated rewards)
        curr_annual_rewards_usd = agent.curr_annual_rewards_avl * avl_price
        compounding_yield = (curr_annual_rewards_usd / effective_tvl * 100) if effective_tvl > 0 else 0
        compounding_yield_pcts[agent_name] = compounding_yield
        
        # Add to total for average calculation
        total_compounding_rewards_usd += curr_annual_rewards_usd
        
        if amount_restaked > 0:
            avl_price = agent.assets['AVL'].price
            lock_info = ""
            if hasattr(agent, 'avl_lock_preference') and agent.avl_lock_preference > 0:
                lock_info = f" (locked for {agent.avl_lock_preference} days)"
            print(f"[RESTAKE] Agent {agent_name} restaked {amount_restaked:.2f} AVL tokens (${amount_restaked * avl_price:.2f}){lock_info}")
    
    # Calculate average compounding yield
    total_security_minus_rewards = max(s['total_security'] - total_compounding_rewards_usd, 1)
    compounding_avg_yield = (total_compounding_rewards_usd / total_security_minus_rewards * 100) if total_security_minus_rewards > 0 else 0
    
    if total_restaked > 0:
        print(f"[RESTAKE] Day {timestep} summary:")
        print(f"          Total restaked: {total_restaked:.2f} AVL tokens")
        print(f"          Total accumulated: {total_accumulated:.2f} AVL tokens")
    
    return {
        "agents": agents,
        "compounding_yield_pcts": compounding_yield_pcts,
        "compounding_avg_yield": compounding_avg_yield
    }