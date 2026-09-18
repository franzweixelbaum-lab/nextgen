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

def calculate_prognosis(df_db, df_meld):
    """Kombiniert bestehende Ergebnisse mit Meldungen."""
    target_classes = ['U10', 'U12', 'U14']
    
    if not df_db.empty:
        db_filtered = df_db[df_db['Class'].str.contains('|'.join(target_classes), na=False)]
        bisher_athletes = db_filtered[db_filtered['isValid'] == True].groupby(['FirstName', 'LastName', 'Yob']).agg(
            Starts_Bisher=('Event', 'nunique'),
            ClubName=('ClubName', 'first'),
            Class=('Class', 'first')
        ).reset_index()
    else:
        bisher_athletes = pd.DataFrame(columns=['FirstName', 'LastName', 'Yob', 'Starts_Bisher', 'ClubName', 'Class'])

    if df_meld is not None and not df_meld.empty:
        meld_filtered = df_meld[df_meld['Class'].str.contains('|'.join(target_classes), na=False)]
        meld_athletes = meld_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg(
            Starts_Neu=('Event', 'nunique'),
            ClubName_M=('ClubName', 'first'),
            Class_M=('Class', 'first')
        ).reset_index()
        
        prog_df = pd.merge(bisher_athletes, meld_athletes, on=['FirstName', 'LastName', 'Yob'], how='outer')
        prog_df['Starts_Bisher'] = prog_df['Starts_Bisher'].fillna(0).astype(int)
        prog_df['Starts_Neu'] = prog_df['Starts_Neu'].fillna(0).astype(int)
        
        prog_df['Class'] = prog_df['Class'].fillna(prog_df['Class_M'])
        prog_df['ClubName'] = prog_df['ClubName'].fillna(prog_df['ClubName_M'])
        prog_df = prog_df.drop(columns=['Class_M', 'ClubName_M'])
        
        # Für Medaillen zählen nur die neuen Starts
        prog_df['Medal_Starts'] = prog_df['Starts_Neu']
    else:
        prog_df = bisher_athletes.copy()
        prog_df['Starts_Neu'] = 0
        # Ohne Meldeliste zählen die bisherigen Starts für die Medaille (z.B. wenn man nur 1 Event hochgeladen hat)
        prog_df['Medal_Starts'] = prog_df['Starts_Bisher']
        
        if prog_df.empty:
            return pd.DataFrame()

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

# --- DASHBOARD UI ---
st.title("🏆 Moderne Leichtathletik-Auswertung")

with st.sidebar:
    st.header("📤 1. Bisherige Ergebnisse")
    st.info("Hauptdatenbank: Lädt die tatsächlich erbrachten Ergebnisse.")
    file_ergebnisse = st.file_uploader("Ergebnisse (results.csv)", type=['csv'], key="res")
    if file_ergebnisse and st.button("💾 Bisherige Ergebnisse speichern"):
        raw_df = load_and_clean_data(file_ergebnisse)
        if raw_df is not None:
            raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
            st.success("Ergebnisse gespeichert!")
            st.rerun()

    st.header("📤 2. Nennungen (Optional)")
    st.info("Optional: Lade eine Meldeliste für einen kommenden Wettkampf hoch, um den neuen Medaillenbedarf zu simulieren.")
    file_meldungen = st.file_uploader("Nennungen/Meldungen", type=['csv'], key="meld")
    if file_meldungen and st.button("💾 Meldungen für Prognose speichern"):
        meld_df = load_and_clean_data(file_meldungen)
        if meld_df is not None:
            meld_df.to_sql('meldungen', conn, if_exists='replace', index=False)
            st.success("Meldungen gespeichert!")
            st.rerun()

    st.divider()
    if st.button("🗑️ Kompletten Speicher leeren"):
        conn.execute("DROP TABLE IF EXISTS ergebnisse")
        conn.execute("DROP TABLE IF EXISTS meldungen")
        st.rerun()

