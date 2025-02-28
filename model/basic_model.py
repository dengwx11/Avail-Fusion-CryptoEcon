from model.agents_class import AgentStake
import copy
from model.rewards import calc_inflation_rate
from config.config import DELTA_TIME
from model.pool_management import PoolManager
###########################
# environment
###########################

def update_timestep(params, step, h, s, _input):
    timestep = s['timestep']
    
    return "timestep", timestep+1

def policy_update_token_prices(params, step, h, s):
    avl_price_process = params["avl_price_process"]
    eth_price_process = params["eth_price_process"]
    btc_price_process = params["btc_price_process"]
    lens_price_process = params["lens_price_process"]
    agents = s['agents'].copy()
    print("###########################")
    print("timestep", s["timestep"])
    if s["timestep"] % 7 == 0: # update token prices every 7 timesteps
        for asset in ['AVL', 'ETH', 'BTC']:
            # Get the new price for the current asset from its price process
            new_price = locals()[f"{asset.lower()}_price_process"](s["timestep"])
            # Update all agents with new AVL price
            # Create kwargs dict to pass the updated price for the current asset
            price_kwargs = {f"{asset.lower()}_price": new_price}
            AgentStake.update_agent_prices(agents, **price_kwargs)
        print("[DEBUG] update_token_prices")
        print(agents)
    return ({"agents": agents})



###########################
# admin change encoded params for targeting yields
###########################


def policy_tune_rewards_allocation(params, step, h, s):
    """
    Adjust rewards allocation using unified pool manager and target yields.
    Allows admin to replenish the security budget periodically.
    """
    timestep = s["timestep"]
    agents = s["agents"].copy()
    pool_manager = s.get("pool_manager")
    btc_activation = params.get('btc_activation_day', 180)
    
    # Get target yields from parameters or previous state
    target_yields = params["target_yields"].get(
        timestep,  # Check current timestep first
        s.get("target_yields", {})  # Fallback to previous state
    )
    
    # Initialize or update pool manager
    if pool_manager is None:
        # First run, initialize pool manager
        initial_budget = 30e6  # Initial unified security budget
        pool_manager = PoolManager(total_budget=initial_budget)
    
    # Check for budget replenishment schedule
    budget_replenishment = params.get("security_budget_replenishment", {}).get(timestep, 0)
    if budget_replenishment > 0:
        # Admin is adding new tokens to the security budget
        print(f"[DEBUG] Replenishing security budget with {budget_replenishment} tokens")
        
        # Get current budget and allocations before adding new funds
        current_budget = pool_manager.total_budget
        remaining_budget = pool_manager.get_remaining_budget()
        
        # Calculate the current allocation ratios from remaining budget
        total_remaining = sum(remaining_budget.values())
        
        # Default allocations if all budget has been spent
        if total_remaining <= 0:
            if timestep < btc_activation:
                allocations = {
                    'AVL': params['security_budget_pct_before_btc'].get('AVL', 0.7),
                    'ETH': params['security_budget_pct_before_btc'].get('ETH', 0.3),
                    'BTC': 0.0
                }
            else:
                allocations = {
                    'AVL': params['security_budget_pct_after_btc'].get('AVL', 0.5),
                    'ETH': params['security_budget_pct_after_btc'].get('ETH', 0.2),
                    'BTC': params['security_budget_pct_after_btc'].get('BTC', 0.3)
                }
        else:
            # Use current allocation ratios
            allocations = {
                pool: budget / total_remaining
                for pool, budget in remaining_budget.items()
                if pool not in pool_manager._deleted_pools
            }
            
            # Normalize allocations to sum to 1
            allocation_sum = sum(allocations.values())
            if allocation_sum > 0:
                allocations = {k: v/allocation_sum for k, v in allocations.items()}
        
        # Update pool manager's total budget
        pool_manager.total_budget += budget_replenishment
        
        # Allocate new budget according to the current ratios
        new_budget_allocation = {k: v * budget_replenishment for k, v in allocations.items()}
        
        # Add new allocation to each pool's budget
        for pool, amount in new_budget_allocation.items():
            if pool not in pool_manager._deleted_pools:
                pool_manager._allocated_budgets[pool] = pool_manager._allocated_budgets.get(pool, 0) + amount
    
    # Handle BTC activation (existing code)
    if timestep == btc_activation:
        # Adjust budget allocations for BTC activation
        # Allocate budget based on target security percentages
        if timestep < btc_activation:
            allocations = {
                'AVL': params['security_budget_pct_before_btc'].get('AVL', 0.7),
                'ETH': params['security_budget_pct_before_btc'].get('ETH', 0.3),
                'BTC': 0.0
            }
        else:
            allocations = {
                'AVL': params['security_budget_pct_after_btc'].get('AVL', 0.5),
                'ETH': params['security_budget_pct_after_btc'].get('ETH', 0.2),
                'BTC': params['security_budget_pct_after_btc'].get('BTC', 0.3)
            }
        pool_manager.allocate_budget(allocations)
    
    # Calculate required rewards based on target yields
    timesteps_per_year = 365 / DELTA_TIME
    avl_price = agents['avl_maxi'].assets['AVL'].price
    
    required_rewards = {}
    for asset, yield_pct in target_yields.items():
        # Skip assets not yet activated (BTC before activation day)
        if asset == 'BTC' and timestep < btc_activation:
            continue
            
        agent = agents[f"{asset.lower()}_maxi"]
        annual_rewards_usd = agent.total_tvl * yield_pct
        annual_rewards_avl = annual_rewards_usd / avl_price
        
        # Store required rewards
        required_rewards[asset] = annual_rewards_avl
    
    # Allocate rewards with pool manager constraints
    for asset, amount in required_rewards.items():
        agent_key = f"{asset.lower()}_maxi"
        # Get daily rewards with budget constraints
        daily_amount = amount / timesteps_per_year
        actual_rewards = pool_manager.get_pool_rewards(asset, daily_amount)
        
        # Apply rewards to agent
        if actual_rewards > 0:
            agents[agent_key].add_rewards(actual_rewards * timesteps_per_year)
        else:
            agents[agent_key].add_rewards(0)
    
    # Log pool manager state for this timestep
    if pool_manager and timestep % 1 == 0:  # Log every timestep (adjust frequency if needed)
        log_pool_manager_state(timestep, pool_manager, agents)
    
    return {
        "target_yields": target_yields,
        "pool_manager": pool_manager,
        "agents": agents
    }

