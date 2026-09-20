import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
from io import BytesIO

# --- KONFIGURATION ---
st.set_page_config(page_title="Leichtathletik Auswertung Pro", layout="wide", page_icon="🏆")

def get_connection():
    return sqlite3.connect('leichtathletik.db', check_same_thread=False)

conn = get_connection()

# --- CUP-PUNKTESYSTEM ---
CUP_PARAMS = {
    # ==================== U10 ====================
    'U10_M_60M':  {'Typ': 'Lauf',   'a': 35.0,   'b': 14.5,  'c': 1.81},
    'U10_M_10H':  {'Typ': 'Lauf',   'a': 4.5,    'b': 34.0,  'c': 1.81},
    'U10_M_600':  {'Typ': 'Lauf',   'a': 0.055,  'b': 260.0, 'c': 1.85},
    'U10_M_WEI':  {'Typ': 'Sprung', 'a': 0.22,   'b': 100.0, 'c': 1.40},
    'U10_M_VOR':  {'Typ': 'Wurf',   'a': 18.0,   'b': 3.0,   'c': 1.05},
    
    'U10_W_60M':  {'Typ': 'Lauf',   'a': 36.0,   'b': 14.8,  'c': 1.81},
    'U10_W_10H':  {'Typ': 'Lauf',   'a': 4.5,    'b': 35.0,  'c': 1.81},
    'U10_W_600':  {'Typ': 'Lauf',   'a': 0.050,  'b': 270.0, 'c': 1.85},
    'U10_W_WEI':  {'Typ': 'Sprung', 'a': 0.24,   'b': 90.0,  'c': 1.40},
    'U10_W_VOR':  {'Typ': 'Wurf',   'a': 20.0,   'b': 2.5,   'c': 1.05},

    # ==================== U12 ====================
    'U12_M_60M':  {'Typ': 'Lauf',   'a': 40.0,   'b': 13.0,  'c': 1.81},
    'U12_M_20H':  {'Typ': 'Lauf',   'a': 2.5,    'b': 56.0,  'c': 1.81},
    'U12_M_600':  {'Typ': 'Lauf',   'a': 0.060,  'b': 250.0, 'c': 1.85},
    'U12_M_1K0':  {'Typ': 'Lauf',   'a': 0.040,  'b': 370.0, 'c': 1.85},
    'U12_M_1KSC': {'Typ': 'Lauf',   'a': 0.042,  'b': 380.0, 'c': 1.85},
    'U12_M_WEI':  {'Typ': 'Sprung', 'a': 0.16,   'b': 140.0, 'c': 1.40},
    'U12_M_VOR':  {'Typ': 'Wurf',   'a': 13.0,   'b': 5.0,   'c': 1.10},

    'U12_W_60M':  {'Typ': 'Lauf',   'a': 42.0,   'b': 13.4,  'c': 1.81},
    'U12_W_20H':  {'Typ': 'Lauf',   'a': 2.5,    'b': 58.0,  'c': 1.81},
    'U12_W_600':  {'Typ': 'Lauf',   'a': 0.055,  'b': 260.0, 'c': 1.85},
    'U12_W_1K0':  {'Typ': 'Lauf',   'a': 0.040,  'b': 390.0, 'c': 1.85},
    'U12_W_1KSC': {'Typ': 'Lauf',   'a': 0.040,  'b': 400.0, 'c': 1.85},
    'U12_W_WEI':  {'Typ': 'Sprung', 'a': 0.18,   'b': 130.0, 'c': 1.40},
    'U12_W_VOR':  {'Typ': 'Wurf',   'a': 14.0,   'b': 4.5,   'c': 1.10},

    # ==================== U14 ====================
    'U14_M_60M':  {'Typ': 'Lauf',   'a': 45.0,   'b': 12.0,  'c': 1.81},
    'U14_M_20H':  {'Typ': 'Lauf',   'a': 2.6,    'b': 52.0,  'c': 1.81},
    'U14_M_600':  {'Typ': 'Lauf',   'a': 0.065,  'b': 240.0, 'c': 1.85},
    'U14_M_1K0':  {'Typ': 'Lauf',   'a': 0.042,  'b': 350.0, 'c': 1.85},
    'U14_M_1KSC': {'Typ': 'Lauf',   'a': 0.044,  'b': 365.0, 'c': 1.85},
    'U14_M_WEI':  {'Typ': 'Sprung', 'a': 0.14,   'b': 180.0, 'c': 1.40},
    'U14_M_VOR':  {'Typ': 'Wurf',   'a': 10.5,   'b': 8.0,   'c': 1.12},

    'U14_W_60M':  {'Typ': 'Lauf',   'a': 46.0,   'b': 12.5,  'c': 1.81},
    'U14_W_20H':  {'Typ': 'Lauf',   'a': 2.6,    'b': 54.0,  'c': 1.81},
    'U14_W_600':  {'Typ': 'Lauf',   'a': 0.060,  'b': 250.0, 'c': 1.85},
    'U14_W_1K0':  {'Typ': 'Lauf',   'a': 0.042,  'b': 370.0, 'c': 1.85},
    'U14_W_1KSC': {'Typ': 'Lauf',   'a': 0.042,  'b': 385.0, 'c': 1.85},
    'U14_W_WEI':  {'Typ': 'Sprung', 'a': 0.16,   'b': 170.0, 'c': 1.40},
    'U14_W_VOR':  {'Typ': 'Wurf',   'a': 11.5,   'b': 6.5,   'c': 1.12},
}

