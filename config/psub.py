import model.basic_model as basic_model
import model.cold_start as cold_start
import model.agents as agents

psub = [
    {
        "policies": {
             },
        "variables": {
            "timestep": basic_model.update_timestep,
            "avl_price": basic_model.update_avl_price,
            "eth_price": basic_model.update_eth_price,
        }
    }, {
        "policies": {
            "action":basic_model.policy_tune_rewards_allocation
             },
        "variables": {
            "rewards_allocation": basic_model.update_rewards_allocation,
        }
    }, 
    {
        "policies": {
            "action":cold_start.cold_start_staking_policy
             },
        "variables": {
            "AVL_stake": cold_start.update_validators_cold_start_avl,
            "ETH_stake": cold_start.update_validators_cold_start_eth
        }
    },
    {
        "policies": {
            "action":basic_model.calc_rewards
             },
        "variables": {
            "total_annual_rewards": basic_model.update_total_annual_rewards,
            "total_annual_rewards_fusion": basic_model.update_total_annual_rewards_fusion,
            "total_fdv": basic_model.update_total_fdv,
            "inflation_rate": basic_model.update_inflation_rate,
        }
    }, 
    
    {
        "policies": {
            "action": basic_model.calc_security_shares
            },
            "variables": {
                "AVL_security_pct": basic_model.update_AVL_pct,
                "ETH_security_pct": basic_model.update_ETH_pct,
                "total_security": basic_model.update_total_security,
                "ETH_stake": basic_model.update_ETH_stake,
                "AVL_stake": basic_model.update_AVL_stake,
                "staking_ratio_all": basic_model.update_staking_ratio_all,  
                "staking_ratio_avl": basic_model.update_staking_ratio_avl,
                "staking_ratio_eth": basic_model.update_staking_ratio_eth,
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
        "policies": {
            "action": agents.calc_rewards_allocation
            },
            "variables": {
                "AVL_stake": agents.update_AVL_stake,
                "ETH_stake": agents.update_ETH_stake,
            }
    },
    {
        "policies": {
            "action": agents.calc_yields
            },
            "variables": {
                "yield_pcts": agents.update_yields,
                "avg_yield": agents.update_avg_yield,
            }
    },
]