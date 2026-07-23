"""Navigation entry point for the public Streamlit application."""

import streamlit as st


pages = [
    st.Page("pages/0_Home.py", title="Start here", icon="🧭", default=True),
    st.Page("pages/1_Global_AMR.py", title="Global AMR", icon="🌍"),
    st.Page("pages/2_Conflict_and_AMR.py", title="Conflict and AMR", icon="⚖️"),
    st.Page("pages/3_One_Health.py", title="One Health", icon="🌿"),
    st.Page("pages/4_RD_Alignment.py", title="R&D Alignment", icon="🔬"),
    st.Page("pages/5_Country_Profile.py", title="Country Profile", icon="📍"),
    st.Page("pages/6_Methods_and_Data_Quality.py", title="Methods and Data Quality", icon="📘"),
]

st.navigation(pages, position="sidebar").run()
