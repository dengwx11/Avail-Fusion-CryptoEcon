import model.basic_model as basic_model
import model.cold_start as cold_start
import model.yield_apy as yield_apy
import model.utils as utils
import model.btc_activation as btc_activation

psub = [
    {
        "policies": { # basic environment: timestep and token prices
            "action": basic_model.policy_update_token_prices
             },
        "variables": {
            "timestep": basic_model.update_timestep,
            "agents": utils.generic_state_updater("agents"),
        }
    }, 
    {
        "policies": { # cold start if timestep < COLD_START_DURATION_TIMESTEPS
            "action":cold_start.policy_cold_start_staking
             },
        "variables": {
            "agents": utils.generic_state_updater("agents"),
        }
    },
    
    {
        "policies": { # update all system metrics and rewards allocation
            "action": basic_model.policy_calc_security_shares
            },
            "variables": {
                "total_security": utils.generic_state_updater("total_security"),
                "staking_ratio_all": utils.generic_state_updater("staking_ratio_all"),  
                "staking_ratio_fusion": utils.generic_state_updater("staking_ratio_fusion"),
            }
    }, 
    # {
    #     "policies": {
    #         "action": basic_model.calc_agents_balances
    #         },
    #         "variables": {
    #             "ETH_stake": basic_model.update_ETH_stake,
    #             "AVL_stake": basic_model.update_AVL_stake,
    #         }
    # },
    {
        "policies": { # calculate yields for each agent
            "action": yield_apy.policy_calc_yields
            },
            "variables": {
                "yield_pcts": utils.generic_state_updater("yield_pcts"),
                "avg_yield": utils.generic_state_updater("avg_yield"),
            }
    },
    {
        "policies": { # update inflation and rewards allocation for next timestep
            "action":basic_model.policy_update_inflation_and_rewards
             },
        "variables": {
            "total_annual_inflation_rewards_in_avl": utils.generic_state_updater("total_annual_inflation_rewards_in_avl"),
            "total_annual_inflation_rewards_usd": utils.generic_state_updater("total_annual_inflation_rewards_usd"),
            "total_fdv": utils.generic_state_updater("total_fdv"),
            "inflation_rate": utils.generic_state_updater("inflation_rate"),
        }
    },
    {
        "policies": {
            "action": btc_activation.policy_activate_btc_pool
        },
        "variables": {
            "pool_manager": utils.generic_state_updater("pool_manager"),
        }
    },
    {
        "policies": {
            "action": basic_model.policy_tune_rewards_allocation
        },
        "variables": {
            "target_yields": utils.generic_state_updater("target_yields"),
            "pool_manager": utils.generic_state_updater("pool_manager"),
            "agents": utils.generic_state_updater("agents"),
        }
    }
]