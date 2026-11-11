
import streamlit as st

from database.db import init_db, get_session
from database.operations import (
    count_logs,
    count_logs_by_level,
    get_logs
)


st.set_page_config(
    page_title="AI Log Analysis System",
    page_icon="🔐",
    layout="wide"
)

# Initialize database
init_db()

st.title("🔐 AI Log Analysis System")

st.caption("Intelligent Log Monitoring and Analysis")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "Dashboard",
        "Log Explorer",
        "Security Analytics",
        "AI Analysis",
        "Reports"
    ]
)


if page == "Dashboard":

    st.header("System Overview")

    with get_session() as session:

        total = count_logs(session)

        counts = count_logs_by_level(session)

        errors = counts.get("ERROR", 0)

        warnings = counts.get("WARNING", 0)

        critical = counts.get("CRITICAL", 0)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Logs", total)

        col2.metric("Errors", errors)

        col3.metric("Warnings", warnings)

        col4.metric("Critical", critical)

        st.subheader("Recent Logs")

        recent_logs = get_logs(session, limit=10)

        if recent_logs:

            for log in recent_logs:

                st.write(
                    f"**{log.level}** | "
                    f"{log.source} | "
                    f"{log.message}"
                )

        else:

            st.info("No logs found. Upload logs to begin.")


elif page == "Log Explorer":

    st.header("Log Explorer")

    with get_session() as session:

        selected_level = st.selectbox(
            "Filter by severity",
            ["ALL", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )

        logs = get_logs(
            session,
            level=selected_level,
            limit=500
        )

        rows = [
            {
                "ID": log.id,
                "Timestamp": log.timestamp,
                "Level": log.level,
                "Source": log.source,
                "Message": log.message
            }
            for log in logs
        ]

        st.dataframe(
            rows,
            use_container_width=True
        )


elif page == "Security Analytics":

    st.header("Security Analytics")

    st.info("Security event detection will be implemented next.")


elif page == "AI Analysis":

    st.header("AI Analysis")

    st.info("Intelligent analysis will be implemented in a later milestone.")


elif page == "Reports":

    st.header("Reports")

    st.info("PDF report generation will be implemented in a later milestone.")
