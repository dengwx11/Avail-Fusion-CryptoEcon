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
    color_cycle = itertools.cycle(['#1f77b4', '#ff7f0e'])  # 示例颜色序列
    fig = make_subplots(rows=1, cols=2, subplot_titles=("AVL Prices", "ETH Prices"))

    # AVL 价格绘制在第一列
    for subset in df.subset.unique():
        color = next(color_cycle)
        fig.add_trace(
            go.Scatter(
                x=df[df.subset == subset]["timestep"],
                y=df[df.subset == subset]["avl_price"],
                name=f"{scenario_names[subset]} AVL",
                line=dict(color=color, dash='dot'),
                mode='lines'
            ),
            row=1, col=1
        )
        
    # ETH 价格绘制在第二列
    for subset in df.subset.unique():
        color = next(color_cycle)
        fig.add_trace(
            go.Scatter(
                x=df[df.subset == subset]["timestep"],
                y=df[df.subset == subset]["eth_price"],
                name=f"{scenario_names[subset]} ETH",
                line=dict(color=color, dash='dot'),
                mode='lines'
            ),
            row=1, col=2
        )

    fig.update_layout(
        title={
            'text': "Token Prices by Subset",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Time",
        xaxis2_title="Time",  # 确保第二个x轴也有标题
        yaxis_title="Price (USD)",
        legend=dict(
            orientation="h",  # Horizontal orientation
            yanchor="bottom",
            y=-0.4,  # Position it a bit below the x-axis
            xanchor="center",
            x=0.5,  # Center it
            font=dict(
                size=18,  # Adjust the size as needed
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

    # AVL Security Percentage
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["avg_yield"],
            name="Avg overall yield %",
            line=dict(color='#1f77b4', dash='dot'),  # Blue color
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
        yaxis_title="Avg overall yield %",
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


def plot_yield_pct(df, init_agent_eth_alloc):
    fig = go.Figure()


    num_curves = len(df["yield_pcts"].iloc[0])


    for i in range(num_curves):
        eth_alloc_label = f"{init_agent_eth_alloc[i]*100:.2f}%" 
        fig.add_trace(
            go.Scatter(
                x=df["timestep"],
                y=df["yield_pcts"].apply(lambda x: x[i]),  
                name=f"Yield % Curve {i+1} (Eth Alloc: {eth_alloc_label})", 
                line=dict(width=2, dash='dot') 
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


def plot_staking_ratio_inflation_rate(df):
    fig = go.Figure()

    # Staking Ratio
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["staking_ratio"] * 100,
            name="Staking Ratio (%)",
            line=dict(color='#1f77b4', dash='dot'),  # Blue color
            yaxis='y1'
        )
    )

    # Inflation Rate
    fig.add_trace(
        go.Scatter(
            x=df["timestep"],
            y=df["inflation_rate"] * 100,
            name="Inflation Rate (%)",
            line=dict(color='#ff7f0e', dash='dot'),  # Orange color
            yaxis='y2'
        )
    )

    fig.update_layout(
        title={
            'text': "Staking Ratio and Inflation Rate",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Timestep",
        yaxis=dict(
            title="Staking Ratio (%)",
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            )
        ),
        yaxis2=dict(
            title="Inflation Rate (%)",
            titlefont=dict(
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