import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Leichtathletik Auswertung", layout="wide", page_icon="🏆")

def get_connection():
    return sqlite3.connect('leichtathletik.db', check_same_thread=False)

conn = get_connection()

# --- DATENVERARBEITUNG ---
def load_and_clean_data(file):
    """Liest CSV stabil ein."""
    try:
        file.seek(0)
        try:
            df = pd.read_csv(file, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding='latin1')
        
        if df.shape[1] <= 1:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='latin1')
        
        # Vor-Bereinigung: Result_Num für Grafiken
        if 'Result' in df.columns:
            df['Result_Num'] = pd.to_numeric(df['Result'].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen: {e}")
        return None

def get_filtered_ranking(df):
    """Berechnet das Ranking für U10-U14 mit Leistungsprüfung."""
    
    # 1. Filter auf Klassen U10, U12, U14 (enthält WU10, MU10 etc.)
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()

    # 2. Nur gültige Leistungen zählen (nicht leer, nicht "aufg.", nicht "n.a.", nicht "ab.")
    invalid_terms = ['aufg.', 'n.a.', 'ab.', 'disq.', 'ogv.']
    
    def is_valid(res):
        res_str = str(res).lower().strip()
        if pd.isna(res) or any(term in res_str for term in invalid_terms) or res_str == "":
            return False
        return True

    # Markiere gültige Leistungen
    df_filtered['isValid'] = df_filtered['Result'].apply(is_valid)
    
    # Hilfsspalte für Anzeige
    df_filtered['Perf_String'] = df_filtered.apply(
        lambda x: f"{x['Event']} ({x['Result']})" if x['isValid'] else f"{x['Event']} (-)", 
        axis=1
    )

    # 3. Gruppierung
    ranking = df_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg({
        'ClubName': 'first',
        'Class': 'first',
        'Perf_String': lambda x: ', '.join(x.astype(str)),
        'isValid': 'sum'  # Zählt nur die True-Werte (gültige Leistungen)
    }).reset_index()

    # 4. Kategorisierung nach gültigen Leistungen
    def categorize(count):
        if count >= 3: return "🥇 Gold"
        elif count == 2: return "🥈 Silber"
        elif count == 1: return "🥉 Bronze"
        return "Teilgenommen"

    ranking['Kategorie'] = ranking['isValid'].apply(categorize)
    
    # Sortierung
    cat_order = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2, "Teilgenommen": 3}
    ranking['Sort'] = ranking['Kategorie'].map(cat_order)
    ranking = ranking.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

    return ranking

# --- UI ---
st.title("🏆 Nachwuchs-Auswertung (U10-U14)")

with st.sidebar:
    st.header("📤 Daten-Upload")
    uploaded_file = st.file_uploader("results.csv hochladen", type=['csv'])
    if uploaded_file:
        raw_df = load_and_clean_data(uploaded_file)
        if raw_df is not None:
            if st.button("💾 Datenbank aktualisieren"):
                raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
                st.sidebar.success("Daten gespeichert!")
    
    if st.button("🗑️ DB löschen"):
        conn.execute("DROP TABLE IF EXISTS ergebnisse")
        st.rerun()

try:
    df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)
    if not df_db.empty:
        tab1, tab2 = st.tabs(["🏆 Medaillen-Ranking", "📊 Statistik & Rohdaten"])

        with tab1:
            rank_df = get_filtered_ranking(df_db)
            
            # --- HEADER SUMMEN ---
            gold_count = len(rank_df[rank_df['Kategorie'] == "🥇 Gold"])
            silber_count = len(rank_df[rank_df['Kategorie'] == "🥈 Silber"])
            bronze_count = len(rank_df[rank_df['Kategorie'] == "🥉 Bronze"])

            c1, c2, c3 = st.columns(3)
            c1.metric("Anzahl GOLD", f"{gold_count}x")
            c2.metric("Anzahl SILBER", f"{silber_count}x")
            c3.metric("Anzahl BRONZE", f"{bronze_count}x")
            
            st.divider()

            # Suche & Tabelle
            search = st.text_input("Suche nach Name oder Verein:")
            display_df = rank_df
            if search:
                display_df = rank_df[
                    rank_df['LastName'].str.contains(search, case=False) | 
                    rank_df['FirstName'].str.contains(search, case=False) |
                    rank_df['ClubName'].str.contains(search, case=False)
                ]

            st.dataframe(
                display_df[['Kategorie', 'FirstName', 'LastName', 'Class', 'ClubName', 'Perf_String', 'isValid']],
                column_config={
                    "Kategorie": "Status",
                    "Perf_String": "Gültige Leistungen",
                    "isValid": "Anzahl",
                    "Class": "Klasse",
                    "ClubName": "Verein"
                },
                use_container_width=True,
                hide_index=True
            )

        with tab2:
            st.subheader("Rohdaten Übersicht")
            st.dataframe(df_db, use_container_width=True)
    else:
        st.info("Bitte lade eine Datei hoch.")
except Exception as e:
    st.info("Warte auf Daten-Upload...")