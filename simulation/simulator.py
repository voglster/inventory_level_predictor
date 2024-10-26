import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, List
from models.data_classes import SiteParameters

def calculate_needed_railcars(current_inv: float, incoming: float, 
                            params: SiteParameters, reorder_point: float) -> int:
    """
    Calculate needed railcars when inventory drops below reorder point.
    Returns number of railcars needed to get back above reorder point.
    """
    total_current_coverage = current_inv + incoming
    
    if total_current_coverage < reorder_point:
        shortage = reorder_point - total_current_coverage
        return max(1, int(np.ceil(shortage / params.railcar_capacity)))
    return 0

def generate_delivery_time(profile, scenario: str) -> int:
    """Generate delivery time based on scenario"""
    if scenario == 'best_case':
        mean, std = profile.min_days, 0.5
    elif scenario == 'worst_case':
        mean, std = profile.max_days, 0.5
    else:
        mean, std = profile.mean_days, profile.std_days
        
    delivery = np.random.normal(mean, std)
    return int(np.clip(delivery, profile.min_days, profile.max_days))

def simulate_days(params: SiteParameters, reorder_point: float, 
                 scenario: str = 'expected', days: int = 90) -> Tuple[pd.DataFrame, List]:
    """
    Simulate inventory levels with reordering based on reorder point.
    Orders are placed whenever inventory + incoming falls below reorder point.
    """
    start_date = datetime.now()
    
    # Initialize tracking
    dates = []
    inventory = []
    railcars_in_transit = []
    orders = []
    reorder_points = []
    
    # Start at 1.5 times reorder point to show natural decline
    current_inv = reorder_point 
    pending_deliveries = []  # (delivery_date, amount)
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        dates.append(current_date)
        
        # Process deliveries
        delivered_today = sum(amount for del_date, amount in pending_deliveries 
                            if del_date == current_date)
        current_inv += delivered_today
        pending_deliveries = [(d, a) for d, a in pending_deliveries 
                            if d != current_date]
        
        # Process weekday demand
        if current_date.weekday() < 5:
            demand_multiplier = 0.8 if scenario == 'best_case' else 1.2 if scenario == 'worst_case' else 1.0
            demand = np.random.normal(
                params.typical_daily_usage * demand_multiplier,
                params.usage_variability
            )
            demand = max(0, min(demand, current_inv))
            current_inv -= demand
        
        # Check if we need to order - consider both current inventory and incoming
        incoming = sum(amount for _, amount in pending_deliveries)
        needed_railcars = calculate_needed_railcars(
            current_inv, 
            incoming, 
            params, 
            reorder_point
        )
        
        if needed_railcars > 0:
            # Generate delivery dates based on scenario
            delivery_time = generate_delivery_time(params.delivery_profile, scenario)
            delivery_date = current_date + timedelta(days=delivery_time)
            
            # Place order for all needed railcars
            pending_deliveries.append((delivery_date, needed_railcars * params.railcar_capacity))
            orders.append((current_date, needed_railcars))
            
        inventory.append(current_inv)
        railcars_in_transit.append(len(pending_deliveries))
        reorder_points.append(reorder_point)
    
    return pd.DataFrame({
        'date': dates,
        'inventory': inventory,
        'railcars_in_transit': railcars_in_transit,
        'reorder_point': reorder_points,
        'incoming': [sum(amount for _, amount in pending_deliveries) for _ in range(days)]
    }), orders