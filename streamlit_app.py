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
    'M_60M':  {'Typ': 'Lauf',   'a': 45.0,   'b': 12.5,  'c': 1.81},
    'M_10H':  {'Typ': 'Lauf',   'a': 5.0,    'b': 25.0,  'c': 1.81},
    'M_20H':  {'Typ': 'Lauf',   'a': 3.5,    'b': 45.0,  'c': 1.81},
    'M_1K0':  {'Typ': 'Lauf',   'a': 0.08,   'b': 300.0, 'c': 1.85},
    'M_1KSC': {'Typ': 'Lauf',   'a': 0.08,   'b': 300.0, 'c': 1.85},
    'M_800':  {'Typ': 'Lauf',   'a': 0.1,    'b': 240.0, 'c': 1.85},
    'M_WEI':  {'Typ': 'Sprung', 'a': 0.15,   'b': 150.0, 'c': 1.4}, 
    'M_VOR':  {'Typ': 'Wurf',   'a': 12.0,   'b': 5.0,   'c': 1.1}, 
    'W_60M':  {'Typ': 'Lauf',   'a': 48.0,   'b': 13.0,  'c': 1.81},
    'W_10H':  {'Typ': 'Lauf',   'a': 5.0,    'b': 26.0,  'c': 1.81},
    'W_20H':  {'Typ': 'Lauf',   'a': 3.5,    'b': 48.0,  'c': 1.81},
    'W_1K0':  {'Typ': 'Lauf',   'a': 0.08,   'b': 320.0, 'c': 1.85},
    'W_1KSC': {'Typ': 'Lauf',   'a': 0.08,   'b': 320.0, 'c': 1.85},
    'W_800':  {'Typ': 'Lauf',   'a': 0.1,    'b': 260.0, 'c': 1.85},
    'W_WEI':  {'Typ': 'Sprung', 'a': 0.18,   'b': 140.0, 'c': 1.41},
    'W_VOR':  {'Typ': 'Wurf',   'a': 13.0,   'b': 4.0,   'c': 1.1},
}

def calculate_cup_points(row):
    try:
        res = row.get('Result_Num', np.nan)
        event = str(row.get('Event', '')).upper().strip()
        gender = str(row.get('Gender', '')).upper().strip()
        
        if pd.isna(res) or res <= 0 or not gender: return 0
            
        key = f"{gender}_{event}"
        if key not in CUP_PARAMS: return 100
            
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

# --- DATEN BEREINIGUNG ---
def is_valid_result(res):
    if pd.isna(res): return False
    return any(char.isdigit() for char in str(res))

def parse_result_to_number(val):
    if pd.isna(val) or str(val).strip() == '': return np.nan
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

        # Spaltennamen bereinigen und übersetzen (für Athmin/Nennungen)
        df.columns = [str(c).strip() for c in df.columns]
        col_map = {
            'Vorname': 'FirstName',
            'Nachname': 'LastName',
            'Name': 'LastName',        # Fallback für manche Systeme
            'Verein': 'ClubName',
            'Jahrgang': 'Yob',
            'JG': 'Yob',
            'Jg.': 'Yob',              # Oft in Nennlisten verwendet
            'Jg': 'Yob',
            'Klasse': 'Class',
            'AK': 'Class',             # Altersklasse
            'Bewerb': 'Event',
            'Disziplin': 'Event',
            'Geschlecht': 'Gender',
            'm/w': 'Gender'
        }
        df = df.rename(columns=col_map)
        
        # Sicherheitsnetz: Fehlt eine der Pflicht-Spalten, wird sie leer angelegt
        mandatory_cols = ['FirstName', 'LastName', 'Yob', 'ClubName', 'Class', 'Event', 'Gender']
        for col in mandatory_cols:
            if col not in df.columns:
                df[col] = ''
                
        # Leere Werte (NaN) in Gruppierungsfeldern durch Strings ersetzen, 
        # damit 'groupby' diese Zeilen nicht verschluckt oder abstürzt
        df[['FirstName', 'LastName', 'Yob']] = df[['FirstName', 'LastName', 'Yob']].fillna('')
        
        if 'Result' in df.columns:
            df['Result_Num'] = df['Result'].apply(parse_result_to_number)
            df['isValid'] = df['Result'].apply(is_valid_result)
            df['CupPoints'] = df.apply(calculate_cup_points, axis=1)
        else:
            df['Result'] = None
            df['Result_Num'] = np.nan
            df['isValid'] = False
            df['CupPoints'] = 0

        if 'PB' in df.columns: df['PB_Num'] = df['PB'].apply(parse_result_to_number)
        if 'SB' in df.columns: df['SB_Num'] = df['SB'].apply(parse_result_to_number)
            
        return df
    except Exception as e:
        st.error(f"Fehler beim Einlesen: {e}")
        return None

