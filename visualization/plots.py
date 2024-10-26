import plotly.graph_objects as go
import numpy as np
from typing import Tuple, List
import pandas as pd

def create_scenario_plot(sim_data: pd.DataFrame, 
                        orders: List[Tuple], 
                        scenario_name: str) -> go.Figure:
    """Create plot for a given scenario"""
    fig = go.Figure()
    
    # Main inventory line
    fig.add_trace(go.Scatter(
        x=sim_data['date'],
        y=sim_data['inventory'],
        name='Inventory Level',
        line=dict(color='blue')
    ))
    
    # Reorder point line
    fig.add_trace(go.Scatter(
        x=sim_data['date'],
        y=sim_data['reorder_point'],
        name='Reorder Point',
        line=dict(color='red', dash='dash')
    ))
    
    # Order points
    if orders:
        order_dates = [order[0] for order in orders]
        order_inventories = [sim_data[sim_data['date'] == date]['inventory'].iloc[0] 
                           for date in order_dates]
        order_sizes = [order[1] for order in orders]
        
        fig.add_trace(go.Scatter(
            x=order_dates,
            y=order_inventories,
            mode='markers',
            name='Orders Placed',
            marker=dict(
                size=[size * 10 for size in order_sizes],
                color='yellow',
                line=dict(color='black', width=1)
            ),
            text=[f'{size} railcar(s)' for size in order_sizes],
            hoverinfo='text+y+x'
        ))
    
    fig.update_layout(
        title=f'Projected Inventory Levels - {scenario_name}',
        xaxis_title='Date',
        yaxis_title='Gallons',
        height=400,
        hovermode='x unified'
    )
    
    return fig

def get_scenario_metrics(sim_data: pd.DataFrame, orders: List[Tuple]) -> dict:
    """Calculate metrics for a scenario"""
    return {
        'average_inventory': int(np.mean(sim_data['inventory'])),
        'total_railcars': sum(order[1] for order in orders),
        'near_stockouts': sum(1 for inv in sim_data['inventory'] if inv <= 1000)
    }