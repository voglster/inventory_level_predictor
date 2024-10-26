import streamlit as st
from models.data_classes import BusinessPriority, DeliveryTimeProfile, SiteParameters
from models.calculations import calculate_reorder_targets
from simulation.simulator import simulate_days
from visualization.plots import create_scenario_plot, get_scenario_metrics

def format_recommendation(reorder_point: float, railcar_capacity: float = 30000) -> str:
    """Format the recommendation in railcar terms"""
    railcars = max(1, round(reorder_point / railcar_capacity, 1))
    return f"""
    # 🚨 Recommendation
    ### Place new orders when you have {railcars} or fewer railcars worth of propane
    #### ({int(reorder_point):,} gallons)
    """

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

    # Display the main recommendation prominently
    st.markdown(format_recommendation(results['reorder_point']))
    
    # Add explanation of the recommendation
    with st.expander("📊 Understanding this recommendation"):
        st.markdown(f"""
        This recommendation is based on:
        - Daily usage: {daily_usage:,} gallons
        - Lead time: {delivery_mean} days (±{delivery_std} days)
        - Business priority: {business_case}
        
        The reorder point includes:
        - Lead time demand: {int(results['lead_time_demand']):,} gallons
        - Safety stock: {int(results['safety_stock']):,} gallons
        
        Expected stockouts per year: {results['expected_stockout_days_per_year']} days
        """)

    # Simulation and visualization
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
                st.metric("Average Inventory", 
                         f"{metrics['average_inventory']:,} gal",
                         f"{metrics['average_inventory']/30000:.1f} railcars")
            with col2:
                st.metric("Total Railcars Ordered", f"{metrics['total_railcars']}")
            with col3:
                st.metric("Near Stockouts", f"{metrics['near_stockouts']} days")

            # Add scenario-specific insights
            if metrics['near_stockouts'] > results['expected_stockout_days_per_year']:
                st.warning(f"⚠️ This scenario shows more stockouts than expected. Consider increasing safety stock.")
            if metrics['average_inventory'] > 2 * results['reorder_point']:
                st.info("💡 Average inventory seems high. Consider more aggressive settings to reduce holding costs.")

if __name__ == "__main__":
    main()