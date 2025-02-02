from typing import Dict, List
from model.agents_class import AgentStake, AssetAllocation

def create_maxi_agents(
    eth_balance: float = 32,  # ~1 ETH at 3000 USD
    avl_balance: float = 10000,  # ~1000 USD at 0.1 price
    btc_balance: float = 0.1,  # ~3000 USD at 30000 price
    eth_price: float = 3000,
    avl_price: float = 0.1,
    btc_price: float = 30000
) -> Dict[str, AgentStake]:
    """Create named agents with 100% allocation to one asset"""
    return {
        'avl_maxi': AgentStake(assets={
            'AVL': AssetAllocation(pct=1.0, balance=avl_balance, price=avl_price),
            'ETH': AssetAllocation(pct=0.0, balance=0, price=eth_price),
            'BTC': AssetAllocation(pct=0.0, balance=0, price=btc_price)
        }),
        'eth_maxi': AgentStake(assets={
            'AVL': AssetAllocation(pct=0.0, balance=0, price=avl_price),
            'ETH': AssetAllocation(pct=1.0, balance=eth_balance, price=eth_price),
            'BTC': AssetAllocation(pct=0.0, balance=0, price=btc_price)
        }),
        'btc_maxi': AgentStake(assets={
            'AVL': AssetAllocation(pct=0.0, balance=0, price=avl_price),
            'ETH': AssetAllocation(pct=0.0, balance=0, price=eth_price),
            'BTC': AssetAllocation(pct=1.0, balance=btc_balance, price=btc_price)
        })
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
