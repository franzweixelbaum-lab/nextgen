import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import io

# --- KONFIGURATION ---
st.set_page_config(page_title="Leichtathletik Auswertung Pro", layout="wide")

# Datenbankverbindung (lokale Datei)
def get_connection():
    return sqlite3.connect('leichtathletik_data.db', check_same_thread=False)

conn = get_connection()

# --- FUNKTIONEN ---
def load_data(file):
    """Liest die Datei mit robustem Encoding und Fehlerhandling ein."""
    try:
        # Den Lesekopf sicherheitshalber an den Anfang setzen
        file.seek(0)
        # Erst UTF-8 versuchen, dann Latin1 (für Excel-CSVs)
        try:
            df = pd.read_csv(file, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding='latin1')
        
        # Falls die Datei nur eine Spalte hat -> falscher Trenner (Komma statt Semikolon)
        if df.shape[1] <= 1:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='latin1')
            
        return df
    except Exception as e:
        st.error(f"Kritischer Fehler beim Einlesen: {e}")
        return None

def preprocess_df(df):
    """Bereinigt numerische Spalten für Datenbank und Grafiken."""
    if 'Result' in df.columns:
        # Ersetzt Komma durch Punkt und macht es zu einer Zahl
        df['Result_Num'] = pd.to_numeric(df['Result'].astype(str).str.replace(',', '.'), errors='coerce')
    if 'Wind' in df.columns:
        df['Wind_Num'] = pd.to_numeric(df['Wind'].astype(str).str.replace('+', '').str.replace(',', '.'), errors='coerce')
    return df

# --- UI / DASHBOARD ---
st.title("🏆 Leichtathletik Analyse-Dashboard")

# Sidebar für Uploads
with st.sidebar:
    st.header("📤 Daten-Management")
    uploaded_file = st.file_uploader("results.csv hochladen", type=['csv'])
    
    if uploaded_file:
        df_raw = load_data(uploaded_file)
        if df_raw is not None:
            df_clean = preprocess_df(df_raw)
            st.success("Datei erfolgreich analysiert!")
            
            if st.button("💾 In Datenbank speichern/ersetzen"):
                df_clean.to_sql('ergebnisse', conn, if_exists='replace', index=False)
                st.balloons()
                st.sidebar.success("Datenbank aktualisiert!")

# --- DATEN-AUSWERTUNG ---
try:
    # Daten aus DB laden
    df = pd.read_sql('SELECT * FROM ergebnisse', conn)

    if not df.empty:
        # Tabs für bessere Übersicht
        tab1, tab2, tab3 = st.tabs(["📊 Analyse", "📋 Datentabelle", "⚙️ Filter"])

        with tab1:
            st.subheader("Leistungsanalyse")
            col_a, col_b = st.columns([1, 3])
            
            with col_a:
                event = st.selectbox("Disziplin wählen", options=sorted(df['Event'].unique()))
                plot_type = st.radio("Grafiktyp", ["Boxplot (Verteilung)", "Scatter (Einzelwerte)"])
            
            with col_b:
                filtered_df = df[df['Event'] == event].dropna(subset=['Result_Num'])
                
                if plot_type == "Boxplot (Verteilung)":
                    fig = px.box(filtered_df, x="Class", y="Result_Num", color="Class", 
                                 points="all", hover_data=["FirstName", "LastName"])
                else:
                    fig = px.scatter(filtered_df, x="ClassRank", y="Result_Num", color="Gender",
                                     size="Result_Num", hover_name="LastName", title=f"Ergebnisse: {event}")
                
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Gesamte Datenbank")
            st.dataframe(df, use_container_width=True)

        with tab3:
            st.subheader("Datenbank-Aktionen")
            if st.button("⚠️ Datenbank leeren"):
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS ergebnisse")
                st.warning("Alle Daten gelöscht. Bitte Seite neu laden.")
    else:
        st.info("Noch keine Daten in der Datenbank. Bitte lade links eine CSV-Datei hoch.")

except Exception as e:
    st.info("Willkommen! Bitte lade eine CSV-Datei hoch, um zu starten.")