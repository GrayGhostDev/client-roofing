"""
iSwitch Roofs CRM - Customers Management Page
Real-time customer management with premium market segmentation and lifetime value tracking
Version: 2.0.0
Date: 2025-10-09
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.api_client import get_api_client
from utils.realtime import (
    auto_refresh,
    display_last_updated,
    create_realtime_indicator,
    show_connection_status,
    display_data_source_badge
)
from utils.charts import create_kpi_card
from utils.pusher_script import inject_pusher_script, pusher_status_indicator
from utils.notifications import notification_preferences_sidebar
import plotly.express as px
import plotly.graph_objects as go

# Page config
# Initialize API client
api_client = get_api_client()

# Auto-refresh every 30 seconds
auto_refresh(interval_ms=30000, key="customers_refresh")

# Inject Pusher real-time client (subscribes to customers, projects, leads channels)
inject_pusher_script(channels=['customers', 'projects', 'leads'], debug=False)

# Custom CSS
st.markdown("""
    <style>
    .customer-card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        background-color: white;
    }
    .ultra-premium-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    .professional-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    .standard-badge {
        background: linear-gradient(135deg, #4CAF50 0%, #45A049 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    .active-customer {
        border-left: 5px solid #4caf50;
    }
    .inactive-customer {
        border-left: 5px solid #ff9800;
    }
    .churned-customer {
        border-left: 5px solid #f44336;
    }
    .metric-box {
        padding: 15px;
        border-radius: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🏠 Customer Management")
st.markdown("Real-time customer tracking with premium market segmentation")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Connection status
    show_connection_status(api_client)
    create_realtime_indicator(active=True)
    display_last_updated(key="customers_last_updated")

    # Pusher status and notification preferences
    pusher_status_indicator()
    notification_preferences_sidebar()

    st.markdown("---")
    st.header("🔍 Filters")

    # Market segment filter
    segment_options = ["All", "Ultra-Premium", "Professional", "Standard"]
    segment_filter = st.selectbox("Market Segment", segment_options)

    # Status filter
    status_options = ["All", "Active", "Inactive", "Churned"]
    status_filter = st.selectbox("Customer Status", status_options)

    # Property type filter
    property_options = ["All", "Residential", "Commercial", "Multi-Family"]
    property_filter = st.selectbox("Property Type", property_options)

    # Lifetime value filter
    st.subheader("Lifetime Value")
    ltv_range = st.slider(
        "LTV range ($)",
        0, 500000, (0, 500000),
        step=10000,
        format="$%d"
    )

    # Project count filter
    st.subheader("Projects")
    project_range = st.slider("Number of projects", 0, 20, (0, 20))

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    if st.button("📥 Export to CSV", use_container_width=True):
        st.info("Export functionality coming soon!")

    if st.button("📧 Email Campaign", use_container_width=True):
        st.info("Email campaign functionality coming soon!")

# Premium market definitions
ULTRA_PREMIUM_CITIES = ["Bloomfield Hills", "Birmingham", "Grosse Pointe"]
PROFESSIONAL_CITIES = ["Troy", "Rochester Hills", "West Bloomfield"]

def determine_market_segment(address: str, lifetime_value: float = 0) -> str:
    """Determine customer's market segment based on location and LTV"""
    if not address:
        return "standard"

    address_lower = address.lower()

    # Check for ultra-premium cities
    for city in ULTRA_PREMIUM_CITIES:
        if city.lower() in address_lower:
            return "ultra_premium"

    # Check for professional cities
    for city in PROFESSIONAL_CITIES:
        if city.lower() in address_lower:
            return "professional"

    # Also consider LTV
    if lifetime_value >= 100000:
        return "ultra_premium"
    elif lifetime_value >= 50000:
        return "professional"

    return "standard"

def get_segment_badge(segment: str) -> str:
    """Get HTML badge for market segment"""
    if segment == "ultra_premium":
        return '<span class="ultra-premium-badge">⭐ Ultra-Premium</span>'
    elif segment == "professional":
        return '<span class="professional-badge">💼 Professional</span>'
    else:
        return '<span class="standard-badge">✓ Standard</span>'

# Search bar
search_query = st.text_input(
    "🔍 Search customers by name, email, phone, or address...",
    ""
)

# Fetch customer metrics
try:
    response = api_client.get_customers()
    customers_data = response if isinstance(response, list) else []

    if customers_data:
        display_data_source_badge("live")

        # Calculate metrics with market segmentation
        customers_count = len(customers_data)
        active_customers = len([
            c for c in customers_data
            if c.get('status') in ['active', 'vip']  # Fixed: was 'customer_status'
        ])
        total_revenue = sum(c.get('lifetime_value', 0) for c in customers_data)
        avg_ltv = total_revenue / customers_count if customers_count > 0 else 0

        # Premium market breakdown
        ultra_premium_count = 0
        professional_count = 0
        ultra_premium_revenue = 0
        professional_revenue = 0

        for customer in customers_data:
            # Build full address from separate fields
            full_address = f"{customer.get('city', '')} {customer.get('state', '')}"
            segment = determine_market_segment(
                full_address,
                customer.get('lifetime_value', 0)
            )
            if segment == "ultra_premium":
                ultra_premium_count += 1
                ultra_premium_revenue += customer.get('lifetime_value', 0)
            elif segment == "professional":
                professional_count += 1
                professional_revenue += customer.get('lifetime_value', 0)
    else:
        display_data_source_badge("demo")
        st.info("📊 No customer data available - Displaying demo metrics")
        customers_count = 45
        active_customers = 38
        total_revenue = 2150000
        avg_ltv = 47778
        ultra_premium_count = 8
        professional_count = 15
        ultra_premium_revenue = 720000
        professional_revenue = 810000

except Exception as e:
    display_data_source_badge("demo")
    st.warning("⚠️ Backend connection unavailable - Displaying demo metrics")
    st.info(f"💡 Error: {str(e)}")
    customers_count = 45
    active_customers = 38
    total_revenue = 2150000
    avg_ltv = 47778
    ultra_premium_count = 8
    professional_count = 15
    ultra_premium_revenue = 720000
    professional_revenue = 810000

# Top metrics with KPI cards
st.header("📊 Customer Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    create_kpi_card(
        label="Total Customers",
        value=customers_count,
        format_func=lambda x: f"{int(x)}",
        color="#667eea"
    )

with col2:
    create_kpi_card(
        label="Active Customers",
        value=active_customers,
        delta=f"{(active_customers/customers_count*100):.1f}% active",
        format_func=lambda x: f"{int(x)}",
        color="#4CAF50"
    )

with col3:
    create_kpi_card(
        label="Total Revenue",
        value=total_revenue,
        format_func=lambda x: f"${x:,.0f}",
        color="#764ba2"
    )

with col4:
    create_kpi_card(
        label="Avg Lifetime Value",
        value=avg_ltv,
        format_func=lambda x: f"${x:,.0f}",
        color="#FF9800"
    )

st.markdown("---")

# Premium Market Segmentation Overview
st.header("🏘️ Premium Market Segmentation")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("⭐ Ultra-Premium")
    st.metric(
        "Customers",
        ultra_premium_count,
        f"${ultra_premium_revenue/ultra_premium_count if ultra_premium_count > 0 else 0:,.0f} avg"
    )
    st.markdown(f"**Total Revenue:** ${ultra_premium_revenue:,.0f}")
    st.markdown(f"**Cities:** {', '.join(ULTRA_PREMIUM_CITIES)}")

with col2:
    st.subheader("💼 Professional")
    st.metric(
        "Customers",
        professional_count,
        f"${professional_revenue/professional_count if professional_count > 0 else 0:,.0f} avg"
    )
    st.markdown(f"**Total Revenue:** ${professional_revenue:,.0f}")
    st.markdown(f"**Cities:** {', '.join(PROFESSIONAL_CITIES)}")

with col3:
    st.subheader("📊 Market Share")
    premium_total = ultra_premium_count + professional_count
    premium_percent = (premium_total / customers_count * 100) if customers_count > 0 else 0
    st.metric(
        "Premium Customers",
        premium_total,
        f"{premium_percent:.1f}% of total"
    )
    premium_revenue_total = ultra_premium_revenue + professional_revenue
    st.markdown(f"**Premium Revenue:** ${premium_revenue_total:,.0f}")
    premium_revenue_percent = (
        premium_revenue_total / total_revenue * 100
        if total_revenue > 0 else 0
    )
    st.markdown(f"**Revenue Share:** {premium_revenue_percent:.1f}%")

st.markdown("---")

# View tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Customer List",
    "📊 Analytics",
    "🎯 Segments",
    "🏘️ Premium Markets"
])

