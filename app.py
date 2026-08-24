"""
PDF-zu-Bild-Konvertierungsservice
----------------------------------
Nimmt ein PDF per POST entgegen und liefert jede Seite als Base64-kodiertes PNG zurueck.
Nutzt PyMuPDF (fitz) - rendert PDFs komplett in Python, ohne Poppler/Ghostscript-Abhaengigkeit.

Aufruf:
  POST /pdf-to-images
  Header: Authorization: Bearer <API_KEY>
  Body:   multipart/form-data, Feld "file" = PDF-Binaerdaten

Antwort:
  {
    "page_count": 2,
    "pages": ["<base64_png_seite1>", "<base64_png_seite2>"]
  }
"""

import base64
import io
import os

import fitz  # PyMuPDF
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI(title="PDF-to-Image Converter", version="1.0")

# API-Key aus Umgebungsvariable lesen (siehe docker-compose.yml / .env)
API_KEY = os.getenv("API_KEY", "changeme")

# Aufloesung der gerenderten Bilder (150-200 DPI reicht i.d.R. gut fuer Vision-Modelle)
RENDER_DPI = int(os.getenv("RENDER_DPI", "150"))

# Sicherheitslimit gegen ueberdimensionierte Uploads (in MB)
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))


def check_auth(authorization: str | None) -> None:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Fehlender oder ungueltiger Authorization-Header")
    token = authorization.removeprefix("Bearer ").strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Ungueltiger API-Key")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pdf-to-images")
async def pdf_to_images(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    check_auth(authorization)

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail=f"Ungueltiger Dateityp: {file.content_type}")

    pdf_bytes = await file.read()

    size_mb = len(pdf_bytes) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu gross ({size_mb:.1f} MB). Limit: {MAX_UPLOAD_MB} MB",
        )

    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Leere Datei erhalten")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"PDF konnte nicht geoeffnet werden: {exc}")

    if doc.page_count == 0:
        raise HTTPException(status_code=422, detail="PDF enthaelt keine Seiten")

    zoom = RENDER_DPI / 72  # 72 DPI ist die PDF-Standardaufloesung
    matrix = fitz.Matrix(zoom, zoom)

    pages_b64 = []
    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        png_bytes = pix.tobytes("png")
        pages_b64.append(base64.b64encode(png_bytes).decode("ascii"))

    doc.close()

    return JSONResponse(
        content={
            "page_count": len(pages_b64),
            "pages": pages_b64,
        }
    )
