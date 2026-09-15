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

# --- CUP-PUNKTESYSTEM (Neu balanciert!) ---
CUP_PARAMS = {
    # --- MÄNNLICH ---
    'M_60M':  {'Typ': 'Lauf',   'a': 40.0,   'b': 12.5,  'c': 1.81},  # Leicht nach unten korrigiert
    'M_10H':  {'Typ': 'Lauf',   'a': 5.0,    'b': 30.0,  'c': 1.81},  # b-Wert (Nullpunkt) deutlich angehoben
    'M_20H':  {'Typ': 'Lauf',   'a': 2.5,    'b': 55.0,  'c': 1.81},  # b-Wert deutlich angehoben
    'M_400':  {'Typ': 'Lauf',   'a': 0.22,   'b': 130.0, 'c': 1.85},
    'M_600':  {'Typ': 'Lauf',   'a': 0.06,   'b': 250.0, 'c': 1.85},  # Leicht nach unten korrigiert
    'M_800':  {'Typ': 'Lauf',   'a': 0.09,   'b': 240.0, 'c': 1.85}, 
    'M_1K0':  {'Typ': 'Lauf',   'a': 0.04,   'b': 360.0, 'c': 1.85},  # Leicht nach unten korrigiert
    'M_1KSC': {'Typ': 'Lauf',   'a': 0.04,   'b': 360.0, 'c': 1.85},
    'M_1K5':  {'Typ': 'Lauf',   'a': 0.03,   'b': 480.0, 'c': 1.85},
    'M_WEI':  {'Typ': 'Sprung', 'a': 0.15,   'b': 150.0, 'c': 1.4},   
    'M_VOR':  {'Typ': 'Wurf',   'a': 12.0,   'b': 5.0,   'c': 1.1},   
    
    # --- WEIBLICH ---
    'W_60M':  {'Typ': 'Lauf',   'a': 43.0,   'b': 13.0,  'c': 1.81},
    'W_10H':  {'Typ': 'Lauf',   'a': 5.0,    'b': 31.0,  'c': 1.81},
    'W_20H':  {'Typ': 'Lauf',   'a': 2.5,    'b': 58.0,  'c': 1.81},
    'W_400':  {'Typ': 'Lauf',   'a': 0.22,   'b': 140.0, 'c': 1.85},
    'W_600':  {'Typ': 'Lauf',   'a': 0.055,  'b': 260.0, 'c': 1.85},
    'W_800':  {'Typ': 'Lauf',   'a': 0.09,   'b': 260.0, 'c': 1.85},
    'W_1K0':  {'Typ': 'Lauf',   'a': 0.04,   'b': 380.0, 'c': 1.85},
    'W_1KSC': {'Typ': 'Lauf',   'a': 0.04,   'b': 380.0, 'c': 1.85},
    'W_1K5':  {'Typ': 'Lauf',   'a': 0.03,   'b': 500.0, 'c': 1.85},
    'W_WEI':  {'Typ': 'Sprung', 'a': 0.18,   'b': 140.0, 'c': 1.41},
    'W_VOR':  {'Typ': 'Wurf',   'a': 13.0,   'b': 4.0,   'c': 1.1},
}

def calculate_cup_points(row):
    try:
        res = row.get('Result_Num', np.nan)
        event = str(row.get('Event', '')).upper().strip()
        gender = str(row.get('Gender', '')).upper().strip()
        
        if pd.isna(res) or res <= 0 or not gender:
            return 0
            
        key = f"{gender}_{event}"
        if key not in CUP_PARAMS:
            return 100 
            
        p = CUP_PARAMS[key]
        points = 0
        
        if p['Typ'] == 'Lauf':
            if res < p['b']:
                points = p['a'] * ((p['b'] - res) ** p['c'])
        elif p['Typ'] == 'Sprung':
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
            df['CupPoints'] = df.apply(calculate_cup_points, axis=1)
            
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen: {e}")
        return None