try:
    # Live-Berechnung bei jedem Laden
    df_db = pd.DataFrame()
    try:
        df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)
        if not df_db.empty:
            df_db['Result_Num'] = df_db['Result'].apply(parse_result_to_number)
            df_db['isValid'] = df_db['Result'].apply(is_valid_result)
            df_db['CupPoints'] = df_db.apply(calculate_cup_points, axis=1)
    except sqlite3.OperationalError:
        pass
    
    df_meld = pd.DataFrame()
    try:
        df_meld = pd.read_sql('SELECT * FROM meldungen', conn)
    except sqlite3.OperationalError:
        pass

    if not df_db.empty or not df_meld.empty:
        st.subheader("🔍 Auswertung filtern")
        c1, c2, c3, c4 = st.columns(4)
        with c1: f_search = st.text_input("Suchen (Name/Verein):", "")
        with c2: f_class = st.multiselect("Altersklasse:", sorted(df_db['Class'].dropna().unique().tolist()) if not df_db.empty else [])
        with c3: f_gender = st.multiselect("Geschlecht:", sorted(df_db['Gender'].dropna().unique().tolist()) if not df_db.empty else [])
        with c4: f_club = st.multiselect("Verein:", sorted(df_db['ClubName'].dropna().unique().tolist()) if not df_db.empty else [])

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

        tab_med, tab_prog, tab_cup, tab_all_perfs, tab_raw = st.tabs([
            "🏅 Event-Medaillenbedarf", "🔮 Cup-Prognose", "📊 Gesamtwertung Cup", "🏅 Alle Leistungen & Punkte", "📋 Rohdaten"
        ])

        # Berechne Basis für Medaillen und Prognose (auf U10/U12/U14 Basis)
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

        # --- TAB 1: MEDAILLENBEDARF (NUR AKTUELLES EVENT) ---
        with tab_med:
            st.subheader("Übersicht: Medaillenbedarf (1 bis 3+ Starts im Event)")
            if not prog_df.empty:
                if df_meld.empty:
                    st.info("Keine Nennungsliste hochgeladen. Zeigt die Medaillen basierend auf der geladenen Ergebnisse-Datei.")
                else:
                    st.success("Medaillen werden **NUR** aus den Starts der neuen Nennungsliste berechnet! Alte Starts werden hier ignoriert.")
                
                # Wir filtern Kinder ohne Medaillenstarts (also 0 neue Starts) heraus
                med_df = prog_df[prog_df['Medal_Starts'] > 0].copy()
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Starter im Event", len(med_df))
                c2.metric("🥇 Gold (3+ Starts)", len(med_df[med_df['Event-Medaille'] == "🥇 Gold"]))
                c3.metric("🥈 Silber (2 Starts)", len(med_df[med_df['Event-Medaille'] == "🥈 Silber"]))
                c4.metric("🥉 Bronze (1 Start)", len(med_df[med_df['Event-Medaille'] == "🥉 Bronze"]))

                cat_order = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2}
                med_df['Sort'] = med_df['Event-Medaille'].map(cat_order)
                med_df = med_df.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

                st.dataframe(med_df[['Event-Medaille', 'FirstName', 'LastName', 'Class', 'ClubName', 'Medal_Starts']], 
                             column_config={
                                 "Medal_Starts": "Gewertete Event-Starts"
                             },
                             width='stretch', hide_index=True)
                
                csv_med = med_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Medaillenliste herunterladen", csv_med, "medaillenbedarf_event.csv", "text/csv")
            else:
                st.warning("Keine Athleten der Klassen U10-U14 gefunden.")

        # --- TAB 2: CUP-PROGNOSE (ALLES KOMBINIERT) ---
        with tab_prog:
            st.subheader("Übersicht: Cup-Qualifikation (Saison: 6+ Starts)")
            if not prog_df.empty:
                if df_meld.empty:
                    st.info("Zeigt den aktuellen Stand der Cup-Qualifikation aus der Ergebnis-Datenbank.")
                else:
                    st.success("Kombiniert die alten Ergebnisse mit den neuen Nennungen. Zeigt, wer nach diesem Event die 6 Starts voll haben wird.")

                qual_count = len(prog_df[prog_df['Starts_Gesamt'] >= 6])
                nah_dran_count = len(prog_df[(prog_df['Starts_Gesamt'] >= 4) & (prog_df['Starts_Gesamt'] < 6)])

                c1, c2 = st.columns(2)
                c1.metric("✅ Qualifiziert (6+ Starts)", qual_count)
                c2.metric("🟡 Nah dran (4 oder 5 Starts)", nah_dran_count)

                prog_df_sorted = prog_df.sort_values(by=['Starts_Gesamt', 'LastName'], ascending=[False, True])

                st.dataframe(prog_df_sorted[['Prognose Gesamt', 'FirstName', 'LastName', 'Class', 'ClubName', 'Starts_Bisher', 'Starts_Neu', 'Starts_Gesamt']], 
                             column_config={
                                 "Starts_Bisher": "Starts Bisher",
                                 "Starts_Neu": "Starts neu",
                                 "Starts_Gesamt": "Starts Saison gesamt"
                             },
                             width='stretch', hide_index=True)

                csv_prog = prog_df_sorted.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Prognoseliste herunterladen", csv_prog, "cup_prognose.csv", "text/csv")
            else:
                st.warning("Keine Athleten der Klassen U10-U14 gefunden.")

        # --- TAB 3: GESAMTWERTUNG CUP ---
        with tab_cup:
            if not filtered_df.empty:
                cup_df, valid_perfs_df, counted_indices = get_cup_data(filtered_df)
                if not cup_df.empty:
                    st.dataframe(cup_df[['Status', 'Fortschritt', 'Class', 'Gender', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'EventDetails']], width='stretch', hide_index=True)
                else:
                    st.info("Keine Cup-Teilnehmer mit diesen Filtern gefunden.")

        # --- TAB 4: ALLE LEISTUNGEN ---
        with tab_all_perfs:
            if not filtered_df.empty:
                _, valid_perfs_df, counted_indices = get_cup_data(filtered_df)
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

        # --- TAB 5: ROHDATEN ---
        with tab_raw:
            st.write("Ergebnisse in der Datenbank:")
            st.dataframe(filtered_df, width='stretch')

    else:
        st.info("Bitte lade CSV-Dateien in der Seitenleiste hoch.")

except Exception as e:
    st.error(f"Ein Fehler ist aufgetreten: {e}")
