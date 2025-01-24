from model.agents_class import Stake

def policy_agent_rebalance(params, step, h, s):
    #print("calc security shares")
    yield_pcts = s["yield_pcts"]

    AVL_stake = s["AVL_stake"]
    ETH_stake = s["ETH_stake"]
    agents_avl_balance = AVL_stake.agents_balances
    agents_eth_balance = ETH_stake.agents_balances

    c_avl = params["c_avl"]
    c_eth = params["c_eth"]
    avl_yield_equilibrium = params["avl_yield_equilibrium"]
    eth_yield_equilibrium = params["eth_yield_equilibrium"]

    delta_avl_balance_rate = (yield_pcts[1]/100 - avl_yield_equilibrium)**2 * c_avl if yield_pcts[1]/100 - avl_yield_equilibrium > 0 else 0
    agents_avl_balance = [balance * (1 + delta_avl_balance_rate) for balance in agents_avl_balance]

    delta_eth_balance_rate = (yield_pcts[0]/100 - eth_yield_equilibrium)**2 * c_eth if yield_pcts[0]/100 - eth_yield_equilibrium > 0 else 0
    agents_eth_balance = [balance * (1 + delta_eth_balance_rate) for balance in agents_eth_balance]


    AVL_stake.update_balances(agents_avl_balance)
    ETH_stake.update_balances(agents_eth_balance)
    
    return ({
        "AVL_stake": AVL_stake,
        "ETH_stake": ETH_stake,
    })

def update_ETH_stake(params, step, h, s, _input):
    return ("ETH_stake", _input["ETH_stake"])

def update_AVL_stake(params, step, h, s, _input):
    return ("AVL_stake", _input["AVL_stake"])
