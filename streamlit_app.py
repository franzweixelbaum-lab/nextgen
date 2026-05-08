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

    # 1. Daten filtern
    is_competitive = ~df['NotCompetitive'].astype(str).str.strip().str.lower().isin(['true', '1', 't', 'ja', 'yes'])
    df_ak = df[(df['Class'] == klasse) & is_competitive].copy()

    df_ak = df_ak.dropna(subset=['Result', 'ClassRank'])
    df_ak['Result'] = df_ak['Result'].astype(str).str.strip()
    df_ak = df_ak[~df_ak['Result'].isin(['ab.', 'ogV', 'aufg.', 'n.a.', 'disq.', ''])]

    df_ak['ClassRank'] = pd.to_numeric(df_ak['ClassRank'], errors='coerce')
    df_ak = df_ak.dropna(subset=['ClassRank'])

    if df_ak.empty:
        return pd.DataFrame(), {}, pd.DataFrame()

    # Anzahl der Vereine in dieser Klasse ermitteln
    anzahl_vereine = df_ak['ClubName'].nunique()

    df_ak['Event'] = df_ak['Event'].astype(str).str.strip()
    df_ak['Bewerbsgruppe'] = df_ak['Event'].map(EVENT_MAPPING).fillna('Unbekannt')
    df_ak['Name'] = df_ak.apply(get_competitor_name, axis=1)

    # Alle Einzelleistungen sammeln und Punkte pro Bewerb zuteilen
    results_list = []
    
    for event, event_df in df_ak.groupby('Event'):
        event_df = event_df.sort_values('ClassRank')
        seen_clubs = set()
        club_rank = 1
        
        for _, row in event_df.iterrows():
            club = row['ClubName']
            # Nur der bestplatzierte Athlet pro Verein erhält Punkte
            if club not in seen_clubs:
                seen_clubs.add(club)
                punkte = max(0, anzahl_vereine - club_rank + 1)
                club_rank += 1
                is_best_in_event = True
            else:
                punkte = 0
                is_best_in_event = False
                
            results_list.append({
                'Verein': str(club),
                'Bewerbsgruppe': row['Bewerbsgruppe'],
                'Bewerb (Code)': row['Event'],
                'Athlet/Staffel': row['Name'],
                'Leistung': row['Result'],
                'Rang': int(row['ClassRank']),
                'Punkte': int(punkte),
                'IsBestInEvent': is_best_in_event,
                'Status': ''
            })

    df_results = pd.DataFrame(results_list)
    ergebnisse = []
    details_pro_verein = {}

    # Gruppenauswertung pro Verein
    for verein, group in df_results.groupby('Verein'):
        gesamt_punkte = 0
        gewertete_bewerbe = 0
        platzierungen = []
        verein_details = []

        for bg, bg_group in group.groupby('Bewerbsgruppe'):
            if bg == 'Unbekannt':
                continue
            
            # Trennen in beste Ergebnisse und Streichresultate im selben Bewerb
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
                    platzierungen.append(row['Rang'])
                else:
                    row['Status'] = '❌ Streichresultat (Gruppen-Limit)'
                    row['Punkte'] = 0 # Zählt nicht fürs Endergebnis
                verein_details.append(row)
                
            for row in other_in_events.to_dict('records'):
                row['Status'] = '❌ Streichresultat (2.+ Athlet im Bewerb)'
                verein_details.append(row)

        details_pro_verein[verein] = verein_details

        # Tie-Breaker
        siege = platzierungen.count(1)
        zweite = platzierungen.count(2)
        dritte = platzierungen.count(3)

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

        # Tabs (Register) für die Ansicht erstellen
        tab1, tab2 = st.tabs(["🏆 Gesamtwertung & Vereinsdetails", "📋 Alle Einzelergebnisse"])

        # --- TAB 1: Übersicht & Gesamtwertung ---
        with tab1:
            st.header(f"Endergebnis: {klasse}")
            
            if df_ergebnis.empty:
                st.warning("Kein Verein in dieser Klasse hat die erforderlichen 8 gültigen und gewerteten Bewerbe erreicht.")
            else:
                st.dataframe(df_ergebnis, use_container_width=True)

                st.markdown("### Details pro Verein")
                st.info("In den Details sind nun **alle Athleten** sichtbar. Gewertete Leistungen sind mit ✅ markiert, Streichresultate mit ❌.")
                
                # Qualifizierte Vereine (mit >= 8 Bewerben)
                for idx, row in df_ergebnis.iterrows():
                    verein = row['Verein']
                    punkte = float(row['Gesamtpunkte'])
                    
                    with st.expander(f"🏅 {verein} — Gesamtpunkte: {punkte:.0f}"):
                        if verein in details_dict and details_dict[verein]:
                            df_det = pd.DataFrame(details_dict[verein])
                            # Drop the internal sorting column
                            df_det = df_det.drop(columns=['IsBestInEvent'], errors='ignore')
                            # Sortieren nach Gruppe und Status (Gewertete oben)
                            df_det = df_det.sort_values(by=['Bewerbsgruppe', 'Status', 'Punkte'], ascending=[True, False, False]).reset_index(drop=True)
                            st.dataframe(df_det, use_container_width=True)
                    
                # Vereine, die außerhalb der Wertung sind (< 8 Bewerbe)
                nicht_qualifiziert = [v for v in details_dict.keys() if v not in df_ergebnis['Verein'].tolist()]
                if nicht_qualifiziert:
                    st.write("---")
                    st.subheader("Außerhalb der Wertung (< 8 gewertete Bewerbe)")
                    for verein in nicht_qualifiziert:
                        # Berechne die Anzahl der "Gewerteten" Bewerbe
                        df_det = pd.DataFrame(details_dict[verein])
                        anz_gewertet = len(df_det[df_det['Status'] == '✅ Gewertet'])
                        
                        with st.expander(f"❌ {verein} — Gewertete Bewerbe: {anz_gewertet}/8"):
                            df_det = df_det.drop(columns=['IsBestInEvent'], errors='ignore')
                            df_det = df_det.sort_values(by=['Bewerbsgruppe', 'Status', 'Punkte'], ascending=[True, False, False]).reset_index(drop=True)
                            st.dataframe(df_det, use_container_width=True)

        # --- TAB 2: Register mit allen Einzelergebnissen ---
        with tab2:
            st.header(f"Alle erfassten Athleten und Punktzuweisungen ({klasse})")
            if not df_all_details.empty:
                # Wir sortieren die Gesamttabelle alphabetisch nach Verein und dann nach Punkten
                df_all_details = df_all_details.sort_values(by=['Verein', 'Bewerbsgruppe', 'Status'], ascending=[True, True, False]).reset_index(drop=True)
                st.dataframe(df_all_details, use_container_width=True)
            else:
                st.info("Keine auswertbaren Leistungsdaten gefunden.")
else:
    st.info("⬆️ Bitte laden Sie eine CSV-Datei hoch, um mit der Auswertung zu beginnen.")