def get_age_group(cls_str):
    if not cls_str or pd.isna(cls_str): return 'U12'
    cls_upper = str(cls_str).upper()
    if 'U10' in cls_upper: return 'U10'
    if 'U14' in cls_upper: return 'U14'
    if 'U12' in cls_upper: return 'U12'
    return 'U12'

def is_run_event(event_name):
    e = str(event_name).upper()
    field_keywords = ['WEI', 'HOC', 'VOR', 'BAL', 'KUG', 'SPE', 'DIS', 'STA', 'ZON']
    return not any(f in e for f in field_keywords)

def calculate_cup_points(row):
    try:
        res = row.get('Result_Num', np.nan)
        event = str(row.get('Event', '')).upper().strip()
        gender = str(row.get('Gender', '')).upper().strip()
        age = get_age_group(row.get('Class', ''))
        
        if pd.isna(res) or res <= 0 or not gender: return 0
            
        key = f"{age}_{gender}_{event}"
        if key not in CUP_PARAMS:
            key_fallback = f"U12_{gender}_{event}"
            if key_fallback in CUP_PARAMS: p = CUP_PARAMS[key_fallback]
            else: return 100
        else:
            p = CUP_PARAMS[key]
            
        points = 0
        if p['Typ'] == 'Lauf':
            if res < p['b']: points = p['a'] * ((p['b'] - res) ** p['c'])
        elif p['Typ'] == 'Sprung':
            val = res * 100 if res < 10 else res 
            if val > p['b']: points = p['a'] * ((val - p['b']) ** p['c'])
        elif p['Typ'] == 'Wurf':
            if res > p['b']: points = p['a'] * ((res - p['b']) ** p['c'])
                
        return int(np.floor(points))
    except Exception: return 0

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
            
        if 'Event' in df.columns:
            df['Event'] = df['Event'].astype(str).str.upper().str.strip()
            df['Event'] = df['Event'].replace('WEZ', 'WEI')
            
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen: {e}")
        return None

def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone()[0] == 1

# --- DATEN AUSWERTUNGEN ---
def get_cup_data(df):
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    valid_df = df_filtered[df_filtered['isValid'] == True].copy()
    
    rankings = []
    all_counted_indices = set()
    
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
        
        total_points = sorted_res.loc[counted_idx, 'CupPoints'].sum()
        details = []
        for idx, row in sorted_res.iterrows():
            if idx in counted_idx: details.append(f"**{row['Event']} ({row['Result']} -> {int(row['CupPoints'])} Pkt) ⭐**")
            else: details.append(f"{row['Event']} ({row['Result']} -> {int(row['CupPoints'])} Pkt)")
            
        rankings.append({
            'Status': status, 'Fortschritt': progress, 'Class': a_class, 'Gender': gender,
            'FirstName': fname, 'LastName': lname, 'ClubName': club,
            'CupPoints': int(total_points), 'EventDetails': '\n'.join(details), 
            '_status_sort': status_sort
        })
        
    ranking_df = pd.DataFrame(rankings)
    if not ranking_df.empty:
        ranking_df = ranking_df.sort_values(['_status_sort', 'Class', 'Gender', 'CupPoints'], ascending=[True, True, True, False]).drop(columns=['_status_sort'])
    return ranking_df, valid_df, all_counted_indices

