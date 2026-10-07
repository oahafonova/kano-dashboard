# kano_dashboard.py
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Kano-Dashboard", layout="centered")

# Pfad zur DB (bei Bedarf anpassen)
# DB_PATH = r"C:\Users\intune\Desktop\DIPLOMARBEIT\DBQualitaet\kano.db"
DB_PATH = "kano.db"

PRODUCT_NAME = "Industrieklebstoff"

FEATURES = [
    (1, "Sehr schnelle Aushärtung"),
    (2, "Besonders saubere Anwendung"),
    (3, "Umweltfreundliche Verpackung"),
    (4, "Hohe Klebkraft"),
    (5, "Zuverlässige Haltbarkeit"),
    (6, "Gutes Preis-Leistungs-Verhältnis"),
    (7, "Sichere Anwendung"),
    (8, "Keine gesundheitsschädlichen Stoffe"),
    (9, "Klare Produktbeschreibung"),
    (10, "Farbe der Verpackung"),
    (11, "Design des Etiketts"),
    (12, "Herkunftsland des Produkts"),
]
FEATURE_DICT = {nr: name for nr, name in FEATURES}

# KANO-Matrix (Mapping functional, dysfunctional -> Kategorie)
KANO_MATRIX = {
    ("Gefällt mir", "Gefällt mir nicht"): "A",
    ("Gefällt mir", "Akzeptiere ich"): "A",
    ("Gefällt mir", "Egal"): "A",
    ("Gefällt mir", "Erwarte ich"): "O",
    ("Gefällt mir", "Gefällt mir"): "Q",

    ("Erwarte ich", "Gefällt mir nicht"): "O",
    ("Erwarte ich", "Akzeptiere ich"): "O",
    ("Erwarte ich", "Egal"): "O",
    ("Erwarte ich", "Erwarte ich"): "M",
    ("Erwarte ich", "Gefällt mir"): "Q",

    ("Egal", "Gefällt mir nicht"): "O",
    ("Egal", "Akzeptiere ich"): "I",
    ("Egal", "Egal"): "I",
    ("Egal", "Erwarte ich"): "M",
    ("Egal", "Gefällt mir"): "Q",

    ("Akzeptiere ich", "Gefällt mir nicht"): "O",
    ("Akzeptiere ich", "Akzeptiere ich"): "I",
    ("Akzeptiere ich", "Egal"): "I",
    ("Akzeptiere ich", "Erwarte ich"): "M",
    ("Akzeptiere ich", "Gefällt mir"): "Q",

    ("Gefällt mir nicht", "Gefällt mir nicht"): "R",
    ("Gefällt mir nicht", "Akzeptiere ich"): "R",
    ("Gefällt mir nicht", "Egal"): "R",
    ("Gefällt mir nicht", "Erwarte ich"): "R",
    ("Gefällt mir nicht", "Gefällt mir"): "Q",
}

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS kano_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,
    feature TEXT NOT NULL,
    functional_answer TEXT NOT NULL,
    dysfunctional_answer TEXT NOT NULL,
    kano_category TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

st.title("Kano-Fragebogen - Industrieklebstoff")

# Formular für alle Fragen
with st.form("kano_form"):
    st.subheader("Bitte beantworten Sie alle Fragen:")
    answers = []
    for nr, name in FEATURES:
        st.markdown(f"**{nr}. {name}**")
        functional = st.selectbox(
            f"Wenn das Merkmal vorhanden ist ({nr}. {name}):",
            ["Gefällt mir", "Erwarte ich", "Egal", "Akzeptiere ich", "Gefällt mir nicht"],
            key=f"functional_{nr}"
        )
        dysfunctional = st.selectbox(
            f"Wenn das Merkmal NICHT vorhanden ist ({nr}. {name}):",
            ["Gefällt mir", "Erwarte ich", "Egal", "Akzeptiere ich", "Gefällt mir nicht"],
            key=f"dysfunctional_{nr}"
        )
        answers.append((nr, name, functional, dysfunctional))

    submitted = st.form_submit_button("Alle Antworten speichern")

    if submitted:
        inserted = 0
        for nr, name, functional, dysfunctional in answers:
            kano = KANO_MATRIX.get((functional, dysfunctional), "Q")  
            cur.execute(
                "INSERT INTO kano_answers (product, feature, functional_answer, dysfunctional_answer, kano_category) VALUES (?,?,?,?,?)",
                (PRODUCT_NAME, name, functional, dysfunctional, kano)
            )
            inserted += 1
        conn.commit()
        st.success(f"{inserted} Antworten gespeichert!")

