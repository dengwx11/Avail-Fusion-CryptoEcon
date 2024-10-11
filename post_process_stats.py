import pandas as pd
import numpy as np

def aggregate_summary(df_list, simulation_list):
    # Initialize a list to store the summary statistics
    summary_stats = []

    for i, df in enumerate(df_list):
        # Calculate mean and standard deviation for each required column
        avl_security_pct_mean = df['AVL_security_pct'].mean()
        avl_security_pct_std = df['AVL_security_pct'].std()

        total_security_mean = df['total_security'].mean()
        total_security_std = df['total_security'].std()

        avg_yield_mean = df['avg_yield'].mean()
        avg_yield_std = df['avg_yield'].std()

        # Extract 'yield_pcts' and split into two columns for ETH and AVL agent yields
        df['eth_yield'] = df['yield_pcts'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else np.nan)
        df['avl_yield'] = df['yield_pcts'].apply(lambda x: x[1] if isinstance(x, list) and len(x) > 1 else np.nan)

        eth_yield_mean = df['eth_yield'].mean()
        eth_yield_std = df['eth_yield'].std()

        avl_yield_mean = df['avl_yield'].mean()
        avl_yield_std = df['avl_yield'].std()

        avl_reward_pct = simulation_list[i].model.params['AVL_reward_pct']
        avl_upper_security_pct = simulation_list[i].model.params['AVL_upper_security_pct']


        # Get AVL_reward_pct and AVL_upper_security_pct from the corresponding simulation parameters
        if isinstance(avl_reward_pct, list):
            avl_reward_pct = np.mean(avl_reward_pct)
        if isinstance(avl_upper_security_pct, list):
            avl_upper_security_pct = np.mean(avl_upper_security_pct)

        # Round to two decimal places
        avl_reward_pct = round(avl_reward_pct, 2)
        avl_upper_security_pct = round(avl_upper_security_pct, 0)

        # Append results to the list
        summary_stats.append({
            'AVL_security_pct_mean': avl_security_pct_mean,
            'AVL_security_pct_std': avl_security_pct_std,
            'total_security_mean': total_security_mean,
            'total_security_std': total_security_std,
            'avg_yield_mean': avg_yield_mean,
            'avg_yield_std': avg_yield_std,
            'eth_yield_mean': eth_yield_mean,
            'eth_yield_std': eth_yield_std,
            'avl_yield_mean': avl_yield_mean,
            'avl_yield_std': avl_yield_std,
            'AVL_reward_pct': avl_reward_pct,
            'AVL_upper_security_pct': avl_upper_security_pct
        })

    # Convert the summary statistics list to a DataFrame
    summary_df = pd.DataFrame(summary_stats)
    return summary_df