def create_excel_report(cup_df):
    output = BytesIO()
    df_sorted = cup_df.sort_values(by=['Class', 'Gender', 'CupPoints'], ascending=[True, True, False])
    cols_to_keep = ['Class', 'Gender', 'Status', 'Fortschritt', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'EventDetails']
    df_export = df_sorted[cols_to_keep].copy()
    
    df_export = df_export.rename(columns={
        'Class': 'Altersklasse', 'Gender': 'Geschlecht', 'Status': 'Qualifikation',
        'Fortschritt': 'Starts (gewertet)', 'CupPoints': 'Punkte', 'FirstName': 'Vorname',
        'LastName': 'Nachname', 'ClubName': 'Verein', 'EventDetails': 'Details der Leistungen (⭐ in Wertung)'
    })
    df_export['Details der Leistungen (⭐ in Wertung)'] = df_export['Details der Leistungen (⭐ in Wertung)'].str.replace('**', '')

    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df_export.to_excel(writer, index=False, sheet_name='Cup_Gesamtwertung')
    
    workbook = writer.book
    worksheet = writer.sheets['Cup_Gesamtwertung']
    
    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'fg_color': '#D7E4BC', 'border': 1})
    cell_format = workbook.add_format({'valign': 'vcenter'})
    points_format = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'bold': True})
    details_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    
    for col_num, value in enumerate(df_export.columns.values):
        worksheet.write(0, col_num, value, header_format)
        
    worksheet.set_column('A:B', 12, cell_format)
    worksheet.set_column('C:C', 18, cell_format)
    worksheet.set_column('D:D', 15, cell_format)
    worksheet.set_column('E:E', 12, points_format)
    worksheet.set_column('F:G', 15, cell_format)
    worksheet.set_column('H:H', 20, cell_format)
    worksheet.set_column('I:I', 50, details_format)
    
    writer.close()
    return output.getvalue()

def calculate_prognosis(df_db, df_meld):
    target_classes = ['U10', 'U12', 'U14']
    
    if not df_db.empty:
        db_filtered = df_db[df_db['Class'].str.contains('|'.join(target_classes), na=False)].copy()
        
        all_db_athletes = db_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg(
            Starts_All_DB=('Event', 'nunique'),
            ClubName=('ClubName', 'first'),
            Class=('Class', 'first')
        ).reset_index()
        
        valid_db = db_filtered[db_filtered['isValid'] == True]
        valid_athletes = valid_db.groupby(['FirstName', 'LastName', 'Yob']).agg(
            Starts_Bisher=('Event', 'nunique')
        ).reset_index()
        
        bisher_athletes = pd.merge(all_db_athletes, valid_athletes, on=['FirstName', 'LastName', 'Yob'], how='left')
        bisher_athletes['Starts_Bisher'] = bisher_athletes['Starts_Bisher'].fillna(0).astype(int)
    else:
        bisher_athletes = pd.DataFrame(columns=['FirstName', 'LastName', 'Yob', 'Starts_All_DB', 'Starts_Bisher', 'ClubName', 'Class'])

    if df_meld is not None and not df_meld.empty:
        meld_filtered = df_meld[df_meld['Class'].str.contains('|'.join(target_classes), na=False)].copy()
        meld_athletes = meld_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg(
            Starts_Neu=('Event', 'nunique'),
            ClubName_M=('ClubName', 'first'),
            Class_M=('Class', 'first')
        ).reset_index()
        
        prog_df = pd.merge(bisher_athletes, meld_athletes, on=['FirstName', 'LastName', 'Yob'], how='outer')
        prog_df['Starts_Bisher'] = prog_df['Starts_Bisher'].fillna(0).astype(int)
        prog_df['Starts_Neu'] = prog_df['Starts_Neu'].fillna(0).astype(int)
        prog_df['Starts_All_DB'] = prog_df['Starts_All_DB'].fillna(0).astype(int)
        
        prog_df['Class'] = prog_df['Class'].fillna(prog_df['Class_M'])
        prog_df['ClubName'] = prog_df['ClubName'].fillna(prog_df['ClubName_M'])
        prog_df = prog_df.drop(columns=['Class_M', 'ClubName_M'])
        
        prog_df['Medal_Starts'] = prog_df['Starts_Neu']
    else:
        prog_df = bisher_athletes.copy()
        prog_df['Starts_Neu'] = 0
        prog_df['Medal_Starts'] = prog_df['Starts_All_DB']
        if prog_df.empty: return pd.DataFrame()

    prog_df['Starts_Gesamt'] = prog_df['Starts_Bisher'] + prog_df['Starts_Neu']
    
    def medal_forecast(starts):
        if starts >= 3: return "🥇 Gold"
        elif starts == 2: return "🥈 Silber"
        elif starts == 1: return "🥉 Bronze"
        return "Keine"
        
    prog_df['Event-Medaille'] = prog_df['Medal_Starts'].apply(medal_forecast)
    prog_df['Prognose Gesamt'] = prog_df['Starts_Gesamt'].apply(
        lambda x: "✅ Wird qualifiziert (6+)" if x >= 6 else f"⏳ Es fehlen noch {6-x} Starts"
    )
    
    return prog_df

