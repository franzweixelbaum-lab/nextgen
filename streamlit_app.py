import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import numpy as np

# --- KONFIGURATION ---
st.set_page_config(page_title="Leichtathletik Auswertung Pro", layout="wide", page_icon="🏆")

def get_connection():
    return sqlite3.connect('leichtathletik.db', check_same_thread=False)

conn = get_connection()

# --- CUP-PUNKTESYSTEM (Vereinseigener fairer Schlüssel U10-U14) ---
# Struktur: a (Multiplikator), b (Basiswert/Limit), c (Exponent)
CUP_PARAMS = {
    # --- MÄNNLICH ---
    'M_60M':  {'Typ': 'Lauf',   'a': 45.0,   'b': 12.5,  'c': 1.81},
    'M_10H':  {'Typ': 'Lauf',   'a': 15.0,   'b': 30.0,  'c': 1.8},   # Hindernis kurz
    'M_20H':  {'Typ': 'Lauf',   'a': 5.0,    'b': 55.0,  'c': 1.8},   # Hindernis lang
    'M_1K0':  {'Typ': 'Lauf',   'a': 0.05,   'b': 480.0, 'c': 1.85},  # 1000m (in Sekunden)
    'M_1KSC': {'Typ': 'Lauf',   'a': 0.05,   'b': 480.0, 'c': 1.85},  # Cross/Hindernis 1km
    'M_800':  {'Typ': 'Lauf',   'a': 0.08,   'b': 360.0, 'c': 1.85},
    'M_WEI':  {'Typ': 'Sprung', 'a': 0.15,   'b': 150.0, 'c': 1.4},   # Weit (in cm)
    'M_VOR':  {'Typ': 'Wurf',   'a': 12.0,   'b': 5.0,   'c': 1.1},   # Vortex (in m)
    
    # --- WEIBLICH ---
    'W_60M':  {'Typ': 'Lauf',   'a': 48.0,   'b': 13.0,  'c': 1.81},
    'W_10H':  {'Typ': 'Lauf',   'a': 16.0,   'b': 32.0,  'c': 1.8},
    'W_20H':  {'Typ': 'Lauf',   'a': 5.5,    'b': 60.0,  'c': 1.8},
    'W_1K0':  {'Typ': 'Lauf',   'a': 0.045,  'b': 520.0, 'c': 1.85},
    'W_1KSC': {'Typ': 'Lauf',   'a': 0.045,  'b': 520.0, 'c': 1.85},
    'W_800':  {'Typ': 'Lauf',   'a': 0.07,   'b': 390.0, 'c': 1.85},
    'W_WEI':  {'Typ': 'Sprung', 'a': 0.18,   'b': 140.0, 'c': 1.41},  # Weit (in cm)
    'W_VOR':  {'Typ': 'Wurf',   'a': 13.0,   'b': 4.0,   'c': 1.1},   # Vortex (in m)
}

def calculate_cup_points(row):
    """Berechnet die Punkte für ein einzelnes Ergebnis."""
    try:
        res = row.get('Result_Num', np.nan)
        event = str(row.get('Event', '')).upper().strip()
        gender = str(row.get('Gender', '')).upper().strip()
        
        if pd.isna(res) or res <= 0 or not gender:
            return 0
            
        key = f"{gender}_{event}"
        if key not in CUP_PARAMS:
            # Fallback für unbekannte Bewerbe (gibt 100 Trostpunkte für gültige Teilnahme)
            return 100 
            
        p = CUP_PARAMS[key]
        points = 0
        
        if p['Typ'] == 'Lauf':
            if res < p['b']:
                points = p['a'] * ((p['b'] - res) ** p['c'])
        elif p['Typ'] == 'Sprung':
            # Weitsprung in der CSV ist oft in Metern (z.B. 3,70). Formel braucht cm!
            val = res * 100 if res < 10 else res 
            if val > p['b']:
                points = p['a'] * ((val - p['b']) ** p['c'])
        elif p['Typ'] == 'Wurf':
            if res > p['b']:
                points = p['a'] * ((res - p['b']) ** p['c'])
                
        return int(np.floor(points))
    except Exception:
        return 0

# --- DATEN BEREINIGUNG ---
def is_valid_result(res):
    if pd.isna(res): return False
    return any(char.isdigit() for char in str(res))

def parse_result_to_number(val):
    if pd.isna(val): return np.nan
    val_str = str(val).strip().replace(',', '.')
    if ':' in val_str:
        parts = val_str.split(':')
        if len(parts) == 2:
            try: return float(parts[0]) * 60 + float(parts[1])
            except ValueError: return np.nan
    try: return float(val_str)
    except ValueError: return np.nan

def load_and_clean_data(file):
    try:
        file.seek(0)
        try: df = pd.read_csv(file, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding='latin1')
        
        if df.shape[1] <= 1:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='latin1')
        
        if 'Result' in df.columns:
            df['Result_Num'] = df['Result'].apply(parse_result_to_number)
            df['isValid'] = df['Result'].apply(is_valid_result)
            # Punkte direkt beim Einlesen berechnen!
            df['CupPoints'] = df.apply(calculate_cup_points, axis=1)
            
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen: {e}")
        return None

# --- DATEN AUSWERTUNGEN ---
def get_cup_ranking(df):
    """Berechnet die Gesamtpunktzahl für den Cup (U10-U14)."""
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    valid_df = df_filtered[df_filtered['isValid'] == True]
    
    ranking = valid_df.groupby(['FirstName', 'LastName', 'Yob']).agg({
        'ClubName': 'first',
        'Class': 'first',
        'Gender': 'first',
        'CupPoints': 'sum', # Punkte aufsummieren
        'Event': lambda x: ', '.join(x.astype(str)), # Absolvierte Bewerbe
        'isValid': 'count' # Anzahl der Bewerbe
    }).reset_index()
    
    return ranking.sort_values(['Class', 'Gender', 'CupPoints'], ascending=[True, True, False])

