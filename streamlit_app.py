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

        # 1. Spaltennamen von Leerzeichen befreien
        df.columns = df.columns.str.strip()

        # 2. Automatische Übersetzung deutscher Spalten in das interne System
        rename_map = {
            'Klasse': 'Class', 'Altersklasse': 'Class', 'AK': 'Class',
            'Verein': 'ClubName', 'Club': 'ClubName',
            'Vorname': 'FirstName', 
            'Nachname': 'LastName', 'Name': 'LastName',
            'Jahrgang': 'Yob', 'JG': 'Yob',
            'Bewerb': 'Event', 'Disziplin': 'Event',
            'Ergebnis': 'Result', 'Leistung': 'Result', 'Zeit': 'Result', 'Weite': 'Result',
            'Geschlecht': 'Gender', 'M/W': 'Gender'
        }
        for ger, eng in rename_map.items():
            if ger in df.columns and eng not in df.columns:
                df = df.rename(columns={ger: eng})

        # 3. Sicherheitsnetz: Falls Spalten komplett fehlen, Platzhalter setzen, damit nichts abstürzt!
        required_cols = {
            'Class': 'U12', 'ClubName': 'Unbekannt', 'FirstName': 'Unbekannt',
            'LastName': 'Unbekannt', 'Yob': 2010, 'Event': '60M', 'Gender': 'M'
        }
        for col, default_val in required_cols.items():
            if col not in df.columns:
                df[col] = default_val

        # 4. Datenbereinigung
        if 'Event' in df.columns:
            df['Event'] = df['Event'].astype(str).str.upper().str.strip()
            df['Event'] = df['Event'].replace('WEZ', 'WEI')
            
        if 'Jahr' in df.columns:
            df['Jahr'] = df['Jahr'].fillna('Unbekannt').astype(str)
            df['Jahr'] = df['Jahr'].replace('0.0', 'Unbekannt').replace('0', 'Unbekannt')
            df['Jahr'] = df['Jahr'].apply(lambda x: x.split('.')[0] if '.' in str(x) else x)
            
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
    
    group_cols = ['FirstName', 'LastName', 'Yob', 'ClubName', 'Gender', 'Class']
    if 'Jahr' in valid_df.columns:
        group_cols.append('Jahr')
        
    for group_keys, group in valid_df.groupby(group_cols):
        if 'Jahr' in valid_df.columns:
            fname, lname, yob, club, gender, a_class, jahr = group_keys
        else:
            fname, lname, yob, club, gender, a_class = group_keys
            jahr = "Aktuell"
            
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
            
        result_dict = {
            'Status': status, 'Fortschritt': progress, 'Class': a_class, 'Gender': gender,
            'FirstName': fname, 'LastName': lname, 'ClubName': club,
            'CupPoints': int(total_points), 'EventDetails': '\n'.join(details), 
            '_status_sort': status_sort
        }
        if 'Jahr' in valid_df.columns:
            result_dict['Jahr'] = jahr
            
        rankings.append(result_dict)
        
    ranking_df = pd.DataFrame(rankings)
    if not ranking_df.empty:
        sort_cols = ['_status_sort', 'Class', 'Gender', 'CupPoints']
        if 'Jahr' in valid_df.columns: sort_cols = ['Jahr'] + sort_cols
        ranking_df = ranking_df.sort_values(sort_cols, ascending=[False if c == 'Jahr' else (True if c != 'CupPoints' else False) for c in sort_cols]).drop(columns=['_status_sort'])
    return ranking_df, valid_df, all_counted_indices