with tab1:
    # Add new customer button
    if st.button("➕ Add New Customer", type="primary"):
        st.session_state['show_new_customer_form'] = True

    # Fetch customers data
    try:
        response = api_client.get_customers()
        customers_data = response if isinstance(response, list) else []

        if customers_data:
            # Add market segment and normalize field names for each customer
            for customer in customers_data:
                # Build full address from separate fields
                full_address = f"{customer.get('street_address', '')} {customer.get('city', '')} {customer.get('state', '')} {customer.get('zip_code', '')}".strip()
                customer['address'] = full_address

                # Normalize field names to match what the UI expects
                customer['customer_status'] = customer.get('status', 'active')
                customer['total_projects'] = customer.get('project_count', 0)

                # Determine market segment
                customer['market_segment'] = determine_market_segment(
                    full_address,
                    customer.get('lifetime_value', 0)
                )

            df = pd.DataFrame(customers_data)

            # Apply filters
            if segment_filter != "All":
                segment_map = {
                    "Ultra-Premium": "ultra_premium",
                    "Professional": "professional",
                    "Standard": "standard"
                }
                df = df[df['market_segment'] == segment_map[segment_filter]]

            if status_filter != "All":
                df = df[df['customer_status'] == status_filter.lower()]

            if property_filter != "All":
                df = df[
                    df['property_type'] == property_filter.lower().replace("-", "_")
                ]

            # LTV filter
            df = df[
                (df['lifetime_value'] >= ltv_range[0]) &
                (df['lifetime_value'] <= ltv_range[1])
            ]

            # Project count filter
            df = df[
                (df['total_projects'] >= project_range[0]) &
                (df['total_projects'] <= project_range[1])
            ]

            if search_query:
                search_mask = (
                    df['first_name'].str.contains(
                        search_query, case=False, na=False
                    ) |
                    df['last_name'].str.contains(
                        search_query, case=False, na=False
                    ) |
                    df['email'].str.contains(search_query, case=False, na=False) |
                    df['phone'].str.contains(search_query, case=False, na=False)
                )
                df = df[search_mask]

            # Display customers
            st.subheader(f"Showing {len(df)} customers")

            # Sort by LTV descending
            df = df.sort_values('lifetime_value', ascending=False)

            for idx, customer in df.iterrows():
                segment_badge = get_segment_badge(customer['market_segment'])
                status_class = f"{customer.get('customer_status', 'active')}-customer"

                expander_title = (
                    f"🏠 {customer['first_name']} {customer['last_name']} - "
                    f"${customer.get('lifetime_value', 0):,.0f} LTV"
                )

                with st.expander(expander_title):
                    # Display segment badge
                    st.markdown(segment_badge, unsafe_allow_html=True)

                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**Email:** {customer.get('email', 'N/A')}")
                        st.write(f"**Phone:** {customer.get('phone', 'N/A')}")
                        st.write(f"**Address:** {customer.get('address', 'N/A')}")
                        st.write(
                            f"**Property Type:** "
                            f"{customer.get('property_type', 'N/A')}"
                        )

                    with col2:
                        st.write(
                            f"**Lifetime Value:** "
                            f"${customer.get('lifetime_value', 0):,.2f}"
                        )
                        st.write(
                            f"**Total Projects:** "
                            f"{customer.get('total_projects', 0)}"
                        )
                        st.write(
                            f"**Last Project:** "
                            f"{customer.get('last_project_date', 'N/A')}"
                        )
                        st.write(
                            f"**Customer Since:** "
                            f"{customer.get('created_at', 'N/A')}"
                        )

                    with col3:
                        if st.button(
                            "View Details",
                            key=f"view_cust_{customer['id']}"
                        ):
                            st.session_state['selected_customer_id'] = customer['id']
                            st.rerun()

                        if st.button("Edit", key=f"edit_cust_{customer['id']}"):
                            st.session_state['edit_customer_id'] = customer['id']

                        if st.button(
                            "New Project",
                            key=f"project_{customer['id']}"
                        ):
                            st.session_state['new_project_customer_id'] = (
                                customer['id']
                            )

                    # Show customer notes if available
                    if customer.get('notes'):
                        st.info(f"**Notes:** {customer['notes']}")
        else:
            st.info("📊 No customers found yet.")

    except Exception as e:
        st.error(f"❌ Error loading customers: {str(e)}")

