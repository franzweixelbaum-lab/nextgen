import streamlit as st
import pandas as pd

# Konfiguration und Mapping der Bewerbe zu den Bewerbsgruppen (lt. ÖLV U16 Regeln)
EVENT_MAPPING = {
    '100': 'Sprint',
    '1K0': 'Ausdauer',
    '1K5': 'Ausdauer',
    '80H': 'Hürden',
    '10H': 'Hürden',
    'HOC': 'Sprung',
    'WEI': 'Sprung',
    'STA': 'Sprung',
    'KUG': 'Stoß/Wurf',
    'SPE': 'Stoß/Wurf',
    'DIS': 'Stoß/Wurf',
    'HAM': 'Stoß/Wurf',
    'STF': 'Staffel',
    '4X1': 'Staffel'
}

def get_competitor_name(row):
    """Sicheres Auslesen des Namens, egal ob Athlet oder Staffel"""
    t = str(row.get('Type', '')).strip()
    if t == 'Athlete':
        return f"{row.get('FirstName', '')} {row.get('LastName', '')}".strip()
    else:
        # Fallback für Staffeln
        if 'RelayName' in row and pd.notna(row['RelayName']) and str(row['RelayName']).strip() != "":
            return str(row['RelayName'])
        if 'TeamName' in row and pd.notna(row['TeamName']) and str(row['TeamName']).strip() != "":
            return str(row['TeamName'])
        return f"{row.get('ClubName', 'Unbekannt')} Staffel"

