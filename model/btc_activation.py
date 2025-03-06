def policy_activate_btc_pool(params, substep, state_history, previous_state):
    """
    Policy to handle BTC pool activation at the specified timestep
    """
    timestep = previous_state['timestep']
    pool_manager = previous_state.get('pool_manager')
    btc_activation_day = params.get('btc_activation_day', 180)
    
    # Only run this when we've reached BTC activation day
    if timestep == btc_activation_day:
        print(f"\n{'*'*80}")
        print(f"BTC POOL ACTIVATION - DAY {timestep}")
        print(f"{'*'*80}")
        
        # Get BTC pool configuration from parameters
        btc_config = params.get('btc_pool_config', {
            # Default config as fallback
            'base_deposit': 1e5,
            'max_extra_deposit': 4e5,
            'deposit_k': 6.0,
            'apy_threshold': 0.02,
            'base_withdrawal': 8e3,
            'max_extra_withdrawal': 2e5,
            'withdrawal_k': 9.0,
            'max_cap': float('inf')
        })
        
        # Add BTC pool configuration to the pool manager
        pool_manager.pools['BTC'] = btc_config
        
        # Initialize BTC pool's budget allocation
        pool_manager._allocated_budgets['BTC'] = 0
        
        # Make sure BTC is not in paused or deleted pools
        if 'BTC' in pool_manager._paused_deposits:
            pool_manager._paused_deposits.remove('BTC')
            
        if 'BTC' in pool_manager._deleted_pools:
            pool_manager._deleted_pools.remove('BTC')
        
        # Log BTC activation
        print(f"BTC Pool Activated and Open for Deposits")
        print(f"Configuration:")
        for key, value in btc_config.items():
            print(f"  {key}: {value}")
        
        print(f"Current budget allocations:")
        for asset, amount in pool_manager._allocated_budgets.items():
            print(f"  {asset}: {amount:,.0f} AVL tokens")
        
        print(f"{'*'*80}\n")
    
    return {'pool_manager': pool_manager} 