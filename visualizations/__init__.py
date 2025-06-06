"""
Visualization package for the Avail Fusion simulation.

This package provides visualization functions for analyzing simulation results.
"""

# Core visualization functions will be imported from the main module
# when it's available in the codebase

# Import comparison plots (these are our new extensions)
try:
    from .comparison_plots import (
        plot_token_prices_comparison,
        plot_security_comparison,
        plot_yields_comparison,
        plot_staking_inflation_comparison,
        plot_tvl_asset_distribution,
        plot_asset_tvl_comparison,
        plot_rewards_comparison,
        plot_comparison_dashboard
    )
except ImportError:
    # The comparison plots module might not be available yet
    pass

import itertools
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from visualizations.plotly_theme import (
    cadlabs_colors,
    cadlabs_colorway_sequence,
)

legend_state_variable_name_mapping = {
    "timestep": "Day",
    "price": "AVL/ETH price", 
    "AVL_security_pct": "AVL security %",
    "ETH_security_pct": "ETH security %",
    "total_security": "Total security",
    "staking_ratio_all": "Staking ratio",
    "staking_ratio_avl": "AVL staking ratio",
    "staking_ratio_eth": "ETH staking ratio",
}


def update_legend_names(fig, name_mapping=legend_state_variable_name_mapping):
    for i, dat in enumerate(fig.data):
        for elem in dat:
            if elem == "name":
                try:
                    fig.data[i].name = name_mapping[fig.data[i].name]
                except KeyError:
                    continue
    return fig


def plot_token_price_per_subset(df, scenario_names):
    fig = make_subplots(rows=1, cols=3, subplot_titles=("AVL Prices", "ETH Prices", "BTC Prices"))

    # Extract prices from agents for each subset
    for subset in df.subset.unique():
        color = cadlabs_colorway_sequence[subset]  # Get unique color for each subset
        subset_df = df[df.subset == subset]
        
        # Extract AVL prices from avl_maxi agent
        avl_prices = [agents['avl_maxi'].assets['AVL'].price 
                     for agents in subset_df['agents']]
        
        # Plot AVL prices
        fig.add_trace(
            go.Scatter(
                x=subset_df["timestep"],
                y=avl_prices,
                name=f"{scenario_names[subset]} AVL",
                line=dict(color=color, dash='solid'),  # Solid line for AVL
                mode='lines'
            ),
            row=1, col=1
        )
        
        # Extract ETH prices from eth_maxi agent
        eth_prices = [agents['eth_maxi'].assets['ETH'].price 
                     for agents in subset_df['agents']]
        
        # Plot ETH prices
        fig.add_trace(
            go.Scatter(
                x=subset_df["timestep"],
                y=eth_prices,
                name=f"{scenario_names[subset]} ETH",
                line=dict(color=color, dash='dot'),  # Dotted line for ETH
                mode='lines'
            ),
            row=1, col=2
        )

        # Extract BTC prices from BTC agent
        btc_prices = [agents['btc_maxi'].assets['BTC'].price 
                     for agents in subset_df['agents']]
        
        # Plot BTC prices
        fig.add_trace(
            go.Scatter(
                x=subset_df["timestep"],
                y=btc_prices,
                name=f"{scenario_names[subset]} BTC",
                line=dict(color=color, dash='dot'),  # Dotted line for BTC
                mode='lines'
            ),
            row=1, col=3
        )   

    # Rest of the layout code remains the same
    fig.update_layout(
        title={
            'text': "Token Prices by Subset",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Time",
        xaxis2_title="Time",
        yaxis_title="Price (USD)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5,
            font=dict(
                size=18,
                color="black",
            ),
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=18,
            color="black"),
        plot_bgcolor='rgba(255, 255, 255, 1)', 
        paper_bgcolor='rgba(255, 255, 255, 1)',
    )

    return fig


