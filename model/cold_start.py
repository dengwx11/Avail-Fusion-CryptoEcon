#### Cold Start Staking Policy ####
# No ETH staking, only AVAIL staking: new_avail_deposit_daily_factor_dollar = 1e6
# No AVAIL staking, only ETH staking: new_deposit_daily_factor_dollar = 5e6
# Cold start duration: 12 months

from model.agents_class import AgentStake


def policy_cold_start_staking(params, substep, state_history, previous_state):
    """Unified cold start policy with direct agent updates"""
    # Get state and parameters
    timestep = previous_state['timestep']
    agents = previous_state['agents'].copy()
    print("[DEBUG] policy_cold_start_staking")
    print(agents)
    
    # Calculate current yields
    avl_yield = agents['avl_maxi'].current_yield * 100 if timestep >1 else 20
    eth_yield = agents['eth_maxi'].current_yield * 100 if timestep >1 else 10
    print(avl_yield)
    print(eth_yield)
    
    # Apply cold start boost if needed
    if timestep < params['COLD_START_DURATION_TIMESTEPS']:
        boost = params['COLD_START_BOOST_FACTOR']
        avl_yield *= boost
        eth_yield *= boost
        
        # Update AVL maxi agent
        avl_deposit = params['NEW_AVAIL_DEPOSIT_DAILY_FACTOR_DOLLAR'] * avl_yield * previous_state['AVL_security_pct']
        print(avl_deposit)
        agents['avl_maxi'] = update_agent_deposit(
            agents['avl_maxi'],
            asset='AVL',
            usd_amount=avl_deposit,
            price=agents['avl_maxi'].assets['AVL'].price
        )
        
        # Update ETH maxi agent
        eth_deposit = params['NEW_ETH_DEPOSIT_DAILY_FACTOR_DOLLAR'] * eth_yield * previous_state['ETH_security_pct']
        print(eth_deposit)
        agents['eth_maxi'] = update_agent_deposit(
            agents['eth_maxi'],
            asset='ETH',
            usd_amount=eth_deposit,
            price=agents['eth_maxi'].assets['ETH'].price
        )
    print("[DEBUG] policy_cold_start_staking")
    print(agents)
    return {'agents': agents}

def update_agent_deposit(agent, asset: str, usd_amount: float, price: float):
    """Helper function to update agent's asset balance"""
    new_balance = agent.assets[asset].balance + usd_amount/price
    agent.update_asset(asset, balance=new_balance)
    return agent



