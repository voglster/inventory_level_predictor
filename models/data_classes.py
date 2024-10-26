from dataclasses import dataclass
from enum import Enum

class BusinessPriority(Enum):
    HIGH = "high"                  # Very rare runouts ok (99%)
    STANDARD = "standard"          # Occasional runouts ok (95%)
    LOW_MARGIN = "low_margin"      # More frequent runouts ok (90%)

@dataclass
class DeliveryTimeProfile:
    """Parameters describing delivery time characteristics"""
    mean_days: float              # Average delivery time in days
    std_days: float              # Standard deviation in days
    min_days: float              # Minimum possible delivery time
    max_days: float              # Maximum possible delivery time

@dataclass
class SiteParameters:
    """Parameters describing the site's operational characteristics"""
    business_priority: BusinessPriority
    typical_daily_usage: float    # Average gallons used per workday
    usage_variability: float      # Standard deviation of daily usage
    railcar_capacity: float       # Typical railcar capacity in gallons
    delivery_profile: DeliveryTimeProfile
    price_risk_tolerance: float   # 0-1, how much price risk is acceptable
    
    def get_service_level(self) -> float:
        """Convert business priority to service level percentage"""
        service_levels = {
            BusinessPriority.HIGH: 0.99,         # 99%
            BusinessPriority.STANDARD: 0.95,     # 95%
            BusinessPriority.LOW_MARGIN: 0.90    # 90%
        }
        return service_levels[self.business_priority]