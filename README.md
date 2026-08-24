# PDF-zu-Bild-Konvertierungsservice

Kleiner FastAPI-Service, der ein PDF entgegennimmt und jede Seite als Base64-PNG zurueckgibt.
Genutzt als Fallback-Schritt in n8n, wenn aus einem PDF-Anhang kein Text extrahiert werden konnte
und der Inhalt stattdessen visuell an ein Vision-Modell (z.B. Qwen3.6-27b-nvfp4) gesendet werden soll.

## 1. API-Key setzen

In der Datei `.env` den Platzhalter durch einen eigenen, langen zufaelligen Key ersetzen:

```
API_KEY=hier-einen-langen-zufaelligen-key-eintragen
```

Diesen Key spaeter 1:1 im n8n HTTP Request Node als `Authorization: Bearer <API_KEY>` verwenden.

## 2. Container starten

```bash
docker compose up --build -d
```

Test, ob der Service laeuft:

```bash
curl http://localhost:8000/health
# -> {"status":"ok"}
```

## 3. Mit ngrok oeffentlich erreichbar machen

Da n8n Cloud ist, braucht es eine oeffentliche HTTPS-URL statt localhost:

```bash
ngrok http 8000
```

ngrok gibt dir eine URL wie `https://abc123.ngrok-free.app` aus. Diese URL (Achtung: aendert sich bei
jedem Neustart von ngrok im Free-Tier, dann muss die URL in n8n aktualisiert werden) nutzt du als Ziel
im n8n HTTP Request Node.

## 4. Aufruf testen

```bash
curl -X POST https://abc123.ngrok-free.app/pdf-to-images \
  -H "Authorization: Bearer <API_KEY>" \
  -F "file=@/pfad/zu/testdatei.pdf"
```

Antwort:

```json
{
  "page_count": 2,
  "pages": ["<base64_png_seite1>", "<base64_png_seite2>"]
}
```

## 5. Einbindung in n8n (HTTP Request Node)

- Methode: POST
- URL: `https://abc123.ngrok-free.app/pdf-to-images`
- Authentication: Header Auth
  - Name: `Authorization`
  - Value: `Bearer <API_KEY>`
- Body Content Type: Form-Data (Multipart)
  - Parameter Name: `file`
  - Parameter Type: n8n Binary File
  - Input Data Field Name: `data` (Property-Name aus "Get Anhang3")

Die Antwort (`pages`-Array) kannst du danach direkt in den naechsten Schritt geben, der die Bilder
als `image_url`-Content an das Vision-Modell (Qwen) schickt.

## Hinweise

- `RENDER_DPI` in `.env` steuert die Aufloesung der erzeugten Bilder (150 ist ein guter Standardwert,
  bei sehr kleiner Schrift ggf. auf 200-300 erhoehen, das vergroessert aber auch die Dateigroesse/
  Tokenkosten beim Vision-Modell).
- `MAX_UPLOAD_MB` begrenzt die maximale PDF-Groesse, die verarbeitet wird.
- Der Container laeuft als Nicht-root-User und exponiert ausschliesslich Port 8000.
- Laptop und ngrok muessen laufen, solange der n8n-Workflow diesen Fallback-Pfad nutzen soll.
