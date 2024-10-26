import streamlit as st
from models.data_classes import BusinessPriority, DeliveryTimeProfile, SiteParameters
from models.calculations import calculate_reorder_targets
from simulation.simulator import simulate_days
from visualization.plots import create_scenario_plot, get_scenario_metrics

def main():
    st.set_page_config(page_title="Terminal Inventory Management", layout="wide")
    st.title("Terminal Inventory Management Calculator")

    # Input section
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Terminal Configuration")
        
        daily_usage = st.number_input(
            "Daily Usage (Gallons)",
            value=20000,
            step=1000,
            help="Average gallons sold per workday"
        )
        
        business_case = st.selectbox(
            "Business Priority",
            ["Standard Commercial", "Low Margin", "High Priority"],
            index=0,
            help="Determines your service level and safety stock"
        )
        
        business_case_map = {
            "Standard Commercial": "standard",
            "Low Margin": "low_margin",
            "High Priority": "high"
        }
        
        delivery_mean = st.number_input(
            "Average Delivery Time (Days)",
            value=5,
            min_value=1,
            help="Typical number of days from order to delivery"
        )
        
        delivery_std = st.number_input(
            "Delivery Time Variation (Days)",
            value=2,
            min_value=1,
            help="How much delivery times typically vary"
        )
        
        price_risk = st.slider(
            "Price Risk Tolerance",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Lower = more conservative, Higher = more aggressive"
        )

    # Create parameters
    params = SiteParameters(
        business_priority=BusinessPriority(business_case_map[business_case]),
        typical_daily_usage=daily_usage,
        usage_variability=daily_usage * 0.2,
        railcar_capacity=30000,
        delivery_profile=DeliveryTimeProfile(
            mean_days=delivery_mean,
            std_days=delivery_std,
            min_days=max(1, delivery_mean - 2*delivery_std),
            max_days=delivery_mean + 3*delivery_std
        ),
        price_risk_tolerance=price_risk
    )

    # Calculate targets
    results = calculate_reorder_targets(params)

    # Simulation and visualization
    with col2:
        st.markdown("### Simulation Results")
        
        scenarios = {
            "Expected Case": "expected",
            "Best Case": "best_case",
            "Worst Case": "worst_case"
        }
        
        tabs = st.tabs(list(scenarios.keys()))
        
        for tab, (scenario_name, scenario_type) in zip(tabs, scenarios.items()):
            with tab:
                sim_data, orders = simulate_days(params, results['reorder_point'], 
                                              scenario=scenario_type)
                
                fig = create_scenario_plot(sim_data, orders, scenario_name)
                st.plotly_chart(fig, use_container_width=True)
                
                metrics = get_scenario_metrics(sim_data, orders)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Inventory", f"{metrics['average_inventory']:,} gal")
                with col2:
                    st.metric("Total Railcars Ordered", f"{metrics['total_railcars']}")
                with col3:
                    st.metric("Near Stockouts", f"{metrics['near_stockouts']} days")

if __name__ == "__main__":
    main()