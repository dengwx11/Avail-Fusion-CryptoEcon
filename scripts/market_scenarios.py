"""
Market scenario definitions and price trajectory generation for the Avail Fusion simulation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

def generate_price_paths(
    n_periods: int = 365,
    initial_prices: Dict[str, float] = {'AVL': 0.05, 'ETH': 2500.0, 'BTC': 100000.0},
    annual_returns: Dict[str, float] = {'AVL': 0.5, 'ETH': 0.3, 'BTC': 0.2},
    annual_volatilities: Dict[str, float] = {'AVL': 0.7, 'ETH': 0.8, 'BTC': 0.9},
    correlation_matrix: Optional[np.ndarray] = None,
    regime_changes: Optional[Dict] = None,
    seed: int = 42
) -> Tuple[List[float], List[float], List[float]]:
    """
    Generate correlated price paths for multiple tokens
    
    Parameters:
    -----------
    n_periods : int
        Number of periods to simulate (default: 365 days)
    initial_prices : dict
        Initial prices for each token
    annual_returns : dict
        Annual returns for each token
    annual_volatilities : dict
        Annual volatilities for each token
    correlation_matrix : np.array
        Correlation matrix between tokens
    regime_changes : dict
        Dictionary specifying regime changes
    seed : int
        Random seed for reproducibility
    
    Returns:
    --------
    Tuple[List[float], List[float], List[float]]
        Lists of price paths for AVL, ETH, and BTC
    """
    np.random.seed(seed)
    
    tokens = list(initial_prices.keys())
    n_tokens = len(tokens)
    
    # Default correlation matrix if none provided
    if correlation_matrix is None:
        correlation_matrix = np.array([
            [1.0, 0.6, 0.6],
            [0.6, 1.0, 0.8],
            [0.6, 0.8, 1.0]
        ])
    
    # Convert annual parameters to daily
    daily_returns = {t: (1 + annual_returns[t])**(1/n_periods) - 1 for t in tokens}
    daily_volatilities = {t: annual_volatilities[t] / np.sqrt(n_periods) for t in tokens}
    
    # Create Cholesky decomposition for correlated random numbers
    L = np.linalg.cholesky(correlation_matrix)
    
    # Initialize price matrix
    prices = np.zeros((n_periods + 1, n_tokens))
    for i, token in enumerate(tokens):
        prices[0, i] = initial_prices[token]
    
    # Generate correlated returns
    for t in range(1, n_periods + 1):
        # Check for regime changes
        if regime_changes and t in regime_changes:
            change = regime_changes[t]
            if 'returns' in change:
                daily_returns = {t: (1 + change['returns'][t])**(1/n_periods) - 1 
                               for t in tokens if t in change['returns']}
            if 'volatilities' in change:
                daily_volatilities = {t: change['volatilities'][t] / np.sqrt(n_periods) 
                                    for t in tokens if t in change['volatilities']}
        
        # Generate correlated normal random variables
        z = np.random.standard_normal(n_tokens)
        correlated_z = np.dot(L, z)
        
        # Update prices
        for i, token in enumerate(tokens):
            mu = daily_returns[token]
            sigma = daily_volatilities[token]
            prices[t, i] = prices[t-1, i] * np.exp(mu - 0.5 * sigma**2 + sigma * correlated_z[i])
    
    # Return price paths for each token
    return prices[:, 0].tolist(), prices[:, 1].tolist(), prices[:, 2].tolist(), prices[:, 0].tolist()

# Define market scenarios
MARKET_SCENARIOS = {
    # Base Scenarios
    'all_bearish_low_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': -0.4, 'ETH': -0.4, 'BTC': -0.4},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.005},
        'correlation_matrix': np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
    },
    'all_bearish_high_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': -0.4, 'ETH': -0.4, 'BTC': -0.4},
        'annual_volatilities': {'AVL': 0.3, 'ETH': 0.1, 'BTC': 0.05},
        'correlation_matrix': np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
    },
    'all_neutral_low_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 0.0, 'ETH': 0.0, 'BTC': 0.0},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.005},
        'correlation_matrix': np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
    },
    'all_neutral_high_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 0.0, 'ETH': 0.0, 'BTC': 0.0},
        'annual_volatilities': {'AVL': 0.3, 'ETH': 0.1, 'BTC': 0.05},
        'correlation_matrix': np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
    },
    'all_bullish_low_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 1.0, 'ETH': 1.0, 'BTC': 0.5},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.005},
        'correlation_matrix': np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
    },
    'all_bullish_high_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 1.0, 'ETH': 1.0, 'BTC': 0.5},
        'annual_volatilities': {'AVL': 0.3, 'ETH': 0.1, 'BTC': 0.05},
        'correlation_matrix': np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
    },

    # Alpha Outperformance Scenarios
    'alpha_outperforms_bull': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 1, 'ETH': 0.5, 'BTC': 0.3},
        'annual_volatilities': {'AVL': 0.2, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.6, 0.6],
            [0.6, 1.0, 0.8],
            [0.6, 0.8, 1.0]
        ])
    },
    'alpha_outperforms_bear': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': -0.2, 'ETH': -0.5, 'BTC': -0.5},
        'annual_volatilities': {'AVL': 0.2, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.6, 0.6],
            [0.6, 1.0, 0.8],
            [0.6, 0.8, 1.0]
        ])
    },
    'alpha_outperforms_high_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 1.2, 'ETH': 0.5, 'BTC': 0.5},
        'annual_volatilities': {'AVL': 0.5, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.6, 0.6],
            [0.6, 1.0, 0.8],
            [0.6, 0.8, 1.0]
        ])
    },

    # Beta Outperformance Scenarios
    'beta_outperforms_bull': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 0.5, 'ETH': 1.5, 'BTC': 0.5},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.6, 0.6],
            [0.6, 1.0, 0.8],
            [0.6, 0.8, 1.0]
        ])
    },
    'beta_outperforms_bear': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': -0.8, 'ETH': -0.2, 'BTC': -0.2},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.6, 0.6],
            [0.6, 1.0, 0.8],
            [0.6, 0.8, 1.0]
        ])
    },
    'beta_outperforms_high_vol': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 0.2, 'ETH': 1.2, 'BTC': 0.5},
        'annual_volatilities': {'AVL': 0.3, 'ETH': 0.1, 'BTC': 0.05},
        'correlation_matrix': np.array([
            [1.0, 0.6, 0.6],
            [0.6, 1.0, 0.8],
            [0.6, 0.8, 1.0]
        ])
    },

    # Uncorrelated Scenarios
    'uncorrelated_mixed': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 1.0, 'ETH': 0.5, 'BTC': -0.3},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.2, 0.2],
            [0.2, 1.0, 0.2],
            [0.2, 0.2, 1.0]
        ])
    },
    'Uncorrelated_fully_mixed': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': -0.4, 'ETH': 0.0, 'BTC': 1.0},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.2, 0.2],
            [0.2, 1.0, 0.2],
            [0.2, 0.2, 1.0]
        ])
    },
    'Uncorrelated_divergent_volatilities': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 0.0, 'ETH': 0.0, 'BTC': 0.0},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.2, 0.2],
            [0.2, 1.0, 0.2],
            [0.2, 0.2, 1.0]
        ])
    },

    # Regime Transition Scenarios
    'bull_to_bear': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': 1, 'ETH': 0.5, 'BTC': 0.3},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.8, 0.8],
            [0.8, 1.0, 0.8],
            [0.8, 0.8, 1.0]
        ]),
        'regime_changes': {
            180: {
                'returns': {'AVL': -0.8, 'ETH': -0.5, 'BTC': -0.3}
            }
        }
    },
    'bear_to_bull': {
        'initial_prices': {'AVL': 0.05, 'ETH': 2500, 'BTC': 100000},
        'annual_returns': {'AVL': -0.8, 'ETH': -0.5, 'BTC': -0.3},
        'annual_volatilities': {'AVL': 0.1, 'ETH': 0.05, 'BTC': 0.01},
        'correlation_matrix': np.array([
            [1.0, 0.8, 0.8],
            [0.8, 1.0, 0.8],
            [0.8, 0.8, 1.0]
        ]),
        'regime_changes': {
            180: {
                'returns': {'AVL': 1, 'ETH': 0.5, 'BTC': 0.3}
            }
        }
    },
    # 'alpha_crash': {
    #     'initial_prices': {'AVL': 0.1, 'ETH': 1500, 'BTC': 85000},
    #     'annual_returns': {'AVL': 0.1, 'ETH': 0.1, 'BTC': 0.1},
    #     'annual_volatilities': {'AVL': 0.5, 'ETH': 0.5, 'BTC': 0.5},
    #     'correlation_matrix': np.array([
    #         [1.0, 0.6, 0.6],
    #         [0.6, 1.0, 0.8],
    #         [0.6, 0.8, 1.0]
    #     ]),
    #     'regime_changes': {
    #         30: {
    #             'returns': {'AVL': -0.5},
    #             'volatilities': {'AVL': 1.0}
    #         },
    #         60: {
    #             'returns': {'AVL': -0.05},
    #             'volatilities': {'AVL': 0.5}
    #         }
    #     }
    # },
    # 'beta_crash': {
    #     'initial_prices': {'AVL': 0.1, 'ETH': 1500, 'BTC': 85000},
    #     'annual_returns': {'AVL': 0.1, 'ETH': 0.1, 'BTC': 0.1},
    #     'annual_volatilities': {'AVL': 0.5, 'ETH': 0.5, 'BTC': 0.5},
    #     'correlation_matrix': np.array([
    #         [1.0, 0.6, 0.6],
    #         [0.6, 1.0, 0.8],
    #         [0.6, 0.8, 1.0]
    #     ]),
    #     'regime_changes': {
    #         30: {
    #             'returns': {'ETH': -0.5, 'BTC': -0.5},
    #             'volatilities': {'ETH': 1.0, 'BTC': 1.0}
    #         },
    #         60: {
    #             'returns': {'ETH': -0.05, 'BTC': -0.05},
    #             'volatilities': {'ETH': 0.5, 'BTC': 0.5}
    #         }
    #     }
    # },
    # 'volatility_spike': {
    #     'initial_prices': {'AVL': 0.1, 'ETH': 1500, 'BTC': 85000},
    #     'annual_returns': {'AVL': 0.0, 'ETH': 0.0, 'BTC': 0.0},
    #     'annual_volatilities': {'AVL': 0.3, 'ETH': 0.3, 'BTC': 0.3},
    #     'correlation_matrix': np.array([
    #         [1.0, 0.8, 0.8],
    #         [0.8, 1.0, 0.8],
    #         [0.8, 0.8, 1.0]
    #     ]),
    #     'regime_changes': {
    #         180: {
    #             'volatilities': {'AVL': 0.8, 'ETH': 0.8, 'BTC': 0.8}
    #         }
    #     }
    # }
}

def get_scenario_prices(
        scenario_name: str, 
        n_periods: int = 365, 
        seed: int = 42) -> Tuple[List[float], List[float], List[float]]:
    """
    Get price paths for a specific market scenario
    
    Parameters:
    -----------
    scenario_name : str
        Name of the scenario to run
    n_periods : int
        Number of periods to simulate
    seed : int
        Random seed for reproducibility
        
    Returns:
    --------
    Tuple[List[float], List[float], List[float]]
        Lists of price paths for AVL, ETH, and BTC
    """
    if scenario_name not in MARKET_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}")
    
    scenario = MARKET_SCENARIOS[scenario_name]
    return generate_price_paths(
        n_periods=n_periods,
        initial_prices=scenario['initial_prices'],
        annual_returns=scenario['annual_returns'],
        annual_volatilities=scenario['annual_volatilities'],
        correlation_matrix=scenario.get('correlation_matrix'),
        regime_changes=scenario.get('regime_changes'),
        seed=seed
    ) 