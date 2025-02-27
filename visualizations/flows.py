import plotly.graph_objects as go
import numpy as np

def plot_sigmoid_flows(
    apy_range=(0.0, 0.25),
    pool_configs=None
):
    """
    Visualize sigmoid flow functions for different pool types
    
    Args:
        apy_range: Tuple of (min_apy, max_apy) to plot
        pool_configs: Dict of pool configurations, or None to use defaults
    
    Returns:
        Plotly figure object
    """
    if pool_configs is None:
        # Use default configurations
        pool_configs = {
            'AVL': {
                'base_deposit': 1e5,
                'max_extra_deposit': 5e6,
                'deposit_k': 5.0,
                'apy_threshold': 0.10,
                'base_withdrawal': 1e4,
                'max_extra_withdrawal': 2e6,
                'withdrawal_k': 7.0
            },
            'ETH': {
                'base_deposit': 5e4,
                'max_extra_deposit': 3e6,
                'deposit_k': 8.0,
                'apy_threshold': 0.03,
                'base_withdrawal': 5e3,
                'max_extra_withdrawal': 1.5e6,
                'withdrawal_k': 10.0
            },
            'BTC': {
                'base_deposit': 1e5,
                'max_extra_deposit': 4e6,
                'deposit_k': 6.0,
                'apy_threshold': 0.02,
                'base_withdrawal': 8e3,
                'max_extra_withdrawal': 2e6,
                'withdrawal_k': 9.0
            }
        }
    
    # Create APY range to plot
    apy_values = np.linspace(apy_range[0], apy_range[1], 100)
    
    # Create figure
    fig = go.Figure()
    
    # Plot sigmoid curves for each pool type
    colors = {'AVL': '#1f77b4', 'ETH': '#ff7f0e', 'BTC': '#2ca02c'}
    
    for pool_type, config in pool_configs.items():
        # Calculate deposit flows
        deposit_base = config['base_deposit']
        deposit_max = config['max_extra_deposit']
        deposit_k = config['deposit_k']
        apy_threshold = config['apy_threshold']
        
        deposit_values = [
            deposit_base + deposit_max * (1.0 / (1.0 + np.exp(-deposit_k * (apy - apy_threshold))))
            for apy in apy_values
        ]
        
        # Calculate withdrawal flows
        withdrawal_base = config['base_withdrawal']
        withdrawal_max = config['max_extra_withdrawal']
        withdrawal_k = config['withdrawal_k']
        
        withdrawal_values = [
            withdrawal_base + withdrawal_max * (1.0 / (1.0 + np.exp(-withdrawal_k * (apy_threshold - apy))))
            for apy in apy_values
        ]
        
        # Calculate net flows
        net_flows = [d - w for d, w in zip(deposit_values, withdrawal_values)]
        
        # Add traces
        fig.add_trace(go.Scatter(
            x=apy_values,
            y=deposit_values,
            mode='lines',
            name=f'{pool_type} Deposits',
            line=dict(color=colors[pool_type])
        ))
        
        fig.add_trace(go.Scatter(
            x=apy_values,
            y=withdrawal_values,
            mode='lines',
            name=f'{pool_type} Withdrawals',
            line=dict(color=colors[pool_type], dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=apy_values,
            y=net_flows,
            mode='lines',
            name=f'{pool_type} Net Flow',
            line=dict(color=colors[pool_type], dash='dot')
        ))
        
        # Add vertical line at threshold APY
        fig.add_vline(
            x=apy_threshold,
            line_dash="dash",
            line_color=colors[pool_type],
            annotation_text=f"{pool_type} Threshold: {apy_threshold:.1%}"
        )
    
    # Update layout
    fig.update_layout(
        title="Sigmoid Flow Functions by Pool Type",
        xaxis_title="APY",
        yaxis_title="Daily Flow (USD)",
        xaxis_tickformat=".0%",
        template="plotly_white",
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig 