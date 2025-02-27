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

def plot_price(samples: list):
    x = list(range(1, len(samples) + 1))
    plt.scatter(x, samples)

    plt.title('Scatter Plot of Values')
    plt.xlabel('Index')
    plt.ylabel('Value')

    plt.show()