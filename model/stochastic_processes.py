from config.config import (
    TIMESTEPS,
    DELTA_TIME,
)
import numpy as np
from stochastic import processes
import matplotlib.pyplot as plt

def create_stochastic_avail_price_process(
    timesteps=TIMESTEPS,  
    dt=DELTA_TIME,        
    rng=np.random.default_rng(1),
    price_traj_type='convex',  # convex, concave or none
    minimum_avl_price=0.05,
    target_avg=0.1,
    maximum_avl_price=1.0,
    volatility=1.0,
):
    process = processes.continuous.BrownianMotion(t=(timesteps * dt), rng=rng)
    samples = process.sample(timesteps + 1)

    # Normalize to [0,1] first
    normalized_samples = (np.abs(samples) - np.min(np.abs(samples))) / (np.max(np.abs(samples)) - np.min(np.abs(samples)))
    
    # Apply volatility to normalized values while maintaining 0-1 bounds
    normalized_samples = 0.5 + (normalized_samples - 0.5) * volatility
    #normalized_samples = np.clip(normalized_samples, 0, 1)
    
    # Scale to final price range
    samples = normalized_samples * (maximum_avl_price - minimum_avl_price) + minimum_avl_price

    #plot_price(samples)
    t = timesteps * dt
    if price_traj_type == 'convex':
        para = (maximum_avl_price - minimum_avl_price) / ((t + 1)**2)
        print(para.__class__)
        samples_add_on = [para * (i**2)+minimum_avl_price for i in range(t+2)]
    elif price_traj_type == 'concave':
        para = (maximum_avl_price - minimum_avl_price) / ((t + 1)**2)
        samples_add_on = [para * ((t+1-i)**2)+minimum_avl_price for i in range(t+2)]
    else:
        samples_add_on = [0 for _ in range(timesteps + 1)]
    
    samples = [max(sample + add_on, minimum_avl_price) for sample, add_on in zip(samples, samples_add_on)]
    #plot_price(samples)
    curr_average = sum(samples) / len(samples)
    adjustment_factor = (target_avg - minimum_avl_price) / (curr_average - minimum_avl_price)
    samples = [minimum_avl_price + (sample - minimum_avl_price) * adjustment_factor for sample in samples]
    
    return samples

def create_price_with_volatility_strike(
    timesteps=TIMESTEPS,
    dt=DELTA_TIME,
    base_price=0.1,
    strike_timestep=100,
    pct_change=0.5,  # Can be positive (pump) or negative (dump)
):
    """
    Create a simple price series with a single volatility strike at a specified timestep.
    
    Args:
        timesteps: Number of timesteps in the simulation
        dt: Delta time (time increment per step)
        base_price: Base price before the volatility strike
        strike_timestep: Timestep at which the price change occurs
        pct_change: Percentage change at strike_timestep (+0.5 = +50%, -0.3 = -30%)
        
    Returns:
        list: Price series with a single volatility strike
    """
    # Create array with constant base price
    price_series = [base_price] * (timesteps + 1)
    
    # Validate strike_timestep
    if 0 <= strike_timestep <= timesteps:
        # Calculate new price after strike
        new_price = base_price * (1 + pct_change)
        
        # Apply new price from strike_timestep onwards
        for i in range(strike_timestep, timesteps + 1):
            price_series[i] = new_price
    
    return price_series

def create_price_with_multiple_volatility_strikes(
    timesteps=TIMESTEPS,
    dt=DELTA_TIME,
    base_price=0.1,
    volatility_events=None,  # List of (timestep, pct_change) tuples
    num_random_events=0,
    min_pct_change=-0.8,
    max_pct_change=1,
    rng=np.random.default_rng(1)
):
    """
    Create a price series with multiple volatility strikes.
    The price remains constant between strikes.
    
    Args:
        timesteps: Number of timesteps in the simulation
        dt: Delta time (time increment per step)
        base_price: Initial price
        volatility_events: List of tuples (timestep, pct_change) for specific events
        num_random_events: Number of random volatility events to generate
        min_pct_change: Minimum percent change for random events
        max_pct_change: Maximum percent change for random events
        rng: Random number generator
        
    Returns:
        list: Price series with volatility strikes
    """
    # Initialize price series with base price
    price_series = [base_price] * (timesteps + 1)
    
    # Collect all volatility events (specified + random)
    all_events = []
    
    # Add specified events
    if volatility_events:
        all_events.extend([(t, pct) for t, pct in volatility_events if 0 <= t <= timesteps])
    
    # Add random events if requested
    if num_random_events > 0:
        # Generate random timesteps (ensure they're unique)
        random_timesteps = rng.choice(
            range(1, timesteps + 1),  # Avoid timestep 0
            size=min(num_random_events, timesteps),
            replace=False
        )
        
        # Generate random percentage changes
        random_pct_changes = rng.uniform(min_pct_change, max_pct_change, size=len(random_timesteps))
        
        # Add random events
        all_events.extend(zip(random_timesteps, random_pct_changes))
    
    # Sort events by timestep
    all_events.sort()
    
    # Apply events sequentially
    current_price = base_price
    last_timestep = 0
    
    for timestep, pct_change in all_events:
        # Calculate new price
        new_price = current_price * (1 + pct_change)
        
        # Apply new price from this timestep until the next event
        for i in range(timestep, timesteps + 1):
            price_series[i] = new_price
        
        # Update current price for next event
        current_price = new_price
        last_timestep = timestep
    
    return price_series

def plot_price(samples: list):
    x = list(range(1, len(samples) + 1))
    plt.scatter(x, samples)

    plt.title('Scatter Plot of Values')
    plt.xlabel('Index')
    plt.ylabel('Value')

    plt.show()