# --- DATEN AUSWERTUNGEN ---
def get_cup_ranking(df):
    if df.empty or 'isValid' not in df.columns: return pd.DataFrame()
    target_classes = ['U10', 'U12', 'U14']
    valid_df = df[df['Class'].str.contains('|'.join(target_classes), na=False) & (df['isValid'] == True)].copy()
    if valid_df.empty: return pd.DataFrame()
    
    ranking = valid_df.groupby(['FirstName', 'LastName', 'Yob']).agg({
        'ClubName': 'first', 'Class': 'first', 'Gender': 'first',
        'CupPoints': 'sum', 
        'Event': lambda x: ', '.join(x.astype(str)), 
        'isValid': 'count'
    }).reset_index()
    return ranking.sort_values(['Class', 'Gender', 'CupPoints'], ascending=[True, True, False])

def get_medal_ranking(df):
    if df.empty: return pd.DataFrame()
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    
    df_filtered['Perf_String'] = df_filtered.apply(
        lambda x: f"{x['Event']} ({x['Result']})" if x.get('isValid', False) else f"{x['Event']} (-)", axis=1
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
    if df.empty or 'isValid' not in df.columns: return pd.DataFrame()
    target_classes = ['U10', 'U12', 'U14']
    valid_df = df[df['Class'].str.contains('|'.join(target_classes), na=False) & (df['isValid'] == True)].dropna(subset=['Result_Num'])
    
    time_events = ['M', 'H', '100', '200', '400', '600', '800', '1K', '2K', '3K']
    winners = []
    for (event, age_class), group in valid_df.groupby(['Event', 'Class']):
        is_time = any(t in event.upper() for t in time_events)
        winner_row = group.loc[group['Result_Num'].idxmin()] if is_time else group.loc[group['Result_Num'].idxmax()]
        winners.append(winner_row)
        
    return pd.DataFrame(winners).sort_values(['Event', 'Class']) if winners else pd.DataFrame()

# --- VORSCHAU & FAVORITEN ---
def get_entry_medal_preview(df):
    if df.empty: return pd.DataFrame()
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    
    ranking = df_filtered.groupby(['FirstName', 'LastName', 'Yob']).agg({
        'ClubName': 'first', 'Class': 'first',
        'Event': lambda x: ', '.join(x.astype(str)),
        'FirstName': 'count'
    }).rename(columns={'FirstName': 'Nennungen'}).reset_index()

    def categorize_preview(count):
        if count >= 3: return "🥇 Vorauss. Gold (3+ Nennungen)"
        elif count == 2: return "🥈 Vorauss. Silber (2 Nennungen)"
        elif count == 1: return "🥉 Vorauss. Bronze (1 Nennung)"
        return "Keine"

    ranking['Vorschau'] = ranking['Nennungen'].apply(categorize_preview)
    cat_order = {"🥇 Vorauss. Gold (3+ Nennungen)": 0, "🥈 Vorauss. Silber (2 Nennungen)": 1, "🥉 Vorauss. Bronze (1 Nennung)": 2, "Keine": 3}
    ranking['Sort'] = ranking['Vorschau'].map(cat_order)
    return ranking.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

def get_favorites_list(df):
    df_fav = df.copy()
    has_pb = 'PB_Num' in df_fav.columns
    has_sb = 'SB_Num' in df_fav.columns
    
    if not has_pb and not has_sb: return pd.DataFrame()
        
    if has_pb and has_sb:
        df_fav['Sort_Mark'] = df_fav['PB_Num'].fillna(df_fav['SB_Num'])
        df_fav['Mark_String'] = df_fav['PB'].fillna(df_fav['SB'])
    elif has_pb:
        df_fav['Sort_Mark'] = df_fav['PB_Num']
        df_fav['Mark_String'] = df_fav['PB']
    else:
        df_fav['Sort_Mark'] = df_fav['SB_Num']
        df_fav['Mark_String'] = df_fav['SB']
        
    df_fav = df_fav.dropna(subset=['Sort_Mark'])
    if df_fav.empty: return pd.DataFrame()

    time_events = ['M', 'H', '100', '200', '400', '600', '800', '1K', '2K', '3K']
    favorites = []
    
    for (event, age_class), group in df_fav.groupby(['Event', 'Class']):
        is_time = any(t in str(event).upper() for t in time_events)
        sorted_group = group.sort_values('Sort_Mark', ascending=is_time)
        favorites.append(sorted_group.head(3))
        
    return pd.concat(favorites).reset_index(drop=True) if favorites else pd.DataFrame()

# --- DASHBOARD UI ---
st.title("🏆 Moderne Leichtathletik-Auswertung")

with st.sidebar:
    st.header("📤 Daten-Upload")
    uploaded_results = st.file_uploader("1️⃣ Ergebnisse hochladen (results.csv)", type=['csv'])
    uploaded_nennungen = st.file_uploader("2️⃣ Nennungen hochladen (optional)", type=['csv'])
    
    if st.button("💾 Daten analysieren & speichern"):
        if uploaded_results:
            raw_df = load_and_clean_data(uploaded_results)
            if raw_df is not None:
                raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
        if uploaded_nennungen:
            nen_df = load_and_clean_data(uploaded_nennungen)
            if nen_df is not None:
                nen_df.to_sql('nennungen', conn, if_exists='replace', index=False)
        st.rerun()

    st.divider()
    if st.button("🗑️ Datenbank leeren"):
        conn.execute("DROP TABLE IF EXISTS ergebnisse")
        conn.execute("DROP TABLE IF EXISTS nennungen")
        st.rerun()

# Daten laden
df_db = pd.DataFrame()
df_nennungen = pd.DataFrame()

try:
    df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)
