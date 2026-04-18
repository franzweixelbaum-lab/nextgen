import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Leichtathletik Auswertung Pro", layout="wide", page_icon="🏆")

def get_connection():
    return sqlite3.connect('leichtathletik.db', check_same_thread=False)

conn = get_connection()

# --- DATENVERARBEITUNG ---
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

def get_filtered_ranking(df):
    """Berechnet das Gold/Silber/Bronze Ranking für U10-U14."""
    target_classes = ['U10', 'U12', 'U14']
    df_filtered = df[df['Class'].str.contains('|'.join(target_classes), na=False)].copy()
    invalid_terms = ['aufg.', 'n.a.', 'ab.', 'disq.', 'ogv.', 'o.v.']
    
    def is_valid(res):
        res_str = str(res).lower().strip()
        if pd.isna(res) or any(term in res_str for term in invalid_terms) or res_str == "":
            return False
        return True

    df_filtered['isValid'] = df_filtered['Result'].apply(is_valid)
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
        return "Teilgenommen"

    ranking['Kategorie'] = ranking['isValid'].apply(categorize)
    cat_order = {"🥇 Gold": 0, "🥈 Silber": 1, "🥉 Bronze": 2, "Teilgenommen": 3}
    ranking['Sort'] = ranking['Kategorie'].map(cat_order)
    return ranking.sort_values(['Sort', 'LastName']).drop(columns=['Sort'])

def get_winners_list(df):
    """Ermittelt die Sieger (Platz 1) pro Bewerb und Klasse."""
    valid_df = df.dropna(subset=['Result_Num']).copy()
    
    # Bewerbe identifizieren, bei denen die kleinste Zahl gewinnt (Zeitbewerbe)
    # Alles was 'M', 'H', '100', '200', '800' enthält, wird als Lauf gewertet
    time_events = ['M', 'H', '100', '200', '800', '1K', '2K', '3K']
    
    winners = []
    for (event, age_class), group in valid_df.groupby(['Event', 'Class']):
        is_time = any(t in event.upper() for t in time_events)
        if is_time:
            winner_row = group.loc[group['Result_Num'].idxmin()]
        else:
            winner_row = group.loc[group['Result_Num'].idxmax()]
        winners.append(winner_row)
        
    winners_df = pd.DataFrame(winners)
    return winners_df[['Event', 'Class', 'FirstName', 'LastName', 'ClubName', 'Result']].sort_values(['Event', 'Class'])

# --- UI ---
st.title("🏆 Online Auswertungssystem")

with st.sidebar:
    st.header("📤 Daten-Upload")
    uploaded_file = st.file_uploader("results.csv hochladen", type=['csv'])
    if uploaded_file:
        raw_df = load_and_clean_data(uploaded_file)
        if raw_df is not None:
            if st.button("💾 In Datenbank speichern"):
                raw_df.to_sql('ergebnisse', conn, if_exists='replace', index=False)
                st.sidebar.success("Daten gespeichert!")
                st.rerun()

try:
    df_db = pd.read_sql('SELECT * FROM ergebnisse', conn)
    if not df_db.empty:
        tab_rank, tab_win, tab_plot, tab_raw = st.tabs(["🏅 Medaillen-Ranking", "🥇 Siegerliste", "📊 Analyse", "📋 Rohdaten"])

        with tab_rank:
            rank_df = get_filtered_ranking(df_db)
            g_count = len(rank_df[rank_df['Kategorie'] == "🥇 Gold"])
            s_count = len(rank_df[rank_df['Kategorie'] == "🥈 Silber"])
            b_count = len(rank_df[rank_df['Kategorie'] == "🥉 Bronze"])

            c1, c2, c3 = st.columns(3)
            c1.metric("🥇 Gold (3+)", g_count)
            c2.metric("🥈 Silber (2)", s_count)
            c3.metric("🥉 Bronze (1)", b_count)
            st.divider()
            st.dataframe(rank_df[['Kategorie', 'FirstName', 'LastName', 'Class', 'ClubName', 'Perf_String', 'isValid']], use_container_width=True, hide_index=True)

        with tab_win:
            st.subheader("Die Erstplatzierten aller Bewerbe")
            winners_df = get_winners_list(df_db)
            st.dataframe(
                winners_df, 
                column_config={"Result": "Bestleistung", "FirstName": "Vorname", "LastName": "Nachname", "Class": "Klasse", "ClubName": "Verein"},
                use_container_width=True, 
                hide_index=True
            )
            csv_win = winners_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Siegerliste herunterladen", csv_win, "siegerliste.csv", "text/csv")

        with tab_plot:
            sel_event = st.selectbox("Wähle einen Bewerb:", sorted(df_db['Event'].unique()))
            plot_df = df_db[df_db['Event'] == sel_event].dropna(subset=['Result_Num'])
            fig = px.box(plot_df, x="Class", y="Result_Num", color="Class", points="all", hover_data=["FirstName", "LastName"])
            st.plotly_chart(fig, use_container_width=True)

        with tab_raw:
            st.dataframe(df_db, use_container_width=True)
    else:
        st.info("Bitte CSV-Datei hochladen.")
except Exception as e:
    st.info("Bereit für den Daten-Upload.")