st.divider()
st.header("Auswertung")

df = pd.read_sql("SELECT * FROM kano_answers", conn)

if df.empty:
    st.info("Noch keine Daten vorhanden.")
    conn.close()
    st.stop()

# Filter nach Produkt (falls mehrere Produkte in DB)
products = df["product"].unique().tolist()
sel_product = st.selectbox("Produkt auswählen", products, index=products.index(PRODUCT_NAME) if PRODUCT_NAME in products else 0)
df = df[df["product"] == sel_product]

# Pivot: Verteilung pro Merkmal
pivot = pd.pivot_table(
    df,
    index="feature",
    columns="kano_category",
    aggfunc="size",
    fill_value=0
)

# Sicherstellen, dass alle relevanten Kategorien vorhanden sind
for col in ["A", "O", "M", "I", "R", "Q"]:
    if col not in pivot.columns:
        pivot[col] = 0

# Dominante Kategorie (A,O,M,I) — falls alle 0, setze 'I' als Default
pivot["dominant_kano"] = pivot[["A", "O", "M", "I"]].replace(0, -1).idxmax(axis=1)
pivot["dominant_kano"] = pivot["dominant_kano"].replace({-1: "I"})

# CS / DS Berechnung mit Division-by-zero Schutz
den = pivot[["A", "O", "M", "I"]].sum(axis=1).replace(0, pd.NA)
pivot["CS"] = ((pivot["A"] + pivot["O"]) / den).fillna(0)
pivot["DS"] = (-(pivot["M"] + pivot["O"]) / den).fillna(0)

pivot = pivot.reset_index().rename(columns={"feature": "Merkmal"})

st.subheader("Kano-Verteilung (Tabelle)")
st.dataframe(pivot)

# CSV-Export der Auswertung
csv = pivot.to_csv(index=False, sep=';')
st.download_button("Auswertung als CSV herunterladen", csv, file_name="kano_auswertung.csv", mime="text/csv")

# Balkendiagramm (Gesamtverteilung)
st.subheader("Kano-Verteilung (Balkendiagramm)")
bar = pivot[["A", "O", "M", "I"]].sum()
fig1, ax1 = plt.subplots(figsize=(5, 3))
bar.plot(
    kind="bar",
    ax=ax1,
    color=["#2ecc71", "#3498db", "#e74c3c", "#95a5a6"]
)
ax1.set_ylabel("Anzahl Antworten")
ax1.set_xlabel("Kano-Kategorie")
ax1.set_xticklabels(["A (Begeisterung)", "O (Leistung)", "M (Basis)", "I (Indifferent)"], rotation=0,
    fontsize=8)
st.pyplot(fig1, use_container_width=True)

# Kano-Diagramm (CS vs DS)
st.subheader("Kano-Diagramm")
COLOR_MAP = {"A": "#2ecc71", "O": "#3498db", "M": "#e74c3c", "I": "#95a5a6"}

fig2, ax2 = plt.subplots(figsize=(5, 3))
for idx, row in pivot.iterrows():
    cat = row["dominant_kano"] if row["dominant_kano"] in COLOR_MAP else "I"
    color = COLOR_MAP.get(cat, "#7f8c8d")

    ax2.scatter(row["DS"], row["CS"], s=60, color=color, edgecolors="black", zorder=3)

    feature_nr = None
    for nr, name in FEATURES:
        if name == row["Merkmal"]:
            feature_nr = nr
            break

    if feature_nr is not None:
        x_offset = -0.03 if row["DS"] < -0.5 else 0.03
        y_offset = -0.03 if row["CS"] < 0.5 else 0.03

        ax2.text(
            row["DS"] + x_offset,
            row["CS"] + y_offset,
            str(feature_nr),
            fontsize=7,
            fontweight="bold",
            ha="center",
            va="center",
            zorder=4
        )

ax2.axvline(-0.5, color="black")
ax2.axhline(0.5, color="black")

ax2.set_xlim(-1.05, 0.05)
ax2.set_ylim(-0.05, 1.05)

ax2.set_xlabel("Unzufriedenheit (DS)")
ax2.set_ylabel("Zufriedenheit (CS)")
#ax2.set_title("Kano-Diagramm")
ax2.grid(True, linestyle="--", alpha=0.4)
st.pyplot(fig2, use_container_width=True)

st.subheader("Legende der Merkmale")
for nr, name in FEATURES:
    st.write(f"**{nr}** - {name}")

conn.close()
