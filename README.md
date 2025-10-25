# Bundesliga Match Prediction System

Ein fortschrittliches Prognosesystem für Bundesliga-Spiele basierend auf **Poisson-Simulation** unter Einbeziehung von:
- **ELO-Ratings** (dynamisch berechnet aus Spielergebnissen)
- **xG-Werten** (Expected Goals)
- **Kaderwert** (monetär)
- **Verletzten-Status**
- **Head-to-Head Bilanz**

## 🎯 Features

- ⚽ **Präzise Spielprognosen** mit Wahrscheinlichkeiten für Sieg/Unentschieden/Niederlage
- 📊 **Detaillierte Analysen** inkl. erwartete Tore, wahrscheinlichste Ergebnisse
- 💰 **Wett-Insights** (Over/Under 2.5, BTTS)
- 📈 **ELO-Rating-System** speziell für Bundesliga optimiert
- 🔄 **Live-Daten** von OpenLigaDB (kostenlos, kein API-Key erforderlich)
- 🧪 **Mock-Daten** für Entwicklung und Testing

## 📋 Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Manager)

## 🚀 Installation & Lokale Nutzung

### 1. Repository klonen

```bash
git clone https://github.com/R3mbrandt/BuLi.git
cd BuLi
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. Script ausführen

#### Demo mit Mock-Daten (funktioniert überall)

```bash
python predict.py
```

Dies zeigt:
- Bundesliga-Tabelle
- ELO-Rankings
- Beispiel-Prognose (Bayern vs Dortmund)

#### Spezifische Begegnung vorhersagen

```bash
python predict.py --team1 "Bayern" --team2 "Dortmund"
```

Teamnamen können abgekürzt werden:
```bash
python predict.py --team1 "Bayern" --team2 "RB"      # RB Leipzig
python predict.py --team1 "Lever" --team2 "Frank"   # Leverkusen vs Frankfurt
```

#### Kompletten Spieltag vorhersagen

```bash
python predict.py --matchday 15
```

#### Live-Daten nutzen (benötigt Internet)

```bash
python predict.py --live --team1 "Bayern" --team2 "Leipzig"
```

⚠️ **Hinweis**: Live-Daten von OpenLigaDB funktionieren möglicherweise nicht in allen Umgebungen (z.B. Cloud-IDEs). Bei Problemen einfach ohne `--live` Flag nutzen.

#### ELO-Rankings anzeigen

```bash
python predict.py --show-elo
```

#### Tabelle anzeigen

```bash
python predict.py --show-table
```

## 🏗️ Projektstruktur

```
BuLi/
├── predict.py                    # Haupt-CLI-Script
├── requirements.txt              # Python-Dependencies
├── src/
│   ├── data_sources/
│   │   ├── openligadb.py        # OpenLigaDB API Client (kostenlos!)
│   │   ├── fbref.py             # FBref Scraper (für xG-Daten)
│   │   ├── clubelo.py           # ClubELO Integration
│   │   └── mock_data.py         # Mock-Daten für Entwicklung
│   └── models/
│       ├── elo_rating.py        # ELO-Rating-System
│       ├── poisson_model.py     # Poisson-basiertes Prognosemodell
│       └── prediction_engine.py # Haupt-Prognose-Engine
├── tests/
└── data/                         # Lokaler Daten-Cache (wird erstellt)
```

## 🔬 Technische Details

### ELO-Rating-System

Das ELO-System wird dynamisch aus allen Spielergebnissen berechnet und berücksichtigt:
- **Heimvorteil**: +100 ELO-Punkte für Heimmannschaft
- **Tordifferenz**: Größere Siege werden stärker gewichtet
- **K-Faktor**: 32 (Standard für Fußball)

Formel für erwarteten Score:
```
E(A) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))
```

### Poisson-Simulationsmodell

Das Modell nutzt die **Poisson-Verteilung** zur Berechnung von Torwahrscheinlichkeiten:

```python
P(X = k) = (λ^k * e^(-λ)) / k!
```

Wobei `λ` (Lambda) die erwartete Anzahl Tore ist, berechnet aus:
- Team-Angriffsstärke (aus xG-Daten)
- Gegnerische Abwehrschwäche
- Heimvorteil-Faktor (1.3)

### Gewichtung der Faktoren

Die finale Prognose kombiniert alle Faktoren mit folgenden Standard-Gewichten:

| Faktor | Gewicht | Beschreibung |
|--------|---------|--------------|
| **ELO** | 35% | Aktuelle Teamstärke basierend auf Ergebnissen |
| **xG** | 30% | Expected Goals (Angriffs-/Abwehrqualität) |
| **Kaderwert** | 15% | Monetärer Wert des Kaders |
| **H2H** | 10% | Head-to-Head Bilanz |
| **Verletzungen** | 10% | Anzahl verletzter Spieler |

Diese können im Code angepasst werden.

## 📊 Beispiel-Output

```
======================================================================
MATCH PREDICTION: Bayern München vs Borussia Dortmund
======================================================================

