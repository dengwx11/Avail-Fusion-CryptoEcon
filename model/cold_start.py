#### Cold Start Staking Policy ####
# No ETH staking, only AVAIL staking: new_avail_deposit_daily_factor_dollar = 1e6
# No AVAIL staking, only ETH staking: new_deposit_daily_factor_dollar = 5e6
# Cold start duration: 12 months

from model.agents_class import AgentStake
from model.pool_management import PoolManager
import numpy as np


def policy_cold_start_staking(params, substep, state_history, previous_state):
    """
    Unified cold start policy with sigmoid-based deposit/withdrawal flows
    """
    # Get state and parameters
    timestep = previous_state['timestep']
    agents = previous_state['agents'].copy()
    pool_manager = previous_state.get('pool_manager')
    btc_activation = params.get('btc_activation_day', 180)
    
    # Process only during cold start period
    if timestep < params['COLD_START_DURATION_TIMESTEPS']:
        # Determine active pools based on BTC activation day
        active_pools = ['AVL', 'ETH']
        if timestep >= btc_activation:
            active_pools.append('BTC')
        
        # Calculate flows for each active pool
        for asset in active_pools:
            agent_key = f'{asset.lower()}_maxi'
            agent = agents[agent_key]
            
            # Skip deleted pools
            if asset not in pool_manager.get_active_pools():
                continue
            
            # Get current yield for this pool
            current_yield = agent.current_yield
            
            # Check if pool is at capacity
            is_at_capacity = pool_manager.check_cap_status(asset, agent.total_tvl)
            
            # Calculate deposit and withdrawal flows
            flows = pool_manager.calculate_flows(asset, current_yield, agent.total_tvl)
            
            # Apply net flow (deposit - withdrawal)
            net_flow_usd = flows['deposit'] - flows['withdrawal']
            
            # Skip if net flow is negligible
            if abs(net_flow_usd) < 1.0:
                continue
                
            # Update agent's asset balance
            if net_flow_usd > 0:
                # Deposit case
                new_tokens = net_flow_usd / agent.assets[asset].price
                new_balance = agent.assets[asset].balance + new_tokens
                agent.update_asset(asset, balance=new_balance)
            else:
                # Withdrawal case (limit by available balance)
                tokens_to_withdraw = min(
                    abs(net_flow_usd) / agent.assets[asset].price,
                    agent.assets[asset].balance * 0.9  # Prevent full withdrawal
                )
                new_balance = max(0, agent.assets[asset].balance - tokens_to_withdraw)
                agent.update_asset(asset, balance=new_balance)
    
    return {'agents': agents}

def update_agent_deposit(agent, asset: str, usd_amount: float, price: float):
    """Helper function to update agent's asset balance"""
    new_balance = agent.assets[asset].balance + usd_amount/price
    agent.update_asset(asset, balance=new_balance)
    return agent



