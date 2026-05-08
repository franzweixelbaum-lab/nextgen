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
        # Fallback für Staffeln, falls RelayName oder TeamName existieren oder fehlen
        if 'RelayName' in row and pd.notna(row['RelayName']) and str(row['RelayName']).strip() != "":
            return str(row['RelayName'])
        if 'TeamName' in row and pd.notna(row['TeamName']) and str(row['TeamName']).strip() != "":
            return str(row['TeamName'])
        return f"{row.get('ClubName', 'Unbekannt')} Staffel"

def load_and_evaluate(df, klasse):
    # Sicherheits-Check für notwendige Spalten
    required_cols = ['Class', 'NotCompetitive', 'Result', 'ClassRank', 'ClubName', 'Event']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Fehler: Folgende benötigte Spalten fehlen in der CSV: {', '.join(missing)}")
        st.stop()

    # Bereinigung der Klassenspalte
    df['Class'] = df['Class'].astype(str).str.strip()

    # 1. Daten filtern nach Klasse (WU16 oder MU16) und 'Außer Wertung' ausschließen
    # Wir filtern sehr robust, falls 'NotCompetitive' als String oder Bool daherkommt
    is_competitive = ~df['NotCompetitive'].astype(str).str.strip().str.lower().isin(['true', '1', 't', 'ja', 'yes'])
    df_ak = df[(df['Class'] == klasse) & is_competitive].copy()

    # Ungültige Ergebnisse aussortieren (abgemeldet, ohne gültigen Versuch, aufgegeben, etc.)
    df_ak = df_ak.dropna(subset=['Result', 'ClassRank'])
    df_ak['Result'] = df_ak['Result'].astype(str).str.strip()
    df_ak = df_ak[~df_ak['Result'].isin(['ab.', 'ogV', 'aufg.', 'n.a.', 'disq.', ''])]

    # ClassRank zu numerischem Wert konvertieren (Fehlerhafte Werte werden zu NaN -> dropna)
    df_ak['ClassRank'] = pd.to_numeric(df_ak['ClassRank'], errors='coerce')
    df_ak = df_ak.dropna(subset=['ClassRank'])

    if df_ak.empty:
        return pd.DataFrame(), {}

    # 2. Anzahl der in der Altersklasse teilnehmenden Vereine ermitteln
    anzahl_vereine = df_ak['ClubName'].nunique()

    # 3. Bestes Ergebnis pro Verein und Bewerb ermitteln
    df_ak = df_ak.sort_values('ClassRank')
    best_per_club_event = df_ak.drop_duplicates(subset=['ClubName', 'Event'], keep='first').copy()

    # 4. Punkte berechnen: (Gesamtzahl Vereine in der Klasse) - Platzierung + 1
    best_per_club_event['Punkte'] = anzahl_vereine - best_per_club_event['ClassRank'] + 1
    best_per_club_event['Punkte'] = best_per_club_event['Punkte'].clip(lower=0)

    # 5. Bewerbsgruppe matchen und Anzeige-Namen formatieren
    best_per_club_event['Event'] = best_per_club_event['Event'].astype(str).str.strip()
    best_per_club_event['Bewerbsgruppe'] = best_per_club_event['Event'].map(EVENT_MAPPING).fillna('Unbekannt')
    best_per_club_event['Name'] = best_per_club_event.apply(get_competitor_name, axis=1)

    # 6. Auswertung auf Vereinsebene nach den Gruppen-Regeln
    ergebnisse = []
    details_pro_verein = {}

    for verein, group in best_per_club_event.groupby('ClubName'):
        gesamt_punkte = 0
        gewertete_bewerbe = 0
        platzierungen = []
        detail_zeilen = []

        for bg, bg_group in group.groupby('Bewerbsgruppe'):
            if bg == 'Unbekannt':
                continue  # Unbekannte Bewerbe ignorieren
            
            # Sortieren nach Punkten (absteigend)
            bg_group = bg_group.sort_values('Punkte', ascending=False)
            
            # Regel: Sprung & Stoß/Wurf max. 2 Ergebnisse, alle anderen max. 1 Ergebnis
            top_n = 2 if bg in ['Sprung', 'Stoß/Wurf'] else 1
            best_results = bg_group.head(top_n)
            
            gesamt_punkte += best_results['Punkte'].sum()
            gewertete_bewerbe += len(best_results)
            platzierungen.extend(best_results['ClassRank'].tolist())

            for _, row in best_results.iterrows():
                detail_zeilen.append({
                    'Bewerbsgruppe': bg,
                    'Bewerb (Code)': row['Event'],
                    'Athlet/Staffel': row['Name'],
                    'Leistung': row['Result'],
                    'Rang': int(row['ClassRank']),
                    'Punkte': int(row['Punkte'])
                })

        details_pro_verein[verein] = detail_zeilen

        # Tie-Breaker ermitteln (Anzahl der 1., 2., 3. Plätze)
        siege = platzierungen.count(1)
        zweite = platzierungen.count(2)
        dritte = platzierungen.count(3)

        # Ein Verein wird nur dann im Endergebnis gelistet, wenn er mind. 8 Bewerbe aufweist
        if gewertete_bewerbe >= 8:
            ergebnisse.append({
                'Verein': str(verein),
                'Gesamtpunkte': float(gesamt_punkte),
                'Gewertete Bewerbe': int(gewertete_bewerbe),
                '1. Plätze': int(siege),
                '2. Plätze': int(zweite),
                '3. Plätze': int(dritte)
            })

    # Dataframes für Ausgabe aufbereiten
    df_endergebnis = pd.DataFrame(ergebnisse)
    if not df_endergebnis.empty:
        # Ranking und Tie-Breaker anwenden
        df_endergebnis = df_endergebnis.sort_values(
            by=['Gesamtpunkte', '1. Plätze', '2. Plätze', '3. Plätze'], 
            ascending=[False, False, False, False]
        ).reset_index(drop=True)
        df_endergebnis.index += 1
        df_endergebnis.index.name = 'Rang'

    return df_endergebnis, details_pro_verein

