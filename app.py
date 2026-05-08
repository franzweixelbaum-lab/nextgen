Das lässt sich in Streamlit sehr einfach mit dem Widget `st.file_uploader` umsetzen. Dadurch erscheint auf der Webseite ein Feld, in das Sie die CSV-Datei einfach per Drag-and-Drop hineinziehen oder über einen Dialog auswählen können.

Hier ist der angepasste Code für Ihre `app.py`. Ersetzen Sie den vorherigen Code vollständig hiermit:

```python
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
    'STF': 'Staffel'
}

def load_and_evaluate(df, klasse):
    # 1. Daten filtern nach Klasse (WU16 oder MU16) und 'Außer Wertung' ausschließen
    df_ak = df[(df['Class'] == klasse) & (df['NotCompetitive'] == False)].copy()

    # Ungültige Ergebnisse aussortieren (abgemeldet, ohne gültigen Versuch, aufgegeben, etc.)
    df_ak = df_ak[~df_ak['Result'].isin(['ab.', 'ogV', 'aufg.', 'n.a.'])]
    df_ak['ClassRank'] = pd.to_numeric(df_ak['ClassRank'], errors='coerce')
    df_ak = df_ak.dropna(subset=['ClassRank'])
    
    # 2. Anzahl der in der Altersklasse teilnehmenden Vereine ermitteln (für die Maximalpunkte)
    anzahl_vereine = df_ak['ClubName'].nunique()

    # 3. Bestes Ergebnis pro Verein und Bewerb ermitteln
    df_ak = df_ak.sort_values('ClassRank')
    best_per_club_event = df_ak.drop_duplicates(subset=['ClubName', 'Event'], keep='first').copy()

    # 4. Punkte berechnen: (Gesamtzahl Vereine in der Klasse) - Platzierung + 1
    best_per_club_event['Punkte'] = anzahl_vereine - best_per_club_event['ClassRank'] + 1
    best_per_club_event['Punkte'] = best_per_club_event['Punkte'].clip(lower=0)

    # 5. Bewerbsgruppe matchen und Anzeige-Namen formatieren
    best_per_club_event['Bewerbsgruppe'] = best_per_club_event['Event'].map(EVENT_MAPPING)
    best_per_club_event['Name'] = best_per_club_event.apply(
        lambda row: f"{row['FirstName']} {row['LastName']}" if row['Type'] == 'Athlete' else str(row['RelayName']), 
        axis=1
    )

    # 6. Auswertung auf Vereinsebene nach den Gruppen-Regeln
    ergebnisse = []
    details_pro_verein = {}

    for verein, group in best_per_club_event.groupby('ClubName'):
        gesamt_punkte = 0
        gewertete_bewerbe = 0
        platzierungen = []
        detail_zeilen = []

        # Gruppieren nach Bewerbsgruppe
        for bg, bg_group in group.groupby('Bewerbsgruppe'):
            # Sortieren nach Punkten (absteigend), um die besten Ergebnisse zu nehmen
            bg_group = bg_group.sort_values('Punkte', ascending=False)
            
            # Regel: Sprung & Stoß/Wurf max. 2 Ergebnisse, alle anderen max. 1 Ergebnis
            top_n = 2 if bg in ['Sprung', 'Stoß/Wurf'] else 1
            best_results = bg_group.head(top_n)
            
            gesamt_punkte += best_results['Punkte'].sum()
            gewertete_bewerbe += len(best_results)
            platzierungen.extend(best_results['ClassRank'].tolist())

            # Details für das UI sammeln
            for _, row in best_results.iterrows():
                detail_zeilen.append({
                    'Bewerbsgruppe': bg,
                    'Bewerb (Code)': row['Event'],
                    'Athlet/Staffel': row['Name'],
                    'Leistung': row['Result'],
                    'Rang im Bewerb': int(row['ClassRank']),
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
                'Verein': verein,
                'Gesamtpunkte': gesamt_punkte,
                'Gewertete Bewerbe': gewertete_bewerbe,
                '1. Plätze': siege,
                '2. Plätze': zweite,
                '3. Plätze': dritte
            })

    # Dataframes für die Ausgabe aufbereiten
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
st.set_page_config(page_title="ÖLV U16 Vereinemeisterschaft Auswertung", layout="wide")
st.title("ÖLV U16 Vereinemeisterschaften - Punkteauswertung")
st.markdown("Basierend auf den offiziellen Regulativ-Vorgaben des ÖLV (Punkte anhand der Anzahl an teilnehmenden Vereinen in der Altersklasse, Gruppen-Wertungs-Limitierungen, Mindestanzahl von 8 Bewerben für die Gesamtwertung).")

# NEU: Datei-Upload Widget
uploaded_file = st.file_uploader("Laden Sie hier die ATHMIN-Ergebnisdatei (CSV) hoch", type=["csv"])

if uploaded_file is not None:
    # CSV aus dem Upload laden
    try:
        df_raw = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    except Exception as e:
        st.error(f"Fehler beim Lesen der Datei. Bitte stellen Sie sicher, dass es sich um eine gültige CSV mit Semikolon als Trennzeichen handelt. Detailfehler: {e}")
        st.stop()

    # Altersklasse zur Auswahl
    klasse = st.selectbox("Wähle die Altersklasse zur Auswertung:", ["WU16", "MU16"])

    if st.button("Ergebnis Berechnen", type="primary"):
        df_ergebnis, details_dict = load_and_evaluate(df_raw, klasse)

        st.header(f"Endergebnis: {klasse}")
        if df_ergebnis.empty:
            st.warning("Kein Verein hat die erforderlichen 8 gültigen und gewerteten Bewerbe erreicht.")
        else:
            # Haupttabelle formatieren
            st.dataframe(df_ergebnis.style.format(precision=0), use_container_width=True)

            st.header("Details pro Verein (Gewertete Athleten & Staffeln)")
            
            # Details der qualifizierten Vereine anzeigen
            st.subheader("Qualifizierte Vereine (im Gesamtranking)")
            for verein in df_ergebnis['Verein'].tolist():
                punkte = df_ergebnis[df_ergebnis['Verein'] == verein]['Gesamtpunkte'].values
                with st.expander(f"🏅 {verein} — Gesamtpunkte: {punkte:.0f}"):
                    df_det = pd.DataFrame(details_dict[verein])
                    df_det = df_det.sort_values(by=['Bewerbsgruppe', 'Punkte'], ascending=[True, False]).reset_index(drop=True)
                    st.table(df_det)
                    
            # Optional: Zeigt Vereine an, die gestartet sind, aber keine 8 Disziplinen vollbekommen haben
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
```

**Was sich geändert hat:**
Die Zeile mit `pd.read_csv('results_vereine.csv', ...)` wurde durch `uploaded_file = st.file_uploader(...)` ersetzt. Die App wartet nun, bis der Benutzer eine Datei hochlädt. Erst wenn die Datei im Browser bereitgestellt wird (`if uploaded_file is not None:`), wird das Auswahlmenü für die Altersklasse sowie der Berechnen-Button eingeblendet.