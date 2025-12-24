"""
AIDN Dashboard - Demo UI
========================

Simple Streamlit interface showcasing AIDN dashboard features.
"""

import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta


# Configure Streamlit page
st.set_page_config(
    page_title="AIDN Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)


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

        st.markdown("---")
        st.header("👤 Agent Selection")

        # Mock agent data
        agent_name = st.selectbox("Select Agent", ["John Smith"])
        st.success(f"✅ Agent: {agent_name}")

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

    # Mock metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📋 Total Leads", "5", "+2 from yesterday")

    with col2:
        st.metric("🆕 Fresh Leads", "3")

    with col3:
        st.metric("📅 Appointments Booked", "1", "+1 today")

    with col4:
        st.metric("📈 Conversion Rate", "20.0%", "+5% improvement")

    st.markdown("---")

    # Mock leads data
    st.subheader("📝 Recent Leads")
    mock_leads = pd.DataFrame([
        {
            "Name": "Mary Johnson",
            "Phone": "(555) 0101",
            "City": "Chicago, IL",
            "Lead Type": "Final Expense",
            "Status": "fresh",
            "Last Called": "Never"
        },
        {
            "Name": "Robert Davis",
            "Phone": "(555) 0102",
            "City": "Springfield, IL",
            "Lead Type": "Term Life",
            "Status": "fresh",
            "Last Called": "Never"
        },
        {
            "Name": "Jennifer Wilson",
            "Phone": "(555) 0103",
            "City": "Peoria, IL",
            "Lead Type": "Whole Life",
            "Status": "booked",
            "Last Called": "2024-12-23 14:30"
        },
        {
            "Name": "Michael Brown",
            "Phone": "(555) 0104",
            "City": "Rockford, IL",
            "Lead Type": "Mortgage Protection",
            "Status": "fresh",
            "Last Called": "Never"
        },
        {
            "Name": "Sarah Miller",
            "Phone": "(555) 0105",
            "City": "Naperville, IL",
            "Lead Type": "Final Expense",
            "Status": "fresh",
            "Last Called": "Never"
        }
    ])

    st.dataframe(mock_leads, use_container_width=True)


def show_lead_management():
    """Show lead management interface."""
    st.header("📁 Lead Management")

    tab1, tab2 = st.tabs(["📤 Upload Leads", "📋 Manage Leads"])

    with tab1:
        st.subheader("📤 Upload New Leads")

        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file with lead data. Required columns: first_name, last_name, phone"
        )

        if uploaded_file is not None:
            st.success("✅ File uploaded successfully!")
            st.info("📊 In a real implementation, leads would be processed and imported to the database.")

    with tab2:
        st.subheader("📋 Manage Existing Leads")

        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "🎯 Filter by Status",
                ["fresh", "no_answer", "not_interested", "booked", "callback"],
                default=["fresh", "booked"]
            )

        with col2:
            search_term = st.text_input("🔍 Search by name or phone")

        st.markdown("**📊 Showing 5 leads**")

        # Mock lead details
        mock_leads = [
            {
                "name": "Mary Johnson",
                "phone": "(555) 0101",
                "status": "fresh",
                "type": "Final Expense",
                "city": "Chicago, IL",
                "calls": 0,
                "created": "2024-12-20"
            },
            {
                "name": "Jennifer Wilson",
                "phone": "(555) 0103",
                "status": "booked",
                "type": "Whole Life",
                "city": "Peoria, IL",
                "calls": 1,
                "created": "2024-12-19"
            }
        ]

        for lead in mock_leads:
            if lead["status"] in status_filter:
                with st.expander(f"👤 {lead['name']} - {lead['phone']}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**📊 Status:** {lead['status']}")
                        st.write(f"**🎯 Lead Type:** {lead['type']}")
                        st.write(f"**🔗 Source:** Direct Mail")

                    with col2:
                        st.write(f"**🌆 City:** {lead['city']}")
                        st.write(f"**🗺️ State:** Illinois")
                        st.write(f"**📞 Calls:** {lead['calls']}")

                    with col3:
                        st.write(f"**📅 Created:** {lead['created']}")
                        if lead['calls'] > 0:
                            st.write("**📞 Last Called:** 2024-12-23 14:30")


