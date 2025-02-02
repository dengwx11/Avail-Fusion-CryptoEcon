from model.agents_class import AgentStake
import copy
from model.rewards import calc_inflation_rate

###########################
# environment
###########################

def update_timestep(params, step, h, s, _input):
    timestep = s['timestep']
    
    return "timestep", timestep+1

def update_avl_price(params, step, h, s, _input):
    avl_price_process = params["avl_price_process"]
    
    avl_new_price = avl_price_process(s['run'],s["timestep"])
    
    return ("avl_price", avl_new_price)

def update_eth_price(params, step, h, s, _input):
    eth_price_process = params["eth_price_process"]
    
    eth_new_price = eth_price_process(s['run'],s["timestep"])

    
    return ("eth_price", eth_new_price)


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
# environment
###########################

def update_AVL_pct(params, step, h, s, _input):
    AVL_security_pct = _input["AVL_security_pct"]
    return ("AVL_security_pct", AVL_security_pct)

def update_ETH_pct(params, step, h, s, _input):
    ETH_security_pct = _input["ETH_security_pct"]
    return ("ETH_security_pct", ETH_security_pct)



def update_total_security(params, step, h, s, _input):
    total_security = _input["total_security"]
    return ("total_security", total_security)   






def calc_rewards(params, step, h, s):
    #print('calc_rewards')
    avl_price = s["avl_price"]
    staking_ratio = s['staking_ratio_avl']


    #inflation_rate = params["inflation_rate"]
    inflation_decay = params["inflation_decay"]
    target_staking_rate = params["target_staking_rate"]
    min_inflation_rate = params["min_inflation_rate"]
    max_inflation_rate = params["max_inflation_rate"]
    inflation_rate = calc_inflation_rate(staking_ratio, inflation_decay, target_staking_rate, min_inflation_rate, max_inflation_rate)
    #inflation_rate = calc_inflation_rate(staking_ratio)


    rewards_allocation = s['rewards_allocation']
    
    total_fdv = avl_price * 10000000000
    total_annual_rewards = total_fdv * inflation_rate
    total_annual_rewards_fusion = rewards_allocation * total_annual_rewards / 100


    return ({
        "total_annual_rewards": total_annual_rewards,
        "total_annual_rewards_fusion": total_annual_rewards_fusion,
        "total_fdv": total_fdv,
        "inflation_rate": inflation_rate
    })


def update_total_annual_rewards(params, step, h, s, _input):
    return ("total_annual_rewards",_input["total_annual_rewards"])  

def update_total_annual_rewards_fusion(params, step, h, s, _input):
    return ("total_annual_rewards_fusion",_input["total_annual_rewards_fusion"])  

def update_total_fdv(params, step, h, s, _input):
    return ("total_fdv", _input["total_fdv"]) 

def update_inflation_rate(params, step, h, s, _input):
    return ("inflation_rate", _input["inflation_rate"])


def calc_agents_balances(params, step, h, s):
    ETH_security_share = params["ETH_upper_security_pct"]
    AVL_security_share = params["AVL_upper_security_pct"]
    #print("ETH_security_share", ETH_security_share)
    init_agent_eth_alloc = params["ETH_agent_allocation"] ## [1.0,0.0]
    init_agent_avl_alloc = params["AVL_agent_allocation"] ## [0.0,1.0]

    total_security = s["total_security"]
    avl_price = s["avl_price"]
    eth_price = s["eth_price"]
    t = s["timestep"]

    avl_stake = copy.deepcopy(s["AVL_stake"])
    eth_stake = copy.deepcopy(s["ETH_stake"])

    #print("run", s['run'])

    agents_composition = [ETH_security_share, AVL_security_share]

    AVL_security_pct = [ i*j for i,j in zip(init_agent_avl_alloc, agents_composition)]
    ETH_security_pct = [ i*j for i,j in zip(init_agent_eth_alloc, agents_composition)]

    if t == 0:
        agents_avl_balance = [total_security * pct / avl_price for pct in AVL_security_pct]
        agents_eth_balance = [total_security * pct / eth_price for pct in ETH_security_pct]
    else:
        agents_avl_balance = avl_stake.agents_balances
        agents_eth_balance = eth_stake.agents_balances

    avl_stake.update_balances(agents_avl_balance)
    eth_stake.update_balances(agents_eth_balance)

    return ({
        "AVL_stake": avl_stake,
        "ETH_stake": eth_stake,
    })

    

def calc_security_shares(params, step, h, s):
    #print("calc security shares")
    avl_price = s["avl_price"]
    eth_price = s["eth_price"]
    total_annual_rewards_fusion = s["total_annual_rewards_fusion"]
    total_security = s["total_security"]
    total_fdv = s["total_fdv"]

    AVL_stake = s["AVL_stake"]
    ETH_stake = s["ETH_stake"]


    agents_avl_balance = AVL_stake.agents_balances
    agents_eth_balance = ETH_stake.agents_balances
    ETH_reward_pct = params["ETH_reward_pct"]
    AVL_reward_pct = params["AVL_reward_pct"]



    total_security = AVL_stake.upper_bound + ETH_stake.upper_bound

    if total_security != 0:
        AVL_security_pct = AVL_stake.upper_bound / total_security * 100
        ETH_security_pct = ETH_stake.upper_bound / total_security * 100
    else:
        AVL_security_pct = params["AVL_upper_security_pct"] * 100
        ETH_security_pct = params["ETH_upper_security_pct"] * 100

    ETH_stake.set_rewards(ETH_reward_pct * total_annual_rewards_fusion / 100)
    AVL_stake.set_rewards(AVL_reward_pct * total_annual_rewards_fusion / 100)
    
    print("ETH_security_pct", ETH_security_pct)
    print("AVL_security_pct", AVL_security_pct)
    print("total_security", total_security)
    
    return ({
        "AVL_security_pct": AVL_security_pct,
        "ETH_security_pct": ETH_security_pct,
        "total_security": total_security,
        "AVL_stake": AVL_stake,
        "ETH_stake": ETH_stake,
        "staking_ratio_all": total_security / total_fdv,
        "staking_ratio_avl": AVL_stake.upper_bound / total_security,
        "staking_ratio_eth": ETH_stake.upper_bound / total_security
    })

def update_ETH_stake(params, step, h, s, _input):
    ETH_stake = _input["ETH_stake"]
    ETH_stake.update_price(s["eth_price"])
    return ("ETH_stake", ETH_stake)

def update_AVL_stake(params, step, h, s, _input):
    AVL_stake = _input["AVL_stake"]
    AVL_stake.update_price(s["avl_price"])
    return ("AVL_stake", AVL_stake) 

def update_staking_ratio_avl(params, step, h, s, _input):
    return ("staking_ratio_avl", _input["staking_ratio_avl"])  

def update_staking_ratio_eth(params, step, h, s, _input):
    return ("staking_ratio_eth", _input["staking_ratio_eth"]) 

def update_staking_ratio_all(params, step, h, s, _input):
    return ("staking_ratio_all", _input["staking_ratio_all"]) 