def log_pool_manager_state(timestep, pool_manager, agents):
    """Log detailed pool manager state for tracking"""
    budget_summary = pool_manager.get_budget_summary()
    active_pools = pool_manager.get_active_pools()
    
    # Header with timestep and budget summary
    print(f"\n{'='*80}")
    print(f"DAY {timestep} - POOL MANAGER STATUS")
    print(f"{'='*80}")
    
    # Budget information
    print(f"BUDGET SUMMARY:")
    print(f"  Initial Budget:       {budget_summary['initial_budget']:,.2f} AVL")
    print(f"  Current Total Budget: {budget_summary['current_total_budget']:,.2f} AVL")
    print(f"  Allocated Budget:     {budget_summary['allocated_budget']:,.2f} AVL")
    print(f"  Spent Budget:         {budget_summary['spent_budget']:,.2f} AVL")
    print(f"  Unallocated Budget:   {budget_summary['unallocated_budget']:,.2f} AVL")
    print(f"  Utilization:          {budget_summary['budget_utilization_pct']:.2f}%")
    
    # Pool allocation information
    print(f"\nPOOL ALLOCATIONS:")
    remaining_budget = pool_manager.get_remaining_budget()
    for pool in sorted(remaining_budget.keys()):
        agent_key = f"{pool.lower()}_maxi"
        
        # Get pool status
        is_paused = pool in pool_manager._paused_deposits
        is_deleted = pool in pool_manager._deleted_pools
        cap_paused = pool in pool_manager._cap_paused_deposits
        status = "DELETED" if is_deleted else ("PAUSED" if is_paused else "ACTIVE")
        
        # Get agent data
        agent_tvl = agents[agent_key].total_tvl if agent_key in agents else 0
        agent_yield = agents[agent_key].current_yield * 100 if agent_key in agents else 0
        
        # Get pool config
        pool_config = pool_manager.pools.get(pool, {})
        max_cap = pool_config.get('max_cap', float('inf'))
        cap_display = f"{max_cap:,.2f}" if max_cap < float('inf') else "∞"
        
        # Print pool info
        print(f"  {pool}:")
        print(f"    Status:           {status}{' (CAP REACHED)' if cap_paused else ''}")
        print(f"    Remaining Budget: {remaining_budget[pool]:,.2f} AVL")
        print(f"    Current TVL:      ${agent_tvl:,.2f}")
        print(f"    Current Yield:    {agent_yield:.2f}%")
        print(f"    Max Cap:          ${cap_display}")
    
    print(f"{'='*80}\n")




