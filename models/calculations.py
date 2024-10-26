import numpy as np
from .data_classes import SiteParameters

def calculate_reorder_targets(params: SiteParameters) -> dict:
    """
    Calculate reorder point based on lead time demand and safety stock.
    
    Reorder Point = Lead Time Demand + Safety Stock
    - Lead Time Demand = Daily Usage * Lead Time Days
    - Safety Stock based on service level and variability
    """
    service_level = params.get_service_level()
    
    # Calculate lead time demand (only business days)
    business_days_in_lead_time = params.delivery_profile.mean_days * (5/7)  # Convert to business days
    lead_time_demand = params.typical_daily_usage * business_days_in_lead_time
    
    # Calculate safety stock
    z_score = np.abs(np.percentile(np.random.standard_normal(10000), service_level * 100))
    
    # Consider both demand and lead time variability
    demand_uncertainty = params.usage_variability * np.sqrt(business_days_in_lead_time)
    lead_time_uncertainty = params.typical_daily_usage * params.delivery_profile.std_days * (5/7)
    
    safety_stock = z_score * np.sqrt(demand_uncertainty**2 + lead_time_uncertainty**2)
    
    # Calculate reorder point
    reorder_point = lead_time_demand + safety_stock
    
    # Calculate recommended railcars
    min_railcars = max(1, np.ceil(lead_time_demand / params.railcar_capacity))
    max_railcars = np.ceil((lead_time_demand + safety_stock) / params.railcar_capacity)
    risk_adjusted_railcars = min_railcars + (max_railcars - min_railcars) * (1 - params.price_risk_tolerance)
    
    return {
        'reorder_point': reorder_point,
        'recommended_railcars': int(min_railcars),
        'max_railcars': int(np.ceil(risk_adjusted_railcars)),
        'safety_stock': safety_stock,
        'expected_stockout_days_per_year': int(250 * (1 - service_level)),
        'lead_time_demand': lead_time_demand
    }