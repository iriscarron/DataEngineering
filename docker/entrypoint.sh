#!/bin/bash
# Script de demarrage: scrape les donnees puis lance l'app

echo "Demarrage du scraping DVF+..."
python etl/scraper.py

echo "Lancement de l'application Streamlit..."
streamlit run main.py --server.address=0.0.0.0 --server.port=8501
