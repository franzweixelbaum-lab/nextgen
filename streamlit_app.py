import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Leichtathletik Auswertung Pro", layout="wide", page_icon="🏆")

def get_connection():
    return sqlite3.connect('leichtathletik.db', check_same_thread=False)

conn = get_connection()

# --- HILFSFUNKTIONEN ---
def is_valid_result(res):
    """Prüft streng auf sportlich verwertbare Leistungen."""
    invalid_terms = ['aufg.', 'n.a.', 'ab.', 'disq.', 'ogv.', 'o.v.', 'dns', 'dnf', 'nm']
    res_str = str(res).lower().strip()
    if pd.isna(res) or any(term in res_str for term in invalid_terms) or res_str == "":
        return False
    return True

def load_and_clean_data(file):
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
        
        if 'Result' in df.columns:
            df['Result_Num'] = pd.to_numeric(df['Result'].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen: {e}")
        return None

# --- DATEN-AUSWERTUNG ---
def get_filtered_ranking(df):
    """Berechnet Medaillen für U10-U14."""
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    df_filtered['isValid'] = df_filtered['Result'].apply(is_valid_result)
    
    df_filtered['Perf_String'] = df_filtered.apply(
        lambda x: f"{x['Event']} ({x['Result']})" if x['isValid'] else f"{x['Event']} (-)", axis=1
    )

    ranking = df_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg({
        'ClubName': 'first', 'Class': 'first',
        'Perf_String': lambda x: ', '.join(x.astype(str)),
        'isValid': 'sum'
    }).reset_index()

    def categorize(count):
        if count >= 3: return "🥇 Gold"
        elif count == 2: return "🥈 Silber"
        elif count == 1: return "🥉 Bronze"
        return "DNS" # Geändert von 'Teilgenommen'

    ranking['Kategorie'] = ranking['isValid'].apply(categorize)
    cat_order = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2, "DNS": 3}
    ranking['Sort'] = ranking['Kategorie'].map(cat_order)
    return ranking.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

def get_winners_list(df):
    """Ermittelt Sieger für U10-U14."""
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    df_filtered['isValid'] = df_filtered['Result'].apply(is_valid_result)
    valid_df = df_filtered[df_filtered['isValid'] == True].dropna(subset=['Result_Num'])
    
    time_events = ['M', 'H', '100', '200', '800', '1K', '2K', '3K']
    winners = []
    
    for (event, age_class), group in valid_df.groupby(['Event', 'Class']):
        is_time = any(t in event.upper() for t in time_events)
        winner_row = group.loc[group['Result_Num'].idxmin()] if is_time else group.loc[group['Result_Num'].idxmax()]
        winners.append(winner_row)
        
    return pd.DataFrame(winners).sort_values(['Event', 'Class']) if winners else pd.DataFrame()

# --- DASHBOARD UI ---
st.title("🏆 Zentrale Auswertung: Nachwuchs")

with st.sidebar:
    st.header("📤 Daten-Upload")
    uploaded_file = st.file_uploader("results.csv hochladen", type=['csv'])
    if uploaded_file:
        raw_df = load_and_clean_data(uploaded_file)
        if raw_df is not None:
            if st.button("💾 Daten in DB speichern"):
                raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
                st.rerun()

    st.divider()
    if st.button("🗑️ Datenbank leeren"):
        conn.execute("DROP TABLE IF EXISTS ergebnisse")
        st.rerun()

try:
    df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)
    
    if not df_db.empty:
        # GLOBALER FILTER
        st.subheader("🔍 Globale Suche & Filter")
        search_query = st.text_input("Suchen nach Name, Verein oder Altersklasse (wirkt auf alle Tabs):", "")

        # Tabs
        tab_rank, tab_win, tab_plot, tab_raw = st.tabs(["🏅 Medaillen-Ranking", "🥇 Siegerliste", "📊 Analyse", "📋 Rohdaten"])

        with tab_rank:
            rank_df = get_filtered_ranking(df_db)
            
            # Statistik-Header
            g, s, b = len(rank_df[rank_df['Kategorie'] == "🥇 Gold"]), len(rank_df[rank_df['Kategorie'] == "🥈 Silber"]), len(rank_df[rank_df['Kategorie'] == "🥉 Bronze"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Medaillen GOLD", g)
            c2.metric("Medaillen SILBER", s)
            c3.metric("Medaillen BRONZE", b)
            
            # Filter anwenden
            if search_query:
                rank_df = rank_df[rank_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

            st.dataframe(rank_df[['Kategorie', 'FirstName', 'LastName', 'Class', 'ClubName', 'Perf_String', 'isValid']], 
                         column_config={"isValid": "Gültig", "Perf_String": "Leistungen"}, use_container_width=True, hide_index=True)
            
            csv_rank = rank_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Medaillen-Liste herunterladen", csv_rank, "medaillen_ranking.csv", "text/csv")

        with tab_win:
            winners_df = get_winners_list(df_db)
            if not winners_df.empty:
                if search_query:
                    winners_df = winners_df[winners_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                
                st.dataframe(winners_df[['Event', 'Class', 'FirstName', 'LastName', 'ClubName', 'Result']], use_container_width=True, hide_index=True)
                csv_win = winners_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Siegerliste herunterladen", csv_win, "siegerliste.csv", "text/csv")
            else:
                st.warning("Keine Siegerdaten verfügbar.")

        with tab_plot:
            sel_event = st.selectbox("Bewerb für Grafik wählen:", sorted(df_db['Event'].unique()))
            plot_df = df_db[df_db['Event'] == sel_event].dropna(subset=['Result_Num'])
            if search_query:
                plot_df = plot_df[plot_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            
            if not plot_df.empty:
                fig = px.box(plot_df, x="Class", y="Result_Num", color="Class", points="all", hover_data=["FirstName", "LastName"])
                st.plotly_chart(fig, use_container_width=True)

        with tab_raw:
            raw_display = df_db
            if search_query:
                raw_display = raw_display[raw_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            st.dataframe(raw_display, use_container_width=True)

    else:
        st.info("Bitte lade eine CSV-Datei hoch.")
except Exception as e:
    st.info("Bereit für den Daten-Upload.")