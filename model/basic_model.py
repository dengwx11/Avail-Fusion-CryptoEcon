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
    if s["timestep"] % 1 == 0: # update token prices every 7 timesteps
        for asset in ['AVL', 'ETH', 'BTC']:
            # Get the new price for the current asset from its price process
            new_price = locals()[f"{asset.lower()}_price_process"](s["timestep"])
            # Update all agents with new AVL price
            # Create kwargs dict to pass the updated price for the current asset
            price_kwargs = {f"{asset.lower()}_price": new_price}
            AgentStake.update_agent_prices(agents, **price_kwargs)
        print("[DEBUG] update_token_prices")
        #print(agents)
    return ({"agents": agents})



###########################
# admin change encoded params for targeting yields
###########################


def policy_tune_rewards_allocation(params, step, h, s):
    """
    Calculate and allocate rewards to agents based on their staked assets and boosting multipliers.
    
    For AVL staking, applies boosting multipliers based on:
    1. Lock period (longer locks get higher multipliers)
    2. Pool share (larger stakes get higher multipliers)
    """
    timestep = s["timestep"]
    agents = s['agents'].copy()
    pool_manager = s.get('pool_manager')
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
    budget_replenishment = params.get("security_budget_replenishment", {}).get(timestep)
    if budget_replenishment:
        # Admin is adding new tokens to specific pools
        print(f"\n{'$'*80}")
        print(f"SECURITY BUDGET REPLENISHMENT - DAY {timestep}")
        print(f"{'$'*80}")
        
        total_replenishment = sum(budget_replenishment.values())
        print(f"Adding {total_replenishment:,.0f} AVL tokens to security budget")
        
        # Update pool manager's total budget
        pool_manager.total_budget += total_replenishment
        
        # Add new allocation directly to each specified pool's budget
        for pool, amount in budget_replenishment.items():
            if pool not in pool_manager._deleted_pools:
                # Add the replenishment amount to the pool's allocated budget
                pool_manager._allocated_budgets[pool] = pool_manager._allocated_budgets.get(pool, 0) + amount
                print(f"  {pool} pool: +{amount:,.0f} AVL tokens")
        
        print(f"{'$'*80}\n")
    
    # Get boosting parameters
    avl_boosting_enabled = params.get('avl_boosting_enabled', True)
    lock_multipliers = params.get('avl_lock_period_multipliers', {})
    share_multipliers = params.get('avl_pool_share_multipliers', {})
    
    # Process unlocks for all agents at the start of each timestep
    for agent in agents.values():
        unlocked_amount = agent.process_avl_unlocks(timestep)
        if unlocked_amount > 0:
            print(f"  {agent.id}: Unlocked {unlocked_amount:.2f} AVL tokens")
    
    # Get current AVL price for calculations
    avl_price = agents['avl_maxi'].assets['AVL'].price
    
    # Calculate total AVL pool balance for share calculations
    total_avl_pool_balance = sum(
        agent.assets['AVL'].balance for agent in agents.values() 
        if 'AVL' in agent.assets
    )
    
    print(f"\n💰 REWARDS ALLOCATION - DAY {timestep}")
    print(f"{'='*60}")
    print(f"AVL Price: ${avl_price:.4f}")
    print(f"Total AVL Pool Balance: {total_avl_pool_balance:,.2f} AVL")
    print(f"AVL Boosting Enabled: {avl_boosting_enabled}")
    
    # Dictionary to store required rewards for each asset type
    required_rewards = {}
    
    # Calculate required rewards for each asset type
    for asset_type in ['AVL', 'ETH', 'BTC']:
        # Skip assets not yet activated (BTC before activation day)
        if asset_type == 'BTC' and (timestep < btc_activation or 'BTC' not in pool_manager.pools):
            continue
        
        # Skip rewards calculation if asset's yield is not defined
        if asset_type not in target_yields:
            continue
        
        yield_pct = target_yields[asset_type]
        annual_rewards_avl = 0.0
        
        print(f"\n--- {asset_type} Pool ---")
        
        # For each agent, calculate rewards for this asset type
        for agent_name, agent in agents.items():
            # Only calculate rewards for this asset if agent holds it
            if asset_type in agent.assets and agent.assets[asset_type].balance > 0:
                asset_balance = agent.assets[asset_type].balance
                asset_price = agent.assets[asset_type].price
                asset_tvl = asset_balance * asset_price
                
                # Calculate base rewards
                base_annual_rewards_usd = asset_tvl * yield_pct
                base_annual_rewards_avl = base_annual_rewards_usd / avl_price
                
                # Apply boosting for AVL assets
                if asset_type == 'AVL' and avl_boosting_enabled:
                    boost_multiplier = agent.calculate_avl_boost_multiplier(
                        total_avl_pool_balance, lock_multipliers, share_multipliers
                    )
                    
                    # Get lock distribution for display
                    lock_distribution = agent.get_avl_lock_distribution()
                    unlocked_balance = agent.assets['AVL'].unlocked_balance
                    pool_share_pct = (asset_balance / total_avl_pool_balance * 100) if total_avl_pool_balance > 0 else 0
                    
                    print(f"  {agent_name}: TVL: ${asset_tvl:,.2f}")
                    print(f"    Unlocked: {unlocked_balance:.2f} AVL")
                    if lock_distribution:
                        for period, amount in lock_distribution.items():
                            print(f"    Locked {period}d: {amount:.2f} AVL")
                    print(f"    Pool Share: {pool_share_pct:.3f}%")
                    print(f"    Boost Multiplier: {boost_multiplier:.3f}x")
                    
                    # Apply boost to rewards
                    boosted_annual_rewards_avl = base_annual_rewards_avl * boost_multiplier
                    annual_rewards_avl += boosted_annual_rewards_avl
                    
                    print(f"    Base Rewards: {base_annual_rewards_avl:,.2f} AVL/year")
                    print(f"    Boosted Rewards: {boosted_annual_rewards_avl:,.2f} AVL/year")
                else:
                    # No boosting for non-AVL assets or when boosting is disabled
                    annual_rewards_avl += base_annual_rewards_avl
                    
                    print(f"  {agent_name}: {asset_type} TVL: ${asset_tvl:,.2f}, "
                          f"Yield: {yield_pct*100:.2f}%, "
                          f"Rewards: {base_annual_rewards_avl:,.2f} AVL/year")
        
        # Store the total required rewards for this asset type
        required_rewards[asset_type] = annual_rewards_avl
    
    # Allocate rewards to each agent with pool manager constraints
    agent_rewards = {agent_name: 0.0 for agent_name in agents.keys()}
    
    for asset_type, total_required in required_rewards.items():
        if total_required <= 0:
            continue
            
        # Get actual rewards from pool manager (may be capped by budget)
        actual_rewards = pool_manager.get_pool_rewards(asset_type, total_required)
        
        # Calculate scaling factor if rewards were capped
        scaling_factor = actual_rewards / total_required if total_required > 0 else 0
        
        # Check for excessive unused budget (potential issue indicator)
        remaining_budget = pool_manager._allocated_budgets.get(asset_type, 0)
        if remaining_budget > total_required * 10:  # More than 10x required budget
            print(f"⚠️  WARNING: {asset_type} pool has excessive unused budget: {remaining_budget:,.0f} AVL")
            print(f"   Required: {total_required:,.0f} AVL, Ratio: {remaining_budget/total_required:.1f}x")
        
        if scaling_factor < 1.0:
            print(f"\n⚠️  {asset_type} pool budget constraint: {scaling_factor:.1%} of requested rewards allocated")
            
            # Mark pool as having zero yield due to budget depletion
            if scaling_factor <= 0.01:  # Less than 1% of requested rewards
                pool_manager._zero_yield_pools.add(asset_type)
                print(f"🚨 {asset_type} pool marked as budget-depleted (zero yield)")
        
        # Distribute actual rewards proportionally to agents
        for agent_name, agent in agents.items():
            if asset_type in agent.assets and agent.assets[asset_type].balance > 0:
                asset_balance = agent.assets[asset_type].balance
                asset_price = agent.assets[asset_type].price
                asset_tvl = asset_balance * asset_price
                
                # Calculate base agent rewards
                base_agent_rewards_usd = asset_tvl * target_yields[asset_type]
                base_agent_rewards_avl = base_agent_rewards_usd / avl_price
                
                # Apply boosting for AVL
                if asset_type == 'AVL' and avl_boosting_enabled:
                    boost_multiplier = agent.calculate_avl_boost_multiplier(
                        total_avl_pool_balance, lock_multipliers, share_multipliers
                    )
                    boosted_agent_rewards_avl = base_agent_rewards_avl * boost_multiplier
                    final_agent_rewards = boosted_agent_rewards_avl * scaling_factor
                else:
                    final_agent_rewards = base_agent_rewards_avl * scaling_factor
                
                agent_rewards[agent_name] += final_agent_rewards
    
    # Apply rewards to agents
    for agent_name, reward_amount in agent_rewards.items():
        if reward_amount > 0:
            agents[agent_name].add_rewards(reward_amount)
    
    print(f"\n📊 Final Reward Summary:")
    for agent_name, reward_amount in agent_rewards.items():
        if reward_amount > 0:
            print(f"  {agent_name}: {reward_amount:,.2f} AVL/year")
    
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
    
    # Spent budget per pool
    spent_budget_per_pool = budget_summary.get('spent_budget_per_pool', {})
    if spent_budget_per_pool:
        print(f"\nSPENT BUDGET PER POOL:")
        for pool, spent in sorted(spent_budget_per_pool.items()):
            print(f"  {pool}: {spent:,.2f} AVL")
    
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
        print(f"    Spent Budget:     {spent_budget_per_pool.get(pool, 0):,.2f} AVL")
        print(f"    Current TVL:      ${agent_tvl:,.2f}")
        print(f"    Current Yield:    {agent_yield:.2f}%")
        print(f"    Max Cap:          ${cap_display}")
    
    print(f"{'='*80}\n")




