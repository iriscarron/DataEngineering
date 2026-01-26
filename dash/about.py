"""À propos de DVF Paris - Page d'information du projet."""
import streamlit as st


def render_about():
    """affiche la page a propos."""
    st.markdown("## à propos")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style='text-align: center; padding: 2rem;'>
            <div style='font-size: 1.2rem; margin-bottom: 1rem;'>
                projet réalisé par
            </div>
            <div style='font-size: 1.5rem; font-weight: 600;'>
                iris carron & cléo detrez
            </div>
            <div style='font-size: 0.9rem; margin-top: 1rem; color: #666;'>
                data engineering - 2026
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