def get_winners_list(df):
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    
    if 'isValid' not in df_filtered.columns:
        df_filtered['isValid'] = df_filtered['Result'].apply(is_valid_result)
        
    valid_df = df_filtered[df_filtered['isValid'] == True].dropna(subset=['Result_Num'])
    
    winners = []
    for (event, age_class, gender), group in valid_df.groupby(['Event', 'Class', 'Gender']):
        if is_run_event(event):
            winner_row = group.loc[group['Result_Num'].idxmin()]
        else:
            winner_row = group.loc[group['Result_Num'].idxmax()]
        winners.append(winner_row)
        
    if winners:
        return pd.DataFrame(winners).sort_values(['Event', 'Class', 'Gender'])
    return pd.DataFrame()

def get_bestenliste(df):
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    
    if 'isValid' not in df_filtered.columns:
        df_filtered['isValid'] = df_filtered['Result'].apply(is_valid_result)
        
    valid_df = df_filtered[df_filtered['isValid'] == True].dropna(subset=['Result_Num'])
    
    pb_list = []
    for (event, a_class, gender, fname, lname, yob, club), group in valid_df.groupby(['Event', 'Class', 'Gender', 'FirstName', 'LastName', 'Yob', 'ClubName']):
        if is_run_event(event):
            best_idx = group['Result_Num'].idxmin()
        else:
            best_idx = group['Result_Num'].idxmax()
        pb_list.append(group.loc[best_idx])
        
    if not pb_list:
        return pd.DataFrame()
        
    pb_df = pd.DataFrame(pb_list)
    
    ranked_list = []
    for (event, a_class, gender), group in pb_df.groupby(['Event', 'Class', 'Gender']):
        sorted_group = group.sort_values(by='Result_Num', ascending=is_run_event(event)).copy()
        sorted_group['Rang'] = range(1, len(sorted_group) + 1)
        ranked_list.append(sorted_group)
        
    bestenliste_df = pd.concat(ranked_list)
    return bestenliste_df.sort_values(['Event', 'Class', 'Gender', 'Rang'])

