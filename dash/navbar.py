"""Barre de navigation horizontale pour DVF Paris Analytics."""

import streamlit as st


def navbar(labels, key="nav"):
    """navbar horizontale simple qui renvoie le label selectionne."""
    if key not in st.session_state:
        st.session_state[key] = labels[0]

    cols = st.columns(len(labels))
    for col, label in zip(cols, labels):
        activated = label == st.session_state[key]
        if col.button(label, use_container_width=True, key=f"{key}-{label}"):
            st.session_state[key] = label
            st.rerun()
        # highlight active tab
        if activated:
            col.markdown(
                (
                    "<div style='height:3px;background:#0f766e;"
                    "border-radius:4px;margin-top:-6px'></div>"
                ),
                unsafe_allow_html=True,
            )
    st.markdown(
        "<hr style='margin-top:0.2rem;margin-bottom:1rem'>",
        unsafe_allow_html=True,
    )
    return st.session_state[key]