with tab2:
    st.subheader("Customer Analytics")

    try:
        response = api_client.get_customers()
        customers_data = response if isinstance(response, list) else []

        if customers_data:
            # Add market segment and normalize field names for each customer
            for customer in customers_data:
                # Build full address from separate fields
                full_address = f"{customer.get('street_address', '')} {customer.get('city', '')} {customer.get('state', '')} {customer.get('zip_code', '')}".strip()
                customer['address'] = full_address

                # Normalize field names to match what the UI expects
                customer['customer_status'] = customer.get('status', 'active')
                customer['total_projects'] = customer.get('project_count', 0)

                # Determine market segment
                customer['market_segment'] = determine_market_segment(
                    full_address,
                    customer.get('lifetime_value', 0)
                )

            df = pd.DataFrame(customers_data)

            col1, col2 = st.columns(2)

            with col1:
                # Customer status distribution
                if 'customer_status' in df.columns:
                    status_counts = df['customer_status'].value_counts()
                    fig = px.pie(
                        values=status_counts.values,
                        names=status_counts.index,
                        title="Customers by Status",
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Market segment distribution
                if 'market_segment' in df.columns:
                    segment_counts = df['market_segment'].value_counts()
                    segment_labels = {
                        'ultra_premium': 'Ultra-Premium',
                        'professional': 'Professional',
                        'standard': 'Standard'
                    }
                    segment_names = [
                        segment_labels.get(s, s) for s in segment_counts.index
                    ]
                    fig = px.pie(
                        values=segment_counts.values,
                        names=segment_names,
                        title="Customers by Market Segment",
                        hole=0.4,
                        color_discrete_sequence=['#FFD700', '#667eea', '#4CAF50']
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Lifetime value distribution by segment
            if 'lifetime_value' in df.columns and 'market_segment' in df.columns:
                segment_labels = {
                    'ultra_premium': 'Ultra-Premium',
                    'professional': 'Professional',
                    'standard': 'Standard'
                }
                df['segment_label'] = df['market_segment'].map(segment_labels)

                fig = px.box(
                    df,
                    x='segment_label',
                    y='lifetime_value',
                    title="Lifetime Value Distribution by Market Segment",
                    labels={
                        'segment_label': 'Market Segment',
                        'lifetime_value': 'Lifetime Value ($)'
                    },
                    color='segment_label',
                    color_discrete_sequence=['#FFD700', '#667eea', '#4CAF50']
                )
                st.plotly_chart(fig, use_container_width=True)

            # Top customers by LTV
            st.subheader("Top 10 Customers by Lifetime Value")
            top_customers = df.nlargest(10, 'lifetime_value')[[
                'first_name', 'last_name', 'lifetime_value',
                'total_projects', 'segment_label'
            ]]
            st.dataframe(top_customers, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

with tab3:
    st.subheader("Customer Segments")

    # Define segments
    segments = [
        {
            "name": "VIP Customers",
            "description": "High lifetime value (>$100k) with 3+ projects",
            "icon": "⭐",
            "color": "#FFD700"
        },
        {
            "name": "Regular Customers",
            "description": "1-2 projects, active status",
            "icon": "👥",
            "color": "#4CAF50"
        },
        {
            "name": "At-Risk Customers",
            "description": "No projects in last 12 months",
            "icon": "⚠️",
            "color": "#FF9800"
        },
        {
            "name": "Churned Customers",
            "description": "Inactive for 2+ years",
            "icon": "📉",
            "color": "#F44336"
        }
    ]

    for segment in segments:
        with st.expander(f"{segment['icon']} {segment['name']}"):
            st.write(f"**Description:** {segment['description']}")
            st.write("**Count:** Calculating...")
            st.write("**Total Revenue:** Calculating...")

            if st.button(
                f"View {segment['name']}",
                key=f"segment_{segment['name']}"
            ):
                st.info(f"Segment filtering for {segment['name']} coming soon!")

with tab4:
    st.subheader("🏘️ Premium Market Analysis")

    try:
        response = api_client.get_customers()
        customers_data = response if isinstance(response, list) else []

        if customers_data:
            # Add market segment to each customer
            for customer in customers_data:
                customer['market_segment'] = determine_market_segment(
                    customer.get('address', ''),
                    customer.get('lifetime_value', 0)
                )

            # Premium market revenue comparison
            ultra_premium_df = [
                c for c in customers_data
                if c['market_segment'] == 'ultra_premium'
            ]
            professional_df = [
                c for c in customers_data
                if c['market_segment'] == 'professional'
            ]

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("⭐ Ultra-Premium Segment")
                if ultra_premium_df:
                    ultra_df = pd.DataFrame(ultra_premium_df)
                    st.metric(
                        "Total Customers",
                        len(ultra_df)
                    )
                    st.metric(
                        "Total Revenue",
                        f"${ultra_df['lifetime_value'].sum():,.0f}"
                    )
                    st.metric(
                        "Avg Deal Size",
                        f"${ultra_df['lifetime_value'].mean():,.0f}"
                    )
                else:
                    st.info("No ultra-premium customers yet")

            with col2:
                st.subheader("💼 Professional Segment")
                if professional_df:
                    prof_df = pd.DataFrame(professional_df)
                    st.metric(
                        "Total Customers",
                        len(prof_df)
                    )
                    st.metric(
                        "Total Revenue",
                        f"${prof_df['lifetime_value'].sum():,.0f}"
                    )
                    st.metric(
                        "Avg Deal Size",
                        f"${prof_df['lifetime_value'].mean():,.0f}"
                    )
                else:
                    st.info("No professional segment customers yet")

    except Exception as e:
        st.error(f"Error loading premium market data: {str(e)}")

# New Customer Form
if st.session_state.get('show_new_customer_form', False):
    st.markdown("---")
    st.subheader("➕ Add New Customer")

    with st.form("new_customer_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name *")
            last_name = st.text_input("Last Name *")
            email = st.text_input("Email *")
            phone = st.text_input("Phone *")

        with col2:
            address = st.text_input("Address *")
            property_type = st.selectbox(
                "Property Type",
                ["Residential", "Commercial", "Multi-Family"]
            )
            converted_from_lead = st.text_input(
                "Converted from Lead ID (optional)"
            )

        notes = st.text_area("Notes")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Customer",
                type="primary",
                use_container_width=True
            )
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state['show_new_customer_form'] = False
                st.rerun()

        if submitted:
            if not all([first_name, last_name, email, phone, address]):
                st.error("Please fill in all required fields marked with *")
            else:
                try:
                    customer_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "property_type": property_type.lower().replace("-", "_"),
                        "notes": notes
                    }

                    if converted_from_lead:
                        customer_data['converted_from_lead_id'] = (
                            converted_from_lead
                        )

                    response = api_client.create_customer(customer_data)

                    if response:
                        st.success("✅ Customer created successfully!")
                        st.session_state['show_new_customer_form'] = False
                        st.rerun()
                    else:
                        st.error("Failed to create customer. Please try again.")
                except Exception as e:
                    st.error(f"Error creating customer: {str(e)}")

# Customer Detail Modal
if st.session_state.get('selected_customer_id'):
    customer_id = st.session_state['selected_customer_id']

    st.markdown("---")
    st.subheader("Customer Details")

    try:
        # Fetch customer details
        customer = api_client.get_customer(customer_id)

        if customer:
            # Build full address and normalize fields
            full_address = f"{customer.get('street_address', '')} {customer.get('city', '')} {customer.get('state', '')} {customer.get('zip_code', '')}".strip()
            customer['address'] = full_address
            customer['customer_status'] = customer.get('status', 'active')
            customer['total_projects'] = customer.get('project_count', 0)

            # Add market segment
            customer['market_segment'] = determine_market_segment(
                full_address,
                customer.get('lifetime_value', 0)
            )
            segment_badge = get_segment_badge(customer['market_segment'])

            st.markdown(segment_badge, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    f"**Name:** {customer['first_name']} {customer['last_name']}"
                )
                st.write(f"**Email:** {customer['email']}")
                st.write(f"**Phone:** {customer['phone']}")
                st.write(f"**Address:** {customer['address']}")

            with col2:
                st.write(
                    f"**Status:** "
                    f"{customer.get('customer_status', 'active').title()}"
                )
                st.write(
                    f"**Lifetime Value:** "
                    f"${customer.get('lifetime_value', 0):,.2f}"
                )
                st.write(
                    f"**Total Projects:** "
                    f"{customer.get('total_projects', 0)}"
                )
                st.write(
                    f"**Customer Since:** "
                    f"{customer.get('created_at', 'N/A')}"
                )

            # Project history
            st.subheader("Project History")
            projects = api_client.get_customer_projects(customer_id)

            if projects:
                for project in projects:
                    with st.expander(
                        f"📋 {project['name']} - {project['status']}"
                    ):
                        st.write(f"**Value:** ${project['value']:,.2f}")
                        st.write(f"**Start Date:** {project['start_date']}")
                        st.write(
                            f"**End Date:** "
                            f"{project.get('end_date', 'In Progress')}"
                        )
                        st.write(
                            f"**Description:** "
                            f"{project.get('description', 'N/A')}"
                        )
            else:
                st.info("No projects found for this customer.")

            if st.button("Close", use_container_width=True):
                del st.session_state['selected_customer_id']
                st.rerun()

    except Exception as e:
        st.error(f"Error loading customer details: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
### 🎯 Customer Management Features
- ✅ **Real-Time Updates**: Live customer data with 30-second refresh
- ✅ **Premium Segmentation**: Ultra-Premium, Professional, and Standard tiers
- ✅ **Lifetime Value Tracking**: Monitor customer revenue contribution
- ✅ **Market Intelligence**: City-based premium market identification
- ✅ **Status Monitoring**: Active/Inactive/Churned customer tracking

### 🏘️ Premium Market Targets
- **Ultra-Premium**: Bloomfield Hills, Birmingham, Grosse Pointe ($45K avg)
- **Professional**: Troy, Rochester Hills, West Bloomfield ($27K avg)
- **Growth Strategy**: Target 42,000 premium properties in SE Michigan
""")