def create_excel_report(cup_df):
    output = BytesIO()
    
    sort_cols = ['Class', 'Gender', 'CupPoints']
    if 'Jahr' in cup_df.columns: sort_cols = ['Jahr'] + sort_cols
    
    df_sorted = cup_df.sort_values(by=sort_cols, ascending=[False if c == 'Jahr' else (True if c != 'CupPoints' else False) for c in sort_cols])
    
    cols_to_keep = ['Class', 'Gender', 'Status', 'Fortschritt', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'EventDetails']
    if 'Jahr' in df_sorted.columns: cols_to_keep.insert(0, 'Jahr')
    
    df_export = df_sorted[cols_to_keep].copy()
    
    rename_dict = {
        'Class': 'Altersklasse', 'Gender': 'Geschlecht', 'Status': 'Qualifikation',
        'Fortschritt': 'Starts (gewertet)', 'CupPoints': 'Punkte', 'FirstName': 'Vorname',
        'LastName': 'Nachname', 'ClubName': 'Verein', 'EventDetails': 'Details der Leistungen (⭐ in Wertung)'
    }
    df_export = df_export.rename(columns=rename_dict)
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
        
    offset = 1 if 'Jahr' in df_export.columns else 0
    if offset: worksheet.set_column(0, 0, 8, cell_format)
    worksheet.set_column(0+offset, 1+offset, 12, cell_format)
    worksheet.set_column(2+offset, 2+offset, 18, cell_format)
    worksheet.set_column(3+offset, 3+offset, 15, cell_format)
    worksheet.set_column(4+offset, 4+offset, 12, points_format)
    worksheet.set_column(5+offset, 6+offset, 15, cell_format)
    worksheet.set_column(7+offset, 7+offset, 20, cell_format)
    worksheet.set_column(8+offset, 8+offset, 50, details_format)
    
    writer.close()
    return output.getvalue()

def calculate_prognosis(df_db, df_meld):
    target_classes = ['U10', 'U12', 'U14']
    
    if not df_db.empty:
        db_filtered = df_db[df_db['Class'].str.contains('|'.join(target_classes), na=False)].copy()
        all_db_athletes = db_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg(Starts_All_DB=('Event', 'nunique'), ClubName=('ClubName', 'first'), Class=('Class', 'first')).reset_index()
        valid_db = db_filtered[db_filtered['isValid'] == True]
        valid_athletes = valid_db.groupby(['FirstName', 'LastName', 'Yob']).agg(Starts_Bisher=('Event', 'nunique')).reset_index()
        bisher_athletes = pd.merge(all_db_athletes, valid_athletes, on=['FirstName', 'LastName', 'Yob'], how='left')
        bisher_athletes['Starts_Bisher'] = bisher_athletes['Starts_Bisher'].fillna(0).astype(int)
    else:
        bisher_athletes = pd.DataFrame(columns=['FirstName', 'LastName', 'Yob', 'Starts_All_DB', 'Starts_Bisher', 'ClubName', 'Class'])

    if df_meld is not None and not df_meld.empty:
        meld_filtered = df_meld[df_meld['Class'].str.contains('|'.join(target_classes), na=False)].copy()
        meld_athletes = meld_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg(Starts_Neu=('Event', 'nunique'), ClubName_M=('ClubName', 'first'), Class_M=('Class', 'first')).reset_index()
        
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
    
    group_cols = ['Event', 'Class', 'Gender']
    if 'Jahr' in valid_df.columns:
        group_cols = ['Jahr'] + group_cols
        
    winners = []
    for keys, group in valid_df.groupby(group_cols):
        event = keys[0] if 'Jahr' not in valid_df.columns else keys[1]
        if is_run_event(event): winner_row = group.loc[group['Result_Num'].idxmin()]
        else: winner_row = group.loc[group['Result_Num'].idxmax()]
        winners.append(winner_row)
        
    if winners:
        sort_cols = ['Event', 'Class', 'Gender']
        if 'Jahr' in valid_df.columns: sort_cols = ['Jahr'] + sort_cols
        return pd.DataFrame(winners).sort_values(sort_cols, ascending=[False if c == 'Jahr' else True for c in sort_cols])
    return pd.DataFrame()

