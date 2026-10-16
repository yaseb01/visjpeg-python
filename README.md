# VisJPEG Python

Interaktive JPEG-Kompressions-Visualisierung fuer Studierende.
Konvertiert aus dem originalen Java-Projekt VisJPEG 2.0.

## Schnellstart (3 Schritte)

```bash
# 1. Repository klonen oder herunterladen
cd visjpeg_python

# 2. Abhaengigkeiten installieren
pip install -e .

# 3. Starten
visjpeg
```

Der Browser oeffnet automatisch unter: **http://localhost:8501**

Das war's! Kein Docker, kein X11 noetig.

---

## Systemvoraussetzungen

- Python 3.9 oder neuer
- Ein moderner Webbrowser

## Installation

### Variante A: Mit pip (empfohlen)

```bash
git clone <repo-url>
cd visjpeg_python
pip install -e .
```

Dann starten mit:
```bash
visjpeg
```

### Variante B: Mit virtueller Umgebung (venv)

Sauberste Variante, wenn man nichts am systemweiten Python veraendern moechte
(z. B. im Hoersaal-, Pool- oder Heimarbeitsplatz):

```bash
git clone <repo-url>
cd visjpeg_python

# 1. Virtuelle Umgebung anlegen (einmalig)
python3 -m venv .venv           # Windows: py -m venv .venv

# 2. Aktivieren (in jedem neuen Terminal)
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3. Installieren und starten
pip install -e .
visjpeg
```

Hinweise:
- Vor jedem Start nur noch Schritt 2 (Aktivieren) noetig, danach `visjpeg`.
- Beenden der Umgebung: `deactivate`.
- Zum Aufraeumen einfach den Ordner `.venv` loeschen.

### Variante C: Ohne Installation (direkt aus dem Ordner)

```bash
cd visjpeg_python
pip install -r requirements.txt
python -m visjpeg
```

### Variante D: Mit Docker

```bash
cd visjpeg_python
docker-compose up --build
```

Oder manuell:
```bash
docker build -t visjpeg .
docker run -p 8501:8501 visjpeg
```

## Nutzung

1. **Bild waehlen**: In der Seitenleiste ein Beispielbild auswaehlen oder ein eigenes hochladen.
2. **Block auswaehlen**: Klicke direkt auf das Y-Bild, um einen 8x8-Block zu waehlen. Alternativ: Pfeil-Buttons darunter.
3. **Schritt-fuer-Schritt**: Die 6 Schritte der JPEG-Kompression durchgehen (Weiter/Zurueck-Buttons oder Radio-Auswahl):
    - **Farbraum**: RGB → YIQ Konvertierung und Subsampling
    - **DCT**: Diskrete Cosinus-Transformation
    - **Quantisierung**: Quantisierung und Dequantisierung + Blockvergleich Original vs. Rekonstruiert
    - **Zick-Zack**: Zick-Zack-Scan der Koeffizienten
    - **DPCM + RLE**: Differenzielle DC-Kodierung und Lauflaengenkodierung
    - **Entropie**: Huffman-Kodierung mit sortierbaren Tabellen und Bitlaengen-Histogrammen
4. **Parameter veraendern**: Qualitaetsfaktor und Subsampling in der Seitenleiste anpassen.

## Features

- 15 Beispielbilder inklusive
- Eigenes Bild hochladen (JPG, PNG, GIF, BMP)
- **Klick-Auswahl** des 8x8-Blocks (Plotly) + D-Pad-Fallback
- Schritt-fuer-Schritt-Navigation (Weiter/Zurueck)
- **Kompressionsrate** und Bits-pro-Pixel in der Uebersicht
- **Blockvergleich** Original vs. Rekonstruiert (Quantisierungs-Tab)
- **Huffman-Tabellen** als sortierbare DataFrames + Bitlaengen-Histogramme
- Live-DCT, Quantisierung, Zick-Zack-Scan
- RLE- und DPCM-Darstellung
- Differenzbild-Ansicht
- Automatischer Browser-Start
- Keine Kompilierung noetig

## Projektstruktur

```
visjpeg_python/
├── pyproject.toml          # Paket-Definition
├── requirements.txt        # Python-Abhaengigkeiten
├── run.py                  # Direktstart (ohne Installation)
├── Dockerfile              # Docker-Image
├── docker-compose.yml      # Docker Compose
├── tests/
│   └── test_pipeline.py    # Pipeline-Golden-Tests
└── visjpeg/
    ├── __init__.py
    ├── __main__.py         # Einstiegspunkt fuer python -m visjpeg
    ├── streamlit_app.py    # Streamlit-Web-App
    ├── jpeg_image.py       # Bildladen, YIQ, DCT, etc. (numpy-beschleunigt)
    ├── block.py            # Block, FloatBlock, BlockVektor
    ├── matrix.py           # 8x8 Matrix-Klasse
    ├── jpeg_parameter.py   # JPEG-Parameter, Quantisierungsmatrizen
    ├── huffman.py          # Huffman-Kodierung
    └── rle.py              # RLE-Symbolklassen
```

## Architektur

Die Kernalgorithmen sind unabhaengig vom GUI:

- `jpeg_image.py` laedt Bilder und fuehrt YIQ-Konvertierung, Subsampling, DCT, Quantisierung durch (numpy-beschleunigt).
- `block.py` enthaelt die schnelle 8x8 DCT/iDCT, Zig-Zag-Scan und 3D-Balkendiagramme.
- `huffman.py` und `rle.py` implementieren die Entropie-Kodierung.

Die **Streamlit-App** (`streamlit_app.py`) nutzt diese Module und stellt sie im Browser dar.

## Technische Details

- **GUI**: Streamlit (Web-App, laeuft im Browser)
- **Interaktion**: Plotly (Klick-Auswahl)
- **Bildverarbeitung**: Pillow (PIL)
- **Mathematik**: NumPy (vektorisiert)
- **Keine Abhaengigkeit von**: Java, X11

## Troubleshooting

### Port 8501 ist bereits belegt

VisJPEG waehlt automatisch einen freien Port. Alternativ manuell:

```bash
visjpeg --server.port 8502
```

### Bilder werden nicht angezeigt

Stelle sicher, dass die Beispielbilder im Ordner `visjpeg/` liegen:
```bash
ls visjpeg/*.jpg visjpeg/*.gif
```

### Streamlit nicht gefunden

```bash
pip install streamlit Pillow numpy matplotlib plotly
```

### Tests ausfuehren

```bash
pip install pytest
pytest tests/ -v
```

## Lizenz

MIT License - siehe original VisJPEG 2.0.