📊 MATCH OUTCOME PROBABILITIES:
----------------------------------------------------------------------
  Home Win:  80.6%
  Draw:      11.7%
  Away Win:   7.6%

⚽ EXPECTED GOALS:
----------------------------------------------------------------------
  Bayern München                : 3.15
  Borussia Dortmund             : 0.93

🎯 MOST LIKELY SCORE:
----------------------------------------------------------------------
  3:0 (8.8%)

📈 TOP 5 PROBABLE SCORES:
----------------------------------------------------------------------
    3:0 -   8.8%
    2:0 -   8.4%
    3:1 -   8.2%
    2:1 -   7.8%
    4:0 -   6.9%

💰 BETTING INSIGHTS:
----------------------------------------------------------------------
  Over 2.5 Goals:  77.3%
  Under 2.5 Goals: 22.7%
  BTTS Yes:        57.9%
  BTTS No:         42.1%

🔍 FACTOR BREAKDOWN:
----------------------------------------------------------------------
  ELO:         Home 61.3% | Away 38.7%
  xG:          Home 53.7% | Away 46.3%
  Squad Value: Home 62.0% | Away 38.0%
  H2H:         Home 80.0% | Away 20.0%
  Injuries:    Home -6.0% | Away -9.0%

  Combined:    Home 61.8% | Away 38.2%
======================================================================
```

## 📡 Datenquellen

### Primäre Quellen (kostenlos, funktionieren lokal):

1. **OpenLigaDB** ([openligadb.de](https://www.openligadb.de/))
   - ✅ Kostenlos & Open Source
   - ✅ Kein API-Key erforderlich
   - ✅ Echtzeit Bundesliga-Daten
   - ✅ Spielergebnisse, Tabelle, Spieltage

2. **FBref** ([fbref.com](https://fbref.com/))
   - ✅ Detaillierte xG-Statistiken
   - ✅ Umfassende Team-Analysen
   - ℹ️ Scraping erforderlich (im Code implementiert)

3. **Transfermarkt** (für zukünftige Erweiterung)
   - Kaderwerte
   - Verletzungsdaten
   - Spielerwerte

### Alternative Quellen:

- **ClubELO**: Vordefinierte ELO-Ratings (optional)
- **API-Football**: Umfassende API (100 Requests/Tag kostenlos)
- **Football-Data.org**: Zusätzliche Statistiken

## 🧪 Testing & Entwicklung

### Unit Tests ausführen

```bash
# Mock-Daten testen
python src/data_sources/mock_data.py

# ELO-System testen
python src/models/elo_rating.py

# Poisson-Modell testen
python src/models/poisson_model.py

# Prognose-Engine testen
cd src/models && python prediction_engine.py
```

### OpenLigaDB-Integration testen

```bash
python src/data_sources/openligadb.py
```

## 🔧 Anpassung & Erweiterung

### Eigene Gewichte setzen

```python
from src.models.prediction_engine import BundesligaPredictionEngine