def load_and_evaluate(df, klasse):
    required_cols = ['Class', 'NotCompetitive', 'Result', 'ClassRank', 'ClubName', 'Event']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Fehler: Folgende benötigte Spalten fehlen in der CSV: {', '.join(missing)}")
        st.stop()

    df['Class'] = df['Class'].astype(str).str.strip()

    # 1. Daten filtern (Wettbewerbsfähig, keine Abmeldungen/o.g.V.)
    is_competitive = ~df['NotCompetitive'].astype(str).str.strip().str.lower().isin(['true', '1', 't', 'ja', 'yes'])
    df_ak = df[(df['Class'] == klasse) & is_competitive].copy()

    df_ak = df_ak.dropna(subset=['Result', 'ClassRank'])
    df_ak['Result'] = df_ak['Result'].astype(str).str.strip()
    df_ak = df_ak[~df_ak['Result'].isin(['ab.', 'ogV', 'aufg.', 'n.a.', 'disq.', ''])]

    df_ak['ClassRank'] = pd.to_numeric(df_ak['ClassRank'], errors='coerce')
    df_ak = df_ak.dropna(subset=['ClassRank'])

    if df_ak.empty:
        return pd.DataFrame(), {}, pd.DataFrame()

    # WICHTIG: Höchstpunktezahl = Gesamtanzahl der Vereine in dieser Klasse
    anzahl_vereine = df_ak['ClubName'].nunique()

    df_ak['Event'] = df_ak['Event'].astype(str).str.strip()
    df_ak['Bewerbsgruppe'] = df_ak['Event'].map(EVENT_MAPPING).fillna('Unbekannt')
    df_ak['Name'] = df_ak.apply(get_competitor_name, axis=1)

    results_list = []
    
    # 2. Auswertung pro Bewerb (Ermittlung des Vereins-Rangs und Punktevergabe)
    for event, event_df in df_ak.groupby('Event'):
        
        # Sortieren nach dem offiziellen Gesamtrang im Bewerb
        event_df = event_df.sort_values('ClassRank')
        
        # Den besten Athleten / die beste Staffel pro Verein extrahieren
        best_per_club = event_df.drop_duplicates(subset=['ClubName'], keep='first').copy()
        
        # NEUE LOGIK FÜR GLEICHSTÄNDE: 
        # Wir berechnen das Ranking der verbleibenden Vereine anhand ihres ClassRanks.
        # "method='min'" sorgt dafür, dass Gleichstände denselben Platz bekommen und der
        # darauffolgende den übersprungenen Platz annimmt (z.B. Platzierungen 1, 1, 3, 4, 4, 6...)
        best_per_club['VereinsRang'] = best_per_club['ClassRank'].rank(method='min').astype(int)
        
        # Punkteberechnung: Höchstpunkte - VereinsRang + 1 (Minimum 0)
        best_per_club['Punkte_kalkuliert'] = anzahl_vereine - best_per_club['VereinsRang'] + 1
        best_per_club['Punkte_kalkuliert'] = best_per_club['Punkte_kalkuliert'].clip(lower=0)
        
        # Mapping-Dictionaries erstellen, um sie gleich der Gesamtliste zuzuweisen
        club_points_map = best_per_club.set_index('ClubName')['Punkte_kalkuliert'].to_dict()
        club_rank_map = best_per_club.set_index('ClubName')['VereinsRang'].to_dict()
        
        seen_clubs = set()
        
        for _, row in event_df.iterrows():
            club = row['ClubName']
            
            # Prüfen, ob es der bestplatzierte Athlet des Vereins in diesem Bewerb ist
            is_best_in_event = club not in seen_clubs
            
            if is_best_in_event:
                seen_clubs.add(club)
                punkte = club_points_map[club]
                vereins_rang = club_rank_map[club]
            else:
                punkte = 0
                vereins_rang = None # Zweitstarter erhalten keinen Vereinsrang
                
            results_list.append({
                'Verein': str(club),
                'Bewerbsgruppe': row['Bewerbsgruppe'],
                'Bewerb': row['Event'],
                'Athlet/Staffel': row['Name'],
                'Leistung': row['Result'],
                'Rang (Gesamt)': int(row['ClassRank']),
                'Rang (Verein)': int(vereins_rang) if vereins_rang is not None else "-",
                'Punkte': int(punkte),
                'IsBestInEvent': is_best_in_event,
                'Status': ''
            })

    df_results = pd.DataFrame(results_list)
    ergebnisse = []
    details_pro_verein = {}

    # 3. Gruppenauswertung pro Verein nach Streichresultat-Regeln
    for verein, group in df_results.groupby('Verein'):
        gesamt_punkte = 0
        gewertete_bewerbe = 0
        platzierungen = [] # Wird für den Tie-Breaker (Siege etc.) gesammelt
        verein_details = []

        for bg, bg_group in group.groupby('Bewerbsgruppe'):
            if bg == 'Unbekannt':
                continue
            
            # Nur die besten pro Bewerb dürfen in die Gruppenwertung einfließen
            best_in_events = bg_group[bg_group['IsBestInEvent'] == True].copy()
            best_in_events = best_in_events.sort_values('Punkte', ascending=False)
            
            other_in_events = bg_group[bg_group['IsBestInEvent'] == False].copy()
            
            # Regel: Sprung & Stoß/Wurf max. 2 Ergebnisse, alle anderen max. 1 Ergebnis
            top_n = 2 if bg in ['Sprung', 'Stoß/Wurf'] else 1
            
            for i, row in enumerate(best_in_events.to_dict('records')):
                if i < top_n:
                    row['Status'] = '✅ Gewertet'
                    gesamt_punkte += row['Punkte']
                    gewertete_bewerbe += 1
                    # Für den Tie-Breaker sammeln wir den VEREINSRANG ein (nicht den Gesamtrang)
                    platzierungen.append(row['Rang (Verein)'])
                else:
                    row['Status'] = '❌ Streichresultat (Gruppen-Limit)'
                    row['Punkte'] = 0 # Zählt nicht fürs Endergebnis
                verein_details.append(row)
                
            for row in other_in_events.to_dict('records'):
                row['Status'] = '❌ Streichresultat (2.+ Athlet im Bewerb)'
                verein_details.append(row)

        details_pro_verein[verein] = verein_details

        # Tie-Breaker aus den gesammelten Vereins-Rängen ermitteln
        siege = platzierungen.count(1)
        zweite = platzierungen.count(2)
        dritte = platzierungen.count(3)

        # Ein Verein wird nur dann gewertet, wenn er mind. 8 gültige Bewerbe hat
        if gewertete_bewerbe >= 8:
            ergebnisse.append({
                'Verein': verein,
                'Gesamtpunkte': float(gesamt_punkte),
                'Gewertete Bewerbe': int(gewertete_bewerbe),
                '1. Plätze': int(siege),
                '2. Plätze': int(zweite),
                '3. Plätze': int(dritte)
            })

    # Gesamtergebnis aufbereiten
    df_endergebnis = pd.DataFrame(ergebnisse)
    if not df_endergebnis.empty:
        df_endergebnis = df_endergebnis.sort_values(
            by=['Gesamtpunkte', '1. Plätze', '2. Plätze', '3. Plätze'], 
            ascending=[False, False, False, False]
        ).reset_index(drop=True)
        df_endergebnis.index += 1
        df_endergebnis.index.name = 'Rang'

    # Alle Details für das zweite Register zusammenführen
    df_all_details = pd.DataFrame([item for sublist in details_pro_verein.values() for item in sublist])
    if not df_all_details.empty:
        df_all_details = df_all_details.drop(columns=['IsBestInEvent'])

    return df_endergebnis, details_pro_verein, df_all_details

# --- Streamlit UI ---
st.set_page_config(page_title="ÖLV U16 Vereinemeisterschaft", layout="wide")
st.title("ÖLV U16 Vereinemeisterschaften - Auswertung")

