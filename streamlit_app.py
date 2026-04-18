import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Verbindung zur Datenbank
conn = sqlite3.connect('leichtathletik.db')

st.set_page_config(page_title="Athletik Auswertung", layout="wide")
st.title("🏆 Online Auswertung mit Plotly")

# --- SIDEBAR: Upload ---
with st.sidebar:
    st.header("Datenimport")
    uploaded_file = st.file_uploader("results.csv hochladen", type=['csv'])

if uploaded_file is not None:
    try:
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
    df = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
    
    # Datenbereinigung für Plotly (Komma -> Punkt für numerische Werte)
    df['Result_Clean'] = pd.to_numeric(df['Result'].astype(str).str.replace(',', '.'), errors='coerce')
    
    if st.sidebar.button("In Datenbank speichern"):
        df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
        st.sidebar.success("Daten gespeichert!")

# --- HAUPTBEREICH: Visualisierung ---
try:
    # Daten aus DB laden
    data = pd.read_sql('SELECT * FROM ergebnisse', conn)

    if not data.empty:
        st.subheader("Interaktive Datenanalyse")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Filter für die Disziplin (Event)
            event_list = data['Event'].unique()
            selected_event = st.selectbox("Disziplin wählen:", event_list)
            
            filtered_data = data[data['Event'] == selected_event].dropna(subset=['Result_Clean'])

        with col2:
            # Plotly Chart: Verteilung der Ergebnisse pro Klasse
            fig = px.box(
                filtered_data, 
                x="Class", 
                y="Result_Clean", 
                points="all",
                color="Class",
                title=f"Ergebnisverteilung für {selected_event}",
                labels={"Result_Clean": "Leistung (Sek/m)", "Class": "Altersklasse"},
                hover_data=["FirstName", "LastName", "ClubName"]
            )
            
            # Layout anpassen
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Zusätzliche Grafik: Zusammenhang Wind vs. Ergebnis (falls relevant)
        if 'Wind' in data.columns and not data['Wind'].isnull().all():
            st.subheader("Einfluss des Winds")
            data['Wind_Clean'] = pd.to_numeric(data['Wind'].astype(str).str.replace('+', '').str.replace(',', '.'), errors='coerce')
            
            fig_wind = px.scatter(
                data.dropna(subset=['Wind_Clean', 'Result_Clean']),
                x="Wind_Clean",
                y="Result_Clean",
                color="Event",
                hover_name="LastName",
                title="Ergebnis im Verhältnis zur Windstärke"
            )
            st.plotly_chart(fig_wind, use_container_width=True)

except Exception as e:
    st.info("Lade eine CSV-Datei hoch und speichere sie, um die Grafiken anzuzeigen.")