from model.agents_class import AgentStake
import copy
from model.rewards import calc_inflation_rate

###########################
# environment
###########################

def update_timestep(params, step, h, s, _input):
    timestep = s['timestep']
    
    return "timestep", timestep+1

def policy_update_token_prices(params, step, h, s):
    avl_price_process = params["avl_price_process"]
    avl_new_price = avl_price_process(s["timestep"])
    eth_price_process = params["eth_price_process"]
    eth_new_price = eth_price_process(s["timestep"])
    
    # Update all agents with new AVL price
    agents = s['agents'].copy()
    AgentStake.update_agent_prices(agents, avl_price=avl_new_price, eth_price=eth_new_price)
    print("[DEBUG] update_token_prices")
    print(agents)
    return ({"agents": agents})



###########################
# admin change encoded params for targeting yields
###########################

def policy_tune_rewards_allocation(params, step, h, s):
    
    avl_rewards_allocation = s["avl_rewards_allocation"]
    fusion_rewards_allocation = s["fusion_rewards_allocation"]

    return ({
        "avl_rewards_allocation": avl_rewards_allocation,
        "fusion_rewards_allocation": fusion_rewards_allocation
        })


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
    
    # Calculate fusion rewards allocation
    fusion_allocation_pct = s['fusion_rewards_allocation']
    total_annual_rewards_fusion_usd = fusion_allocation_pct * total_annual_inflation_rewards_usd

    return {
        "total_annual_inflation_rewards_in_avl": total_annual_inflation_rewards_in_avl,
        "total_annual_inflation_rewards_usd": total_annual_inflation_rewards_usd,
        "total_annual_rewards_fusion_usd": total_annual_rewards_fusion_usd,
        "total_fdv": total_fdv,
        "inflation_rate": inflation_rate
    }

###########################
# security shares and rewards allocation
###########################


def policy_calc_security_shares(params, step, h, s):
    """Calculate security shares and allocate rewards using agent-based structure"""
    agents = s['agents'].copy()
    avl_agent = agents['avl_maxi']
    eth_agent = agents['eth_maxi']
    
    # Get core metrics from agents
    print(agents)
    avl_tvl = avl_agent.total_tvl
    eth_tvl = eth_agent.total_tvl
    total_security = avl_tvl + eth_tvl
    

    # Calculate rewards allocation
    total_rewards_in_avl = s["total_annual_inflation_rewards_in_avl"]
    avl_rewards = s["avl_rewards_allocation"] * total_rewards_in_avl
    eth_rewards = (1 - s["avl_rewards_allocation"]) * total_rewards_in_avl
    
    # Update agent rewards (converting USD to token amounts)
    avl_agent.add_rewards(avl_rewards)
    eth_agent.add_rewards(eth_rewards)
    
    return {
        "total_security": total_security,
        "agents": agents,
        "staking_ratio_all": avl_tvl / s["total_fdv"] + params["native_staking_ratio"] if total_security > 0 else 0.0 + params["native_staking_ratio"],
        "staking_ratio_avl_fusion": avl_tvl / total_security if total_security > 0 else 0.0,
        "staking_ratio_eth_fusion": eth_tvl / total_security if total_security > 0 else 0.0
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

    





