"""Barre de navigation horizontale pour DVF Paris Analytics."""

import streamlit as st


def navbar(labels, icons=None, key="nav"):
    """navbar horizontale simple qui renvoie le label selectionne."""
    if key not in st.session_state:
        st.session_state[key] = labels[0]

    if icons is None:
        icons = {}

    # injecter Font Awesome et créer des boutons HTML personnalisés
    button_clicks = {}

    # construire le HTML avec Font Awesome
    html_parts = ["""
        <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>
        <style>
            .custom-nav-container {
                display: flex;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            .custom-nav-btn {
                flex: 1;
                padding: 0.5rem 1rem;
                border: 1px solid #ddd;
                border-radius: 0.25rem;
                background: transparent;
                color: #3d2817;
                font-size: 0.95rem;
                text-align: center;
                cursor: default;
            }
            .custom-nav-btn.active {
                background: #e6dfd4;
                border-bottom: 3px solid #0f766e;
                font-weight: 600;
            }
            .custom-nav-btn i {
                margin-right: 0.4rem;
            }
            .custom-nav-btn.active i {
                color: #0f766e;
            }
        </style>
        <div class='custom-nav-container'>
    """]

    for label in labels:
        active_class = "active" if label == st.session_state[key] else ""
        icon_class = icons.get(label, "")
        icon_html = f"<i class='{icon_class}'></i>" if icon_class else ""

        html_parts.append(f"""
            <div class='custom-nav-btn {active_class}'>
                {icon_html}{label}
            </div>
        """)

    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)

    # boutons Streamlit invisibles pour la fonctionnalité
    cols = st.columns(len(labels))
    for col, label in zip(cols, labels):
        with col:
            if st.button(label, key=f"{key}-real-{label}", use_container_width=True, label_visibility="collapsed"):
                st.session_state[key] = label
                st.rerun()

    st.markdown("<hr style='margin-top:-3rem;margin-bottom:1rem'>", unsafe_allow_html=True)

    return st.session_state[key]