def plot_security_pct(df):
    fig = go.Figure()

    # AVL Security Percentage
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["AVL_security_pct"],
            name="AVL Security %",
            line=dict(color='#1f77b4', dash='dot'),  # Blue color
        )
    )

    # ETH Security Percentage
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["ETH_security_pct"],
            name="ETH Security %",
            line=dict(color='#ff7f0e', dash='dot'),  # Orange color
        )
    )

    fig.update_layout(
        title={
            'text': "Security Pct",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Timestep",
        yaxis_title="Security %",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=18,
            color="black"
        ),
        plot_bgcolor='rgba(255, 255, 255, 1)', 
        paper_bgcolor='rgba(255, 255, 255, 1)'
    )

    # Optionally save to HTML and JPEG
    #fig.write_html('security_pct_plot.html')
    #fig.write_image('security_pct_plot.jpeg', width=900, height=600)

    return fig


def plot_avg_overall_yield(df):
    fig = go.Figure()

    # Regular yield (dotted line)
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["avg_yield"],
            name="Avg overall yield %",
            line=dict(color='#1f77b4', dash='dot'),  # Blue color with dotted line
        )
    )
    
    # Add compounding yield (solid line of same color) if it exists in the dataframe
    if "compounding_avg_yield" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestep"],
                y=df["compounding_avg_yield"],
                name="Avg compounding yield %",
                line=dict(color='#1f77b4', dash='solid'),  # Same blue color with solid line
            )
        )

    fig.update_layout(
        title={
            'text': "Average Overall Yield %",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Timestep",
        yaxis_title="Avg basic yield %",
        yaxis=dict(
            range=[0, 20],  # Set y-axis range from 0 to 100%
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=18,
            color="black"
        ),
        plot_bgcolor='rgba(255, 255, 255, 1)', 
        paper_bgcolor='rgba(255, 255, 255, 1)'
    )

    return fig

def plot_yield_pct(df):
    fig = go.Figure()

    # Get all unique agent keys across all timesteps
    all_agent_keys = set()
    for yield_dict in df["yield_pcts"]:
        all_agent_keys.update(yield_dict.keys())
    agent_keys = sorted(list(all_agent_keys))
    
    # Create two figures, one for basic yields and one for compounding yields
    has_compounding = "compounding_yield_pcts" in df.columns

    # Plot standard yield curve for each agent (dotted lines)
    for i, agent_key in enumerate(agent_keys):
        # Extract yields for this agent across all timesteps
        yields = []
        for yield_dict in df["yield_pcts"]:
            # Use 0 as default if agent not present at this timestep
            yields.append(yield_dict.get(agent_key, 0))
        
        # Use the same color for each agent, but with dotted line for regular yield
        agent_color = cadlabs_colorway_sequence[i]
        
        fig.add_trace(
            go.Scatter(
                x=df["timestep"],
                y=yields,
                name=f"Basic: {agent_key}", 
                legendgroup="Basic",
                legendgrouptitle_text="Basic Yields" if i == 0 else None,
                line=dict(
                    width=2, 
                    dash='dot',
                    color=agent_color
                )
            )
        )
    
    # Plot compounding yield curve for each agent (solid lines) if available
    if has_compounding:
        for i, agent_key in enumerate(agent_keys):
            # Extract compounding yields for this agent across all timesteps
            compounding_yields = []
            for compounding_yield_dict in df["compounding_yield_pcts"]:
                # Use 0 as default if agent not present at this timestep
                compounding_yields.append(compounding_yield_dict.get(agent_key, 0))
            
            # Use the same color for each agent, but with solid line for compounding yield
            agent_color = cadlabs_colorway_sequence[i]
            
            fig.add_trace(
                go.Scatter(
                    x=df["timestep"],
                    y=compounding_yields,
                    name=f"Compound: {agent_key}", 
                    legendgroup="Compound",
                    legendgrouptitle_text="Compounding Yields" if i == 0 else None,
                    line=dict(
                        width=2, 
                        dash='solid',
                        color=agent_color
                    )
                )
            )

    fig.update_layout(
        title={
            'text': "Agent-specific Yield %",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Timestep",
        yaxis_title="Yield %",
        yaxis=dict(
            range=[0, 30],  # Set y-axis range from 0 to 100%
        ),
        legend=dict(
            orientation="v",
            groupclick="toggleitem",
            traceorder="grouped",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.05,
            bordercolor="LightGrey",
            borderwidth=1
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=18,
            color="black"
        ),
        plot_bgcolor='rgba(255, 255, 255, 1)', 
        paper_bgcolor='rgba(255, 255, 255, 1)',
        # Add more margin on the right for the legend
        margin=dict(r=150)
    )

    return fig

def plot_staking_ratio_inflation_rate(df, assets=['AVL', 'ETH', 'BTC']):
    fig = go.Figure()

    # Add three staking ratio traces with different colors
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["staking_ratio_all"] * 100,
            name="staking_ratio_all",
            line=dict(color=cadlabs_colorway_sequence[0], dash='dot'),
            yaxis='y1'
        )
    )
    for i, asset in enumerate(assets):
        fig.add_trace(
            go.Scatter(
                x=df["timestep"],
                y=df["staking_ratio_fusion"].apply(lambda x: x.get(asset, 0)) * 100,
                name=f"staking_ratio_{asset}_fusion",
                line=dict(color=cadlabs_colorway_sequence[i+1], dash='dot'),
                yaxis='y1'
            )
        )


    # Inflation Rate (secondary axis)
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["inflation_rate"] * 100,
            name="inflation_rate",
            line=dict(color="#ff7f0e", dash='solid'),
            yaxis='y2'
        )
    )

    fig.update_layout(
        title={
            'text': "Staking Ratios and Inflation Rate",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Timestep",
        yaxis=dict(
            title="Staking Ratios (%)",
            title_font=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            )
        ),
        yaxis2=dict(
            title="Inflation Rate (%)",
            title_font=dict(
                color="#ff7f0e"
            ),
            tickfont=dict(
                color="#ff7f0e"
            ),
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-1.3,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=18,
            color="black"
        ),
        plot_bgcolor='rgba(255, 255, 255, 1)', 
        paper_bgcolor='rgba(255, 255, 255, 1)'
    )

    # Apply legend name mapping
    fig = update_legend_names(fig)
    return fig


