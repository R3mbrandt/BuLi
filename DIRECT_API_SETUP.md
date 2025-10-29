# Direkte API-Football Einrichtung

## ❌ Problem: API-Key wird abgelehnt

Dein API-Key `eb05b8d78736fa783e7c77b11370952a` wird von der API mit **403 Forbidden** abgelehnt.

Getestet wurden **alle gängigen Authentifizierungsmethoden**:
- ❌ `x-apisports-key` Header
- ❌ `x-rapidapi-key` Header
- ❌ `apikey` Query Parameter
- ❌ `Authorization Bearer` Header
- ❌ Und 4 weitere Varianten

## 🔍 Bitte überprüfe folgendes:

### 1. API-Key Gültigkeit

Teste deinen Key direkt mit curl:

```bash
curl -X GET "https://v3.football.api-sports.io/status" \
     -H "x-apisports-key: eb05b8d78736fa783e7c77b11370952a"
```

**Erwartete Antwort bei gültigem Key:**
```json
{
  "response": {
    "account": {
      "firstname": "...",
      "lastname": "...",
      "email": "..."
    },
    "subscription": {
      "plan": "...",
      "end": "...",
      "active": true
    },
    "requests": {
      "current": 123,
      "limit_day": 100
    }
  }
}
```

**Bei 403 Forbidden:**
- API-Key ist ungültig oder inaktiv
- Subscription ist abgelaufen
- Account nicht aktiviert

### 2. Dashboard überprüfen

Gehe zu: **https://dashboard.api-football.com/**

Überprüfe:
- ✅ Account aktiviert (Email bestätigt)?
- ✅ Subscription aktiv?
- ✅ API-Key korrekt angezeigt?
- ✅ Request-Limit noch nicht erreicht?

### 3. Fixture-ID verifizieren

Teste die spezifische Fixture:

```bash
curl -X GET "https://v3.football.api-sports.io/fixtures?id=1388375" \
     -H "x-apisports-key: eb05b8d78736fa783e7c77b11370952a"
```

Falls das funktioniert, ist der Key OK und es liegt an meiner Implementation.

### 4. Odds für Fixture testen

```bash
curl -X GET "https://v3.football.api-sports.io/odds?fixture=1388375" \
     -H "x-apisports-key: eb05b8d78736fa783e7c77b11370952a"
```

## 🎯 Nächste Schritte

### Option A: Key funktioniert bei dir lokal

Wenn curl bei dir funktioniert, aber nicht in meinem Code:
1. Sende mir die **exakte curl-Antwort** vom /status endpoint
2. Ich passe dann die Implementation entsprechend an

### Option B: Key funktioniert auch bei dir nicht

Wenn auch curl 403 gibt:
1. Erstelle neuen API-Key im Dashboard
2. Oder aktiviere deine Subscription
3. Oder überprüfe Email-Bestätigung

### Option C: Anderer API-Provider?

Hast du den Key vielleicht von einem anderen Provider?
- **api-football.com** vs **api-sports.io**?
- RapidAPI Marketplace?
- Anderer Reseller?

## 🔧 Curl Test für dich

Bitte führe diesen Befehl auf **deinem System** aus:

```bash
# Test 1: Status
curl -v -X GET "https://v3.football.api-sports.io/status" \
     -H "x-apisports-key: eb05b8d78736fa783e7c77b11370952a"

# Test 2: Spezifische Fixture
curl -v -X GET "https://v3.football.api-sports.io/fixtures?id=1388375" \
     -H "x-apisports-key: eb05b8d78736fa783e7c77b11370952a"
```

Das `-v` Flag zeigt die kompletten HTTP-Headers.

**Bitte sende mir:**
1. HTTP Status Code (200, 403, etc.)
2. Response Headers
3. Response Body (oder Fehlermeldung)

Dann kann ich die exakte Ursache identifizieren!

## 📋 Informationen die ich brauche

Um dir besser helfen zu können, bitte folgende Infos:

1. **Funktioniert curl bei dir lokal?** (Ja/Nein)
2. **Welchen Plan hast du?** (Free, Basic, Pro)
3. **Ist deine Email bestätigt?**
4. **Ist die Subscription aktiv?** (Prüfe im Dashboard)
5. **Hast du den Key gerade erst erstellt?** (Evtl. Aktivierungsverzögerung)

## 🔄 Alternative: RapidAPI

Falls die direkte API Probleme macht, kannst du auch RapidAPI nutzen:

1. Gehe zu: https://rapidapi.com/api-sports/api/api-football
2. Erstelle kostenlosen Account
3. Subscribe zu "Basic" (FREE, 100 requests/day)
4. Kopiere den RapidAPI Key
5. Das System ist bereits für RapidAPI konfiguriert

RapidAPI ist oft einfacher für den Einstieg.

---

**Wichtig**: Der 403-Fehler deutet stark darauf hin, dass etwas mit dem API-Key oder der Subscription nicht stimmt. Bitte überprüfe dein Dashboard und führe die curl-Tests durch.
