"""Barre de navigation horizontale pour DVF Paris Analytics."""

import streamlit as st


# icônes SVG inline
SVG_ICONS = {
    "home": """<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0L0 6v10h6v-6h4v6h6V6L8 0z"/></svg>""",
    "building": """<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M2 2h5v12H2V2zm7 0h5v12H9V2zM3 4h3v2H3V4zm7 0h3v2h-3V4zM3 7h3v2H3V7zm7 0h3v2h-3V7zm-7 3h3v2H3v-2zm7 0h3v2h-3v-2z"/></svg>""",
    "euro": """<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.6 0 0 3.6 0 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm1 11.5H6.5v-1H9v-2H6.5v-1H9v-2H6.5v-1H9V3H7v1.5H5.5v1H7v2H5.5v1H7v2H5.5v1H7V13h2v-1.5z"/></svg>""",
    "map": """<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M0 2l5-2 6 2 5-2v14l-5 2-6-2-5 2V2zm5.5 11.5l5 1.7V4.3l-5-1.7v10.9z"/></svg>""",
    "search": """<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/></svg>""",
    "star": """<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0l2.5 5.1 5.5.8-4 3.9.9 5.5L8 12.7l-4.9 2.6.9-5.5-4-3.9 5.5-.8L8 0z"/></svg>""",
}


def navbar(labels, icons=None, key="nav"):
    """navbar horizontale simple qui renvoie le label selectionne."""
    if key not in st.session_state:
        st.session_state[key] = labels[0]

    if icons is None:
        icons = {}

    # ajouter un style pour les icônes SVG
    st.markdown("""
    <style>
    .nav-icon {
        display: inline-block;
        vertical-align: middle;
        margin-right: 0.3rem;
    }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(len(labels))
    for col, label in zip(cols, labels):
        activated = label == st.session_state[key]

        # créer le label avec icône SVG si disponible
        if label in icons and icons[label] in SVG_ICONS:
            svg = SVG_ICONS[icons[label]]
            # afficher l'icône au-dessus du bouton
            col.markdown(f'<div class="nav-icon" style="text-align: center;">{svg}</div>', unsafe_allow_html=True)

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
