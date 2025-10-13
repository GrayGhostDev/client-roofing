"""
iSwitch Roofs CRM - Leads Management Page
Comprehensive lead management with real-time features, filtering, and analytics
Version: 2.0.0 - Real-Time Integration
Date: 2025-10-09
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from utils.api_client import get_api_client
from utils.realtime import (
    auto_refresh,
    display_last_updated,
    create_realtime_indicator,
    show_connection_status,
    display_data_source_badge
)
from utils.charts import create_conversion_by_temperature, create_response_time_gauge
from utils.pusher_script import inject_pusher_script, pusher_status_indicator
from utils.notifications import notification_preferences_sidebar
import plotly.express as px
import plotly.graph_objects as go

# Initialize API client
api_client = get_api_client()

# Lead Detail Modal Functions
@st.dialog("Lead Details", width="large")
def show_lead_details(lead):
    """Display comprehensive lead information in a modal"""
    st.subheader(f"{lead['first_name']} {lead['last_name']}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Contact Information")
        st.write(f"**Email:** {lead.get('email', 'N/A')}")
        st.write(f"**Phone:** {lead.get('phone', 'N/A')}")
        st.write(f"**Address:** {lead.get('address', 'N/A')}")
        st.write(f"**City:** {lead.get('city', 'N/A')}, {lead.get('state', 'N/A')} {lead.get('zip_code', 'N/A')}")

    with col2:
        st.markdown("### Lead Information")
        st.write(f"**Status:** {lead.get('status', 'N/A').upper()}")
        st.write(f"**Temperature:** {lead.get('temperature', 'cold').upper()}")
        st.write(f"**Lead Score:** {lead.get('lead_score', 0)}/100")
        st.write(f"**Source:** {lead.get('source', 'N/A')}")

    st.markdown("### Property Details")
    col3, col4 = st.columns(2)
    with col3:
        st.write(f"**Property Value:** ${lead.get('property_value', 0):,.0f}")
        st.write(f"**Property Type:** {lead.get('property_type', 'N/A')}")
    with col4:
        st.write(f"**Roof Age:** {lead.get('roof_age', 'N/A')} years")
        st.write(f"**Roof Type:** {lead.get('roof_type', 'N/A')}")

    if lead.get('notes'):
        st.markdown("### Notes")
        st.text_area("Lead Notes", value=lead['notes'], height=150, disabled=True)

    if st.button("Close", type="primary"):
        st.rerun()

@st.dialog("Edit Lead", width="large")
def edit_lead_modal(lead):
    """Edit lead information in a modal"""
    st.subheader(f"Edit: {lead['first_name']} {lead['last_name']}")

    with st.form("edit_lead_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name", value=lead.get('first_name', ''))
            last_name = st.text_input("Last Name", value=lead.get('last_name', ''))
            email = st.text_input("Email", value=lead.get('email', ''))
            phone = st.text_input("Phone", value=lead.get('phone', ''))

        with col2:
            status = st.selectbox("Status",
                options=["new", "contacted", "qualified", "quote_sent", "won", "lost"],
                index=["new", "contacted", "qualified", "quote_sent", "won", "lost"].index(lead.get('status', 'new'))
            )
            temperature = st.selectbox("Temperature",
                options=["cold", "warm", "hot"],
                index=["cold", "warm", "hot"].index(lead.get('temperature', 'cold'))
            )
            source = st.text_input("Source", value=lead.get('source', ''))
            lead_score = st.slider("Lead Score", 0, 100, value=int(lead.get('lead_score', 50)))

        notes = st.text_area("Notes", value=lead.get('notes', ''), height=150)

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submit = st.form_submit_button("Save Changes", type="primary")
        with col_cancel:
            cancel = st.form_submit_button("Cancel")

        if submit:
            # Update lead via API
            update_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "status": status,
                "temperature": temperature,
                "source": source,
                "lead_score": lead_score,
                "notes": notes
            }

            try:
                response = api_client.put(f"/leads/{lead['id']}", json=update_data)
                if response.status_code == 200:
                    st.success("Lead updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Error updating lead: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

        if cancel:
            st.rerun()

@st.dialog("Convert Lead to Customer", width="large")
def convert_lead_modal(lead):
    """Convert lead to customer in a modal"""
    st.subheader(f"Convert: {lead['first_name']} {lead['last_name']}")
    st.info("Converting this lead will create a new customer record and mark the lead as 'won'.")

    with st.form("convert_lead_form"):
        st.markdown("### Customer Information")
        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name (Optional)", value="")
            customer_type = st.selectbox("Customer Type",
                options=["Residential", "Commercial", "Government"],
                index=0
            )

        with col2:
            preferred_contact = st.selectbox("Preferred Contact Method",
                options=["Email", "Phone", "Text"],
                index=0
            )
            referral_source = st.text_input("Referral Source", value=lead.get('source', ''))

        st.markdown("### Project Details")
        project_description = st.text_area("Project Description", height=100)
        estimated_value = st.number_input("Estimated Project Value ($)",
            min_value=0,
            value=int(lead.get('property_value', 0) * 0.1),  # Estimate 10% of property value
            step=1000
        )

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submit = st.form_submit_button("Convert to Customer", type="primary")
        with col_cancel:
            cancel = st.form_submit_button("Cancel")

        if submit:
            # Create customer via API
            customer_data = {
                "first_name": lead['first_name'],
                "last_name": lead['last_name'],
                "email": lead.get('email'),
                "phone": lead.get('phone'),
                "address": lead.get('address'),
                "city": lead.get('city'),
                "state": lead.get('state'),
                "zip_code": lead.get('zip_code'),
                "company_name": company_name if company_name else None,
                "customer_type": customer_type.lower(),
                "preferred_contact_method": preferred_contact.lower(),
                "referral_source": referral_source,
                "notes": f"Converted from lead #{lead['id']}. {project_description}",
                "lead_id": lead['id']
            }

            try:
                # Create customer
                response = api_client.post("/customers", json=customer_data)
                if response.status_code == 201:
                    customer_id = response.json().get('customer_id')

                    # Update lead status to 'won'
                    api_client.put(f"/leads/{lead['id']}", json={"status": "won"})

                    st.success(f"✅ Lead converted to customer successfully! Customer ID: {customer_id}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Error creating customer: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

        if cancel:
            st.rerun()

# Auto-refresh every 30 seconds
auto_refresh(interval_ms=30000, key="leads_refresh")

# Inject Pusher real-time client (subscribes to leads, customers, analytics channels)
inject_pusher_script(channels=['leads', 'customers', 'analytics'], debug=False)

# Custom CSS
st.markdown("""
    <style>
    .lead-card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        background-color: white;
    }
    .hot-lead {
        border-left: 5px solid #dc3545;
    }
    .warm-lead {
        border-left: 5px solid #ffc107;
    }
    .cool-lead {
        border-left: 5px solid #17a2b8;
    }
    .cold-lead {
        border-left: 5px solid #6c757d;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }
    .status-new { background-color: #e3f2fd; color: #1976d2; }
    .status-contacted { background-color: #f3e5f5; color: #7b1fa2; }
    .status-qualified { background-color: #e8f5e9; color: #388e3c; }
    .status-won { background-color: #c8e6c9; color: #2e7d32; }
    .status-lost { background-color: #ffcdd2; color: #c62828; }
    .response-alert {
        padding: 10px;
        border-radius: 5px;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title and header
st.title("👥 Lead Management - Real-Time Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🔍 Filters & Settings")

    # Connection status
    show_connection_status(api_client)
    create_realtime_indicator(active=True)
    display_last_updated(key="leads_last_updated")

    st.markdown("---")

    # Status filter
    status_options = ["All", "New", "Contacted", "Qualified", "Appointment Scheduled",
                     "Inspection Completed", "Quote Sent", "Negotiation", "Won", "Lost", "Nurture"]
    status_filter = st.selectbox("Status", status_options)

    # Temperature filter
    temperature_options = ["All", "Hot", "Warm", "Cool", "Cold"]
    temperature_filter = st.selectbox("Temperature", temperature_options)

    # Source filter
    source_options = ["All", "Google LSA", "Facebook Ads", "Community Marketing",
                     "Insurance Referral", "Real Estate Agent", "Nextdoor"]
    source_filter = st.selectbox("Source", source_options)

    # Date range filter
    st.subheader("Date Range")
    date_range_option = st.selectbox("Period", ["Last 7 days", "Last 30 days", "Last 90 days", "This Year", "Custom"])

    if date_range_option == "Custom":
        date_range = st.date_input(
            "Created between",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )

    # Lead score filter
    st.subheader("Lead Score")
    score_range = st.slider("Score range", 0, 100, (0, 100))

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    if st.button("📥 Export to CSV", use_container_width=True):
        st.info("Export functionality coming soon!")

    # Pusher status and notification preferences
    pusher_status_indicator()
    notification_preferences_sidebar()

# Search bar
search_query = st.text_input("🔍 Search leads by name, email, phone, or address...", "")

# View toggle and metrics
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
with col1:
    view_mode = st.radio("View Mode", ["📋 List View", "📊 Kanban Board", "📈 Analytics"], horizontal=True)

# Fetch leads data and response time metrics
try:
    # Fetch leads from API (returns list directly)
    leads_data = api_client.get_leads(limit=500)

    # Fetch lead response metrics
    try:
        response_metrics = api_client.get_lead_response_metrics()
    except:
        response_metrics = None

    # Update metrics
    if leads_data and len(leads_data) > 0:
        display_data_source_badge("live")

        df = pd.DataFrame(leads_data)

        # Apply filters
        filtered_df = df.copy()

        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter.lower().replace(" ", "_")]

        if temperature_filter != "All":
            filtered_df = filtered_df[filtered_df['temperature'] == temperature_filter.lower()]

        if source_filter != "All":
            filtered_df = filtered_df[filtered_df['source'] == source_filter]

        if search_query:
            search_mask = (
                filtered_df['first_name'].str.contains(search_query, case=False, na=False) |
                filtered_df['last_name'].str.contains(search_query, case=False, na=False) |
                filtered_df['email'].str.contains(search_query, case=False, na=False) |
                filtered_df['phone'].str.contains(search_query, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]

        # Calculate metrics
        total_leads = len(filtered_df)
        hot_leads = len(filtered_df[filtered_df['temperature'] == 'hot'])
        warm_leads = len(filtered_df[filtered_df['temperature'] == 'warm'])

        # Calculate conversion rate
        won_leads = len(filtered_df[filtered_df['status'] == 'won'])
        conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

        # Display metrics
        with col2:
            st.metric("Total Leads", total_leads)
        with col3:
            st.metric("Hot Leads", hot_leads, f"{(hot_leads/total_leads*100):.1f}%" if total_leads > 0 else "0%")
        with col4:
            st.metric("Warm Leads", warm_leads, f"{(warm_leads/total_leads*100):.1f}%" if total_leads > 0 else "0%")
        with col5:
            st.metric("Conversion", f"{conversion_rate:.1f}%",
                     f"{conversion_rate - 25:.1f}%" if conversion_rate > 0 else "N/A")

        st.markdown("---")

        # Response Time Alert Section
        if response_metrics:
            avg_response_time = response_metrics.get("avg_response_time_seconds", 0)
            percent_under_target = response_metrics.get("percent_under_target", 0)
            potential_lost = response_metrics.get("potential_lost_conversions", 0)

            # Show alert if response time is concerning
            if avg_response_time > 120 or percent_under_target < 75:
                st.markdown(f"""
                <div class="response-alert">
                    ⚠️ <strong>Response Time Alert</strong><br>
                    Average response time: <strong>{avg_response_time:.0f} seconds</strong> (Target: 120s)<br>
                    Only <strong>{percent_under_target:.1f}%</strong> of leads responded to within 2 minutes<br>
                    Potential impact: <strong>{potential_lost:.1f} lost conversions</strong> (78% boost if <2min)
                </div>
                """, unsafe_allow_html=True)

        # Display based on view mode
        if view_mode == "📋 List View":
            # Add new lead button
            if st.button("➕ Add New Lead", type="primary", use_container_width=True):
                st.session_state['show_new_lead_form'] = True

            # Display leads
            if not filtered_df.empty:
                st.subheader(f"Showing {len(filtered_df)} leads")

                # Sort by lead score (hottest first)
                filtered_df = filtered_df.sort_values('lead_score', ascending=False)

                # Paginate results
                items_per_page = 20
                total_pages = (len(filtered_df) - 1) // items_per_page + 1
                page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
                start_idx = (page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_df = filtered_df.iloc[start_idx:end_idx]

                # Display leads
                for idx, lead in page_df.iterrows():
                    temperature = lead.get('temperature') or 'cold'
                    temperature_emoji = {"hot": "🔥", "warm": "🌡️", "cool": "❄️", "cold": "🧊"}.get(temperature, "⚪")

                    with st.expander(f"{temperature_emoji} {lead['first_name']} {lead['last_name']} - Score: {lead.get('lead_score', 0)}/100"):
                        col1, col2, col3 = st.columns([2, 2, 1])

                        with col1:
                            st.write(f"**Email:** {lead.get('email', 'N/A')}")
                            st.write(f"**Phone:** {lead.get('phone', 'N/A')}")
                            st.write(f"**Address:** {lead.get('address', 'N/A')}, {lead.get('city', 'N/A')}")
                            st.write(f"**Source:** {lead.get('source', 'N/A')}")

                        with col2:
                            status = lead.get('status') or 'new'
                            st.write(f"**Status:** {status.replace('_', ' ').title()}")
                            st.write(f"**Temperature:** {temperature.title()}")
                            property_value = lead.get('property_value') or 0
                            st.write(f"**Property Value:** ${property_value:,.0f}")

                            # Calculate time since creation
                            created_at = lead.get('created_at')
                            if created_at:
                                try:
                                    # Try ISO format first
                                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    # Fall back to RFC 2822 format (from Flask)
                                    created_time = parsedate_to_datetime(created_at)
                                time_since = datetime.now().astimezone() - created_time
                                st.write(f"**Created:** {time_since.days} days ago")

                        with col3:
                            if st.button(f"View Details", key=f"view_{lead['id']}"):
                                show_lead_details(lead)

                            if st.button(f"Edit", key=f"edit_{lead['id']}"):
                                edit_lead_modal(lead)

                            if lead.get('status') not in ['won', 'lost']:
                                if st.button(f"Convert", key=f"convert_{lead['id']}"):
                                    convert_lead_modal(lead)
            else:
                st.info("No leads found matching your filters.")

        elif view_mode == "📊 Kanban Board":
            st.subheader("Lead Pipeline - Kanban View")

            # Create columns for each major status
            statuses = ["new", "contacted", "qualified", "quote_sent", "won", "lost"]
            status_labels = ["New", "Contacted", "Qualified", "Quote Sent", "Won", "Lost"]
            cols = st.columns(len(statuses))

            for idx, (status, label) in enumerate(zip(statuses, status_labels)):
                with cols[idx]:
                    status_leads = filtered_df[filtered_df['status'] == status]
                    st.markdown(f"### {label} ({len(status_leads)})")

                    for _, lead in status_leads.head(10).iterrows():
                        temp_class = f"{lead.get('temperature', 'cold')}-lead"
                        property_value = lead.get('property_value') or 0
                        st.markdown(f"""
                        <div class='lead-card {temp_class}'>
                            <strong>{lead['first_name']} {lead['last_name']}</strong><br>
                            Score: {lead.get('lead_score', 0)}/100<br>
                            ${property_value:,.0f}<br>
                            <small>{lead.get('city', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)

                    if len(status_leads) > 10:
                        st.caption(f"+{len(status_leads) - 10} more...")

        elif view_mode == "📈 Analytics":
            st.subheader("Lead Analytics Dashboard")

            # Top metrics
            col1, col2 = st.columns(2)

            with col1:
                # Lead Response Time Gauge
                if response_metrics:
                    create_response_time_gauge(
                        avg_time=response_metrics.get("avg_response_time_seconds", 0),
                        target=120,
                        title="Average Lead Response Time (2-Minute Target)"
                    )

            with col2:
                # Temperature distribution
                temp_data = filtered_df['temperature'].value_counts()
                temp_metrics = {
                    "hot": {"total": temp_data.get("hot", 0), "rate": 0},
                    "warm": {"total": temp_data.get("warm", 0), "rate": 0},
                    "cold": {"total": temp_data.get("cold", 0), "rate": 0}
                }
                create_conversion_by_temperature(temp_metrics)

            st.markdown("---")

            # Additional charts
            col1, col2 = st.columns(2)

            with col1:
                # Status distribution pie chart
                status_counts = filtered_df['status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=[(s or 'unknown').replace('_', ' ').title() for s in status_counts.index],
                    title="Lead Status Distribution",
                    color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#43e97b', '#4facfe']
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Source performance
                source_counts = filtered_df['source'].value_counts().head(6)
                fig = px.bar(
                    x=source_counts.index,
                    y=source_counts.values,
                    title="Top Lead Sources",
                    labels={'x': 'Source', 'y': 'Count'},
                    color=source_counts.values,
                    color_continuous_scale='Blues'
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

            # Lead score distribution
            fig = px.histogram(
                filtered_df,
                x='lead_score',
                nbins=20,
                title="Lead Score Distribution",
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig, use_container_width=True)

            # City/Market analysis
            if 'city' in filtered_df.columns:
                city_counts = filtered_df['city'].value_counts().head(10)
                fig = px.bar(
                    x=city_counts.index,
                    y=city_counts.values,
                    title="Top 10 Cities",
                    labels={'x': 'City', 'y': 'Leads'},
                    color=city_counts.values,
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig, use_container_width=True)

    else:
        display_data_source_badge("demo")
        st.info("No leads data available. Add your first lead to get started!")
        if st.button("➕ Add New Lead", type="primary"):
            st.session_state['show_new_lead_form'] = True

except Exception as e:
    display_data_source_badge("demo")
    st.error(f"❌ Error loading leads: {str(e)}")
    st.info("💡 Make sure backend is running on http://localhost:8001")

# New Lead Form
if st.session_state.get('show_new_lead_form', False):
    st.markdown("---")
    st.subheader("➕ Add New Lead")

    with st.form("new_lead_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name *")
            last_name = st.text_input("Last Name *")
            email = st.text_input("Email *")
            phone = st.text_input("Phone *")

        with col2:
            address = st.text_input("Address *")
            city = st.text_input("City *")
            source = st.selectbox("Source", source_options[1:])
            property_value = st.number_input("Property Value ($)", min_value=0, step=10000)

        notes = st.text_area("Notes")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Lead", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state['show_new_lead_form'] = False
                st.rerun()

        if submitted:
            if not all([first_name, last_name, email, phone, address, city]):
                st.error("Please fill in all required fields marked with *")
            else:
                try:
                    # Map UI values to API enum values
                    source_mapping = {
                        "Google LSA": "google_lsa",
                        "Facebook Ads": "facebook_ads",
                        "Community Marketing": "community_marketing",
                        "Insurance Referral": "insurance_referral",
                        "Real Estate Agent": "real_estate_agent",
                        "Nextdoor": "nextdoor"
                    }

                    lead_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "street_address": address,
                        "city": city,
                        "state": "MI",  # Default to Michigan
                        "zip_code": "",  # Optional
                        "source": source_mapping.get(source, "website_form"),
                        "property_value": int(property_value) if property_value else None,
                        "notes": notes if notes else None
                    }

                    response = api_client.create_lead(lead_data)

                    if response and 'data' in response:
                        st.success(f"✅ Lead created successfully! Lead ID: {response['data'].get('id', 'N/A')[:8]}...")
                        st.session_state['show_new_lead_form'] = False
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Failed to create lead. Please try again.")
                except Exception as e:
                    st.error(f"Error creating lead: {str(e)}")
                    st.info("💡 Make sure all required fields are filled and backend is running")

# Footer
st.markdown("---")
st.markdown("""
### 💡 Lead Management Tips
- **Hot Leads (🔥)**: Respond within 2 minutes for 78% conversion boost
- **Lead Score**: Higher scores indicate better quality leads (based on property value, city, source)
- **Premium Markets**: Focus on Bloomfield Hills, Birmingham, Grosse Pointe for higher deal values
- **Real-Time Updates**: Dashboard refreshes automatically every 30 seconds
""")
