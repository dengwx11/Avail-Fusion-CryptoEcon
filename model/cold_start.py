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
        # Log cold start header once per 7 days
        if timestep % 7 == 0:
            print(f"\nCOLD START FLOWS - DAY {timestep}")
            print(f"{'-'*60}")
        
        # Determine active pools based on BTC activation day
        active_pools = ['AVL', 'ETH']
        if timestep >= btc_activation and 'BTC' in pool_manager.pools:
            active_pools.append('BTC')
        
        # Calculate flows for each active pool
        for asset in active_pools:
            agent_key = f'{asset.lower()}_maxi'
            agent = agents[agent_key]
            
            # Skip pools that don't exist in the pool manager
            if asset not in pool_manager.pools:
                continue
            
            # Skip deleted pools
            if asset in pool_manager._deleted_pools:
                continue
            
            # Get current yield for this pool
            current_yield = agent.current_yield
            
            # Check if pool is at capacity
            is_at_capacity = pool_manager.check_cap_status(asset, agent.total_tvl)
            
            # Calculate deposit and withdrawal flows
            flows = pool_manager.calculate_flows(asset, current_yield, agent.total_tvl)
            
            # Log significant flows
            net_flow_usd = flows['deposit'] - flows['withdrawal']
            if abs(net_flow_usd) > 1000:  # Only log significant flows
                print(f"  {asset} Flow: ${net_flow_usd:,.2f} (D: ${flows['deposit']:,.2f}, W: ${flows['withdrawal']:,.2f})")
            
            # Apply net flow (deposit - withdrawal)
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



