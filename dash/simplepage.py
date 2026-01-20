import streamlit as st


def render_simple(df):
    st.header("Page simple")
    st.write("Utilisez cette page comme zone de test pour vos composants.")
    st.write(f"Lignes visibles: {len(df):,}")
    if not df.empty:
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