except Exception: pass

try:
    df_nennungen = pd.read_sql('SELECT * FROM nennungen', conn)
except Exception: pass

has_results = not df_db.empty
has_nennungen = not df_nennungen.empty

if has_results or has_nennungen:
    st.subheader("🔍 Globale Suche")
    search_query = st.text_input("Suchen nach Name, Verein oder Altersklasse:", "")

    tab_preview, tab_cup, tab_rank, tab_win, tab_plot, tab_raw = st.tabs([
        "🔮 Vorschau & Favoriten", "📊 Punkte-Cup", "🏅 Teilnahmen-Medaillen", "🥇 Einzel-Sieger", "📈 Grafiken", "📋 Rohdaten"
    ])
    
    with tab_preview:
        # Vorschau nutzt vorrangig die Nennungen, falls vorhanden. Sonst Ergebnisse als Fallback.
        preview_source_df = df_nennungen if has_nennungen else df_db
        
        st.info("Dieser Bereich dient als Vorschau auf Basis der Nennungen (Meldelisten).")
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Medaillen-Vorschau (nach Nennungen)")
            preview_df = get_entry_medal_preview(preview_source_df)
            if not preview_df.empty:
                if search_query:
                    preview_df = preview_df[preview_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                
                pc1, pc2, pc3 = st.columns(3)
                pc1.metric("🥇 Gold (3+)", len(preview_df[preview_df['Vorschau'] == "🥇 Vorauss. Gold (3+ Nennungen)"]))
                pc2.metric("🥈 Silber (2)", len(preview_df[preview_df['Vorschau'] == "🥈 Vorauss. Silber (2 Nennungen)"]))
                pc3.metric("🥉 Bronze (1)", len(preview_df[preview_df['Vorschau'] == "🥉 Vorauss. Bronze (1 Nennung)"]))
                
                st.dataframe(preview_df[['Vorschau', 'FirstName', 'LastName', 'Class', 'ClubName', 'Nennungen', 'Event']], 
                             column_config={"Nennungen": "Anzahl", "Event": "Gemeldete Bewerbe"}, 
                             width='stretch', hide_index=True)
            else:
                st.warning("Keine Daten für die Vorschau vorhanden.")
                         
        with c2:
            st.subheader("Favoriten (Top 3 nach PB/SB)")
            fav_df = get_favorites_list(preview_source_df)
            if not fav_df.empty:
                if search_query:
                    fav_df = fav_df[fav_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                st.dataframe(fav_df[['Event', 'Class', 'FirstName', 'LastName', 'ClubName', 'Mark_String']],
                             column_config={"Mark_String": "PB/SB"},
                             width='stretch', hide_index=True)
            else:
                st.warning("Keine PB oder SB Spalten in der hochgeladenen Datei gefunden, oder keine Zeiten hinterlegt.")

    with tab_cup:
        if has_results:
            st.info("Das Punkte-System gewichtet Lauf, Sprung und Wurf altersgerecht für einen fairen Mehrkampf.")
            cup_df = get_cup_ranking(df_db)
            if not cup_df.empty:
                if search_query:
                    cup_df = cup_df[cup_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                st.dataframe(cup_df[['Class', 'Gender', 'CupPoints', 'FirstName', 'LastName', 'ClubName', 'isValid', 'Event']], 
                             column_config={"CupPoints": "Gesamtpunkte", "isValid": "Bewerbe (Anzahl)", "Event": "Absolviert"},
                             width='stretch', hide_index=True)
                csv_cup = cup_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Cup-Wertung herunterladen", csv_cup, "cup_wertung.csv", "text/csv")
            else:
                st.warning("Noch keine gültigen Ergebnisse für die Cup-Wertung vorhanden.")
        else:
            st.info("Bitte lade eine Ergebnisliste hoch, um die Punkte zu berechnen.")

    with tab_rank:
        if has_results:
            rank_df = get_medal_ranking(df_db)
            if not rank_df.empty:
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
        else:
            st.info("Bitte lade eine Ergebnisliste hoch, um das Ranking zu sehen.")

    with tab_win:
        if has_results:
            winners_df = get_winners_list(df_db)
            if not winners_df.empty:
                if search_query:
                    winners_df = winners_df[winners_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                st.dataframe(winners_df[['Event', 'Class', 'FirstName', 'LastName', 'ClubName', 'Result']], 
                             width='stretch', hide_index=True)
                csv_win = winners_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Siegerliste herunterladen", csv_win, "siegerliste.csv", "text/csv")
            else:
                st.warning("Noch keine Sieger ermittelbar (fehlende Ergebnisse).")
        else:
            st.info("Bitte lade eine Ergebnisliste hoch, um die Sieger zu ermitteln.")

    with tab_plot:
        if has_results and not df_db[df_db['isValid'] == True].empty:
            sel_event = st.selectbox("Bewerb für Grafik wählen:", sorted(df_db[df_db['isValid'] == True]['Event'].unique()))
            plot_df = df_db[df_db['Event'] == sel_event].dropna(subset=['Result_Num'])
            if search_query:
                plot_df = plot_df[plot_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            
            if not plot_df.empty:
                fig = px.box(plot_df, x="Class", y="Result_Num", color="Class", points="all", hover_data=["FirstName", "LastName", "CupPoints"])
                fig.update_layout(yaxis_title="Ergebnis")
                st.plotly_chart(fig, width="stretch")
        else:
            st.warning("Grafiken sind erst nach Eintragung von Ergebnissen verfügbar.")

    with tab_raw:
        st.write("Ansicht der Datenbanken (Ergebnisse oder Nennungen)")
        raw_display = df_db if has_results else df_nennungen
        if search_query:
            raw_display = raw_display[raw_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
        st.dataframe(raw_display, width='stretch')

else:
    st.info("👈 Bitte lade eine CSV-Datei (Nennungen oder Ergebnisse) in der Seitenleiste hoch, um zu starten.")