from typing import Dict, List
from model.agents_class import AgentStake, AssetAllocation
from model.pool_management import PoolManager

def create_maxi_agents(
    eth_balance: float = 32,  # ~1 ETH at 3000 USD
    avl_balance: float = 10000,  # ~1000 USD at 0.1 price
    btc_balance: float = 0.1,  # ~3000 USD at 30000 price
    eth_price: float = 3000,
    avl_price: float = 0.1,
    btc_price: float = 30000,
    restake_pcts: Dict[str, float] = None
) -> Dict[str, AgentStake]:
    """Create named agents with 100% allocation to one asset and restaking config"""
    # Default restake percentages if not provided
    if restake_pcts is None:
        restake_pcts = {
            'avl_maxi': 1,  # 80% restake for AVL maxis
            'eth_maxi': 1,  # 40% restake for ETH maxis 
            'btc_maxi': 1   # 20% restake for BTC maxis
        }
    
    return {
        'avl_maxi': AgentStake(assets={
            'AVL': AssetAllocation(pct=1.0, balance=avl_balance, price=avl_price),
            'ETH': AssetAllocation(pct=0.0, balance=0, price=eth_price),
            'BTC': AssetAllocation(pct=0.0, balance=0, price=btc_price)
        }, restake_pct=restake_pcts.get('avl_maxi', 1)),
        'eth_maxi': AgentStake(assets={
            'AVL': AssetAllocation(pct=0.0, balance=0, price=avl_price),
            'ETH': AssetAllocation(pct=1.0, balance=eth_balance, price=eth_price),
            'BTC': AssetAllocation(pct=0.0, balance=0, price=btc_price)
        }, restake_pct=restake_pcts.get('eth_maxi', 1)),
        'btc_maxi': AgentStake(assets={
            'AVL': AssetAllocation(pct=0.0, balance=0, price=avl_price),
            'ETH': AssetAllocation(pct=0.0, balance=0, price=eth_price),
            'BTC': AssetAllocation(pct=1.0, balance=btc_balance, price=btc_price)
        }, restake_pct=restake_pcts.get('btc_maxi', 1))
    }

def calculate_agent_composition(agents: List[AgentStake]) -> Dict[str, float]:
    """Calculate TVL composition percentages with AVL first"""
    total_tvl = sum(agent.total_tvl for agent in agents)
    
    # Handle zero TVL case
    if total_tvl <= 0:
        return {'AVL': 0.0, 'ETH': 0.0, 'BTC': 0.0}
    
    # Calculate AVL TVL first
    avl_tvl = sum(a.assets['AVL'].tvl for a in agents)
    eth_tvl = sum(a.assets['ETH'].tvl for a in agents)
    btc_tvl = sum(a.assets['BTC'].tvl for a in agents)
    
    return {
        'AVL': avl_tvl / total_tvl,
        'ETH': eth_tvl / total_tvl,
        'BTC': btc_tvl / total_tvl
    }

def calculate_required_balances(
    target_composition: Dict[str, float],
    total_tvl: float,
    avl_price: float = 0.1,
    eth_price: float = 3000,
    btc_price: float = 30000
) -> Dict[str, float]:
    """Calculate token balances needed to achieve target TVL composition
    
    Args:
        target_composition: Desired TVL percentages (must sum to 1)
        total_tvl: Total desired TVL in USD
        *_price: Current prices for each asset
    
    Returns:
        Dictionary of required token balances for each asset
    """
    # Validate input composition
    sum_percent = sum(target_composition.values())
    if not (0.99 <= sum_percent <= 1.01):
        raise ValueError("Target composition must sum to 1 (±0.01 tolerance)")
    
    # Calculate required USD allocation per asset
    avl_usd = total_tvl * target_composition.get('AVL', 0)
    eth_usd = total_tvl * target_composition.get('ETH', 0)
    btc_usd = total_tvl * target_composition.get('BTC', 0)
    
    # Convert USD to token balances with price safety checks
    return {
        'AVL': avl_usd / avl_price if avl_price > 0 else 0,
        'ETH': eth_usd / eth_price if eth_price > 0 else 0,
        'BTC': btc_usd / btc_price if btc_price > 0 else 0
    }

def initialize_state(init_total_fdv, constants, rewards_result, params, restaking, seed):
    """Initialize simulation state with agents and pool manager"""
    # ... [existing initialization code] ...
    
    # Get restake configuration from parameters
    restake_config = params.get('restake_config', {
        'avl_maxi': restaking,
        'eth_maxi': restaking,
        'btc_maxi': restaking
    })
    restake_config = restake_config[0] if isinstance(restake_config, list) else restake_config
    
    # Create initial agents with restaking config
    agents = create_maxi_agents(
        eth_balance=300,  # Start with some ETH (~$900,000 at $3000)
        avl_balance=9e6,  # Start with some AVL (~$900,000 at $0.1)
        btc_balance=0,    # No BTC initially
        eth_price=3000,
        avl_price=0.1,
        btc_price=30000,
        restake_pcts=restake_config
    )
    
    # Initialize pool manager
    pool_manager = PoolManager(
        total_budget=30e9
    )
    
    # Set initial pool configurations from params
    pool_configs_param = params.get('initial_pool_configs', {
        # default
        'AVL': {
            'base_deposit': 5e4,
            'max_extra_deposit': 5e5,
            'deposit_k': 5.0,
            'apy_threshold': 0.10,
            'base_withdrawal': 5e3,
            'max_extra_withdrawal': 3e5,
            'withdrawal_k': 7.0,
            'max_cap': float('inf')
        },
        'ETH': {
            'base_deposit': 3e4,
            'max_extra_deposit': 5e4,
            'deposit_k': 8.0,
            'apy_threshold': 0.03,
            'base_withdrawal': 1e4,
            'max_extra_withdrawal': 3e4,
            'withdrawal_k': 10.0,
            'max_cap': 100e6
        }
    })

    initial_pool_configs = pool_configs_param[0] if isinstance(pool_configs_param, list) else pool_configs_param
    pool_manager.pools = initial_pool_configs
    
    # Allocate initial budget - direct allocation instead of percentages
    initial_allocations = {
        'AVL': 21e9,  # 70% of 30M
        'ETH': 9e9,   # 30% of 30M
        # BTC removed - will be allocated on activation day
    }
    
    # Set allocated budgets directly
    for pool, amount in initial_allocations.items():
        pool_manager._allocated_budgets[pool] = amount

    
    
    # Return the initial state
    return {
        'timestep': 0,
        'agents': agents,
        
        # admin params
        'pool_manager': pool_manager,
        "target_yields": {'AVL': 0.15, 'ETH': 0.035},

        # security shares
        'total_security': 0,
        'tvl': {
        },
        'total_fdv': init_total_fdv,

        # staking ratios
        "staking_ratio_all": constants["native_staking_ratio"],
        "staking_ratio_fusion": {
            'AVL': 0, 
            'ETH': 0
        },

        # inflation and rewards metrics
        "inflation_rate": rewards_result["init_inflation_rate"],
        "total_annual_inflation_rewards_in_avl": rewards_result["total_inflation_rewards_in_avl"],
        "total_annual_inflation_rewards_usd": rewards_result["total_inflation_rewards_usd"],

        # yield metrics
        'yield_pcts': {
            'avl_maxi': 0,
            'eth_maxi': 0,
            'btc_maxi': 0
        },      
        "avg_yield": 0,
        "compounding_yield_pcts": {},
        "compounding_avg_yield": 0,
        
        
    }
