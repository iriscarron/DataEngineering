"""Barre de navigation horizontale pour DVF Paris Analytics."""

import streamlit as st


def navbar(labels, icons=None, key="nav"):
    """navbar horizontale simple qui renvoie le label selectionne."""
    if key not in st.session_state:
        st.session_state[key] = labels[0]

    # boutons Streamlit natifs pour la navigation
    cols = st.columns(len(labels))
    for col, label in zip(cols, labels):
        with col:
            if st.button(label, key=f"{key}-real-{label}", use_container_width=True):
                st.session_state[key] = label
                st.rerun()

    st.markdown("<hr style='margin-top:-0.5rem;margin-bottom:1rem'>", unsafe_allow_html=True)

    return st.session_state[key]

    return st.session_state[key]
