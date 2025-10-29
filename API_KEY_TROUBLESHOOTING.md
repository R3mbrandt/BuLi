# API-Football Key Troubleshooting

## 🔍 Problem: 403 Forbidden Error

Dein API-Key (`eb05b8d787...0952a`) wird von der API abgelehnt.

## ⚠️ Mögliche Ursachen:

### 1. **RapidAPI vs. Direkter API-Key**
Es gibt zwei Arten von API-Keys für API-Football:

**RapidAPI** (empfohlen):
- URL: https://rapidapi.com/api-sports/api/api-football
- Key-Format: Lange alphanumerische Zeichenkette (oft 50+ Zeichen)
- Header: `x-rapidapi-key`
- Kostenlos: 100 Requests/Tag

**Direkt von API-Football**:
- URL: https://www.api-football.com/
- Anderes Key-Format
- Andere Header-Konfiguration

**Dein Key**: 32 Zeichen - könnte von beiden Plattformen sein

### 2. **Subscription Status**

Prüfe auf RapidAPI:
1. Gehe zu: https://rapidapi.com/developer/dashboard
2. Klicke auf "My Subscriptions"
3. Suche "API-Football"
4. Status sollte "Active" sein

### 3. **API-Key vollständig kopiert?**

Stelle sicher, dass du den kompletten Key kopiert hast:
- Kein Leerzeichen am Anfang/Ende
- Keine Zeilenumbrüche
- Alle Zeichen korrekt

### 4. **Rate Limit erreicht?**

Free Tier: 100 Requests/Tag
- Prüfe auf RapidAPI Dashboard unter "API Calls"
- Limit wird um Mitternacht UTC zurückgesetzt

## ✅ So holst du den richtigen API-Key (RapidAPI):

### Schritt 1: RapidAPI Account
1. Gehe zu https://rapidapi.com/
2. Erstelle Account oder logge dich ein

### Schritt 2: API-Football subscriben
1. Suche "API-Football" oder gehe direkt zu:
   https://rapidapi.com/api-sports/api/api-football
2. Klicke "Subscribe to Test"
3. Wähle Plan:
   - **Basic (FREE)**: 100 requests/day - gut zum Testen
   - **Pro**: $30/month, 3000 requests/day - für produktiven Einsatz

### Schritt 3: API-Key kopieren
1. Nach Subscription siehst du "Code Snippets"
2. Im Header siehst du:
   ```
   x-rapidapi-key: YOUR_API_KEY_HERE
   ```
3. Kopiere **nur** den Key (ohne "x-rapidapi-key:")

### Schritt 4: Key testen
```bash
export API_FOOTBALL_KEY='dein-neuer-key'
python verify_api_key.py
```

## 🔧 Alternative: Ohne API-Key testen

Das System funktioniert auch **ohne API-Key** im Mock-Modus:

```bash
# Einfach ohne API_FOOTBALL_KEY Umgebungsvariable
python predict.py --team1 "Bayern" --team2 "Dortmund"
```

**Mock-Modus Features:**
- ✅ Alle Prediction-Features funktionieren
- ✅ Realistische Sample-Odds basierend auf Team-Stärke
- ✅ Vollständige xG, ELO, Squad Value, H2H Berechnungen
- ❌ Keine Live-Odds von Bookmakers
- ❌ Keine Live-Fixtures

## 📊 Dein aktueller API-Key

```
Key: eb05b8d787...0952a
Länge: 32 Zeichen
Status: ✗ Wird abgelehnt (403 Forbidden)
```

**Empfehlung**: Hole einen neuen API-Key von RapidAPI.

## 🆘 Weitere Hilfe

Wenn du den Key von RapidAPI hast aber er trotzdem nicht funktioniert:

1. **Prüfe Subscription Status**:
   - Dashboard → My Subscriptions → API-Football → "Active"?

2. **Warte 5-10 Minuten**:
   - Nach Subscription kann es kurz dauern bis Key aktiv ist

3. **Teste mit curl**:
   ```bash
   curl -X GET "https://v3.football.api-sports.io/timezone" \
        -H "x-rapidapi-key: DEIN_KEY" \
        -H "x-rapidapi-host: v3.football.api-sports.io"
   ```

   Erwartete Antwort: Liste von Zeitzonen

4. **API-Sports Support**:
   - Email: contact@api-football.com

## ✨ Nächste Schritte

1. **Option A: Neuen Key holen** (empfohlen für Live-Odds)
   - RapidAPI Account erstellen
   - API-Football subscriben (Free oder Pro)
   - Neuen Key testen

2. **Option B: Mock-Modus nutzen** (schneller Start)
   - Weiter ohne API-Key arbeiten
   - Alle Features außer Live-Odds verfügbar
   - Später Key hinzufügen wenn benötigt

Lass mich wissen, welche Option du bevorzugst!
