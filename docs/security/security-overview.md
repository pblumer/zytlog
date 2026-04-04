# Sicherheitsübersicht

## Übersicht

Dieses Dokument beschreibt die Sicherheitsarchitektur und -praktiken für das Zytlog-System.

## Authentifizierung

### JWT (JSON Web Tokens)

Das System verwendet JWT für die API-Authentifizierung.

- **Issuer**: Konfigurierbar via `JWT_ISSUER`
- **Audience**: Muss mit `JWT_AUDIENCE` übereinstimmen
- **Algorithm**: RS256 (empfohlen) oder HS256
- **Expiry**: Konfigurierbar via `JWT_EXPIRY`

#### Setup

```bash
# Generiere RSA-Schlüsselpaar
openssl genrsa -out private.key 2048
openssl rsa -in private.key -pubout -out public.key

# Setze Umgebungsvariablen
export JWT_PRIVATE_KEY="$(cat private.key)"
export JWT_PUBLIC_KEY="$(cat public.key)"
export JWT_ISSUER="zytlog"
export JWT_AUDIENCE="zytlog-api"
```

### Token-Verwaltung

#### Storage

**⚠️ Kritisch**: Tokens dürfen niemals im `localStorage` gespeichert werden (XSS-Risiko). Verwende stattdessen `httpOnly`-Cookies oder secure client-side storage.

**Nicht empfohlen:**
```javascript
// ❌ Unsicher - XSS anfällig
localStorage.setItem('token', jwt);
```

**Empfohlen (Backend-gesetzte Cookies):**
```javascript
// Setze httpOnly Cookie (Backend)
res.cookie('session', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  maxAge: 24 * 60 * 60 * 1000
});
```

**Alternative (In-Memory-Variante):**
```javascript
// ✅ Token nur im Speicher halten, bei Page-Reload neu authentifizieren
let currentToken = null;
// Token nach Login setzen, nach Logout löschen
```

#### Rotation & Revokation

- Tokens sollten mit kurzer Lebensdauer (z.B. 15 Minuten) ausgestellt werden
- Verwende Refresh-Tokens für verlängerte Sitzungen
- Bei Verdacht auf Kompromittierung: `token.equivalent` prüfen und in der DB revoken

**Revokation-Implementierung:**
```sql
-- Tabelle für gesperrte Tokens
CREATE TABLE token_blacklist (
  token_jti VARCHAR(255) PRIMARY KEY,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## API-Sicherheit

### Rate Limiting

- Implementiere pro IP und pro User Limits
- Empfohlene Limits:
  - Auth-Endpoints: 5 Versuche pro Minute
  - Allgemeine API: 1000 Versuche pro Stunde

### CORS

Konfiguriere CORS restriktiv:

```typescript
// backend/src/app.ts
app.use(cors({
  origin: process.env.FRONTEND_URL?.split(',') || ['http://localhost:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
```

### Input Validation

Alle API-Inputs müssen validiert werden (z.B. mit Zod oder class-validator).

## Datenbanksicherheit

- Verwende Prepared Statements / ORM (keine Raw-Queries ohne Escaping)
- Passwörter: bcrypt (mind. cost 12)
- Sensible Daten (PII) verschlüsselt speichern
- Regelmäßige Backups mit Verschlüsselung

## Infrastruktur

### Keycloak

Wenn Keycloak für SSO verwendet wird:

- Nutze TLS für alle Verbindungen
- Deaktiviere anonymen Zugriff
- Konfiguriere starke Passwort-Policies
- Aktiviere Account-Lockout nach mehreren Fehlversuchen
- Überwache Login-Versuche

### Deployment

- Secrets nie im Code-Repository
- Verwende Umgebungsvariablen oder Secret-Management (Vault, AWS Secrets Manager)
- Deine Server sollten regelmäßig gepatcht werden
- Firewall-Regeln auf das notwendige Minimum beschränken

## Monitoring & Auditing

- Logge alle Authentifizierungsversuche (erfolgreich und fehlgeschlagen)
- Protokolliere API-Errors mit Request-ID für Tracing
- Regelmäßige Sicherheitsscans (OWASP ZAP, Snyk)
- Abhängigkeiten auf Vulnerabilität prüfen (`npm audit`, `pip-audit`)

## Checkliste vor Production-Deploy

- [ ] JWT Keys außerhalb des Repos gespeichert
- [ ] Keine `localStorage`-Token
- [ ] CORS korrekt konfiguriert
- [ ] Rate Limiting aktiviert
- [ ] Input Validation auf allen Endpunkten
- [ ] HTTPS/TLS erzwungen
- [ ] Security Headers gesetzt (HSTS, CSP, X-Frame-Options, etc.)
- [ ] Regelmäßige Backups
- [ ] Monitoring & Alerting konfiguriert
- [ ] Incident Response Plan vorhanden

## Vulnerabilitäten melden

Bei Sicherheitsproblemen bitte nicht öffentlich auf GitHub Issues posten, sondern direkten Kontakt: **patrick@blumer.net**

---

**Letzte Aktualisierung**: April 2026
**Verantwortlich**: Security Team