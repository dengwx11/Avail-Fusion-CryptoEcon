"""
Misc. utility and helper functions
"""

import copy
from dataclasses import field
from functools import partial
import csv
import os
from datetime import datetime


def _update_from_signal(
    state_variable,
    signal_key,
    params,
    substep,
    state_history,
    previous_state,
    policy_input,
):
    return state_variable, policy_input[signal_key]


def update_from_signal(state_variable, signal_key=None):
    """A generic State Update Function to update a State Variable directly from a Policy Signal

    Args:
        state_variable (str): State Variable key
        signal_key (str, optional): Policy Signal key. Defaults to None.

    Returns:
        Callable: A generic State Update Function
    """
    if not signal_key:
        signal_key = state_variable
    return partial(_update_from_signal, state_variable, signal_key)


def local_variables(_locals):
    return {
        key: _locals[key]
        for key in [_key for _key in _locals.keys() if "__" not in _key]
    }


def default(obj):
    return field(default_factory=lambda: copy.copy(obj))

def generic_state_updater(field_name: str):
    """Factory function to create state update functions"""
    def update_state(params, step, h, s, _input):
        return (field_name, _input.get(field_name, s.get(field_name)))
    return update_state

def log_pool_data_to_csv(results, filename=None):
    """
    Create a CSV file with pool management data from simulation results
    
    Args:
        results: Simulation results dictionary
        filename: Optional filename, defaults to timestamped file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pool_manager_log_{timestamp}.csv"
    
    # Extract data
    data = []
    for day, state in enumerate(results):
        if 'pool_manager' not in state:
            continue
            
        pool_manager = state['pool_manager']
        budget_summary = pool_manager.get_budget_summary()
        remaining_budget = pool_manager.get_remaining_budget()
        
        # Get agent data
        agents = state['agents']
        
        # Create row for each pool
        for pool in pool_manager.get_active_pools():
            agent_key = f"{pool.lower()}_maxi"
            agent = agents.get(agent_key)
            
            if not agent:
                continue
                
            row = {
                'day': day,
                'pool': pool,
                'status': 'DELETED' if pool in pool_manager._deleted_pools else 
                         ('PAUSED' if pool in pool_manager._paused_deposits else 'ACTIVE'),
                'remaining_budget': remaining_budget.get(pool, 0),
                'tvl': agent.total_tvl,
                'yield_pct': agent.current_yield * 100,
                'total_budget': budget_summary['current_total_budget'],
                'spent_budget': budget_summary['spent_budget'],
                'budget_utilization': budget_summary['budget_utilization_pct']
            }
            data.append(row)
    
    # Write to CSV
    if not data:
        print("No pool data to log")
        return
        
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)
            
    print(f"Pool management data logged to {filename}")