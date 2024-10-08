from dataclasses import dataclass

def calc_rewards_allocation(params, step, h, s):

    #print("calc rewards allocation")

    AVL_stake = s["AVL_stake"]
    ETH_stake = s["ETH_stake"]
    
    AVL_stake.update_rewards( [agent_balance/AVL_stake.upper_bound* AVL_stake.rewards for agent_balance in AVL_stake.agents_scaled_balances])
    ETH_stake.update_rewards( [agent_balance/ETH_stake.upper_bound* ETH_stake.rewards for agent_balance in ETH_stake.agents_scaled_balances])
    

    # TODO: agents allocation
    
    return ({
        "AVL_stake": AVL_stake,
        "ETH_stake": ETH_stake,
    })

def update_AVL_stake(params, step, h, s, _input):
    return ("AVL_stake",_input["AVL_stake"])  

def update_ETH_stake(params, step, h, s, _input):
    return ("ETH_stake",_input["ETH_stake"])  


def calc_yields(params, step, h, s):

    AVL_stake = s["AVL_stake"]
    ETH_stake = s["ETH_stake"]


    @dataclass
    class agent:
        total_balance: float
        total_rewards: float
        total_yield_pct: float

    agent_cnt = len(AVL_stake.agents_balances)

    yield_pcts = [0]*agent_cnt
    
    for i in range(agent_cnt):
        total_balance = AVL_stake.agents_scaled_balances[i] + ETH_stake.agents_scaled_balances[i]
        total_rewards = AVL_stake.agents_rewards[i] + ETH_stake.agents_rewards[i]
        total_yield_pct = total_rewards / total_balance * 100
        yield_pcts[i] = total_yield_pct


    avg_yield = (AVL_stake.rewards+ETH_stake.rewards)/ (sum(AVL_stake.agents_scaled_balances)+sum(ETH_stake.agents_scaled_balances)) * 100

    #print("rewards is " + str(AVL_stake['rewards']+ETH_stake['rewards']))
    #print("total balance is " + str(sum(AVL_stake['agents_balance'])+sum(ETH_stake['agents_balance'])))
    #print("avg yield is " + str(avg_yield))
    return ({
        "yield_pcts": yield_pcts,
        "avg_yield": avg_yield,
    })

def update_yields(params, step, h, s, _input):
    return ("yield_pcts",_input["yield_pcts"])

def update_avg_yield(params, step, h, s, _input):
    return ("avg_yield",_input["avg_yield"])