def get_medal_ranking(df):
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    
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
        return "DNS"

    ranking['Kategorie'] = ranking['isValid'].apply(categorize)
    cat_order = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2, "DNS": 3}
    ranking['Sort'] = ranking['Kategorie'].map(cat_order)
    return ranking.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

def get_winners_list(df):
    target_classes = ['U10', 'U12', 'U14']
    valid_df = df[df['Class'].str.contains('|'.join(target_classes), na=False) & (df['isValid'] == True)].dropna(subset=['Result_Num'])
    
    time_events = ['M', 'H', '100', '200', '400', '600', '800', '1K', '2K', '3K']
    winners = []
    for (event, age_class), group in valid_df.groupby(['Event', 'Class']):
        is_time = any(t in event.upper() for t in time_events)
        winner_row = group.loc[group['Result_Num'].idxmin()] if is_time else group.loc[group['Result_Num'].idxmax()]
        winners.append(winner_row)
        
    return pd.DataFrame(winners).sort_values(['Event', 'Class']) if winners else pd.DataFrame()

# --- DASHBOARD UI ---
st.title("🏆 Moderne Leichtathletik-Auswertung")

with st.sidebar:
    st.header("📤 Daten-Upload")
    uploaded_file = st.file_uploader("results.csv hochladen", type=['csv'])
    if uploaded_file:
        raw_df = load_and_clean_data(uploaded_file)
        if raw_df is not None:
            if st.button("💾 Daten analysieren & speichern"):
                raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
                st.rerun()

    st.divider()
    if st.button("🗑️ Datenbank leeren"):
        conn.execute("DROP TABLE IF EXISTS ergebnisse")
        st.rerun()

try:
    df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)
    
    if not df_db.empty:
        st.subheader("🔍 Globale Suche")
        search_query = st.text_input("Suchen nach Name, Verein oder Altersklasse:", "")

        tab_cup, tab_rank, tab_win, tab_plot, tab_raw = st.tabs([
            "📊 Punkte-Cup", "🏅 Teilnahmen-Medaillen", "🥇 Einzel-Sieger", "📈 Grafiken", "📋 Rohdaten"
        ])

        # --- TAB 1: CUP PUNKTE ---
        with tab_cup:
            st.info("Das Punkte-System gewichtet Lauf, Sprung und Wurf altersgerecht für einen fairen Mehrkampf.")
            cup_df = get_cup_ranking(df_db)
            
            if search_query:
                cup_df = cup_df[cup_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                
            st.dataframe(cup_df[['Class', 'Gender', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'isValid', 'Event']], 
                         column_config={"CupPoints": "Gesamtpunkte", "isValid": "Anzahl Bewerbe", "Event": "Absolviert"},
                         width='stretch', hide_index=True)
            
            csv_cup = cup_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Cup-Wertung herunterladen", csv_cup, "cup_wertung.csv", "text/csv")

        # --- TAB 2: MEDAILLEN RANKING ---
        with tab_rank:
            rank_df = get_medal_ranking(df_db)
            if search_query:
                rank_df = rank_df[rank_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

            c1, c2, c3 = st.columns(3)
            c1.metric("🥇 Gold (3+)", len(rank_df[rank_df['Kategorie'] == "🥇 Gold"]))
            c2.metric("🥈 Silber (2)", len(rank_df[rank_df['Kategorie'] == "🥈 Silber"]))
            c3.metric("🥉 Bronze (1)", len(rank_df[rank_df['Kategorie'] == "🥉 Bronze"]))
            
            st.dataframe(rank_df[['Kategorie', 'FirstName', 'LastName', 'Class', 'ClubName', 'Perf_String', 'isValid']], 
                         column_config={"isValid": "Gültige Leistungen", "Perf_String": "Details"}, 
                         width='stretch', hide_index=True)
            
            csv_rank = rank_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Medaillen-Ranking herunterladen", csv_rank, "medaillen_ranking.csv", "text/csv")

        # --- TAB 3: SIEGERLISTE ---
        with tab_win:
            winners_df = get_winners_list(df_db)
            if not winners_df.empty:
                if search_query:
                    winners_df = winners_df[winners_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                
                st.dataframe(winners_df[['Event', 'Class', 'FirstName', 'LastName', 'ClubName', 'Result']], 
                             width='stretch', hide_index=True)
                csv_win = winners_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Siegerliste herunterladen", csv_win, "siegerliste.csv", "text/csv")

        # --- TAB 4: ANALYSE ---
        with tab_plot:
            sel_event = st.selectbox("Bewerb für Grafik wählen:", sorted(df_db['Event'].unique()))
            plot_df = df_db[df_db['Event'] == sel_event].dropna(subset=['Result_Num'])
            if search_query:
                plot_df = plot_df[plot_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            
            if not plot_df.empty:
                fig = px.box(plot_df, x="Class", y="Result_Num", color="Class", points="all", hover_data=["FirstName", "LastName", "CupPoints"])
                fig.update_layout(yaxis_title="Ergebnis")
                st.plotly_chart(fig, width="stretch")

        # --- TAB 5: ROHDATEN ---
        with tab_raw:
            raw_display = df_db
            if search_query:
                raw_display = raw_display[raw_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            st.dataframe(raw_display, width='stretch')

    else:
        st.info("Bitte lade eine CSV-Datei hoch.")
except Exception as e:
    st.info("Bereit für den Daten-Upload.")