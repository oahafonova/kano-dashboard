Voraussetzungen

Python 3.9+ (empfohlen)

Pakete: streamlit, pandas, numpy, plotly, sqlite3 (sqlite3 ist in der Standardbibliothek)

pip install streamlit pandas numpy plotly

DB und Testdaten erzeugen

Pfad in beiden Dateien anpassen, falls nötig: DB_FILE = r"C:\Users\intune\Desktop\DIPLOMARBEIT\DBQualitaet\qualitaet.sqlite"

Testdaten erzeugen:

python generate_testdata.py

Dashboard starten

Im gleichen Ordner:

streamlit run qm_streamlit_dashboard.py