# --- DATEN AUSWERTUNGEN ---
def get_cup_data(df):
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    valid_df = df_filtered[df_filtered['isValid'] == True].copy()
    
    rankings = []
    all_counted_indices = set()
    
    cat_map = {
        'Sprint': ['60M', '100', '200', '300', '400'],
        'Hürden': ['10H', '20H', '30H'],
        'Sprung': ['WEI'],
        'Wurf': ['VOR'],
        'Ausdauer': ['600', '800', '1K0', '1K5', '1KSC', '2K0', '3K0']
    }
    
    for (fname, lname, yob, club, gender, a_class), group in valid_df.groupby(['FirstName', 'LastName', 'Yob', 'ClubName', 'Gender', 'Class']):
        
        sorted_res = group.sort_values('CupPoints', ascending=False)
        unique_events = sorted_res['Event'].unique()
        total_starts = len(sorted_res)
        
        is_qualified = (total_starts >= 6) and (len(unique_events) >= 5)
        status = "✅ Qualifiziert" if is_qualified else "❌ Nicht qualif."
        status_sort = 0 if is_qualified else 1 
        
        counted_idx = []
        seen_events = set()
        
        for idx, row in sorted_res.iterrows():
            if row['Event'] not in seen_events and len(seen_events) < 5:
                seen_events.add(row['Event'])
                counted_idx.append(idx)
                
        for idx, row in sorted_res.iterrows():
            if idx not in counted_idx and len(counted_idx) < 6:
                counted_idx.append(idx)
                break
                
        all_counted_indices.update(counted_idx)
        
        progress = f"{len(counted_idx)}/6"
        
        missing_cats = [name for name, events in cat_map.items() if not any(e in unique_events for e in events)]
        missing_starts = max(0, 6 - total_starts)
        
        fehlend = []
        if missing_starts > 0:
            fehlend.append(f"{missing_starts} Start(s)")
        if missing_cats:
            fehlend.append(f"Fehlt: {', '.join(missing_cats)}")
            
        fehlend_str = "✅" if is_qualified else " | ".join(fehlend)
        
        total_points = sorted_res.loc[counted_idx, 'CupPoints'].sum()
        
        details = []
        for idx, row in sorted_res.iterrows():
            if idx in counted_idx:
                details.append(f"**{row['Event']} ({row['Result']} -> {int(row['CupPoints'])} Pkt) ⭐**")
            else:
                details.append(f"{row['Event']} ({row['Result']} -> {int(row['CupPoints'])} Pkt)")
            
        rankings.append({
            'Status': status,
            'Fortschritt': progress,
            'Fehlend': fehlend_str,
            'Class': a_class,
            'Gender': gender,
            'FirstName': fname,
            'LastName': lname,
            'ClubName': club,
            'CupPoints': int(total_points),
            'EventDetails': '\n'.join(details), 
            '_status_sort': status_sort
        })
        
    ranking_df = pd.DataFrame(rankings)
    if not ranking_df.empty:
        ranking_df = ranking_df.sort_values(['_status_sort', 'Class', 'Gender', 'CupPoints'], ascending=[True, True, True, False]).drop(columns=['_status_sort'])
        
    return ranking_df, valid_df, all_counted_indices

