#!/bin/bash
# script de demarrage: verifie si les donnees existent, sinon scrape, puis lance l'app

echo "verification des donnees existantes..."
python -c "
from sqlalchemy import create_engine, text
import os
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM transactions'))
        count = result.scalar()
        if count > 0:
            print(f'{count} transactions deja en base, scraping ignore')
            exit(0)
        else:
            print('pas de donnees, lancement du scraping')
            exit(1)
except Exception as e:
    print(f'erreur verification: {e}, lancement du scraping par securite')
    exit(1)
"

if [ $? -eq 1 ]; then
    echo "demarrage du scraping DVF+..."
    python etl/scraper.py
fi

echo "lancement de l'application streamlit..."
streamlit run main.py --server.address=0.0.0.0 --server.port=8501