def show_calling_interface():
    """Show calling interface."""
    st.header("📞 Calling Interface")

    st.subheader("🎯 Next Lead to Call")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **👤 Name:** Mary Johnson
        **📞 Phone:** (555) 0101
        **🌆 City:** Chicago, IL
        **🎯 Lead Type:** Final Expense
        **📊 Previous Attempts:** 0
        """)

    with col2:
        if st.button("📞 Call Lead", type="primary", use_container_width=True):
            with st.spinner("🔄 Initiating call..."):
                st.balloons()
                st.success("✅ Call initiated! Voice agent is now calling Mary Johnson.")
                st.info("🎤 AIDN Voice Agent will handle the conversation and book appointments automatically.")

        if st.button("⏭️ Skip Lead", use_container_width=True):
            st.info("⏭️ Lead skipped. Moving to next lead in queue.")

        if st.button("❌ Mark as Do Not Call", use_container_width=True):
            st.warning("❌ Lead marked as Do Not Call.")

    st.markdown("---")

    # Voice agent status
    st.subheader("🤖 Voice Agent Status")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🟢 Agent Status", "Online")
    with col2:
        st.metric("📞 Calls Today", "12")
    with col3:
        st.metric("📅 Appointments Booked", "3")

    # Recent call activity
    st.subheader("📋 Recent Call Activity")

    call_logs = pd.DataFrame([
        {
            "Time": "14:30",
            "Lead": "Jennifer Wilson",
            "Duration": "2:15",
            "Outcome": "Appointment Booked",
            "Next Action": "Meeting scheduled for tomorrow 10 AM"
        },
        {
            "Time": "13:45",
            "Lead": "Robert Davis",
            "Duration": "0:45",
            "Outcome": "No Answer",
            "Next Action": "Retry in 2 hours"
        },
        {
            "Time": "13:10",
            "Lead": "Michael Brown",
            "Duration": "3:20",
            "Outcome": "Not Interested",
            "Next Action": "Retry in 7 days"
        }
    ])

    st.dataframe(call_logs, use_container_width=True)


def show_analytics():
    """Show analytics dashboard."""
    st.header("📊 Analytics")

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📞 Connection Rate", "15.2%", "+3.2% vs industry")
    with col2:
        st.metric("📅 Booking Rate", "8.5%", "+3.5% vs industry")
    with col3:
        st.metric("💰 Cost per Appointment", "$22", "-$28 vs industry")
    with col4:
        st.metric("⏱️ Agent Time Saved", "72%", "+22% efficiency")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📞 Call Volume by Day")
        chart_data = pd.DataFrame({
            'Day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'Calls': [25, 30, 28, 35, 22],
            'Appointments': [5, 7, 6, 8, 4]
        })
        st.line_chart(chart_data.set_index('Day'))

    with col2:
        st.subheader("🎯 Conversion Funnel")
        funnel_data = pd.DataFrame({
            'Stage': ['Total Leads', 'Connected', 'Interested', 'Booked'],
            'Count': [100, 45, 25, 12],
            'Conversion': ['100%', '45%', '25%', '12%']
        })

        for _, row in funnel_data.iterrows():
            st.metric(row['Stage'], row['Count'], row['Conversion'])

    st.markdown("---")

    # Performance by territory
    st.subheader("🗺️ Performance by Territory")
    territory_data = pd.DataFrame({
        'County': ['Cook', 'DuPage', 'Lake', 'Will', 'Kane'],
        'Leads': [45, 28, 35, 22, 18],
        'Appointments': [8, 5, 7, 4, 3],
        'Conversion Rate': ['17.8%', '17.9%', '20.0%', '18.2%', '16.7%']
    })
    st.dataframe(territory_data, use_container_width=True)


def show_settings():
    """Show settings page."""
    st.header("⚙️ Settings")

    tab1, tab2, tab3 = st.tabs(["👤 Agent Profile", "📞 Calling Hours", "🔧 System"])

    with tab1:
        st.subheader("👤 Agent Profile")

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Agent Name", value="John Smith")
            st.text_input("Phone", value="+1-555-0123")
            st.text_input("Email", value="john@example.com")

        with col2:
            st.text_area("Physical Description",
                        value="Male, 6 feet tall, brown hair, wearing a dark suit")
            st.text_input("Car Description",
                         value="Silver Honda Accord, License: ABC-1234")

        if st.button("💾 Save Profile"):
            st.success("✅ Profile saved successfully!")

    with tab2:
        st.subheader("📞 Calling Schedule")

        # Days of week
        st.write("**📅 Active Days:**")
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            st.checkbox("Mon", value=True)
        with col2:
            st.checkbox("Tue", value=True)
        with col3:
            st.checkbox("Wed", value=False)
        with col4:
            st.checkbox("Thu", value=True)
        with col5:
            st.checkbox("Fri", value=True)
        with col6:
            st.checkbox("Sat", value=True)
        with col7:
            st.checkbox("Sun", value=False)

        st.markdown("---")

        # Time settings
        col1, col2 = st.columns(2)
        with col1:
            st.time_input("⏰ Start Calling", value=pd.to_datetime("09:00").time())
            st.number_input("📞 Max Daily Appointments", min_value=1, max_value=10, value=4)

        with col2:
            st.time_input("🕕 Stop Calling", value=pd.to_datetime("15:00").time())
            st.number_input("⏱️ Gap Between Appointments (hours)", min_value=1, max_value=4, value=2)

    with tab3:
        st.subheader("🔧 System Configuration")

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("🌍 Time Zone", ["Eastern", "Central", "Mountain", "Pacific"], index=1)
            st.checkbox("📹 Enable Call Recording", value=True)
            st.checkbox("📧 Send Daily Reports", value=True)

        with col2:
            st.selectbox("🔊 Voice Model", ["OpenAI TTS", "ElevenLabs"], index=0)
            st.selectbox("🎤 Speech Recognition", ["Deepgram Nova-2"], index=0)
            st.number_input("🔄 Max Call Attempts", min_value=1, max_value=5, value=3)


if __name__ == "__main__":
    main()