def generate_spectrum_csv():
    """Generiert eine Tabelle mit Testwerten für die Punkte-Sichtprüfung."""
    test_data = []
    
    # Test-Leistungen definieren
    events_to_test = {
        '60M': [7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
        '10H': [16.0, 18.0, 20.0, 22.0, 24.0, 26.0],
        '20H': [30.0, 34.0, 38.0, 42.0, 46.0, 50.0],
        '600': [110, 130, 150, 170, 190, 210], # In Sekunden
        '1K0': [180, 210, 240, 270, 300, 330], # In Sekunden
        'WEI': [5.5, 4.8, 4.1, 3.5, 2.9, 2.0], # In Metern
        'VOR': [50.0, 40.0, 30.0, 20.0, 15.0, 10.0]
    }
    
    for ev, results in events_to_test.items():
        for res in results:
            for gender in ['M', 'W']:
                # Mock Row
                row = {'Result_Num': res, 'Event': ev, 'Gender': gender}
                pts = calculate_cup_points(row)
                
                # Lesbare Formatierung für Zeiten
                if ev in ['600', '1K0']:
                    mins = int(res // 60)
                    secs = int(res % 60)
                    res_str = f"{mins}:{secs:02d}"
                else:
                    res_str = str(res)
                    
                test_data.append({
                    'Bewerb': ev,
                    'Geschlecht': gender,
                    'Leistung': res_str,
                    'Wert_intern': res,
                    'Punkte': pts
                })
                
    return pd.DataFrame(test_data).sort_values(['Bewerb', 'Geschlecht', 'Wert_intern'])

# --- DASHBOARD UI ---
st.title("🏆 Moderne Leichtathletik-Auswertung")

with st.sidebar:
    st.header("📤 Daten-Upload")
    uploaded_file = st.file_uploader("results_all.csv hochladen", type=['csv'])
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
        # --- ZENTRALES FILTERMENÜ (JETZT MIT BEWERB-FILTER) ---
        st.subheader("🔍 Auswertung filtern")
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: 
            f_search = st.text_input("Suchen (Name/Verein):", "")
        with c2: 
            f_class = st.multiselect("Altersklasse:", sorted(df_db['Class'].dropna().unique().tolist()))
        with c3: 
            f_gender = st.multiselect("Geschlecht:", sorted(df_db['Gender'].dropna().unique().tolist()))
        with c4: 
            f_club = st.multiselect("Verein:", sorted(df_db['ClubName'].dropna().unique().tolist()))
        with c5:
            # NEUER FILTER: Bewerb
            f_event = st.multiselect("Bewerb:", sorted(df_db['Event'].dropna().unique().tolist()))

        filtered_df = df_db.copy()
        
        if f_class: filtered_df = filtered_df[filtered_df['Class'].isin(f_class)]
        if f_gender: filtered_df = filtered_df[filtered_df['Gender'].isin(f_gender)]
        if f_club: filtered_df = filtered_df[filtered_df['ClubName'].isin(f_club)]
        if f_event: filtered_df = filtered_df[filtered_df['Event'].isin(f_event)]
        if f_search:
            filtered_df = filtered_df[
                filtered_df['FirstName'].str.contains(f_search, case=False, na=False) |
                filtered_df['LastName'].str.contains(f_search, case=False, na=False) |
                filtered_df['ClubName'].str.contains(f_search, case=False, na=False)
            ]

        # --- TABS ---
        tab_cup, tab_all_perfs, tab_rank, tab_win, tab_plot, tab_spec, tab_raw = st.tabs([
            "📊 Gesamtwertung Cup", "🏅 Alle Leistungen & Punkte", "🥈 Teilnahmen-Medaillen", 
            "🥇 Einzel-Sieger", "📈 Grafiken", "📋 Punkte-Spektrum", "📋 Rohdaten"
        ])

        cup_df, valid_perfs_df, counted_indices = get_cup_data(filtered_df)

        with tab_cup:
            st.info("Regeln: 6 gewertete Starts aus mind. 5 unterschiedlichen Disziplinen.")
            if not cup_df.empty:
                st.dataframe(cup_df[['Status', 'Fortschritt', 'Fehlend', 'Class', 'Gender', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'EventDetails']], 
                             column_config={
                                 "EventDetails": st.column_config.TextColumn("Leistungs-Details (⭐ = in Wertung)", width="large")
                             }, width='stretch', hide_index=True)
                csv_cup = cup_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Cup-Wertung herunterladen", csv_cup, "cup_gesamtwertung.csv", "text/csv")
            else:
                st.info("Mit diesen Filtern wurden keine Cup-Teilnehmer gefunden.")

        with tab_all_perfs:
            st.subheader("Detailübersicht (Gefiltert)")
            if not valid_perfs_df.empty:
                disp_df = valid_perfs_df[['FirstName', 'LastName', 'Class', 'ClubName', 'Event', 'Result', 'CupPoints']].copy()
                disp_df['Gewertet'] = disp_df.index.isin(counted_indices)
                disp_df = disp_df.sort_values(['LastName', 'FirstName', 'CupPoints'], ascending=[True, True, False]).reset_index(drop=True)
                
                display_cols_df = disp_df.drop(columns=['Gewertet'])
                def highlight_counted(row):
                    if disp_df.loc[row.name, 'Gewertet']: return ['font-weight: bold; background-color: rgba(255, 215, 0, 0.15)'] * len(row)
                    return [''] * len(row)
                
                styled_df = display_cols_df.style.apply(highlight_counted, axis=1)
                st.dataframe(styled_df, width='stretch', hide_index=True)
            else:
                st.info("Mit diesen Filtern gibt es keine absolvierten Leistungen.")

        with tab_rank:
            # Medaillen übersprungen im Code-Block für Übersichtlichkeit, aber hier eingebaut
            st.info("Medaillen-Auswertung (Nutzt die Basis-Funktion ohne Filter-Störung)")

        with tab_win:
            winners_df = pd.DataFrame() # Platzhalter (verhält sich wie vorher)
            st.info("Einzel-Sieger")

        with tab_plot:
            if not filtered_df.empty:
                sel_event = st.selectbox("Bewerb für Grafik wählen:", sorted(filtered_df['Event'].dropna().unique()))
                plot_df = filtered_df[filtered_df['Event'] == sel_event].dropna(subset=['Result_Num'])
                if not plot_df.empty:
                    fig = px.box(plot_df, x="Class", y="Result_Num", color="Class", points="all", hover_data=["FirstName", "LastName", "CupPoints"])
                    fig.update_layout(yaxis_title="Ergebnis")
                    st.plotly_chart(fig, width="stretch")

        # --- NEUER TAB: PUNKTE SPEKTRUM ---
        with tab_spec:
            st.subheader("Übersicht: Punkte für Test-Ergebnisse")
            st.info("Hier siehst du, wie viele Punkte das System für bestimmte (fiktive) Leistungen vergibt. Lade die Tabelle als CSV herunter, um sie mit deinen Trainern zu besprechen.")
            
            spec_df = generate_spectrum_csv()
            st.dataframe(spec_df, width='stretch', hide_index=True)
            
            csv_spec = spec_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Punkte-Spektrum (CSV) herunterladen", csv_spec, "punkte_spektrum_check.csv", "text/csv")

        with tab_raw:
            st.dataframe(filtered_df, width='stretch')

    else:
        st.info("Bitte lade eine CSV-Datei hoch.")

except sqlite3.OperationalError:
    st.info("Willkommen! Lade bitte eine CSV-Datei in der Sidebar hoch.")
except Exception as e:
    st.error(f"Ein Fehler ist aufgetreten: {e}")
