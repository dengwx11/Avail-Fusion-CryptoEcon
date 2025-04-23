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

def create_linear_price_growth(
    starting_price: float,
    annual_increase_pct: float,
    timesteps=TIMESTEPS,
    dt=DELTA_TIME
):
    """
    Creates a list of token prices that increase linearly over one year.
    
    Args:
        starting_price: Initial token price
        annual_increase_pct: Annual percentage increase (e.g., 0.5 for 50% increase)
        timesteps: Number of timesteps in the simulation
        dt: Delta time between timesteps in years (default: DELTA_TIME)
    
    Returns:
        List of token prices with linear growth pattern
    """
    # Calculate the absolute increase amount over the year
    total_increase = starting_price * annual_increase_pct
    
    # Calculate per-timestep increase
    # We subtract 1 because the starting price is already accounted for
    per_timestep_increase = total_increase / (timesteps)
    
    # Generate the prices list with linear growth
    prices = [starting_price + (i * per_timestep_increase) for i in range(timesteps + 1)]
    
    return prices

def create_compound_price_growth(
    starting_price: float,
    annual_growth_rate: float,
    timesteps=TIMESTEPS,
    dt=DELTA_TIME
):
    """
    Creates a list of token prices that increase with compound growth over one year.
    
    Args:
        starting_price: Initial token price
        annual_growth_rate: Annual growth rate (e.g., 0.5 for 50% growth)
        timesteps: Number of timesteps in the simulation
        dt: Delta time between timesteps in years (default: DELTA_TIME)
    
    Returns:
        List of token prices with compound growth pattern
    """
    # Calculate per-timestep growth rate
    # This uses continuous compounding formula: (1+r)^t = e^(r*t)
    # For timestep dt, we need to find the rate such that (1+r)^(1/dt) = 1+annual_rate
    per_timestep_rate = (1 + annual_growth_rate)**(dt) - 1
    
    # Generate the prices list with compound growth
    prices = [starting_price * ((1 + per_timestep_rate) ** i) for i in range(timesteps + 1)]
    
    return prices

def create_trend_with_noise_price(
    starting_price: float,
    annual_trend_pct: float,
    volatility: float = 0.2,
    trend_type: str = 'linear',  # 'linear' or 'compound'
    timesteps=TIMESTEPS,
    dt=DELTA_TIME,
    seed=42
):
    """
    Creates a list of token prices that follow a trend (linear or compound) 
    with added random noise for more realistic price simulation.
    
    Args:
        starting_price: Initial token price
        annual_trend_pct: Annual percentage trend (e.g., 0.5 for 50% increase)
        volatility: Standard deviation of the random noise as a percentage of price
        trend_type: Type of trend ('linear' or 'compound')
        timesteps: Number of timesteps in the simulation
        dt: Delta time between timesteps in years (default: DELTA_TIME)
        seed: Random seed for reproducibility
        
    Returns:
        List of token prices with trend plus noise
    """
    # Set random seed for reproducibility
    rng = np.random.default_rng(seed)
    
    # Generate base trend prices
    if trend_type == 'linear':
        base_prices = create_linear_price_growth(
            starting_price, annual_trend_pct, timesteps, dt
        )
    else:  # compound
        base_prices = create_compound_price_growth(
            starting_price, annual_trend_pct, timesteps, dt
        )
    
    # Add random noise to each price point
    # The noise is proportional to the current price
    prices_with_noise = []
    for base_price in base_prices:
        # Generate random noise with mean 0 and standard deviation = volatility * price
        noise = rng.normal(0, volatility * base_price)
        # Ensure price doesn't go negative
        price_with_noise = max(base_price + noise, 0.001 * starting_price)
        prices_with_noise.append(price_with_noise)
    
    return prices_with_noise

def plot_price(
    samples: list, 
    title: str = 'Token Price Trajectory',
    ylabel: str = 'Price ($)',
    xlabel: str = 'Timestep',
    line_style: bool = True,
    show_plot: bool = True,
    additional_series: dict = None,
    figsize=(10, 6)
):
    """
    Plot the price trajectory with enhanced visualization options.
    
    Args:
        samples: List of price values to plot
        title: Plot title
        ylabel: Label for y-axis
        xlabel: Label for x-axis
        line_style: If True, show line plot; otherwise, scatter plot
        show_plot: If True, display the plot
        additional_series: Dictionary of additional series to plot {label: values}
        figsize: Tuple of figure dimensions (width, height)
    
    Returns:
        The matplotlib figure object (can be further customized)
    """
    plt.figure(figsize=figsize)
    x = list(range(1, len(samples) + 1))
    
    # Plot the main series
    if line_style:
        main_plot = plt.plot(x, samples, label='Base Trajectory', linewidth=2)
    else:
        main_plot = plt.scatter(x, samples, label='Base Trajectory')
    
    # Plot additional series if provided
    if additional_series:
        for label, values in additional_series.items():
            if len(values) != len(samples):
                # Truncate or extend x values to match the length of this series
                series_x = list(range(1, len(values) + 1))
                plt.plot(series_x, values, label=label)
            else:
                plt.plot(x, values, label=label)
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add legend if there are multiple series
    if additional_series or line_style:
        plt.legend()
    
    # Add price annotations at start, middle, and end
    n = len(samples)
    plt.annotate(f'${samples[0]:.2f}', (1, samples[0]), 
                 textcoords="offset points", xytext=(0,10), ha='center')
    plt.annotate(f'${samples[n//2]:.2f}', (n//2, samples[n//2]), 
                 textcoords="offset points", xytext=(0,10), ha='center')
    plt.annotate(f'${samples[-1]:.2f}', (n, samples[-1]), 
                 textcoords="offset points", xytext=(0,10), ha='center')
    
    if show_plot:
        plt.tight_layout()
        plt.show()
        
    return plt.gcf()  # Return the figure for further customization if needed

