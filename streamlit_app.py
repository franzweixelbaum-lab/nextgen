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
    # --- MÄNNLICH ---
    'M_60M':  {'Typ': 'Lauf',   'a': 45.0,   'b': 12.5,  'c': 1.81},
    'M_10H':  {'Typ': 'Lauf',   'a': 5.0,    'b': 25.0,  'c': 1.81}, 
    'M_20H':  {'Typ': 'Lauf',   'a': 3.5,    'b': 45.0,  'c': 1.81},
    'M_400':  {'Typ': 'Lauf',   'a': 0.25,   'b': 130.0, 'c': 1.85},
    'M_600':  {'Typ': 'Lauf',   'a': 0.06,   'b': 250.0, 'c': 1.85},
    'M_800':  {'Typ': 'Lauf',   'a': 0.1,    'b': 240.0, 'c': 1.85}, 
    'M_1K0':  {'Typ': 'Lauf',   'a': 0.08,   'b': 300.0, 'c': 1.85}, 
    'M_1KSC': {'Typ': 'Lauf',   'a': 0.08,   'b': 300.0, 'c': 1.85},
    'M_1K5':  {'Typ': 'Lauf',   'a': 0.04,   'b': 480.0, 'c': 1.85},
    'M_WEI':  {'Typ': 'Sprung', 'a': 0.15,   'b': 150.0, 'c': 1.4},   
    'M_VOR':  {'Typ': 'Wurf',   'a': 12.0,   'b': 5.0,   'c': 1.1},   
    
    # --- WEIBLICH ---
    'W_60M':  {'Typ': 'Lauf',   'a': 48.0,   'b': 13.0,  'c': 1.81},
    'W_10H':  {'Typ': 'Lauf',   'a': 5.0,    'b': 26.0,  'c': 1.81},
    'W_20H':  {'Typ': 'Lauf',   'a': 3.5,    'b': 48.0,  'c': 1.81},
    'W_400':  {'Typ': 'Lauf',   'a': 0.25,   'b': 140.0, 'c': 1.85},
    'W_600':  {'Typ': 'Lauf',   'a': 0.055,  'b': 260.0, 'c': 1.85},
    'W_800':  {'Typ': 'Lauf',   'a': 0.1,    'b': 260.0, 'c': 1.85},
    'W_1K0':  {'Typ': 'Lauf',   'a': 0.08,   'b': 320.0, 'c': 1.85},
    'W_1KSC': {'Typ': 'Lauf',   'a': 0.08,   'b': 320.0, 'c': 1.85},
    'W_1K5':  {'Typ': 'Lauf',   'a': 0.04,   'b': 500.0, 'c': 1.85},
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
        
        # QUALIFIKATIONS-REGELN
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
        st.subheader("🔍 Globale Suche")
        search_query = st.text_input("Suchen nach Name, Verein oder Altersklasse:", "")

        tab_cup, tab_all_perfs, tab_rank, tab_win, tab_plot, tab_raw = st.tabs([
            "📊 Gesamtwertung Cup", "🏅 Alle Leistungen & Punkte", "🥈 Teilnahmen-Medaillen", "🥇 Einzel-Sieger", "📈 Grafiken", "📋 Rohdaten"
        ])

        # Cup-Daten berechnen
        cup_df, valid_perfs_df, counted_indices = get_cup_data(df_db)

        # --- TAB 1: GESAMTWERTUNG ---
        with tab_cup:
            st.info("Regeln: 6 gewertete Starts aus mind. 5 unterschiedlichen Disziplinen. Gewertete Leistungen sind in den Details markiert.")
            
            display_cup_df = cup_df.copy()
            if search_query and not display_cup_df.empty:
                display_cup_df = display_cup_df[display_cup_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                
            if not display_cup_df.empty:
                st.dataframe(display_cup_df[['Status', 'Fortschritt', 'Fehlend', 'Class', 'Gender', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'EventDetails']], 
                             column_config={
                                 "Status": st.column_config.TextColumn("Qualifikation"),
                                 "Fortschritt": st.column_config.TextColumn("Starts"),
                                 "Fehlend": st.column_config.TextColumn("Es fehlen..."),
                                 "CupPoints": "Punkte (Best 6)",
                                 "EventDetails": st.column_config.TextColumn("Leistungs-Details (⭐ = in Wertung)", width="large")
                             },
                             width='stretch', hide_index=True)
                
                csv_cup = display_cup_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Cup-Wertung herunterladen", csv_cup, "cup_gesamtwertung.csv", "text/csv")
            else:
                st.info("Keine Daten für den Cup gefunden.")

        # --- TAB 2: ALLE LEISTUNGEN & PUNKTE (FEHLER BEHOBEN) ---
        with tab_all_perfs:
            st.subheader("Detailübersicht aller absolvierten Leistungen (U10-U14)")
            st.info("Jede Zeile, die in die Gesamtwertung (Best 6) einfließt, ist **fett markiert** und hat ein ⭐.")
            
            if not valid_perfs_df.empty:
                # Vorbereiten des Dataframes
                disp_df = valid_perfs_df[['FirstName', 'LastName', 'Class', 'ClubName', 'Event', 'Result', 'CupPoints']].copy()
                # Sicher prüfen, ob der Index im Set der gewerteten Leistungen liegt
                disp_df['Gewertet'] = disp_df.index.isin(counted_indices)
                
                # Sortieren und Index neu aufbauen, damit die Zuweisung in Styler sicher funktioniert
                disp_df = disp_df.sort_values(['LastName', 'FirstName', 'CupPoints'], ascending=[True, True, False]).reset_index(drop=True)
                disp_df['Gewertet_Str'] = disp_df['Gewertet'].apply(lambda x: "⭐ Ja" if x else "Nein")
                
                if search_query:
                    disp_df = disp_df[disp_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

                # Sicher aus dem Dataframe die Spalte extrahieren, OHNE sie zu löschen
                display_cols_df = disp_df.drop(columns=['Gewertet'])

                def highlight_counted(row):
                    # Zieht sich die Info sicher über die Original-Zeilennummer (row.name)
                    if disp_df.loc[row.name, 'Gewertet']:
                        return ['font-weight: bold; background-color: rgba(255, 215, 0, 0.15)'] * len(row)
                    return [''] * len(row)
                
                # Style anwenden
                styled_df = display_cols_df.style.apply(highlight_counted, axis=1)
                
                st.dataframe(styled_df, 
                             column_config={
                                 "Result": "Ergebnis",
                                 "CupPoints": "Erreichte Punkte",
                                 "Gewertet_Str": "In Cup-Wertung?"
                             },
                             width='stretch', hide_index=True)
            else:
                st.info("Keine gültigen Leistungen gefunden.")

        # --- TAB 3: MEDAILLEN ---
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

        # --- TAB 4: SIEGER ---
        with tab_win:
            winners_df = get_winners_list(df_db)
            if not winners_df.empty:
                if search_query:
                    winners_df = winners_df[winners_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                
                st.dataframe(winners_df[['Event', 'Class', 'FirstName', 'LastName', 'ClubName', 'Result']], 
                             width='stretch', hide_index=True)
                csv_win = winners_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Siegerliste herunterladen", csv_win, "siegerliste.csv", "text/csv")

        # --- TAB 5: PLOTS ---
        with tab_plot:
            sel_event = st.selectbox("Bewerb für Grafik wählen:", sorted(df_db['Event'].unique()))
            plot_df = df_db[df_db['Event'] == sel_event].dropna(subset=['Result_Num'])
            if search_query:
                plot_df = plot_df[plot_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            
            if not plot_df.empty:
                fig = px.box(plot_df, x="Class", y="Result_Num", color="Class", points="all", hover_data=["FirstName", "LastName", "CupPoints"])
                fig.update_layout(yaxis_title="Ergebnis")
                st.plotly_chart(fig, width="stretch")

        # --- TAB 6: ROHDATEN ---
        with tab_raw:
            raw_display = df_db
            if search_query:
                raw_display = raw_display[raw_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            st.dataframe(raw_display, width='stretch')

    else:
        st.info("Bitte lade eine CSV-Datei hoch.")

except sqlite3.OperationalError:
    st.info("Willkommen! Lade bitte eine CSV-Datei in der Sidebar hoch.")
except Exception as e:
    # NEU: Verhindert, dass echte Code-Fehler verschluckt werden!
    st.error(f"Ein Fehler ist aufgetreten: {e}")