# --- Streamlit UI ---
st.set_page_config(page_title="ÖLV U16 Vereinemeisterschaft", layout="wide")
st.title("ÖLV U16 Vereinemeisterschaften - Auswertung")

uploaded_file = st.file_uploader("Laden Sie hier die ATHMIN-Ergebnisdatei (CSV) hoch", type=["csv"])

if uploaded_file is not None:
    # Robuster Dateiupload (versucht UTF-8, fällt bei Windows-CSVs auf Latin-1 zurück)
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
            df_ergebnis, details_dict = load_and_evaluate(df_raw, klasse)

        st.header(f"Endergebnis: {klasse}")
        
        if df_ergebnis.empty:
            st.warning("Kein Verein in dieser Klasse hat die erforderlichen 8 gültigen und gewerteten Bewerbe erreicht.")
        else:
            # Reines DataFrame ausgeben
            st.dataframe(df_ergebnis, use_container_width=True)

            st.header("Details pro Verein")
            st.subheader("Qualifizierte Vereine (im Gesamtranking)")
            
            for verein in df_ergebnis['Verein'].tolist():
                
                # Hier ist die Korrektur: .iloc stellt sicher, dass wir nur EINE konkrete Zahl bekommen
                punkte_series = df_ergebnis.loc[df_ergebnis['Verein'] == verein, 'Gesamtpunkte']
                punkte = float(punkte_series.iloc) if not punkte_series.empty else 0.0
                
                with st.expander(f"🏅 {verein} — Gesamtpunkte: {punkte:.0f}"):
                    if verein in details_dict and details_dict[verein]:
                        df_det = pd.DataFrame(details_dict[verein])
                        df_det = df_det.sort_values(by=['Bewerbsgruppe', 'Punkte'], ascending=[True, False]).reset_index(drop=True)
                        st.table(df_det)
                
            nicht_qualifiziert = [v for v in details_dict.keys() if v not in df_ergebnis['Verein'].tolist()]
            if nicht_qualifiziert:
                st.write("---")
                st.subheader("Außerhalb der Wertung (< 8 gewertete Bewerbe)")
                for verein in nicht_qualifiziert:
                    anz_bewerbe = len(details_dict[verein])
                    with st.expander(f"❌ {verein} — Gewertete Bewerbe: {anz_bewerbe}/8"):
                        df_det = pd.DataFrame(details_dict[verein])
                        df_det = df_det.sort_values(by=['Bewerbsgruppe', 'Punkte'], ascending=[True, False]).reset_index(drop=True)
                        st.table(df_det)
else:
    st.info("⬆️ Bitte laden Sie eine CSV-Datei hoch, um mit der Auswertung zu beginnen.")