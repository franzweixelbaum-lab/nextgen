import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Leichtathletik Auswertung", layout="wide", page_icon="🏆")

# Datenbankverbindung
def get_connection():
    return sqlite3.connect('leichtathletik.db', check_same_thread=False)

conn = get_connection()

# --- DATENVERARBEITUNG ---
def load_and_clean_data(file):
    """Liest CSV stabil ein und bereinigt Formate."""
    try:
        file.seek(0)
        try:
            df = pd.read_csv(file, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding='latin1')
        
        # Falls Trenner falsch (Komma statt Semikolon)
        if df.shape[1] <= 1:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='latin1')

        # Numerische Konvertierung für Berechnungen & Plotly
        if 'Result' in df.columns:
            df['Result_Num'] = pd.to_numeric(df['Result'].astype(str).str.replace(',', '.'), errors='coerce')
        if 'Wind' in df.columns:
            df['Wind_Num'] = pd.to_numeric(df['Wind'].astype(str).str.replace('+', '').str.replace(',', '.'), errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen: {e}")
        return None

def get_athlete_ranking(df):
    """Erstellt das Ranking basierend auf der Anzahl der Resultate."""
    # Gruppierung nach Athlet (Eindeutigkeit durch Vorname, Nachname, Jahrgang)
    ranking = df.groupby(['FirstName', 'LastName', 'Yob']).agg({
        'Event': lambda x: ', '.join(x.astype(str)),
        'Result': 'count' # Zählt Zeilen mit Werten
    }).reset_index()

    def categorize(count):
        if count >= 3: return "🥇 Gold"
        elif count == 2: return "🥈 Silber"
        elif count == 1: return "🥉 Bronze"
        return "Teilgenommen"

    ranking['Kategorie'] = ranking['Result'].apply(categorize)
    
    # Sortier-Logik
    cat_order = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2, "Teilgenommen": 3}
    ranking['Sort'] = ranking['Kategorie'].map(cat_order)
    return ranking.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

# --- DASHBOARD UI ---
st.title("🏆 Online Auswertungsseite")

# Sidebar: Upload und DB-Steuerung
with st.sidebar:
    st.header("📤 Daten-Upload")
    uploaded_file = st.file_uploader("results.csv hochladen", type=['csv'])
    
    if uploaded_file:
        raw_df = load_and_clean_data(uploaded_file)
        if raw_df is not None:
            st.success("Datei geladen!")
            if st.button("💾 In Datenbank speichern"):
                raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
                st.sidebar.success("Datenbank aktualisiert!")
                st.balloons()

    st.divider()
    if st.button("🗑️ Datenbank leeren"):
        conn.execute("DROP TABLE IF EXISTS ergebnisse")
        st.warning("Daten gelöscht.")

# --- HAUPTBEREICH ---
try:
    # Daten aus der Datenbank ziehen
    df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)

    if not df_db.empty:
        tab1, tab2, tab3 = st.tabs(["📊 Analyse", "🏆 Athleten-Ranking", "📋 Rohdaten"])

        with tab1:
            st.subheader("Leistungs-Visualisierung")
            event_list = sorted(df_db['Event'].unique())
            selected_event = st.selectbox("Bewerb auswählen:", event_list)
            
            plot_df = df_db[df_db['Event'] == selected_event].dropna(subset=['Result_Num'])
            
            fig = px.box(
                plot_df, x="Class", y="Result_Num", color="Class",
                points="all", hover_data=["FirstName", "LastName", "ClubName"],
                title=f"Verteilung der Ergebnisse: {selected_event}",
                labels={"Result_Num": "Leistung", "Class": "Klasse"}
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Ranking nach Anzahl der Leistungen")
            st.info("Kategorien: Gold (3+), Silber (2), Bronze (1)")
            
            rank_df = get_athlete_ranking(df_db)
            
            # Suche
            search = st.text_input("Athlet suchen (Name):")
            if search:
                rank_df = rank_df[rank_df['LastName'].str.contains(search, case=False) | rank_df['FirstName'].str.contains(search, case=False)]

            st.dataframe(
                rank_df[['Kategorie', 'FirstName', 'LastName', 'Yob', 'Event', 'Result']],
                column_config={
                    "Event": "Bewerbe",
                    "Result": "Anzahl",
                    "Kategorie": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Export
            csv_data = rank_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Liste als CSV herunterladen", csv_data, "ranking_liste.csv", "text/csv")

        with tab3:
            st.subheader("Alle Einträge")
            st.dataframe(df_db, use_container_width=True)

    else:
        st.info("Die Datenbank ist leer. Bitte lade eine CSV-Datei über die Seitenleiste hoch.")

except Exception:
    st.info("Willkommen! Bitte lade deine erste Ergebnisliste hoch.")