uploaded_file = st.file_uploader("Laden Sie hier die ATHMIN-Ergebnisdatei (CSV) hoch", type=["csv"])

if uploaded_file is not None:
    try:
        df_raw = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df_raw = pd.read_csv(uploaded_file, sep=';', encoding='latin-1')
    except Exception as e:
        st.error(f"Fehler beim Einlesen der CSV-Datei. Detailfehler: {e}")
        st.stop()

    klasse = st.selectbox("Wähle die Altersklasse zur Auswertung:", ["WU16", "MU16"])

    if st.button("Ergebnis Berechnen", type="primary"):
        with st.spinner("Berechne Ergebnisse..."):
            df_ergebnis, details_dict, df_all_details = load_and_evaluate(df_raw, klasse)

        tab1, tab2 = st.tabs(["🏆 Gesamtwertung & Vereinsdetails", "📋 Alle Einzelergebnisse (Filterbar)"])

        # --- TAB 1: Übersicht & Gesamtwertung ---
        with tab1:
            st.header(f"Endergebnis: {klasse}")
            
            if df_ergebnis.empty:
                st.warning("Kein Verein in dieser Klasse hat die erforderlichen 8 gültigen und gewerteten Bewerbe erreicht.")
            else:
                st.dataframe(df_ergebnis, use_container_width=True)

                st.markdown("### Details pro Verein")
                st.info("Gewertete Leistungen sind mit ✅ markiert, Streichresultate mit ❌. Der **Rang (Verein)** gibt an, wie der Verein in diesem Bewerb abzüglich der Streichresultate anderer Vereine abgeschnitten hat.")
                
                for idx, row in df_ergebnis.iterrows():
                    verein = row['Verein']
                    punkte = float(row['Gesamtpunkte'])
                    
                    with st.expander(f"🏅 {verein} — Gesamtpunkte: {punkte:.0f}"):
                        if verein in details_dict and details_dict[verein]:
                            df_det = pd.DataFrame(details_dict[verein])
                            df_det = df_det.drop(columns=['IsBestInEvent'], errors='ignore')
                            df_det = df_det.sort_values(by=['Bewerbsgruppe', 'Status', 'Punkte'], ascending=[True, False, False]).reset_index(drop=True)
                            st.dataframe(df_det, use_container_width=True)
                    
                nicht_qualifiziert = [v for v in details_dict.keys() if v not in df_ergebnis['Verein'].tolist()]
                if nicht_qualifiziert:
                    st.write("---")
                    st.subheader("Außerhalb der Wertung (< 8 gewertete Bewerbe)")
                    for verein in nicht_qualifiziert:
                        df_det = pd.DataFrame(details_dict[verein])
                        anz_gewertet = len(df_det[df_det['Status'] == '✅ Gewertet'])
                        
                        with st.expander(f"❌ {verein} — Gewertete Bewerbe: {anz_gewertet}/8"):
                            df_det = df_det.drop(columns=['IsBestInEvent'], errors='ignore')
                            df_det = df_det.sort_values(by=['Bewerbsgruppe', 'Status', 'Punkte'], ascending=[True, False, False]).reset_index(drop=True)
                            st.dataframe(df_det, use_container_width=True)

        # --- TAB 2: Register mit allen Einzelergebnissen und Filter ---
        with tab2:
            st.header(f"Einzelergebnisse & Punktevergabe ({klasse})")
            
            if not df_all_details.empty:
                verfuegbare_bewerbe = sorted(df_all_details['Bewerb'].unique())
                
                auswahl = st.multiselect(
                    "Wählen Sie einen oder mehrere Bewerbe zur Filterung aus (leer lassen für alle Ergebnisse):",
                    options=verfuegbare_bewerbe,
                    default=[]
                )
                
                df_filtered = df_all_details.copy()
                if auswahl:
                    df_filtered = df_filtered[df_filtered['Bewerb'].isin(auswahl)]
                
                # Sortierung für perfekte Übersichtlichkeit der ex-aequo Platzierungen: 
                # Zuerst nach Bewerb, dann aufsteigend nach dem bereinigten Vereins-Rang (damit ex-aequo Ränge untereinander stehen)
                # "-" Ränge (Streichresultate) werden nach unten sortiert
                df_filtered['SortRank'] = pd.to_numeric(df_filtered['Rang (Verein)'], errors='coerce').fillna(999)
                df_filtered = df_filtered.sort_values(
                    by=['Bewerb', 'SortRank', 'Rang (Gesamt)'], 
                    ascending=[True, True, True]
                ).drop(columns=['SortRank']).reset_index(drop=True)
                
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.info("Keine auswertbaren Leistungsdaten gefunden.")
else:
    st.info("⬆️ Bitte laden Sie eine CSV-Datei hoch, um mit der Auswertung zu beginnen.")