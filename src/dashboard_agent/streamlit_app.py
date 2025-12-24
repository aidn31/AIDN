"""
AIDN Dashboard - Streamlit Prototype
===================================

Streamlit web interface for AIDN lead management and calling.
"""

import asyncio
import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Optional

# Import AIDN modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.shared.database import DatabaseManager, LeadRepository, AgentRepository, AppointmentRepository
from src.shared.models import Lead, LeadCreate, AgentProfile
from src.voice_agent.call_manager import CallManager

# Configure Streamlit page
st.set_page_config(
    page_title="AIDN Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "db_manager" not in st.session_state:
    st.session_state.db_manager = None
if "current_agent" not in st.session_state:
    st.session_state.current_agent = None


async def init_database():
    """Initialize database connection."""
    if st.session_state.db_manager is None:
        st.session_state.db_manager = DatabaseManager()
        await st.session_state.db_manager.connect()


async def load_agents():
    """Load available agents."""
    if st.session_state.db_manager:
        agent_repo = AgentRepository(st.session_state.db_manager)
        return await agent_repo.get_active_agents()
    return []


async def load_leads(agent_id: str, limit: int = 100) -> List[Lead]:
    """Load leads for an agent."""
    if st.session_state.db_manager and agent_id:
        lead_repo = LeadRepository(st.session_state.db_manager)
        from uuid import UUID
        return await lead_repo.get_leads_for_calling(UUID(agent_id), limit)
    return []


def main():
    """Main Streamlit app."""

    st.title("📞 AIDN Dashboard")
    st.markdown("AI-Powered Insurance Distribution Network")

    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Select Page",
            ["Dashboard", "Lead Management", "Calling", "Analytics", "Settings"]
        )

    # Initialize database
    try:
        asyncio.run(init_database())
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()

    # Agent selection
    try:
        agents = asyncio.run(load_agents())
        if not agents:
            st.warning("No active agents found. Please set up an agent profile first.")
            if st.button("Create Test Agent"):
                # Create a test agent for demo
                create_test_agent()
            st.stop()

        agent_options = {f"{agent.agent_name}": str(agent.id) for agent in agents}
        selected_agent_name = st.selectbox("Select Agent", list(agent_options.keys()))
        selected_agent_id = agent_options[selected_agent_name]
        st.session_state.current_agent = selected_agent_id

    except Exception as e:
        st.error(f"Error loading agents: {e}")
        st.stop()

    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Lead Management":
        show_lead_management()
    elif page == "Calling":
        show_calling_interface()
    elif page == "Analytics":
        show_analytics()
    elif page == "Settings":
        show_settings()


def show_dashboard():
    """Show main dashboard with overview."""
    st.header("Dashboard Overview")

    if not st.session_state.current_agent:
        st.warning("Please select an agent to view dashboard.")
        return

    try:
        # Load data
        leads = asyncio.run(load_leads(st.session_state.current_agent))

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Leads", len(leads))

        with col2:
            fresh_leads = len([l for l in leads if l.call_outcome == "fresh"])
            st.metric("Fresh Leads", fresh_leads)

        with col3:
            booked_leads = len([l for l in leads if l.call_outcome == "booked"])
            st.metric("Appointments Booked", booked_leads)

        with col4:
            if len(leads) > 0:
                conversion_rate = (booked_leads / len(leads)) * 100
            else:
                conversion_rate = 0
            st.metric("Conversion Rate", f"{conversion_rate:.1f}%")

        # Recent leads table
        st.subheader("Recent Leads")
        if leads:
            df = pd.DataFrame([{
                "Name": f"{lead.first_name} {lead.last_name}",
                "Phone": lead.phone,
                "City": lead.city or "N/A",
                "Lead Type": lead.lead_type or "N/A",
                "Status": lead.call_outcome,
                "Last Called": lead.last_called_at.strftime("%Y-%m-%d %H:%M") if lead.last_called_at else "Never"
            } for lead in leads[:10]])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No leads found for this agent.")

    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")


