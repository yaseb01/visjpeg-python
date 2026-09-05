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

Oeffne dann deinen Browser unter: **http://localhost:8501**

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

### Variante B: Ohne Installation (direkt aus dem Ordner)

```bash
cd visjpeg_python
pip install -r requirements.txt
python -m visjpeg
```

### Variante C: Falls pip Probleme macht

```bash
cd visjpeg_python
pip install Pillow streamlit numpy
python -m visjpeg
```

## Nutzung

1. **Bild waehlen**: In der Seitenleiste ein Beispielbild auswaehlen oder ein eigenes hochladen.
2. **Block markieren**: Im DCT-Tab mit den Pfeil-Buttons den gelb markierten 8x8-Block verschieben.
3. **Durch die Tabs klicken**: Die 6 Schritte der JPEG-Kompression durchgehen:
    - **Farbraum**: RGB → YIQ Konvertierung und Subsampling
    - **DCT**: Diskrete Cosinus-Transformation
    - **Quantisierung**: Quantisierung und Dequantisierung
    - **Zick-Zack**: Zick-Zack-Scan der Koeffizienten
    - **DPCM + RLE**: Differenzielle DC-Kodierung und Lauflaengenkodierung
    - **Entropie**: Huffman-Kodierung
4. **Parameter veraendern**: Qualitaetsfaktor und Subsampling in der Seitenleiste anpassen.

## Features

- 11 Beispielbilder inklusive
- Eigenes Bild hochladen (JPG, PNG, GIF, BMP)
- Interaktive 8x8-Block-Auswahl
- Live-DCT, Quantisierung, Zick-Zack-Scan
- RLE- und DPCM-Darstellung
- Differenzbild-Ansicht
- Keine Kompilierung noetig

## Projektstruktur

```
visjpeg_python/
├── pyproject.toml          # Paket-Definition
├── requirements.txt        # Python-Abhaengigkeiten
├── run.py                  # Direktstart (ohne Installation)
└── visjpeg/
    ├── __init__.py
    ├── __main__.py         # Einstiegspunkt fuer python -m visjpeg
    ├── streamlit_app.py    # Streamlit-Web-App
    ├── jpeg_image.py       # Bildladen, YIQ, DCT, etc.
    ├── block.py            # Block, FloatBlock, BlockVektor
    ├── matrix.py           # 8x8 Matrix-Klasse
    ├── jpeg_parameter.py   # JPEG-Parameter, Quantisierungsmatrizen
    ├── huffman.py          # Huffman-Kodierung
    └── rle.py              # RLE-Symbolklassen
```

## Architektur

Die Kernalgorithmen sind unabhaengig vom GUI:

- `jpeg_image.py` laedt Bilder und fuehrt YIQ-Konvertierung, Subsampling, DCT, Quantisierung durch.
- `block.py` enthaelt die schnelle 8x8 DCT/iDCT, Zig-Zag-Scan und 3D-Balkendiagramme.
- `huffman.py` und `rle.py` implementieren die Entropie-Kodierung.

Die **Streamlit-App** (`streamlit_app.py`) nutzt diese Module und stellt sie im Browser dar.

## Technische Details

- **GUI**: Streamlit (Web-App, laeuft im Browser)
- **Bildverarbeitung**: Pillow (PIL)
- **Mathematik**: Python-Standardbibliothek + NumPy
- **Keine Abhaengigkeit von**: Java, Docker, X11

## Troubleshooting

### Port 8501 ist bereits belegt

```bash
visjpeg --server.port 8502
```

Oder im Browser: http://localhost:8502

### Bilder werden nicht angezeigt

Stelle sicher, dass die Beispielbilder im Ordner `visjpeg/` liegen:
```bash
ls visjpeg/*.jpg visjpeg/*.gif
```

### Streamlit nicht gefunden

```bash
pip install streamlit
```

### Pillow nicht gefunden

```bash
pip install Pillow
```

## Lizenz

MIT License - siehe original VisJPEG 2.0.