def get_bestenliste(df):
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    
    if 'isValid' not in df_filtered.columns:
        df_filtered['isValid'] = df_filtered['Result'].apply(is_valid_result)
        
    valid_df = df_filtered[df_filtered['isValid'] == True].dropna(subset=['Result_Num'])
    
    pb_group_cols = ['Event', 'Class', 'Gender', 'FirstName', 'LastName', 'Yob', 'ClubName']
    if 'Jahr' in valid_df.columns: pb_group_cols.append('Jahr')
        
    pb_list = []
    for keys, group in valid_df.groupby(pb_group_cols):
        event = keys[0]
        if is_run_event(event): best_idx = group['Result_Num'].idxmin()
        else: best_idx = group['Result_Num'].idxmax()
        pb_list.append(group.loc[best_idx])
        
    if not pb_list: return pd.DataFrame()
    pb_df = pd.DataFrame(pb_list)
    
    rank_group_cols = ['Event', 'Class', 'Gender']
    if 'Jahr' in pb_df.columns: rank_group_cols = ['Jahr'] + rank_group_cols
        
    ranked_list = []
    for keys, group in pb_df.groupby(rank_group_cols):
        event = keys[0] if 'Jahr' not in pb_df.columns else keys[1]
        sorted_group = group.sort_values(by='Result_Num', ascending=is_run_event(event)).copy()
        sorted_group['Rang'] = range(1, len(sorted_group) + 1)
        ranked_list.append(sorted_group)
        
    bestenliste_df = pd.concat(ranked_list)
    sort_cols = ['Event', 'Class', 'Gender', 'Rang']
    if 'Jahr' in bestenliste_df.columns: sort_cols = ['Jahr'] + sort_cols
    return bestenliste_df.sort_values(sort_cols, ascending=[False if c == 'Jahr' else True for c in sort_cols])