def plot_total_security(df):
    """
    Creates a beautiful and informative plot of Total Security (TVL) over time.
    
    Args:
        df: DataFrame containing simulation results with 'total_security' and 'timestep' columns
        
    Returns:
        Plotly figure object with enhanced visualization
    """
    # Create figure with secondary y-axis
    fig = go.Figure()

    # Add main TVL trace with enhanced styling
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["total_security"],
            name="Total Security (TVL)",
            line=dict(
                color='#2ca02c',  # Green color
                width=3,
                shape='spline'  # Smooth line
            ),
            mode='lines',
            hovertemplate="Day: %{x}<br>TVL: $%{y:,.2f}<extra></extra>"
        )
    )

    # Add a moving average line for trend visualization
    window_size = 7  # 7-day moving average
    moving_avg = df["total_security"].rolling(window=window_size).mean()
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=moving_avg,
            name=f"{window_size}-Day Moving Average",
            line=dict(
                color='#1f77b4',  # Blue color
                width=2,
                dash='dot'
            ),
            mode='lines',
            hovertemplate="Day: %{x}<br>Moving Avg: $%{y:,.2f}<extra></extra>"
        )
    )

    # Calculate and add key statistics as annotations
    final_tvl = df["total_security"].iloc[-1]
    max_tvl = df["total_security"].max()
    min_tvl = df["total_security"].min()
    avg_tvl = df["total_security"].mean()
    
    # Add annotations for key statistics
    annotations = [
        dict(
            x=0.02,
            y=0.95,
            xref="paper",
            yref="paper",
            text=f"Final TVL: ${final_tvl:,.2f}",
            showarrow=False,
            font=dict(size=12, color="#2ca02c"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#2ca02c",
            borderwidth=1,
            borderpad=4
        ),
        dict(
            x=0.02,
            y=0.88,
            xref="paper",
            yref="paper",
            text=f"Max TVL: ${max_tvl:,.2f}",
            showarrow=False,
            font=dict(size=12, color="#2ca02c"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#2ca02c",
            borderwidth=1,
            borderpad=4
        ),
        dict(
            x=0.02,
            y=0.81,
            xref="paper",
            yref="paper",
            text=f"Avg TVL: ${avg_tvl:,.2f}",
            showarrow=False,
            font=dict(size=12, color="#2ca02c"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#2ca02c",
            borderwidth=1,
            borderpad=4
        )
    ]

    # Update layout with enhanced styling
    fig.update_layout(
        title={
            'text': "Total Value Locked (TVL) Over Time",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#2c3e50')
        },
        xaxis=dict(
            title="Day",
            title_font=dict(size=16, color='#2c3e50'),
            tickfont=dict(size=12, color='#2c3e50'),
            gridcolor='rgba(128, 128, 128, 0.2)',
            zerolinecolor='rgba(128, 128, 128, 0.2)',
            showgrid=True
        ),
        yaxis=dict(
            title="Total Value Locked (USD)",
            title_font=dict(size=16, color='#2c3e50'),
            tickfont=dict(size=12, color='#2c3e50'),
            gridcolor='rgba(128, 128, 128, 0.2)',
            zerolinecolor='rgba(128, 128, 128, 0.2)',
            showgrid=True,
            tickformat="$,.0f"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color='#2c3e50'),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#2c3e50",
            borderwidth=1
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=14,
            color="#2c3e50"
        ),
        plot_bgcolor='rgba(255, 255, 255, 1)',
        paper_bgcolor='rgba(255, 255, 255, 1)',
        margin=dict(t=100, b=100),
        annotations=annotations,
        showlegend=True
    )

    # Add range slider for better navigation
    fig.update_xaxes(rangeslider_visible=True)

    return fig

def plot_asset_tvl_stacked(df):
    """
    Creates a stacked area plot of TVL by asset type over time.
    
    Args:
        df: DataFrame containing simulation results with 'tvl' and 'timestep' columns
        
    Returns:
        Plotly figure object with stacked area chart
    """
    fig = go.Figure()
    
    # Get all unique asset types across all timesteps
    all_assets = set()
    for tvl_dict in df["tvl"]:
        if tvl_dict:  # Check if tvl_dict is not empty
            all_assets.update(tvl_dict.keys())
    asset_types = sorted(list(all_assets))
    
    # Create a stacked area plot for each asset
    for i, asset in enumerate(asset_types):
        # Extract TVL for this asset across all timesteps
        tvl_values = []
        for tvl_dict in df["tvl"]:
            # Use 0 as default if asset not present at this timestep
            tvl_values.append(tvl_dict.get(asset, 0) if tvl_dict else 0)
        
        # Use consistent colors across visualizations
        asset_color = cadlabs_colorway_sequence[i % len(cadlabs_colorway_sequence)]
        
        fig.add_trace(
            go.Scatter(
                x=df["timestep"],
                y=tvl_values,
                name=f"{asset} TVL",
                line=dict(width=0, color=asset_color),
                mode='lines',
                stackgroup='one',  # This creates the stacked area effect
                fillcolor=asset_color
            )
        )
    
    fig.update_layout(
        title={
            'text': "Total Value Locked (TVL) by Asset",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Timestep",
        yaxis_title="TVL (USD)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.6,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=18,
            color="black"
        ),
        plot_bgcolor='rgba(255, 255, 255, 1)', 
        paper_bgcolor='rgba(255, 255, 255, 1)'
    )
    
    return fig

def plot_pool_rewards_spent(df):
    """
    Plot the accumulated rewards spent for each pool over time.
    
    Args:
        df: DataFrame containing simulation results with 'pool_manager' and 'timestep' columns
        
    Returns:
        Plotly figure object showing accumulated rewards spent per pool
    """
    fig = go.Figure()
    
    # Extract pool data from all timesteps
    pool_rewards_data = {}
    
    # First, identify all pools that exist at any point
    all_pools = set()
    for _, row in df.iterrows():
        pool_manager = row.get('pool_manager')
        if pool_manager and hasattr(pool_manager, '_spent_budget_per_pool'):
            # All pools that have spent budget tracking
            all_pools.update(pool_manager._spent_budget_per_pool.keys())
    
    # Initialize data structure for each pool
    for pool in all_pools:
        pool_rewards_data[pool] = []
    
    # For each timestep, extract the spent budget for each pool
    timesteps = df['timestep'].tolist()
    
    for i, row in df.iterrows():
        pool_manager = row.get('pool_manager')
        timestep = row['timestep']
        
        # If we have pool manager data
        if pool_manager and hasattr(pool_manager, '_spent_budget_per_pool'):
            # Get the spent budget per pool directly
            spent_budget_per_pool = pool_manager._spent_budget_per_pool
            
            # Add this timestep's data to each pool's list
            for pool in all_pools:
                pool_rewards_data[pool].append(spent_budget_per_pool.get(pool, 0))
        else:
            # No pool manager data for this timestep, add zeros
            for pool in all_pools:
                pool_rewards_data[pool].append(0)
    
    # Create a line plot for each pool
    for i, (pool, values) in enumerate(pool_rewards_data.items()):
        # Ensure we have the same number of values as timesteps
        if len(values) < len(timesteps):
            values.extend([values[-1] if values else 0] * (len(timesteps) - len(values)))
        elif len(values) > len(timesteps):
            values = values[:len(timesteps)]
        
        # Use consistent colors across visualizations
        pool_color = cadlabs_colorway_sequence[i % len(cadlabs_colorway_sequence)]
        
        fig.add_trace(
            go.Scatter(
                x=timesteps,
                y=values,
                name=f"{pool} Rewards Spent",
                line=dict(width=2, color=pool_color),
                mode='lines'
            )
        )
    
    fig.update_layout(
        title={
            'text': "Accumulated Rewards Spent by Pool",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Timestep",
        yaxis_title="Accumulated Rewards (AVL)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.6,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(
            family="Arial",
            size=18,
            color="black"
        ),
        plot_bgcolor='rgba(255, 255, 255, 1)', 
        paper_bgcolor='rgba(255, 255, 255, 1)'
    )
    
    return fig

def plot_staked_token_balances(df):
    """
    Plot the staked token balances for each asset over time.
    
    Args:
        df: DataFrame containing simulation results
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Extract assets from the first non-empty staked_token_balances entry
    first_entry = next((x for x in df['staked_token_balances'] if x), {})
    assets = list(first_entry.keys())
    
    # Add traces for each asset
    for asset in assets:
        balance_series = []
        for _, row in df.iterrows():
            # Get token balance for this asset and timestep
            token_balances = row['staked_token_balances']
            if token_balances and asset in token_balances:
                balance_series.append(token_balances[asset])
            else:
                balance_series.append(0)
        
        # Add trace for this asset
        fig.add_trace(
            go.Scatter(
                x=df["timestep"],
                y=balance_series,
                name=f"{asset} Staked Tokens",
                mode="lines"
            )
        )
    
    # Update layout
    fig.update_layout(
        title="Staked Token Balances Over Time",
        xaxis_title="Day",
        yaxis_title="Token Amount",
        hovermode="x unified",
        template="plotly_white"
    )
    
    return fig