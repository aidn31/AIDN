"""
AIDN Dashboard - Standalone Demo
================================

Streamlit web interface for AIDN lead management and calling.
"""

import asyncio
import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

# Load environment variables
load_dotenv()


class DemoDatabase:
    """Simple synchronous database connection for Streamlit."""

    def __init__(self):
        self.connection_string = os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable is required")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dicts."""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params or ())
                    if cur.description:  # Query returns results
                        return [dict(row) for row in cur.fetchall()]
                    return []
        except Exception as e:
            st.error(f"Database query failed: {e}")
            raise

    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all active agents."""
        query = """
        SELECT id, agent_name, phone, email, physical_description, car_description
        FROM agent_profiles
        WHERE is_active = true
        """
        return self.execute_query(query)

    def get_leads_for_agent(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get leads for an agent."""
        query = """
        SELECT id, first_name, last_name, phone, city, state, county,
               lead_type, lead_source, call_outcome, call_count,
               created_at, last_called_at, next_call_at
        FROM leads
        WHERE agent_id = %s AND is_active = true
        ORDER BY
            CASE call_outcome
                WHEN 'fresh' THEN 1
                WHEN 'callback' THEN 2
                WHEN 'no_answer' THEN 3
                ELSE 4
            END,
            created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (agent_id, limit))

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            self.execute_query("SELECT 1")
            return True
        except:
            return False


# Configure Streamlit page
st.set_page_config(
    page_title="AIDN Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "db" not in st.session_state:
    st.session_state.db = None
if "current_agent" not in st.session_state:
    st.session_state.current_agent = None


def init_database():
    """Initialize database connection."""
    if st.session_state.db is None:
        try:
            st.session_state.db = DemoDatabase()
            # Test connection
            if not st.session_state.db.test_connection():
                raise Exception("Database connection test failed")
            st.success("✅ Database connected successfully!")
        except Exception as e:
            st.error(f"Database initialization failed: {e}")
            st.session_state.db = None
            raise


def load_agents():
    """Load available agents."""
    if st.session_state.db:
        return st.session_state.db.get_agents()
    return []


def load_leads(agent_id: str, limit: int = 100):
    """Load leads for an agent."""
    if st.session_state.db and agent_id:
        return st.session_state.db.get_leads_for_agent(agent_id, limit)
    return []


def main():
    """Main Streamlit app."""

    st.title("📞 AIDN Dashboard")
    st.markdown("**AI-Powered Insurance Distribution Network**")
    st.markdown("---")

    # Sidebar for navigation
    with st.sidebar:
        st.header("🎯 Navigation")
        page = st.selectbox(
            "Select Page",
            ["Dashboard", "Lead Management", "Calling", "Analytics", "Settings"]
        )

    # Initialize database
    try:
        init_database()
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.info("Please ensure PostgreSQL is running and environment variables are set.")
        st.stop()

    # Agent selection
    try:
        agents = load_agents()
        if not agents:
            st.warning("⚠️ No active agents found. Please set up an agent profile first.")
            st.info("Check your database for agent_profiles table.")
            st.stop()

        st.sidebar.markdown("---")
        st.sidebar.header("👤 Agent Selection")
        agent_options = {f"{agent['agent_name']}": str(agent['id']) for agent in agents}
        selected_agent_name = st.sidebar.selectbox("Select Agent", list(agent_options.keys()))
        selected_agent_id = agent_options[selected_agent_name]
        st.session_state.current_agent = selected_agent_id

        st.sidebar.success(f"✅ Agent: {selected_agent_name}")

    except Exception as e:
        st.error(f"❌ Error loading agents: {e}")
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
    st.header("📊 Dashboard Overview")

    if not st.session_state.current_agent:
        st.warning("Please select an agent to view dashboard.")
        return

    try:
        # Load data
        leads = load_leads(st.session_state.current_agent)

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📋 Total Leads", len(leads))

        with col2:
            fresh_leads = len([l for l in leads if l['call_outcome'] == "fresh"])
            st.metric("🆕 Fresh Leads", fresh_leads)

        with col3:
            booked_leads = len([l for l in leads if l['call_outcome'] == "booked"])
            st.metric("📅 Appointments Booked", booked_leads)

        with col4:
            if len(leads) > 0:
                conversion_rate = (booked_leads / len(leads)) * 100
            else:
                conversion_rate = 0
            st.metric("📈 Conversion Rate", f"{conversion_rate:.1f}%")

        st.markdown("---")

        # Recent leads table
        st.subheader("📝 Recent Leads")
        if leads:
            df = pd.DataFrame([{
                "Name": f"{lead['first_name']} {lead['last_name']}",
                "Phone": lead['phone'],
                "City": lead['city'] or "N/A",
                "Lead Type": lead['lead_type'] or "N/A",
                "Status": lead['call_outcome'],
                "Last Called": lead['last_called_at'].strftime("%Y-%m-%d %H:%M") if lead['last_called_at'] else "Never"
            } for lead in leads[:10]])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("ℹ️ No leads found for this agent.")

    except Exception as e:
        st.error(f"❌ Error loading dashboard data: {e}")


def show_lead_management():
    """Show lead management interface."""
    st.header("📁 Lead Management")

    tab1, tab2 = st.tabs(["📤 Upload Leads", "📋 Manage Leads"])

    with tab1:
        st.subheader("📤 Upload New Leads")
        st.info("🔧 Lead upload functionality coming soon!")

    with tab2:
        st.subheader("📋 Manage Existing Leads")

        if st.session_state.current_agent:
            try:
                leads = load_leads(st.session_state.current_agent)

                if leads:
                    # Filter controls
                    col1, col2 = st.columns(2)
                    with col1:
                        status_filter = st.multiselect(
                            "🎯 Filter by Status",
                            ["fresh", "no_answer", "not_interested", "booked", "callback"],
                            default=["fresh", "callback"]
                        )

                    with col2:
                        search_term = st.text_input("🔍 Search by name or phone")

                    # Apply filters
                    filtered_leads = [
                        lead for lead in leads
                        if lead['call_outcome'] in status_filter
                        and (not search_term or search_term.lower() in f"{lead['first_name']} {lead['last_name']} {lead['phone']}".lower())
                    ]

                    st.markdown(f"**📊 Showing {len(filtered_leads)} leads**")

                    # Display leads
                    for lead in filtered_leads[:20]:  # Limit to 20 for performance
                        with st.expander(f"👤 {lead['first_name']} {lead['last_name']} - {lead['phone']}"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.write(f"**📊 Status:** {lead['call_outcome']}")
                                st.write(f"**🎯 Lead Type:** {lead['lead_type'] or 'N/A'}")
                                st.write(f"**🔗 Source:** {lead['lead_source'] or 'N/A'}")

                            with col2:
                                st.write(f"**🌆 City:** {lead['city'] or 'N/A'}")
                                st.write(f"**🗺️ State:** {lead['state'] or 'N/A'}")
                                st.write(f"**📞 Calls:** {lead['call_count']}")

                            with col3:
                                st.write(f"**📅 Created:** {lead['created_at'].strftime('%Y-%m-%d')}")
                                if lead['last_called_at']:
                                    st.write(f"**📞 Last Called:** {lead['last_called_at'].strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.info("ℹ️ No leads found.")

            except Exception as e:
                st.error(f"❌ Error loading leads: {e}")


def show_calling_interface():
    """Show calling interface."""
    st.header("📞 Calling Interface")

    if not st.session_state.current_agent:
        st.warning("⚠️ Please select an agent to start calling.")
        return

    try:
        # Get next lead to call
        leads = load_leads(st.session_state.current_agent, limit=1)

        if leads:
            lead = leads[0]

            st.subheader("🎯 Next Lead to Call")

            col1, col2 = st.columns(2)

            with col1:
                st.info(f"""
                **👤 Name:** {lead['first_name']} {lead['last_name']}
                **📞 Phone:** {lead['phone']}
                **🌆 City:** {lead['city'] or 'N/A'}, {lead['state'] or 'N/A'}
                **🎯 Lead Type:** {lead['lead_type'] or 'N/A'}
                **📊 Previous Attempts:** {lead['call_count']}
                """)

            with col2:
                if st.button("📞 Call Lead", type="primary", use_container_width=True):
                    with st.spinner("🔄 Initiating call..."):
                        st.success("✅ Call initiated! Check your phone system.")

                if st.button("⏭️ Skip Lead", use_container_width=True):
                    st.info("⏭️ Lead skipped.")

                if st.button("❌ Mark as Do Not Call", use_container_width=True):
                    st.warning("❌ Lead marked as Do Not Call.")

        else:
            st.info("ℹ️ No leads available for calling at this time.")

        # Call history
        st.subheader("📋 Recent Call Activity")
        st.info("📊 Call logs would appear here in a real implementation.")

    except Exception as e:
        st.error(f"❌ Error in calling interface: {e}")


def show_analytics():
    """Show analytics dashboard."""
    st.header("📊 Analytics")

    # Placeholder analytics
    st.info("📈 Advanced analytics dashboard coming soon!")

    # Mock data for visualization
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📞 Call Volume by Day")
        chart_data = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'Calls': [25, 30, 28, 35, 22]
        })
        st.bar_chart(chart_data.set_index('Day'))

    with col2:
        st.subheader("🎯 Conversion Funnel")
        funnel_data = pd.DataFrame({
            'Stage': ['Leads', 'Connected', 'Interested', 'Booked'],
            'Count': [100, 45, 25, 12]
        })
        st.bar_chart(funnel_data.set_index('Stage'))


def show_settings():
    """Show settings page."""
    st.header("⚙️ Settings")

    tab1, tab2 = st.tabs(["👤 Agent Profile", "🔧 System Settings"])

    with tab1:
        st.subheader("👤 Agent Profile Settings")
        st.info("🔧 Agent profile management coming soon!")

    with tab2:
        st.subheader("🔧 System Settings")
        st.info("⚙️ System configuration coming soon!")


if __name__ == "__main__":
    main()