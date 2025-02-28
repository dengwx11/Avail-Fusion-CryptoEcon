def policy_activate_btc_pool(params, substep, state_history, previous_state):
    """
    Policy to handle BTC pool activation at the specified timestep
    """
    timestep = previous_state['timestep']
    pool_manager = previous_state.get('pool_manager')
    btc_activation_day = params.get('btc_activation_day', 180)
    
    # Check if we've reached BTC activation day
    if timestep == btc_activation_day:
        print(f"\n{'*'*80}")
        print(f"BTC POOL ACTIVATION - DAY {timestep}")
        print(f"{'*'*80}")
        
        # Update pool allocation percentages
        new_allocations = {
            'AVL': params['security_budget_pct_after_btc'].get('AVL', 0.5),
            'ETH': params['security_budget_pct_after_btc'].get('ETH', 0.2),
            'BTC': params['security_budget_pct_after_btc'].get('BTC', 0.3)
        }
        
        # Update pool manager allocations
        pool_manager.allocate_budget(new_allocations)
        
        # Configure BTC pool with specified parameters
        btc_config = {
            'base_deposit': 1e5,
            'max_extra_deposit': 4e5,
            'deposit_k': 6.0,
            'apy_threshold': 0.02,  # 2%
            'base_withdrawal': 8e3,
            'max_extra_withdrawal': 2e5,
            'withdrawal_k': 9.0,
            'max_cap': float('inf')
        }
        
        # Update BTC pool configuration
        pool_manager.pools['BTC'] = btc_config
        
        # Resume BTC deposits (ensure it's active)
        pool_manager.resume_deposits('BTC')
        
        # Log the BTC pool configuration
        print(f"BTC Pool Configuration:")
        for key, value in btc_config.items():
            print(f"  {key}: {value}")
        
        print(f"New budget allocations:")
        for asset, allocation in new_allocations.items():
            print(f"  {asset}: {allocation*100:.1f}%")
        
        print(f"{'*'*80}\n")
    
    return {'pool_manager': pool_manager} 