def create_statistics_excel(stats_df, event_stats_df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    if not stats_df.empty:
        stats_df.to_excel(writer, index=False, sheet_name='Allgemeine_Statistik')
    if not event_stats_df.empty:
        event_stats_df.to_excel(writer, index=False, sheet_name='Disziplinen_Statistik')
        
    workbook = writer.book
    header_format = workbook.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1})
    
    for sheet_name in writer.sheets:
        worksheet = writer.sheets[sheet_name]
        df_to_format = stats_df if sheet_name == 'Allgemeine_Statistik' else event_stats_df
        for col_num, value in enumerate(df_to_format.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
            
    writer.close()
    return output.getvalue()

# --- DASHBOARD UI ---
st.title("🏆 Moderne Leichtathletik-Auswertung")

with st.sidebar:
    st.header("📤 1. Bisherige Ergebnisse (Gesamtsaison)")
    st.info("Hauptdatenbank: Für die Berechnung der gesamten Saison-Punkte.")
    file_ergebnisse = st.file_uploader("Saison-Ergebnisse", type=['csv'], key="res")
    if file_ergebnisse and st.button("💾 Saison-Ergebnisse speichern"):
        raw_df = load_and_clean_data(file_ergebnisse)
        if raw_df is not None:
            raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
            st.success("Ergebnisse gespeichert!")
            st.rerun()

    st.header("📤 2. Nennungen / Aktuelles Event")
    st.info("Für den Medaillenbedarf des heutigen Wettkampfes.")
    file_meldungen = st.file_uploader("Aktuelle Liste", type=['csv'], key="meld")
    if file_meldungen and st.button("💾 Aktuelle Liste speichern"):
        meld_df = load_and_clean_data(file_meldungen)
        if meld_df is not None:
            meld_df.to_sql('meldungen', conn, if_exists='replace', index=False)
            st.success("Meldungen gespeichert!")
            st.rerun()

    st.divider()
    if st.button("🗑️ Kompletten Speicher leeren"):
        if table_exists(conn, 'ergebnisse'): conn.execute("DROP TABLE ergebnisse")
        if table_exists(conn, 'meldungen'): conn.execute("DROP TABLE meldungen")
        st.rerun()

try:
    df_db = pd.DataFrame()
    if table_exists(conn, 'ergebnisse'):
        df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)
        if not df_db.empty:
            df_db['Result_Num'] = df_db['Result'].apply(parse_result_to_number)
            df_db['isValid'] = df_db['Result'].apply(is_valid_result)
            df_db['CupPoints'] = df_db.apply(calculate_cup_points, axis=1)
    
    df_meld = pd.DataFrame()
    if table_exists(conn, 'meldungen'):
        df_meld = pd.read_sql('SELECT * FROM meldungen', conn)

    if not df_db.empty or not df_meld.empty:
        st.subheader("🔍 Auswertung filtern")
        c1, c2, c3, c4 = st.columns(4)
        
        filter_basis = pd.concat([df_db, df_meld], ignore_index=True) if not df_db.empty and not df_meld.empty else (df_db if not df_db.empty else df_meld)
        
        with c1: f_search = st.text_input("Suchen (Name/Verein):", "")
        with c2: f_class = st.multiselect("Altersklasse:", sorted(filter_basis['Class'].dropna().unique().tolist()))
        with c3: f_gender = st.multiselect("Geschlecht:", sorted(filter_basis['Gender'].dropna().unique().tolist()))
        with c4: f_club = st.multiselect("Verein:", sorted(filter_basis['ClubName'].dropna().unique().tolist()))

        filtered_df = df_db.copy() if not df_db.empty else pd.DataFrame()
        if not filtered_df.empty:
            if f_class: filtered_df = filtered_df[filtered_df['Class'].isin(f_class)]
            if f_gender: filtered_df = filtered_df[filtered_df['Gender'].isin(f_gender)]
            if f_club: filtered_df = filtered_df[filtered_df['ClubName'].isin(f_club)]
            if f_search:
                filtered_df = filtered_df[
                    filtered_df['FirstName'].str.contains(f_search, case=False, na=False) |
                    filtered_df['LastName'].str.contains(f_search, case=False, na=False)
                ]

        # REITER ANGEPASST: 10 Tabs insgesamt
        tab_med, tab_zw, tab_prog, tab_cup, tab_win, tab_best, tab_grafiken, tab_stat, tab_vereine, tab_raw = st.tabs([
            "🏅 Event-Medaillen", "🏆 Zwischenstand", "🔮 Cup-Prognose", "📊 Cup-Wertung", "🥇 Einzelsieger", "📈 Bestenliste", "📊 Grafiken", "📉 Statistiken", "🏠 Vereine", "📋 Rohdaten"
        ])

        prog_df = calculate_prognosis(df_db, df_meld)
        if not prog_df.empty:
            if f_search:
                prog_df = prog_df[
                    prog_df['FirstName'].str.contains(f_search, case=False, na=False) |
                    prog_df['LastName'].str.contains(f_search, case=False, na=False) |
                    prog_df['ClubName'].str.contains(f_search, case=False, na=False)
                ]
            if f_class: prog_df = prog_df[prog_df['Class'].isin(f_class)]
            if f_club: prog_df = prog_df[prog_df['ClubName'].isin(f_club)]

        # --- REITER 1: EVENT-MEDAILLENBEDARF ---
        with tab_med:
            st.subheader("Übersicht: Event-Medaillenbedarf")
            st.info("Zeigt die Medaillen basierend auf den Nennungen für den aktuellen Wettkampf.")
            if not prog_df.empty:
                med_df = prog_df[prog_df['Medal_Starts'] > 0].copy()
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Starter im Event", len(med_df))
                c2.metric("🥇 Gold (3+ Starts)", len(med_df[med_df['Event-Medaille'] == "🥇 Gold"]))
                c3.metric("🥈 Silber (2 Starts)", len(med_df[med_df['Event-Medaille'] == "🥈 Silber"]))
                c4.metric("🥉 Bronze (1 Start)", len(med_df[med_df['Event-Medaille'] == "🥉 Bronze"]))

                cat_order = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2}
                med_df['Sort'] = med_df['Event-Medaille'].map(cat_order)
                med_df = med_df.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

                st.dataframe(med_df[['Event-Medaille', 'FirstName', 'LastName', 'Class', 'ClubName', 'Medal_Starts']], hide_index=True, width='stretch')

        # --- REITER 2: ZWISCHENSTAND STARTS ---
        with tab_zw:
            st.subheader("Aktueller Zwischenstand (Nur Athleten mit echten Leistungen)")
            st.info("Filtert Karteileichen (DNS, Leer) heraus. Zeigt alle an (U10, U12, U14), die bisher messbare Leistungen erbracht haben.")
            if not filtered_df.empty:
                target_classes = ['U10', 'U12', 'U14']
                valid_db = filtered_df[(filtered_df['isValid'] == True) & (filtered_df['Class'].str.contains('|'.join(target_classes), na=False))]
                
                if not valid_db.empty:
                    zwischen_df = valid_db.groupby(['FirstName', 'LastName', 'Yob']).agg(
                        Starts_Bisher=('Event', 'nunique'),
                        ClubName=('ClubName', 'first'),
                        Class=('Class', 'first')
                    ).reset_index()
                    
                    def z_medal(starts):
                        if starts >= 3: return "🥇 Gold"
                        elif starts == 2: return "🥈 Silber"
                        elif starts == 1: return "🥉 Bronze"
                        return "Keine"
                        
                    zwischen_df['Saison-Medaille'] = zwischen_df['Starts_Bisher'].apply(z_medal)
                    cat_order_z = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2}
                    zwischen_df['Sort'] = zwischen_df['Saison-Medaille'].map(cat_order_z)
                    zwischen_df = zwischen_df.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("🥇 Gold-Kurs", len(zwischen_df[zwischen_df['Saison-Medaille'] == "🥇 Gold"]))
                    c2.metric("🥈 Silber-Kurs", len(zwischen_df[zwischen_df['Saison-Medaille'] == "🥈 Silber"]))
                    c3.metric("🥉 Bronze-Kurs", len(zwischen_df[zwischen_df['Saison-Medaille'] == "🥉 Bronze"]))
                    
                    st.dataframe(zwischen_df[['Saison-Medaille', 'FirstName', 'LastName', 'Class', 'ClubName', 'Starts_Bisher']], hide_index=True, width='stretch')
                else:
                    st.info("Keine gültigen U10/U12/U14 Leistungen für einen Zwischenstand gefunden.")
            else:
                st.info("Lade die Saison-Ergebnisse hoch.")

        # --- REITER 3: CUP-PROGNOSE ---
        with tab_prog:
            st.subheader("Übersicht: Cup-Qualifikation (Saison: 6+ Starts)")
            if not prog_df.empty:
                qual_count = len(prog_df[prog_df['Starts_Gesamt'] >= 6])
                nah_dran_count = len(prog_df[(prog_df['Starts_Gesamt'] >= 4) & (prog_df['Starts_Gesamt'] < 6)])

                c1, c2 = st.columns(2)
                c1.metric("✅ Qualifiziert (6+ Starts)", qual_count)
                c2.metric("🟡 Nah dran (4 oder 5 Starts)", nah_dran_count)

                prog_df_sorted = prog_df.sort_values(by=['Starts_Gesamt', 'LastName'], ascending=[False, True])
                st.dataframe(prog_df_sorted[['Prognose Gesamt', 'FirstName', 'LastName', 'Class', 'ClubName', 'Starts_Bisher', 'Starts_Neu', 'Starts_Gesamt']], hide_index=True, width='stretch')

        # --- REITER 4: GESAMTWERTUNG CUP ---
        with tab_cup:
            if not filtered_df.empty:
                cup_df, valid_perfs_df, counted_indices = get_cup_data(filtered_df)
                if not cup_df.empty:
                    excel_data = create_excel_report(cup_df)
                    st.download_button(
                        label="📥 Cup-Wertung als formatierte Excel (.xlsx) herunterladen",
                        data=excel_data,
                        file_name="Cup_Gesamtwertung_Sortiert.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.dataframe(cup_df[['Status', 'Fortschritt', 'Class', 'Gender', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'EventDetails']], width='stretch', hide_index=True)
                else:
                    st.info("Die geladene Datei enthält keine gültigen Leistungen für die Cup-Wertung.")

        # --- REITER 5: EINZELSIEGER ---
        with tab_win:
            st.subheader("🏆 Einzelsieger der jeweiligen Bewerbe")
            st.info("Ermittelt automatisch den Athleten mit der absolut besten Leistung der Saison in seiner/ihrer Altersklasse und Disziplin.")
            if not filtered_df.empty:
                winners_df = get_winners_list(filtered_df)
                if not winners_df.empty:
                    st.dataframe(winners_df[['Event', 'Class', 'Gender', 'FirstName', 'LastName', 'ClubName', 'Result']], hide_index=True, width='stretch')
                    csv_win = winners_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button("📥 Siegerliste herunterladen", csv_win, "einzelsieger.csv", "text/csv")
                else:
                    st.warning("Keine gültigen Leistungen gefunden.")
            else:
                st.info("Lade die Saison-Ergebnisse hoch.")

        # --- REITER 6: BESTENLISTE (PB-Ranking) ---
        with tab_best:
            st.subheader("📈 Saison-Bestenliste (PB-Ranking)")
            st.info("Zeigt das vollständige Ranking aller Athleten anhand ihrer persönlichen Saisonbestleistung (PB).")
            if not filtered_df.empty:
                bestenliste_df = get_bestenliste(filtered_df)
                if not bestenliste_df.empty:
                    all_events = sorted(bestenliste_df['Event'].unique())
                    sel_events = st.multiselect("Nach Disziplin filtern:", all_events, default=[])
                    
                    disp_best = bestenliste_df
                    if sel_events:
                        disp_best = disp_best[disp_best['Event'].isin(sel_events)]
                        
                    st.dataframe(disp_best[['Event', 'Class', 'Gender', 'Rang', 'FirstName', 'LastName', 'ClubName', 'Result']], hide_index=True, width='stretch')
                    
                    csv_best = disp_best.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button("📥 Bestenliste (als CSV) herunterladen", csv_best, "saison_bestenliste.csv", "text/csv")
                else:
                    st.warning("Keine gültigen Leistungen gefunden.")
            else:
                st.info("Lade die Saison-Ergebnisse hoch.")

        # --- REITER 7: GRAFIKEN (Plotly) ---
        with tab_grafiken:
            st.subheader("📊 Interaktive Leistungsanalyse")
            if not filtered_df.empty:
                valid_grafik_df = filtered_df[filtered_df['isValid'] == True].dropna(subset=['Result_Num']).copy()
                if not valid_grafik_df.empty:
                    col_a, col_b = st.columns([1, 3])
                    
                    with col_a:
                        g_event = st.selectbox("Disziplin wählen:", sorted(valid_grafik_df['Event'].unique()))
                        plot_type = st.radio("Grafiktyp:", ["Boxplot (Verteilung)", "Scatter (Einzelwerte)"])
                        
                    with col_b:
                        plot_df = valid_grafik_df[valid_grafik_df['Event'] == g_event]
                        if plot_type == "Boxplot (Verteilung)":
                            fig = px.box(
                                plot_df, x="Class", y="Result_Num", color="Gender", points="all",
                                hover_data=["FirstName", "LastName", "ClubName", "Result"],
                                title=f"Ergebnisverteilung für {g_event}",
                                labels={"Result_Num": "Leistung (Sek/m)", "Class": "Altersklasse"}
                            )
                        else:
                            fig = px.scatter(
                                plot_df, x="Class", y="Result_Num", color="Gender",
                                hover_data=["FirstName", "LastName", "ClubName", "Result"],
                                title=f"Alle Einzelwerte: {g_event}",
                                labels={"Result_Num": "Leistung (Sek/m)", "Class": "Altersklasse"}
                            )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Keine numerischen Ergebnisse für Grafiken vorhanden.")
            else:
                st.info("Bitte Saison-Ergebnisse laden.")

        # --- REITER 8: STATISTIKEN ---
        with tab_stat:
            st.subheader("📉 Detaillierte Statistiken")
            if not filtered_df.empty:
                valid_stats_df = filtered_df[filtered_df['isValid'] == True].dropna(subset=['Result_Num'])
                if not valid_stats_df.empty:
                    
                    stats_data = []
                    for (c_class, c_gender), group in valid_stats_df.groupby(['Class', 'Gender']):
                        num_athletes = len(group.groupby(['FirstName', 'LastName', 'Yob']))
                        num_clubs = group['ClubName'].nunique()
                        num_results = len(group)
                        stats_data.append({
                            'Altersklasse': c_class, 'Geschlecht': c_gender,
                            'Teilnehmer': num_athletes, 'Vereine': num_clubs, 'Erbrachte Leistungen': num_results
                        })
                    
                    stats_df_export = pd.DataFrame(stats_data).sort_values(['Altersklasse', 'Geschlecht'])
                    
                    event_stats_data = []
                    for (c_class, c_gender, c_event), group in valid_stats_df.groupby(['Class', 'Gender', 'Event']):
                        is_run = is_run_event(c_event)
                        best_res = group['Result_Num'].min() if is_run else group['Result_Num'].max()
                        worst_res = group['Result_Num'].max() if is_run else group['Result_Num'].min()
                        med_res = group['Result_Num'].median()
                        
                        event_stats_data.append({
                            'Altersklasse': c_class, 'Geschlecht': c_gender, 'Disziplin': c_event,
                            'Anzahl Leistungen': len(group),
                            'Beste Leistung': round(best_res, 2),
                            'Median': round(med_res, 2),
                            'Schlechteste Leistung': round(worst_res, 2)
                        })
                        
                    event_stats_df_export = pd.DataFrame(event_stats_data).sort_values(['Altersklasse', 'Geschlecht', 'Disziplin'])
                    
                    excel_stats = create_statistics_excel(stats_df_export, event_stats_df_export)
                    st.download_button(
                        label="📥 Statistiken als formatierte Excel (.xlsx) herunterladen",
                        data=excel_stats,
                        file_name="Auswertung_Statistiken.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Allgemeine Teilnehmer-Übersicht:**")
                        st.dataframe(stats_df_export, hide_index=True)
                    with c2:
                        st.write("**Statistiken pro Disziplin:**")
                        st.dataframe(event_stats_df_export, hide_index=True)
                else:
                    st.info("Keine gültigen Leistungen für Statistiken gefunden.")
            else:
                st.info("Bitte Saison-Ergebnisse laden.")

        # --- NEU: REITER 9: VEREINE ---
        with tab_vereine:
            st.subheader("🏠 Allgemeine Vereinsübersicht")
            st.info("Übersicht aller teilnehmenden Vereine (gemeldete Athleten und tatsächliche Starts).")
            if not filtered_df.empty:
                vereine_data = []
                for club, group in filtered_df.groupby('ClubName'):
                    num_athletes = len(group.groupby(['FirstName', 'LastName', 'Yob']))
                    males = len(group[group['Gender'] == 'M'].groupby(['FirstName', 'LastName', 'Yob']))
                    females = len(group[group['Gender'] == 'W'].groupby(['FirstName', 'LastName', 'Yob']))
                    
                    num_nennungen = len(group)
                    num_starts = len(group[group['isValid'] == True])
                    
                    vereine_data.append({
                        'Verein': club,
                        'Athleten (Gemeldet)': num_athletes,
                        'Männlich': males,
                        'Weiblich': females,
                        'Nennungen (Gesamt)': num_nennungen,
                        'Echte Starts (Gültig)': num_starts
                    })
                
                vereine_df_export = pd.DataFrame(vereine_data).sort_values('Athleten (Gemeldet)', ascending=False)
                
                # Tabelle anzeigen
                st.dataframe(vereine_df_export, hide_index=True, width='stretch')
                
                # CSV Export
                csv_vereine = vereine_df_export.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Vereinsübersicht (CSV) herunterladen", csv_vereine, "vereinsuebersicht.csv", "text/csv")
                
                # Zwei Pie-Charts für visuelle Aufbereitung
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    fig_vereine = px.pie(vereine_df_export, values='Athleten (Gemeldet)', names='Verein', title='Gemeldete Athleten nach Vereinen')
                    st.plotly_chart(fig_vereine, use_container_width=True)
                with col_chart2:
                    fig_starts = px.pie(vereine_df_export, values='Echte Starts (Gültig)', names='Verein', title='Erbrachte Starts nach Vereinen')
                    st.plotly_chart(fig_starts, use_container_width=True)
            else:
                st.info("Bitte Saison-Ergebnisse laden.")

        # --- REITER 10: ROHDATEN ---
        with tab_raw:
            st.write("Ergebnisse in den Datenbanken:")
            if not df_db.empty:
                st.write("**Hauptdatenbank (Saison-Ergebnisse):**")
                st.dataframe(filtered_df, width='stretch')
            if not df_meld.empty:
                st.write("**Aktuelle Liste (Meldungen):**")
                st.dataframe(df_meld, width='stretch')

    else:
        st.info("Bitte lade CSV-Dateien in der Seitenleiste hoch, um zu beginnen.")

except Exception as e:
    st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
