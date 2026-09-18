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

# --- CUP-PUNKTESYSTEM (Differenziert nach Altersklasse U10/U12/U14 & Geschlecht) ---
CUP_PARAMS = {
    # ==================== U10 ====================
    # Männlich U10
    'U10_M_60M':  {'Typ': 'Lauf',   'a': 35.0,   'b': 14.5,  'c': 1.81},
    'U10_M_10H':  {'Typ': 'Lauf',   'a': 4.5,    'b': 34.0,  'c': 1.81},
    'U10_M_600':  {'Typ': 'Lauf',   'a': 0.055,  'b': 260.0, 'c': 1.85},
    'U10_M_WEI':  {'Typ': 'Sprung', 'a': 0.22,   'b': 100.0, 'c': 1.40},  # Basis 1.00m
    'U10_M_VOR':  {'Typ': 'Wurf',   'a': 18.0,   'b': 3.0,   'c': 1.05},  # Basis 3m
    
    # Weiblich U10
    'U10_W_60M':  {'Typ': 'Lauf',   'a': 36.0,   'b': 14.8,  'c': 1.81},
    'U10_W_10H':  {'Typ': 'Lauf',   'a': 4.5,    'b': 35.0,  'c': 1.81},
    'U10_W_600':  {'Typ': 'Lauf',   'a': 0.050,  'b': 270.0, 'c': 1.85},
    'U10_W_WEI':  {'Typ': 'Sprung', 'a': 0.24,   'b': 90.0,  'c': 1.40},   # Basis 0.90m
    'U10_W_VOR':  {'Typ': 'Wurf',   'a': 20.0,   'b': 2.5,   'c': 1.05},

    # ==================== U12 ====================
    # Männlich U12
    'U12_M_60M':  {'Typ': 'Lauf',   'a': 40.0,   'b': 13.0,  'c': 1.81},
    'U12_M_20H':  {'Typ': 'Lauf',   'a': 2.5,    'b': 56.0,  'c': 1.81},
    'U12_M_600':  {'Typ': 'Lauf',   'a': 0.060,  'b': 250.0, 'c': 1.85},
    'U12_M_1K0':  {'Typ': 'Lauf',   'a': 0.040,  'b': 370.0, 'c': 1.85},
    'U12_M_1KSC': {'Typ': 'Lauf',   'a': 0.042,  'b': 380.0, 'c': 1.85},
    'U12_M_WEI':  {'Typ': 'Sprung', 'a': 0.16,   'b': 140.0, 'c': 1.40},  # Basis 1.40m
    'U12_M_VOR':  {'Typ': 'Wurf',   'a': 13.0,   'b': 5.0,   'c': 1.10},  # Basis 5m

    # Weiblich U12
    'U12_W_60M':  {'Typ': 'Lauf',   'a': 42.0,   'b': 13.4,  'c': 1.81},
    'U12_W_20H':  {'Typ': 'Lauf',   'a': 2.5,    'b': 58.0,  'c': 1.81},
    'U12_W_600':  {'Typ': 'Lauf',   'a': 0.055,  'b': 260.0, 'c': 1.85},
    'U12_W_1K0':  {'Typ': 'Lauf',   'a': 0.040,  'b': 390.0, 'c': 1.85},
    'U12_W_1KSC': {'Typ': 'Lauf',   'a': 0.040,  'b': 400.0, 'c': 1.85},
    'U12_W_WEI':  {'Typ': 'Sprung', 'a': 0.18,   'b': 130.0, 'c': 1.40},
    'U12_W_VOR':  {'Typ': 'Wurf',   'a': 14.0,   'b': 4.5,   'c': 1.10},

    # ==================== U14 ====================
    # Männlich U14
    'U14_M_60M':  {'Typ': 'Lauf',   'a': 45.0,   'b': 12.0,  'c': 1.81},
    'U14_M_20H':  {'Typ': 'Lauf',   'a': 2.6,    'b': 52.0,  'c': 1.81},
    'U14_M_600':  {'Typ': 'Lauf',   'a': 0.065,  'b': 240.0, 'c': 1.85},
    'U14_M_1K0':  {'Typ': 'Lauf',   'a': 0.042,  'b': 350.0, 'c': 1.85},
    'U14_M_1KSC': {'Typ': 'Lauf',   'a': 0.044,  'b': 365.0, 'c': 1.85},
    'U14_M_WEI':  {'Typ': 'Sprung', 'a': 0.14,   'b': 180.0, 'c': 1.40},  # Basis 1.80m
    'U14_M_VOR':  {'Typ': 'Wurf',   'a': 10.5,   'b': 8.0,   'c': 1.12},  # Basis 8m

    # Weiblich U14
    'U14_W_60M':  {'Typ': 'Lauf',   'a': 46.0,   'b': 12.5,  'c': 1.81},
    'U14_W_20H':  {'Typ': 'Lauf',   'a': 2.6,    'b': 54.0,  'c': 1.81},
    'U14_W_600':  {'Typ': 'Lauf',   'a': 0.060,  'b': 250.0, 'c': 1.85},
    'U14_W_1K0':  {'Typ': 'Lauf',   'a': 0.042,  'b': 370.0, 'c': 1.85},
    'U14_W_1KSC': {'Typ': 'Lauf',   'a': 0.042,  'b': 385.0, 'c': 1.85},
    'U14_W_WEI':  {'Typ': 'Sprung', 'a': 0.16,   'b': 170.0, 'c': 1.40},
    'U14_W_VOR':  {'Typ': 'Wurf',   'a': 11.5,   'b': 6.5,   'c': 1.12},
}