###########################
# update inflation and rewards allocation
###########################
## TODO: need to verify with Gali on how to update rewards allocation

def policy_update_inflation_and_rewards(params, step, h, s):
    """Calculate inflation and rewards allocation using agent-based metrics"""
    # Get core parameters
    agents = s['agents']
    avl_agent = agents['avl_maxi']
    
    # Extract AVL price from agent assets
    avl_price = avl_agent.assets['AVL'].price
    total_supply = params['constants']['total_supply']
    
    # Calculate current staking ratio from state
    staking_ratio = s['staking_ratio_all']
    
    # Calculate inflation rate using curve parameters
    inflation_rate = calc_inflation_rate(
        staking_ratio=staking_ratio,
        inflation_decay=params['inflation_decay'],
        target_staking_rate=params['target_staking_rate'],
        min_inflation_rate=params['min_inflation_rate'],
        max_inflation_rate=params['max_inflation_rate']
    )
    
    # Calculate total rewards
    total_annual_inflation_rewards_in_avl = total_supply * inflation_rate
    total_annual_inflation_rewards_usd = total_annual_inflation_rewards_in_avl * avl_price
    total_fdv = total_supply * avl_price
    


    return {
        "total_annual_inflation_rewards_in_avl": total_annual_inflation_rewards_in_avl,
        "total_annual_inflation_rewards_usd": total_annual_inflation_rewards_usd,
        "total_fdv": total_fdv,
        "inflation_rate": inflation_rate
    }

###########################
# security shares and rewards allocation
###########################


def policy_calc_security_shares(params, step, h, s):
    """Calculate security shares and allocate rewards using agent-based structure"""
    agents = s['agents'].copy()
    pool_manager = s.get('pool_manager')
    total_security = 0
    staking_ratio_fusion = {}
    
    # Get active pools from pool manager
    if pool_manager:
        active_pools = [pool for pool in pool_manager._allocated_budgets.keys() 
                       if pool not in pool_manager._deleted_pools]
    else:
        active_pools = []
        
    # Calculate total security from active pools
    for asset in active_pools:
        agent_key = f'{asset.lower()}_maxi'
        if agent_key in agents:
            total_security += agents[agent_key].total_tvl
            
    # Calculate staking ratio for each active pool
    for asset in active_pools:
        agent_key = f'{asset.lower()}_maxi'
        if agent_key in agents:
            staking_ratio_fusion[asset] = (agents[agent_key].total_tvl / total_security 
                                         if total_security > 0 else 0.0)
    
    return {
        "total_security": total_security,
        "staking_ratio_all": agents['avl_maxi'].total_tvl / s["total_fdv"] + params["native_staking_ratio"],
        "staking_ratio_fusion": staking_ratio_fusion
    }










# def calc_agents_balances(params, step, h, s):
#     ETH_security_share = params["ETH_upper_security_pct"]
#     AVL_security_share = params["AVL_upper_security_pct"]
#     #print("ETH_security_share", ETH_security_share)
#     init_agent_eth_alloc = params["ETH_agent_allocation"] ## [1.0,0.0]
#     init_agent_avl_alloc = params["AVL_agent_allocation"] ## [0.0,1.0]

#     total_security = s["total_security"]
#     avl_price = s["avl_price"]
#     eth_price = s["eth_price"]
#     t = s["timestep"]

#     avl_stake = copy.deepcopy(s["AVL_stake"])
#     eth_stake = copy.deepcopy(s["ETH_stake"])

#     #print("run", s['run'])

#     agents_composition = [ETH_security_share, AVL_security_share]

#     AVL_security_pct = [ i*j for i,j in zip(init_agent_avl_alloc, agents_composition)]
#     ETH_security_pct = [ i*j for i,j in zip(init_agent_eth_alloc, agents_composition)]

#     if t == 0:
#         agents_avl_balance = [total_security * pct / avl_price for pct in AVL_security_pct]
#         agents_eth_balance = [total_security * pct / eth_price for pct in ETH_security_pct]
#     else:
#         agents_avl_balance = avl_stake.agents_balances
#         agents_eth_balance = eth_stake.agents_balances

#     avl_stake.update_balances(agents_avl_balance)
#     eth_stake.update_balances(agents_eth_balance)

#     return ({
#         "AVL_stake": avl_stake,
#         "ETH_stake": eth_stake,
#     })

    