def show_lead_management():
    """Show lead management interface."""
    st.header("Lead Management")

    tab1, tab2 = st.tabs(["Upload Leads", "Manage Leads"])

    with tab1:
        st.subheader("Upload New Leads")

        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file with lead data. Required columns: first_name, last_name, phone"
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview:")
                st.dataframe(df.head(), use_container_width=True)

                if st.button("Import Leads"):
                    # Import leads logic would go here
                    st.success(f"Successfully imported {len(df)} leads!")

            except Exception as e:
                st.error(f"Error reading file: {e}")

    with tab2:
        st.subheader("Manage Existing Leads")

        if st.session_state.current_agent:
            try:
                leads = asyncio.run(load_leads(st.session_state.current_agent))

                if leads:
                    # Filter controls
                    col1, col2 = st.columns(2)
                    with col1:
                        status_filter = st.multiselect(
                            "Filter by Status",
                            ["fresh", "no_answer", "not_interested", "booked", "callback"],
                            default=["fresh", "callback"]
                        )

                    with col2:
                        search_term = st.text_input("Search by name or phone")

                    # Apply filters
                    filtered_leads = [
                        lead for lead in leads
                        if lead.call_outcome in status_filter
                        and (not search_term or search_term.lower() in f"{lead.first_name} {lead.last_name} {lead.phone}".lower())
                    ]

                    # Display leads
                    for lead in filtered_leads[:20]:  # Limit to 20 for performance
                        with st.expander(f"{lead.full_name} - {lead.phone}"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.write(f"**Status:** {lead.call_outcome}")
                                st.write(f"**Lead Type:** {lead.lead_type or 'N/A'}")
                                st.write(f"**Source:** {lead.lead_source or 'N/A'}")

                            with col2:
                                st.write(f"**City:** {lead.city or 'N/A'}")
                                st.write(f"**State:** {lead.state or 'N/A'}")
                                st.write(f"**Calls:** {lead.call_count}")

                            with col3:
                                st.write(f"**Created:** {lead.created_at.strftime('%Y-%m-%d')}")
                                if lead.last_called_at:
                                    st.write(f"**Last Called:** {lead.last_called_at.strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.info("No leads found.")

            except Exception as e:
                st.error(f"Error loading leads: {e}")


def show_calling_interface():
    """Show calling interface."""
    st.header("Calling Interface")

    if not st.session_state.current_agent:
        st.warning("Please select an agent to start calling.")
        return

    try:
        # Get next lead to call
        leads = asyncio.run(load_leads(st.session_state.current_agent, limit=1))

        if leads:
            lead = leads[0]

            st.subheader("Next Lead to Call")

            col1, col2 = st.columns(2)

            with col1:
                st.info(f"""
                **Name:** {lead.full_name}
                **Phone:** {lead.phone}
                **City:** {lead.city or 'N/A'}, {lead.state or 'N/A'}
                **Lead Type:** {lead.lead_type or 'N/A'}
                **Previous Attempts:** {lead.call_count}
                """)

            with col2:
                if st.button("📞 Call Lead", type="primary", use_container_width=True):
                    with st.spinner("Initiating call..."):
                        # In a real implementation, this would trigger the voice agent
                        st.success("Call initiated! Check your phone system.")

                if st.button("⏭️ Skip Lead", use_container_width=True):
                    st.info("Lead skipped.")

                if st.button("❌ Mark as Do Not Call", use_container_width=True):
                    st.warning("Lead marked as Do Not Call.")

        else:
            st.info("No leads available for calling at this time.")

        # Call history
        st.subheader("Recent Call Activity")
        st.info("Call logs would appear here in a real implementation.")

    except Exception as e:
        st.error(f"Error in calling interface: {e}")


def show_analytics():
    """Show analytics dashboard."""
    st.header("Analytics")

    # Placeholder analytics
    st.info("Analytics dashboard coming soon!")

    # Mock data for visualization
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Call Volume by Day")
        chart_data = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'Calls': [25, 30, 28, 35, 22]
        })
        st.bar_chart(chart_data.set_index('Day'))

    with col2:
        st.subheader("Conversion Funnel")
        funnel_data = pd.DataFrame({
            'Stage': ['Leads', 'Connected', 'Interested', 'Booked'],
            'Count': [100, 45, 25, 12]
        })
        st.bar_chart(funnel_data.set_index('Stage'))


def show_settings():
    """Show settings page."""
    st.header("Settings")

    tab1, tab2 = st.tabs(["Agent Profile", "System Settings"])

    with tab1:
        st.subheader("Agent Profile Settings")

        # Mock agent settings form
        agent_name = st.text_input("Agent Name", value="John Smith")
        phone = st.text_input("Phone", value="+1-555-0123")
        email = st.text_input("Email", value="john@example.com")

        st.text_area("Physical Description",
                    value="Male, 6 feet tall, brown hair, wearing a dark suit")
        st.text_input("Car Description",
                     value="Silver Honda Accord")

        if st.button("Save Profile"):
            st.success("Profile saved successfully!")

    with tab2:
        st.subheader("System Settings")

        st.selectbox("Time Zone", ["Eastern", "Central", "Mountain", "Pacific"])
        st.slider("Max Calls Per Day", 1, 100, 50)
        st.checkbox("Enable Call Recording", value=True)
        st.checkbox("Send Daily Reports", value=True)


def create_test_agent():
    """Create a test agent for demo purposes."""
    # This would create a test agent in the database
    st.success("Test agent created successfully!")


if __name__ == "__main__":
    main()