def get_age_group(cls_str):
    """Extrahiert U10, U12 oder U14 aus der Klassen-Bezeichnung."""
    if not cls_str or pd.isna(cls_str):
        return 'U12'
    cls_upper = str(cls_str).upper()
    if 'U10' in cls_upper: return 'U10'
    if 'U14' in cls_upper: return 'U14'
    if 'U12' in cls_upper: return 'U12'
    return 'U12'

def calculate_cup_points(row):
    try:
        res = row.get('Result_Num', np.nan)
        event = str(row.get('Event', '')).upper().strip()
        gender = str(row.get('Gender', '')).upper().strip()
        age = get_age_group(row.get('Class', ''))
        
        if pd.isna(res) or res <= 0 or not gender:
            return 0
            
        key = f"{age}_{gender}_{event}"
        
        # Fallback falls exakte Kombination nicht existiert
        if key not in CUP_PARAMS:
            key_fallback = f"U12_{gender}_{event}"
            if key_fallback in CUP_PARAMS:
                p = CUP_PARAMS[key_fallback]
            else:
                return 100
        else:
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

def generate_spectrum_csv(target_age='U12'):
    """Generiert Testwerte für eine bestimmte Altersklasse (U10, U12, U14)."""
    test_data = []
    
    events_to_test = {
        '60M': [7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5],
        '10H': [16.0, 18.0, 20.0, 22.0, 24.0, 26.0],
        '20H': [32.0, 36.0, 40.0, 44.0, 48.0, 52.0],
        '600': [110, 130, 150, 170, 190, 210],
        '1K0': [180, 210, 240, 270, 300, 330],
        '1KSC': [180, 210, 240, 270, 300, 330], 
        'WEI': [5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0],
        'VOR': [50.0, 40.0, 30.0, 25.0, 20.0, 15.0, 10.0]
    }
    
    for ev, results in events_to_test.items():
        for res in results:
            for gender in ['M', 'W']:
                row = {'Result_Num': res, 'Event': ev, 'Gender': gender, 'Class': target_age}
                pts = calculate_cup_points(row)
                
                if ev in ['600', '1K0', '1KSC']:
                    mins = int(res // 60)
                    secs = int(res % 60)
                    res_str = f"{mins}:{secs:02d}"
                else:
                    res_str = str(res)
                    
                test_data.append({
                    'Altersklasse': target_age,
                    'Bewerb': ev,
                    'Geschlecht': gender,
                    'Leistung': res_str,
                    'Wert_intern': res,
                    'Punkte': pts
                })
                
    return pd.DataFrame(test_data).sort_values(['Bewerb', 'Geschlecht', 'Wert_intern'])

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

        tab_cup, tab_all_perfs, tab_rank, tab_win, tab_plot, tab_spec, tab_raw = st.tabs([
            "📊 Gesamtwertung Cup", "🏅 Alle Leistungen & Punkte", "🥈 Teilnahmen-Medaillen", 
            "🥇 Einzel-Sieger", "📈 Grafiken", "📋 Punkte-Spektrum", "📋 Rohdaten"
        ])

        cup_df, valid_perfs_df, counted_indices = get_cup_data(filtered_df)

        with tab_cup:
            st.info("Regeln: 6 gewertete Starts aus mind. 5 unterschiedlichen Disziplinen. Punkte sind nun exakt nach Altersklasse (U10, U12, U14) abgestimmt.")
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
            rank_df = get_medal_ranking(filtered_df)
            c1, c2, c3 = st.columns(3)
            c1.metric("🥇 Gold (3+)", len(rank_df[rank_df['Kategorie'] == "🥇 Gold"]))
            c2.metric("🥈 Silber (2)", len(rank_df[rank_df['Kategorie'] == "🥈 Silber"]))
            c3.metric("🥉 Bronze (1)", len(rank_df[rank_df['Kategorie'] == "🥉 Bronze"]))
            
            st.dataframe(rank_df[['Kategorie', 'FirstName', 'LastName', 'Class', 'ClubName', 'Perf_String', 'isValid']], 
                         column_config={"isValid": "Gültige Leistungen", "Perf_String": "Details"}, 
                         width='stretch', hide_index=True)

        with tab_win:
            winners_df = get_winners_list(filtered_df)
            if not winners_df.empty:
                st.dataframe(winners_df[['Event', 'Class', 'FirstName', 'LastName', 'ClubName', 'Result']], 
                             width='stretch', hide_index=True)

        with tab_plot:
            if not filtered_df.empty:
                sel_event = st.selectbox("Bewerb für Grafik wählen:", sorted(filtered_df['Event'].dropna().unique()))
                plot_df = filtered_df[filtered_df['Event'] == sel_event].dropna(subset=['Result_Num'])
                if not plot_df.empty:
                    fig = px.box(plot_df, x="Class", y="Result_Num", color="Class", points="all", hover_data=["FirstName", "LastName", "CupPoints"])
                    fig.update_layout(yaxis_title="Ergebnis")
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.warning("Keine Werte für die Grafik vorhanden.")

        # --- NEUER TAB: PUNKTE SPEKTRUM MIT ALTERSWAHL ---
        with tab_spec:
            st.subheader("Übersicht: Punkte für Test-Ergebnisse")
            sel_age = st.radio("Altersklasse für Spektrum wählen:", ["U10", "U12", "U14"], horizontal=True)
            
            spec_df = generate_spectrum_csv(target_age=sel_age)
            st.dataframe(spec_df, width='stretch', hide_index=True)
            
            csv_spec = spec_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(f"📥 Punkte-Spektrum ({sel_age}) herunterladen", csv_spec, f"punkte_spektrum_{sel_age}.csv", "text/csv")

        with tab_raw:
            st.dataframe(filtered_df, width='stretch')

    else:
        st.info("Bitte lade eine CSV-Datei hoch.")

except sqlite3.OperationalError:
    st.info("Willkommen! Lade bitte eine CSV-Datei in der Sidebar hoch.")
except Exception as e:
    st.error(f"Ein Fehler ist aufgetreten: {e}")