###########################
# update inflation and rewards allocation
###########################

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
    """
    Calculate security shares and allocate rewards using agent-based structure
    
    Accounts for all tokens across all agents, including those
    accumulated through restaking, when calculating staking ratios.
    """
    agents = s['agents'].copy()
    pool_manager = s.get('pool_manager')
    
    # Dictionary to store TVL for each asset
    tvl = {}
    
    # New: Dictionary to store actual token balances for each asset
    staked_token_balances = {}
    
    # Get active pools from pool manager
    if pool_manager:
        active_pools = [pool for pool in pool_manager._allocated_budgets.keys() 
                       if pool not in pool_manager._deleted_pools]
    else:
        active_pools = []
    
    # Make sure we're always tracking AVL TVL, even if not in active pools
    all_assets = set(active_pools)
    all_assets.add('AVL')  # Always include AVL
    
    # Calculate TVL and token balances for each asset type by summing across all agents
    for asset in all_assets:
        tvl[asset] = 0
        staked_token_balances[asset] = 0
        
        for agent_name, agent in agents.items():
            if asset in agent.assets:
                # Get asset balance and price for this agent
                asset_balance = agent.assets[asset].balance
                asset_price = agent.assets[asset].price
                
                # Add to asset's TVL
                tvl[asset] += asset_balance * asset_price
                
                # Add to asset's token balance total
                staked_token_balances[asset] += asset_balance
    
    # Calculate total security as the sum of all TVLs from active pools only
    total_security = sum(tvl[asset] for asset in active_pools if asset in tvl)
    
    # Calculate staking ratio for each active pool
    staking_ratio_fusion = {}
    for asset in active_pools:
        staking_ratio_fusion[asset] = (tvl[asset] / total_security 
                                     if total_security > 0 else 0.0)
    
    # Calculate staking ratio using total AVL value
    staking_ratio_all = tvl['AVL'] / s["total_fdv"] if s["total_fdv"] > 0 else 0
    
    return {
        "total_security": total_security,
        "staking_ratio_all": staking_ratio_all + params["native_staking_ratio"],
        "staking_ratio_fusion": staking_ratio_fusion,
        "tvl": tvl,
        "staked_token_balances": staked_token_balances  # New state variable
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

    






###########################
# admin pool actions
###########################

def policy_admin_pool_actions(params, step, h, s):
    """
    Policy to execute admin actions on pools at specified timesteps:
    - Pause deposits for specific pools
    - Resume deposits for specific pools
    - Delete specific pools
    """
    timestep = s["timestep"]
    pool_manager = s.get("pool_manager")
    admin_actions_performed = False
    
    if not pool_manager:
        return {"pool_manager": pool_manager}
    
    # Check for admin pause deposits
    pause_deposits = params.get("admin_pause_deposits", {}).get(timestep, [])
    if pause_deposits:
        for pool_type in pause_deposits:
            if pool_type in pool_manager.get_active_pools():
                pool_manager.pause_deposits(pool_type)
                print(f"ADMIN ACTION: Paused deposits for {pool_type} pool at day {timestep}")
                admin_actions_performed = True
    
    # Check for admin resume deposits
    resume_deposits = params.get("admin_resume_deposits", {}).get(timestep, [])
    if resume_deposits:
        for pool_type in resume_deposits:
            if pool_type in pool_manager.pools and pool_type in pool_manager._paused_deposits:
                pool_manager.resume_deposits(pool_type)
                print(f"ADMIN ACTION: Resumed deposits for {pool_type} pool at day {timestep}")
                admin_actions_performed = True
    
    # Check for admin delete pools
    delete_pools = params.get("admin_delete_pools", {}).get(timestep, [])
    if delete_pools:
        for pool_type in delete_pools:
            if pool_type in pool_manager.get_active_pools():
                # Add the pool to deleted pools
                pool_manager._deleted_pools.add(pool_type)
                # Also pause deposits for the deleted pool
                pool_manager.pause_deposits(pool_type)
                print(f"ADMIN ACTION: Deleted {pool_type} pool at day {timestep}")
                admin_actions_performed = True
    
    # Log all admin actions in detail if any were performed
    if admin_actions_performed:
        print(f"\n{'#'*80}")
        print(f"ADMIN POOL ACTIONS - DAY {timestep}")
        print(f"{'#'*80}")
        print(f"Active pools after admin actions: {pool_manager.get_active_pools()}")
        print(f"Paused deposits: {pool_manager._paused_deposits}")
        print(f"Deleted pools: {pool_manager._deleted_pools}")
        print(f"{'#'*80}\n")
    
    return {"pool_manager": pool_manager}





