#### Cold Start Staking Policy ####
# No ETH staking, only AVAIL staking: new_avail_deposit_daily_factor_dollar = 1e6
# No AVAIL staking, only ETH staking: new_deposit_daily_factor_dollar = 5e6
# Cold start duration: 12 months


def cold_start_staking_policy(params, substep, state_history, previous_state):
    # Get current simulation state
    timestep = previous_state['timestep']
    yield_pcts = previous_state['yield_pcts']

    
    # Get cold start parameters from notebook
    cold_start_duration = params['COLD_START_DURATION_TIMESTEPS']
    avail_deposit_factor = params['NEW_AVAIL_DEPOSIT_DAILY_FACTOR_DOLLAR']
    eth_deposit_factor = params['NEW_ETH_DEPOSIT_DAILY_FACTOR_DOLLAR']
    
    # Calculate boosted rewards during cold start
    
    
    # Calculate daily yield percentage (convert APR to daily)
    eth_yield_pct = yield_pcts[0]  
    avl_yield_pct = yield_pcts[1]

    if timestep < cold_start_duration:
        eth_yield_pct *= params['COLD_START_BOOST_FACTOR']
        avl_yield_pct *= params['COLD_START_BOOST_FACTOR']
    
    # Calculate new deposits based on yield and factors from notebook
    new_avail_deposit = avail_deposit_factor * avl_yield_pct * previous_state['AVL_security_pct']
    new_eth_deposit = eth_deposit_factor * eth_yield_pct * previous_state['ETH_security_pct']

    print("[COLD START] new_avail_deposit is " + str(new_avail_deposit))
    print("[COLD START] new_eth_deposit is " + str(new_eth_deposit))
    
    return {
        'new_avail_deposit': new_avail_deposit,
        'new_eth_deposit': new_eth_deposit
    }

def update_validators_cold_start_avl(params, substep, state_history, previous_state, policy_input):
    # Existing validator update logic
    AVL_stake = previous_state["AVL_stake"]
    avl_price = previous_state["avl_price"]

    AVL_security_share = params["AVL_upper_security_pct"]
    init_agent_avl_alloc = params["AVL_agent_allocation"] ## [0.0,1.0]

    new_avail_deposit = policy_input['new_avail_deposit']

    # Get cold start duration from notebook params
    cold_start_duration = params['COLD_START_DURATION_TIMESTEPS']
    

    agents_avl_balance = AVL_stake.agents_balances + new_avail_deposit/avl_price
    agents_avl_balance *= init_agent_avl_alloc
    print("[COLD START] agents_avl_balance is " + str(agents_avl_balance))
    AVL_stake.update_balances(agents_avl_balance)
    AVL_stake.update_price(avl_price)
    AVL_stake.set_upper_bound()
    
    print("[COLD START] AVL_stake is " + str(AVL_stake.agents_balances))
    print("[COLD START] AVL_stake is " + str(AVL_stake.agents_scaled_balances))
    
    return ( "AVL_stake", AVL_stake)

def update_validators_cold_start_eth(params, substep, state_history, previous_state, policy_input):
    ETH_stake = previous_state["ETH_stake"]
    eth_price = previous_state["eth_price"]

    ETH_security_share = params["ETH_upper_security_pct"]
    init_agent_eth_alloc = params["ETH_agent_allocation"] ## [0.0,1.0]

    new_eth_deposit = policy_input['new_eth_deposit']

    # Get cold start duration from notebook params
    cold_start_duration = params['COLD_START_DURATION_TIMESTEPS']
    
    agents_eth_balance = ETH_stake.agents_balances + new_eth_deposit/eth_price
    agents_eth_balance *= init_agent_eth_alloc
    print("[COLD START] agents_eth_balance is " + str(agents_eth_balance))
    ETH_stake.update_balances(agents_eth_balance)
    ETH_stake.update_price(eth_price)
    ETH_stake.set_upper_bound()
    print("[COLD START] ETH_stake is " + str(ETH_stake.agents_balances))
    print("[COLD START] ETH_stake is " + str(ETH_stake.agents_scaled_balances))
    
    return ("ETH_stake", ETH_stake)