def create_statistics_excel(stats_df, event_stats_df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    if not stats_df.empty: stats_df.to_excel(writer, index=False, sheet_name='Allgemeine_Statistik')
    if not event_stats_df.empty: event_stats_df.to_excel(writer, index=False, sheet_name='Disziplinen_Statistik')
        
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
        filter_basis = pd.concat([df_db, df_meld], ignore_index=True) if not df_db.empty and not df_meld.empty else (df_db if not df_db.empty else df_meld)
        
        has_year = 'Jahr' in filter_basis.columns
        cols = st.columns(5) if has_year else st.columns(4)
        
        f_year = []
        if has_year:
            with cols[0]: f_year = st.multiselect("Jahr:", sorted(filter_basis['Jahr'].dropna().unique().tolist(), reverse=True))
            c_idx = 1
        else:
            c_idx = 0
            
        with cols[c_idx]: f_search = st.text_input("Suchen (Name/Verein):", "")
        with cols[c_idx+1]: f_class = st.multiselect("Altersklasse:", sorted(filter_basis['Class'].dropna().unique().tolist()))
        with cols[c_idx+2]: f_gender = st.multiselect("Geschlecht:", sorted(filter_basis['Gender'].dropna().unique().tolist()))
        with cols[c_idx+3]: f_club = st.multiselect("Verein:", sorted(filter_basis['ClubName'].dropna().unique().tolist()))

        filtered_df = df_db.copy() if not df_db.empty else pd.DataFrame()
        if not filtered_df.empty:
            if has_year and f_year: filtered_df = filtered_df[filtered_df['Jahr'].isin(f_year)]
            if f_class: filtered_df = filtered_df[filtered_df['Class'].isin(f_class)]
            if f_gender: filtered_df = filtered_df[filtered_df['Gender'].isin(f_gender)]
            if f_club: filtered_df = filtered_df[filtered_df['ClubName'].isin(f_club)]
            if f_search:
                filtered_df = filtered_df[
                    filtered_df['FirstName'].str.contains(f_search, case=False, na=False) |
                    filtered_df['LastName'].str.contains(f_search, case=False, na=False)
                ]

        tab_med, tab_zw, tab_prog, tab_cup, tab_win, tab_best, tab_grafiken, tab_stat, tab_vereine, tab_jahr, tab_dyn, tab_raw = st.tabs([
            "🏅 Event-Medaillen", "🏆 Zwischenstand", "🔮 Prognose", "📊 Cup-Wertung", "🥇 Einzelsieger", "📈 Bestenliste", "📊 Grafiken", "📉 Statistiken", "🏠 Vereine", "📅 Jahresvergleich", "⚙️ Dynamisch", "📋 Rohdaten"
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
            if has_year and f_year and 'Jahr' in prog_df.columns: 
                prog_df = prog_df[prog_df['Jahr'].isin(f_year)]

        with tab_med:
            st.subheader("Übersicht: Event-Medaillenbedarf")
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

        with tab_zw:
            st.subheader("Aktueller Zwischenstand (U10-U14, echte Leistungen)")
            if not filtered_df.empty:
                target_classes = ['U10', 'U12', 'U14']
                valid_db = filtered_df[(filtered_df['isValid'] == True) & (filtered_df['Class'].str.contains('|'.join(target_classes), na=False))]
                if not valid_db.empty:
                    zwischen_df = valid_db.groupby(['FirstName', 'LastName', 'Yob', 'ClubName', 'Class'] + (['Jahr'] if has_year else [])).agg(
                        Starts_Bisher=('Event', 'nunique')
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
                    
                    disp_cols = ['Saison-Medaille', 'FirstName', 'LastName', 'Class', 'ClubName', 'Starts_Bisher']
                    if has_year: disp_cols.insert(1, 'Jahr')
                    st.dataframe(zwischen_df[disp_cols], hide_index=True, width='stretch')

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

        with tab_cup:
            if not filtered_df.empty:
                cup_df, valid_perfs_df, counted_indices = get_cup_data(filtered_df)
                if not cup_df.empty:
                    excel_data = create_excel_report(cup_df)
                    st.download_button(label="📥 Cup-Wertung als formatierte Excel (.xlsx) herunterladen", data=excel_data, file_name="Cup_Gesamtwertung_Sortiert.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    disp_cols_c = ['Status', 'Fortschritt', 'Class', 'Gender', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'EventDetails']
                    if has_year: disp_cols_c.insert(0, 'Jahr')
                    st.dataframe(cup_df[disp_cols_c], width='stretch', hide_index=True)

        with tab_win:
            st.subheader("🏆 Einzelsieger der jeweiligen Bewerbe")
            if not filtered_df.empty:
                winners_df = get_winners_list(filtered_df)
                if not winners_df.empty:
                    disp_cols_w = ['Event', 'Class', 'Gender', 'FirstName', 'LastName', 'ClubName', 'Result']
                    if has_year: disp_cols_w.insert(0, 'Jahr')
                    st.dataframe(winners_df[disp_cols_w], hide_index=True, width='stretch')
                    st.download_button("📥 Siegerliste herunterladen", winners_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig'), "einzelsieger.csv", "text/csv")

        with tab_best:
            st.subheader("📈 Saison-Bestenliste (PB-Ranking)")
            if not filtered_df.empty:
                bestenliste_df = get_bestenliste(filtered_df)
                if not bestenliste_df.empty:
                    all_events = sorted(bestenliste_df['Event'].unique())
                    sel_events = st.multiselect("Nach Disziplin filtern:", all_events, default=[])
                    disp_best = bestenliste_df[bestenliste_df['Event'].isin(sel_events)] if sel_events else bestenliste_df
                    disp_cols_b = ['Event', 'Class', 'Gender', 'Rang', 'FirstName', 'LastName', 'ClubName', 'Result']
                    if has_year: disp_cols_b.insert(0, 'Jahr')
                    st.dataframe(disp_best[disp_cols_b], hide_index=True, width='stretch')
                    st.download_button("📥 Bestenliste herunterladen", disp_best.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig'), "saison_bestenliste.csv", "text/csv")

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
                            fig = px.box(plot_df, x="Class", y="Result_Num", color="Gender", points="all", hover_data=["FirstName", "LastName", "ClubName", "Result"], title=f"Ergebnisverteilung für {g_event}", labels={"Result_Num": "Leistung", "Class": "Altersklasse"})
                        else:
                            fig = px.scatter(plot_df, x="Class", y="Result_Num", color="Gender", hover_data=["FirstName", "LastName", "ClubName", "Result"], title=f"Alle Einzelwerte: {g_event}", labels={"Result_Num": "Leistung", "Class": "Altersklasse"})
                        st.plotly_chart(fig, use_container_width=True)

        with tab_stat:
            st.subheader("📉 Detaillierte Statistiken")
            if not filtered_df.empty:
                valid_stats_df = filtered_df[filtered_df['isValid'] == True].dropna(subset=['Result_Num'])
                if not valid_stats_df.empty:
                    stats_group_cols = ['Class', 'Gender']
                    if has_year: stats_group_cols = ['Jahr'] + stats_group_cols
                    
                    stats_data = []
                    for keys, group in valid_stats_df.groupby(stats_group_cols):
                        num_athletes = len(group.groupby(['FirstName', 'LastName', 'Yob']))
                        stats_dict = {'Altersklasse': keys[0] if not has_year else keys[1], 'Geschlecht': keys[1] if not has_year else keys[2], 'Teilnehmer': num_athletes, 'Vereine': group['ClubName'].nunique(), 'Starts': len(group)}
                        if has_year: stats_dict['Jahr'] = keys[0]
                        stats_data.append(stats_dict)
                    
                    stats_df_export = pd.DataFrame(stats_data).sort_values(stats_group_cols)
                    
                    event_stats_data = []
                    ev_group_cols = ['Class', 'Gender', 'Event']
                    if has_year: ev_group_cols = ['Jahr'] + ev_group_cols
                    for keys, group in valid_stats_df.groupby(ev_group_cols):
                        ev = keys[2] if not has_year else keys[3]
                        is_run = is_run_event(ev)
                        best_res = group['Result_Num'].min() if is_run else group['Result_Num'].max()
                        worst_res = group['Result_Num'].max() if is_run else group['Result_Num'].min()
                        med_res = group['Result_Num'].median()
                        ev_dict = {'Altersklasse': keys[0] if not has_year else keys[1], 'Geschlecht': keys[1] if not has_year else keys[2], 'Disziplin': ev, 'Starts': len(group), 'Best': round(best_res,2), 'Median': round(med_res,2), 'Worst': round(worst_res,2)}
                        if has_year: ev_dict['Jahr'] = keys[0]
                        event_stats_data.append(ev_dict)
                        
                    event_stats_df_export = pd.DataFrame(event_stats_data).sort_values(ev_group_cols)
                    
                    st.download_button("📥 Statistiken (Excel) herunterladen", create_statistics_excel(stats_df_export, event_stats_df_export), "Statistiken.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    c1, c2 = st.columns(2)
                    with c1: st.dataframe(stats_df_export, hide_index=True)
                    with c2: st.dataframe(event_stats_df_export, hide_index=True)

        with tab_vereine:
            st.subheader("🏠 Allgemeine Vereinsübersicht")
            if not filtered_df.empty:
                v_group_cols = ['ClubName']
                if has_year: v_group_cols = ['Jahr', 'ClubName']
                vereine_data = []
                for keys, group in filtered_df.groupby(v_group_cols):
                    club = keys if not has_year else keys[1]
                    num_athletes = len(group.groupby(['FirstName', 'LastName', 'Yob']))
                    males = len(group[group['Gender'] == 'M'].groupby(['FirstName', 'LastName', 'Yob']))
                    females = len(group[group['Gender'] == 'W'].groupby(['FirstName', 'LastName', 'Yob']))
                    v_dict = {'Verein': club, 'Athleten (Gemeldet)': num_athletes, 'Männlich': males, 'Weiblich': females, 'Nennungen': len(group), 'Gültige Starts': len(group[group['isValid'] == True])}
                    if has_year: v_dict['Jahr'] = keys[0]
                    vereine_data.append(v_dict)
                
                v_sort = ['Athleten (Gemeldet)'] if not has_year else ['Jahr', 'Athleten (Gemeldet)']
                vereine_df_export = pd.DataFrame(vereine_data).sort_values(v_sort, ascending=[False] if not has_year else [False, False])
                st.dataframe(vereine_df_export, hide_index=True, width='stretch')
                
                if not has_year or len(filtered_df['Jahr'].unique()) == 1:
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1: st.plotly_chart(px.pie(vereine_df_export, values='Athleten (Gemeldet)', names='Verein', title='Gemeldete Athleten'), use_container_width=True)
                    with col_chart2: st.plotly_chart(px.pie(vereine_df_export, values='Gültige Starts', names='Verein', title='Erbrachte Starts'), use_container_width=True)

        with tab_jahr:
            st.subheader("📅 Jahresvergleich (Teilnehmer pro Verein)")
            if not filtered_df.empty and has_year:
                st.info("Jeder Athlet (Name & Jahrgang) wird pro Jahr nur 1x gezählt. Filter in der Seitenleiste (z.B. Altersklasse) werden hier berücksichtigt!")
                
                def count_unique_athletes(group):
                    return len(group.drop_duplicates(subset=['FirstName', 'LastName', 'Yob']))
                    
                # Gefilterte Daten nutzen
                jahres_data = filtered_df.groupby(['Jahr', 'ClubName']).apply(count_unique_athletes)
                
                # Sicherstellen, dass wir einen schönen DataFrame bekommen (Workaround für Pandas Verhalten bei Apply)
                if isinstance(jahres_data, pd.Series):
                    jahres_data = jahres_data.reset_index(name='Athleten')
                elif isinstance(jahres_data, pd.DataFrame):
                    jahres_data = jahres_data.reset_index()
                    # Letzte Spalte umbenennen, falls Pandas sie '0' nennt
                    if 0 in jahres_data.columns:
                        jahres_data = jahres_data.rename(columns={0: 'Athleten'})
                
                if not jahres_data.empty and 'Athleten' in jahres_data.columns:
                    pivot_df = jahres_data.pivot(index='ClubName', columns='Jahr', values='Athleten').fillna(0).astype(int)
                    pivot_df['Gesamt (Alle Jahre)'] = pivot_df.sum(axis=1)
                    pivot_df = pivot_df.sort_values('Gesamt (Alle Jahre)', ascending=False).reset_index()
                    
                    st.dataframe(pivot_df, hide_index=True, width='stretch')
                    st.download_button("📥 Jahresvergleich herunterladen", pivot_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig'), "jahresvergleich_vereine.csv", "text/csv")
                    
                    fig_jahr = px.bar(jahres_data, x='ClubName', y='Athleten', color='Jahr', barmode='group', title="Teilnehmerzahlen über die Jahre (inkl. aktiver Filter)")
                    st.plotly_chart(fig_jahr, use_container_width=True)
                else:
                    st.warning("Keine Daten zum Vergleichen gefunden.")
            else:
                st.warning("Die hochgeladenen Daten enthalten keine Jahres-Spalte oder die aktiven Filter haben alle Daten ausgeblendet.")

        with tab_dyn:
            st.subheader("⚙️ Dynamischer Auswertungs-Baukasten")
            st.info("Baue dir deine eigene Tabelle! Wähle, wonach du gruppieren möchtest und welcher Wert berechnet werden soll.")
            if not filtered_df.empty:
                valid_cols_for_grouping = [c for c in filtered_df.columns if c not in ['Result', 'Result_Num', 'CupPoints', 'isValid', 'NotCompetitive']]
                col_d1, col_d2 = st.columns(2)
                with col_d1: sel_groups = st.multiselect("Gruppieren nach (Zeilen):", valid_cols_for_grouping, default=["ClubName"] if "ClubName" in valid_cols_for_grouping else [])
                with col_d2: sel_calc = st.selectbox("Berechnung (Werte):", ["Anzahl Starts (Gesamt)", "Anzahl eindeutiger Athleten", "Summe Cup-Punkte", "Durchschnitt Cup-Punkte"])
                
                if sel_groups:
                    dyn_df = filtered_df.copy()
                    if sel_calc == "Anzahl Starts (Gesamt)":
                        result_df = dyn_df.groupby(sel_groups).size().reset_index(name='Starts')
                    elif sel_calc == "Anzahl eindeutiger Athleten":
                        def count_unique(x): return len(x.drop_duplicates(subset=['FirstName', 'LastName', 'Yob']))
                        result_df = dyn_df.groupby(sel_groups).apply(count_unique)
                        if isinstance(result_df, pd.Series): result_df = result_df.reset_index(name='Athleten')
                        elif isinstance(result_df, pd.DataFrame): 
                            result_df = result_df.reset_index()
                            if 0 in result_df.columns: result_df = result_df.rename(columns={0: 'Athleten'})
                    elif sel_calc == "Summe Cup-Punkte":
                        result_df = dyn_df.groupby(sel_groups)['CupPoints'].sum().reset_index(name='Punkte (Summe)')
                    elif sel_calc == "Durchschnitt Cup-Punkte":
                        result_df = dyn_df[dyn_df['CupPoints'] > 0].groupby(sel_groups)['CupPoints'].mean().round(1).reset_index(name='Punkte (Ø)')

                    if not result_df.empty and result_df.columns[-1] in result_df.columns:
                        st.dataframe(result_df.sort_values(result_df.columns[-1], ascending=False), hide_index=True, width='stretch')
                        if len(sel_groups) == 1:
                            fig_dyn = px.bar(result_df, x=sel_groups[0], y=result_df.columns[-1], title=f"{sel_calc} nach {sel_groups[0]}")
                            st.plotly_chart(fig_dyn, use_container_width=True)
                else:
                    st.warning("Bitte mindestens eine Spalte zum Gruppieren auswählen.")

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