engine = BundesligaPredictionEngine()
engine.set_weights(
    elo=0.40,         # Mehr Gewicht auf ELO
    xg=0.35,          # Mehr Gewicht auf xG
    squad_value=0.10,
    injuries=0.05,
    h2h=0.10
)
```

### Transfermarkt-Daten hinzufügen

Der Code ist bereits vorbereitet für Transfermarkt-Integration. Einfach in `src/data_sources/transfermarkt.py` implementieren:

```python
class TransfermarktScraper:
    def get_squad_value(self, team: str) -> float:
        # Implementation hier
        pass

    def get_injuries(self, team: str) -> List[Dict]:
        # Implementation hier
        pass
```

## ⚠️ Bekannte Einschränkungen & Troubleshooting

### 1. Live-Daten funktionieren nicht (`--live` schlägt fehl)

**Symptom**:
```bash
python predict.py --live
# ⚠️ Live data fetch failed: 403 Client Error: Forbidden
# 📊 Falling back to mock data for demonstration...
```

**Mögliche Ursachen**:
- Netzwerkbeschränkungen (Firewall, Proxy)
- Cloud-Umgebungen blockieren externe APIs
- IP-Adresse ist temporär rate-limited
- OpenLigaDB API ist nicht erreichbar

**Lösungen**:
1. ✅ **Automatischer Fallback**: Das Script nutzt automatisch Mock-Daten
2. ✅ **Mock-Daten nutzen**: Einfach `--live` weglassen
   ```bash
   python predict.py --team1 "Bayern" --team2 "Dortmund"
   ```
3. ✅ **Lokale Umgebung**: Script auf Ihrem eigenen Rechner ausführen (nicht in Cloud-IDE)
4. ✅ **Netzwerk prüfen**: Firewall/Proxy-Einstellungen überprüfen

**Hinweis**: Mock-Daten sind realistisch generiert und liefern funktionierende Prognosen für Tests!

### 2. Cloud-Umgebungen

Einige Websites (FBref, ClubELO) blockieren Zugriffe aus Cloud-IDEs mit 403 Forbidden
- **Lösung**: Script lokal ausführen
- **Alternative**: Mock-Daten nutzen

### 3. xG-Daten

Nicht alle APIs bieten xG-Werte
- **Lösung**: FBref-Scraping implementiert
- **Fallback**: Tore als Proxy für xG

### 4. Verletzungsdaten

Keine kostenlose API verfügbar
- **Lösung**: Transfermarkt-Scraping (noch zu implementieren)
- **Aktuell**: Mock-Werte verwendet

## 🤝 Beitragen

Contributions sind willkommen! Besonders in folgenden Bereichen:

- [ ] Transfermarkt-Scraper für Live-Kaderwerte
- [ ] Transfermarkt-Scraper für Verletzungsdaten
- [ ] Erweiterte xG-Modelle
- [ ] Visualisierungen (Plots, Diagramme)
- [ ] Web-Interface (Flask/Streamlit)
- [ ] Historische Genauigkeits-Analyse
- [ ] Machine Learning Integration

## 📄 Lizenz

Dieses Projekt ist Open Source und steht unter der MIT-Lizenz.

## 👨‍💻 Autor

Entwickelt von Claude (Anthropic) für Bundesliga-Analytics

## 🙏 Danksagungen

- **OpenLigaDB** für die kostenlose Bundesliga-API
- **FBref** (Sports Reference) für detaillierte Statistiken
- **ClubELO** für ELO-Rating-Konzepte
- **SciPy** für statistische Funktionen

## 📞 Support

Bei Fragen oder Problemen:
1. GitHub Issues öffnen
2. Code-Dokumentation lesen
3. Mock-Daten für Offline-Testing nutzen

---

**Hinweis**: Dieses Tool dient ausschließlich zu Analyse- und Bildungszwecken. Keine Garantie für Genauigkeit der Prognosen. Bitte verantwortungsvoll mit Wettvorhersagen umgehen.
