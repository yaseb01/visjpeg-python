"""
VisJPEG Python - Streamlit Web UI
Einfache Browser-basierte Visualisierung der JPEG-Kompression.
Kein tkinter oder Docker noetig!
"""

import os
import sys
import io
import base64
import math
import tempfile
import hashlib
from PIL import Image, ImageDraw
import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Fix for streamlit direct execution: ensure visjpeg package is importable
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_MODULE_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from visjpeg.jpeg_image import JPEGImage
from visjpeg.jpeg_parameter import JPEGParameter, GUIParameter
from visjpeg.block import Block, FloatBlock, BlockVektor


def pil_to_bytes(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

STANDARD_BILDER = [
    os.path.join(_MODULE_DIR, "test2.gif"),
    os.path.join(_MODULE_DIR, "test3.gif"),
    os.path.join(_MODULE_DIR, "test4.gif"),
    os.path.join(_MODULE_DIR, "test5.gif"),
    os.path.join(_MODULE_DIR, "tria.jpg"),
    os.path.join(_MODULE_DIR, "shuttle.jpg"),
    os.path.join(_MODULE_DIR, "monument.jpg"),
    os.path.join(_MODULE_DIR, "monument2.jpg"),
    os.path.join(_MODULE_DIR, "schrift.jpg"),
    os.path.join(_MODULE_DIR, "schloss.jpg"),
    os.path.join(_MODULE_DIR, "ayersrock.jpg"),
    os.path.join(_MODULE_DIR, "sample-boat-400x300.png"),
    os.path.join(_MODULE_DIR, "sample-hut-400x300.png"),
    os.path.join(_MODULE_DIR, "sample-bumblebee-400x300.png"),
    os.path.join(_MODULE_DIR, "sample-clouds2-400x300.png"),
]

BILD_NAMEN = [
    "Haus (192x144)", "Raytrace-Ringe (800x600)", "Papageien (192x128)",
    "Raytrace-Bruecke (192x144)", "Triathlon (384x288)",
    "Space Shuttle (512x384)", "Monument Valley (192x144)",
    "Monument Valley 2 (192x144)", "Schrift (192x144)",
    "Neuschwanstein (512x384)", "Ayers Rock (365x237)",
    "Boot (400x300)", "Hexenhaus (400x300)", "Hummel (400x300)", "Wolken (400x300)"
]

SCHRITT_NAMEN = [
    "Uebersicht",
    "1. Farbraum",
    "2. DCT",
    "3. Quantisierung",
    "4. Zick-Zack",
    "5. DPCM + RLE",
    "6. Entropie"
]


def get_state():
    if "parameter" not in st.session_state:
        st.session_state.parameter = JPEGParameter()
        st.session_state.our_image = None
        st.session_state.marker_x = 0
        st.session_state.marker_y = 0
        st.session_state.differenzbild = False
        st.session_state.uploaded_file_id = None
    return st.session_state


def init_image(path):
    state = get_state()
    state.our_image = JPEGImage(path)
    state.parameter.filename = path
    state.marker_x = 0
    state.marker_y = 0


def get_image_or_placeholder(path):
    if os.path.exists(path):
        return path
    return None


def show_matrix(matrix, title=""):
    """Zeigt eine 8x8 Matrix als Tabelle."""
    data = []
    for y in range(8):
        row = []
        for x in range(8):
            val = matrix[x][y]
            if isinstance(val, float):
                row.append(f"{val:.1f}")
            else:
                row.append(str(int(val)))
        data.append(row)
    st.write(f"**{title}**")
    st.table(data)


def show_image_pair(left_img, right_img, left_caption="", right_caption=""):
    col1, col2 = st.columns(2)
    with col1:
        st.image(left_img, caption=left_caption, width="stretch")
    with col2:
        st.image(right_img, caption=right_caption, width="stretch")


def matrix_to_image(matrix, size=256):
    """Wandelt eine 8x8 int-Matrix in ein Graustufen-PIL Image um.
    Invertierte Skala: kleine Matrixwerte (feine Schrittweite) -> weiss,
    grosse Matrixwerte (grobe Schrittweite) -> schwarz."""
    img = Image.new("L", (8, 8))
    for y in range(8):
        for x in range(8):
            val = max(0, min(255, int(matrix[x][y])))
            img.putpixel((x, y), 255 - val)
    return img.resize((size, size), Image.NEAREST)


def subsample_reconstruct(sub_img, h_sub, v_sub, target_size=(192, 144)):
    """Vergroessert ein subsampeltes Bild auf Zielgroesse (Nearest-Neighbor).
    Zeigt das echte Untertastungs-Ergebnis ohne Gitter-Linien."""
    return sub_img.convert("L").resize(target_size, Image.NEAREST).convert("RGB")


def subsample_pattern(sub_img, h_sub, v_sub, target_size=(192, 144)):
    """Zeigt nur die Abtastpositionen: beibehaltene Positionen mit Mittelwert-Grauwert,
    alle entfallenen Positionen weiss."""
    w, ht = target_size
    canvas = np.full((ht, w), 255, dtype=np.uint8)
    sub_arr = np.array(sub_img, dtype=np.uint8)
    canvas[::v_sub, ::h_sub] = sub_arr
    return Image.fromarray(canvas, mode="L").convert("RGB")


def block_navigator_plotly(img, state):
    """Zeigt das Y-Bild mit Plotly-Klickauswahl + D-Pad."""
    y_arr = np.array(img.get_y_image())
    h, w = y_arr.shape

    # Block-Rechteck-Koordinaten
    bx, by = state.marker_x, state.marker_y
    rect_x = [bx, bx+8, bx+8, bx, bx]
    rect_y = [by, by, by+8, by+8, by]

    fig = go.Figure()

    # Y-Bild als Heatmap
    fig.add_trace(go.Heatmap(
        z=y_arr,
        colorscale="Gray",
        showscale=False,
        hovertemplate="Pixel (%{x}, %{y})<br>Wert: %{z}<extra></extra>"
    ))

    # Block-Rechteck
    fig.add_trace(go.Scatter(
        x=rect_x, y=rect_y,
        mode="lines",
        line=dict(color="yellow", width=3),
        hoverinfo="skip",
        showlegend=False
    ))

    fig.update_layout(
        width=400, height=320,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(scaleanchor="x", scaleratio=1, range=[h, 0]),
        xaxis=dict(range=[0, w]),
        title=f"Block ({bx}, {by})",
    )

    event = st.plotly_chart(fig, on_select="rerun", key="block_select")

    # Klick-Verarbeitung
    if event and hasattr(event, 'selection') and event.selection:
        points = event.selection.get("points", [])
        if points:
            px = points[0].get("x", None)
            py = points[0].get("y", None)
            if px is not None and py is not None:
                new_bx = (int(px) // 8) * 8
                new_by = (int(py) // 8) * 8
                new_bx = max(0, min(w - 8, new_bx))
                new_by = max(0, min(h - 8, new_by))
                if new_bx != state.marker_x or new_by != state.marker_y:
                    state.marker_x = new_bx
                    state.marker_y = new_by
                    state.our_image.set_marker(new_bx, new_by)
                    st.rerun()

    # D-Pad als Fallback
    def move(dx, dy):
        new_x = max(0, min(w - 8, state.marker_x + dx))
        new_y = max(0, min(h - 8, state.marker_y + dy))
        if new_x != state.marker_x or new_y != state.marker_y:
            state.marker_x = new_x
            state.marker_y = new_y
            state.our_image.set_marker(new_x, new_y)
            st.rerun()

    cols = st.columns([1, 1, 1, 1, 1])
    with cols[1]:
        if st.button("▲", key="nav_up", width="stretch"):
            move(0, -8)
    with cols[0]:
        if st.button("◄", key="nav_left", width="stretch"):
            move(-8, 0)
    with cols[2]:
        if st.button("►", key="nav_right", width="stretch"):
            move(8, 0)
    with cols[3]:
        if st.button("▼", key="nav_down", width="stretch"):
            move(0, 8)
    with cols[4]:
        st.markdown(
            f"<div style='text-align:center; font-family:monospace; font-size:13px; padding-top:8px;'>"
            f"x={state.marker_x}, y={state.marker_y}</div>",
            unsafe_allow_html=True
        )


def _get_subsample_label(h, v):
    if h == 1 and v == 1:
        return "4:4:4 (kein Subsampling)"
    elif h == 2 and v == 1:
        return "4:2:2"
    elif h == 2 and v == 2:
        return "4:2:0"
    else:
        return "4:1:1"


def run_app():
    st.set_page_config(page_title="VisJPEG", page_icon="📷", layout="wide")
    st.title("📷 VisJPEG - JPEG-Kompressions-Visualisierung")
    st.markdown("Interaktive Visualisierung der JPEG-Kompression. Waehle ein Bild und einen Schritt aus.")

    state = get_state()

    # Sidebar: Bildauswahl und Parameter
    with st.sidebar:
        st.header("Bild & Parameter")

        # Bildauswahl
        auswahl = st.selectbox("Beispielbild", BILD_NAMEN, index=0)
        idx = BILD_NAMEN.index(auswahl)
        path = STANDARD_BILDER[idx]

        # Wechsel der Standardbild-Auswahl verwirft einen laufenden Upload
        auswahl_geaendert = state.get("last_auswahl") != auswahl
        if auswahl_geaendert:
            state.last_auswahl = auswahl

        # Eigenes Bild hochladen
        uploaded = st.file_uploader("Eigenes Bild", type=["jpg", "jpeg", "png", "gif", "bmp"])
        zeige_standard = True
        if uploaded is not None:
            file_bytes = uploaded.getvalue()
            file_id = hashlib.md5(file_bytes).hexdigest()
            if auswahl_geaendert and state.get("uploaded_file_id") == file_id:
                # Nutzer hat explizit ein Standardbild gewaehlt -> Upload verwerfen
                state.uploaded_file_id = None
                state.dismissed_upload_id = file_id
            if file_id != state.get("dismissed_upload_id") and file_id != state.uploaded_file_id:
                img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                tmp_path = os.path.join(tempfile.gettempdir(), "visjpeg_upload.png")
                img.save(tmp_path)
                state.uploaded_file_id = file_id
                init_image(tmp_path)
                zeige_standard = False
            elif state.uploaded_file_id == file_id:
                # Aktiver Upload bleibt bestehen (Bugfix: wurde vorher bei jedem
                # Rerun durch die Standardbild-Auswahl ueberschrieben)
                zeige_standard = False

        if zeige_standard and (state.our_image is None or state.parameter.filename != path):
            real_path = get_image_or_placeholder(path)
            if real_path:
                init_image(real_path)
            else:
                st.warning(f"Bild nicht gefunden: {path}")
                return

        # Subsampling
        st.subheader("Subsampling")
        subsample = st.selectbox("Cr/Cb Subsampling", ["4:4:4 (kein Subsampling)", "4:2:2", "4:2:0", "4:1:1"], index=2)
        if subsample == "4:4:4 (kein Subsampling)":
            neu_h, neu_v = 1, 1
        elif subsample == "4:2:2":
            neu_h, neu_v = 2, 1
        elif subsample == "4:2:0":
            neu_h, neu_v = 2, 2
        else:
            neu_h, neu_v = 4, 1
        # Nur bei tatsaechlicher Aenderung invalidieren (Bugfix: vorher lief
        # invalidate() bei jedem Rerun und wischte alle Caches weg)
        if (neu_h, neu_v) != (state.parameter.h_subsample, state.parameter.v_subsample):
            state.parameter.h_subsample = neu_h
            state.parameter.v_subsample = neu_v
            if state.our_image:
                state.our_image.invalidate()

        # Qualitaetsfaktor
        st.subheader("Qualitaet")
        qf = st.slider("Quantisierungsfaktor", 1, 100, state.parameter.q_faktor)
        if qf != state.parameter.q_faktor:
            state.parameter.q_faktor = qf
            state.parameter.q_matrix_lum = JPEGParameter.STANDARD_QMATRIX_LUM.clone()
            state.parameter.q_matrix_lum.scale(qf)
            state.parameter.q_matrix_chrom = JPEGParameter.STANDARD_QMATRIX_CHROM.clone()
            state.parameter.q_matrix_chrom.scale(qf)
            if state.our_image:
                state.our_image.invalidate()

        # Ansicht
        st.subheader("Ansicht")
        state.differenzbild = st.checkbox("Differenzbild", value=state.differenzbild)

    if state.our_image is None:
        st.info("Bitte waehle ein Bild in der Seitenleiste aus.")
        return

    img = state.our_image
    p = state.parameter

    # Block-Navigator: Plotly-Klickauswahl (immer sichtbar)
    block_navigator_plotly(img, state)

    # Schritt-Navigation: Radio + Weiter/Zurueck.
    # Das Radio verwaltet seinen Zustand selbst ueber einen stabilen key;
    # die Buttons schreiben denselben Session-State. Wichtig: KEIN index=
    # uebergeben! Bei einem keyless-Radio fliesst index in die Widget-ID ein
    # – bei jedem Schrittwechsel haette das Radio eine neue Identitaet, und
    # Klicks muessen im Browser teils doppelt erfolgen, bis Frontend- und
    # Backend-Zustand wieder uebereinstimmen.
    st.markdown("---")

    if "schritt_nav" not in st.session_state:
        st.session_state.schritt_nav = SCHRITT_NAMEN[0]
    aktueller_index = SCHRITT_NAMEN.index(st.session_state.schritt_nav)

    nav_cols = st.columns([1, 6, 1])
    with nav_cols[0]:
        if st.button("← Zurueck", width="stretch", disabled=(aktueller_index == 0)):
            st.session_state.schritt_nav = SCHRITT_NAMEN[aktueller_index - 1]
            st.rerun()
    with nav_cols[2]:
        if st.button("Weiter →", width="stretch", disabled=(aktueller_index == len(SCHRITT_NAMEN) - 1)):
            st.session_state.schritt_nav = SCHRITT_NAMEN[aktueller_index + 1]
            st.rerun()

    schritt = st.radio(
        "Schritt",
        SCHRITT_NAMEN,
        horizontal=True,
        label_visibility="collapsed",
        key="schritt_nav",
    )

    st.markdown("---")

    # Schritt-Inhalt
    step = SCHRITT_NAMEN.index(schritt)

    if step == 0:
        # Uebersicht
        st.header("Original vs. Komprimiert")
        orig = img.get_image()
        if state.differenzbild:
            comp = img.get_difference_image(p)
        else:
            comp = img.get_decompressed_jpeg_image(p)
        show_image_pair(orig, comp, "Originalbild", "JPEG-komprimiert" if not state.differenzbild else "Differenzbild")

        # Metriken
        psnr = img.get_psnr(p)
        if psnr == float('inf'):
            psnr_text = "∞ (verlustfrei)"
        else:
            psnr_text = f"{psnr:.2f} dB"

        with st.spinner("Berechne Kompressionsstatistiken..."):
            _, _, _, _, total_bits = img.get_huffman_stats(p)

        original_bits = 192 * 144 * 3 * 8
        compression_ratio = original_bits / total_bits if total_bits > 0 else 0
        bpp = total_bits / (192 * 144)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("PSNR", psnr_text,
                      help="Hoehere PSNR = bessere Qualitaet. Typisch: >40 dB = sehr gut, 30-40 dB = gut, <30 dB = sichtbare Artefakte.")
        with m2:
            st.metric("Kompressionsrate", f"{compression_ratio:.1f}:1",
                      help="Originalgroesse / Komprimierte Groesse. Hoehere Zahl = staerker komprimiert.")
        with m3:
            st.metric("Bits pro Pixel", f"{bpp:.2f} bpp",
                      help="Benötigte Bits pro Pixel. Unkomprimiert: 24 bpp. JPEG typisch: 0.5–3 bpp.")

    elif step == 1:
        # Farbraum
        st.header("Schritt 1: Farbraumkonvertierung")
        st.markdown("Konvertierung von RGB nach YCrCb mit optionalem Subsampling der Chrominanz-Kanaele.")

        # Zeile 1: RGB
        cr, cg, cb = st.columns(3)
        with cr:
            st.image(img.get_r_image(), caption="Rotkanal", width="stretch")
        with cg:
            st.image(img.get_g_image(), caption="Gruenkanal", width="stretch")
        with cb:
            st.image(img.get_b_image(), caption="Blaukanal", width="stretch")

        st.markdown("---")

        # Zeile 2: Y, Cr, Cb nebeneinander – gleiche Anzeigegröße
        i_img = img.get_i_image(p.h_subsample, p.v_subsample)
        q_img = img.get_q_image(p.h_subsample, p.v_subsample)

        anteil = round((1 - 1 / (p.h_subsample * p.v_subsample)) * 100)
        st.subheader("YCrCb-Kanaele & Subsampling")
        st.caption(
            f"**Subsampling {subsample}:** Aus jedem **{p.h_subsample}×{p.v_subsample}-Block** wird "
            f"1 Abtastwert (Mittelwert) – **{anteil}% der Chroma-Pixel entfallen**. "
            f"Cr/Cb: **{i_img.width}×{i_img.height} px** statt 192×144 px. "
            f"Unten rekonstruiert auf Y-Größe (Nearest-Neighbor)."
        )

        cy, ci, cq = st.columns(3)
        with cy:
            st.image(img.get_y_image(), caption="Y-Kanal (Helligkeit), 192×144 px", width="stretch")
        with ci:
            st.image(
                subsample_reconstruct(i_img, p.h_subsample, p.v_subsample),
                caption=f"Cb-Kanal rekonstruiert ({i_img.width}×{i_img.height} → 192×144)",
                width="stretch"
            )
        with cq:
            st.image(
                subsample_reconstruct(q_img, p.h_subsample, p.v_subsample),
                caption=f"Cr-Kanal rekonstruiert ({q_img.width}×{q_img.height} → 192×144)",
                width="stretch"
            )

        # Zeile 3: Abtast-Positionen (nur bei aktivem Subsampling)
        if p.h_subsample > 1 or p.v_subsample > 1:
            st.subheader("Abtast-Positionen – weiße Pixel entfallen")
            st.caption(
                f"Nur die eingetragenen Positionen werden abgetastet "
                f"(jeweils der Mittelwert des {p.h_subsample}×{p.v_subsample}-Blocks); "
                f"alle weißen Pixel entfallen und werden nicht gespeichert."
            )
            cp1, cp2 = st.columns(2)
            with cp1:
                st.image(
                    subsample_pattern(i_img, p.h_subsample, p.v_subsample),
                    caption=f"Cb: Abtast-Positionen ({i_img.width}×{i_img.height} → 192×144)",
                    width="stretch"
                )
            with cp2:
                st.image(
                    subsample_pattern(q_img, p.h_subsample, p.v_subsample),
                    caption=f"Cr: Abtast-Positionen ({q_img.width}×{q_img.height} → 192×144)",
                    width="stretch"
                )

        # Echte Auflösung im Expander
        if p.h_subsample > 1 or p.v_subsample > 1:
            with st.expander("Echte (reduzierte) Auflösung von Cr/Cb anzeigen"):
                col_i, col_q = st.columns(2)
                with col_i:
                    st.image(i_img, caption=f"Cb-Kanal original ({i_img.width}×{i_img.height} px)", width="stretch")
                with col_q:
                    st.image(q_img, caption=f"Cr-Kanal original ({q_img.width}×{q_img.height} px)", width="stretch")

    elif step == 2:
        # DCT
        st.header("Schritt 2: Diskrete Cosinus-Transformation (DCT)")

        block = img.get_marked_block()
        dct_block = block.get_dct()

        c1, c2 = st.columns(2)
        with c1:
            show_matrix(block.matrix, "Originalwerte (8x8 Block)")
            st.image(block.paint_bar3d(300, 200, (0, 0, 255)), caption="3D-Visualisierung Original", width="stretch")
        with c2:
            show_matrix([[round(v, 1) for v in row] for row in dct_block.matrix], "DCT-transformierte Werte")
            st.image(dct_block.paint_bar3d(300, 200, (0, 0, 255)), caption="3D-Visualisierung DCT", width="stretch")

    elif step == 3:
        # Quantisierung
        st.header("Schritt 3: Quantisierung")
        block = img.get_marked_block()
        dct = block.get_dct()
        quant = dct.get_quantisiert(p.q_matrix_lum)
        dequant = quant.get_dequantisiert(p.q_matrix_lum)
        reconstructed = dequant.get_idct()

        c1, c2, c3 = st.columns(3)
        with c1:
            show_matrix(p.q_matrix_lum.matrix, "Quantisierungsmatrix")
            st.image(matrix_to_image(p.q_matrix_lum.matrix),
                     caption="Quantisierungsmatrix – Helligkeit = Schrittweite (weiß=fein, schwarz=grob)",
                     width="stretch")
        with c2:
            show_matrix(quant.matrix, "Quantisierte Werte")
            st.image(quant.paint_bar3d(300, 200, (0, 128, 0)), caption="3D-Visualisierung quantisiert", width="stretch")
        with c3:
            show_matrix([[round(v) for v in row] for row in dequant.matrix], "Dequantisierte Werte")
            st.image(dequant.paint_bar3d(300, 200, (0, 128, 0)), caption="3D-Visualisierung dequantisiert", width="stretch")

        # Blockvergleich: Original vs. Rekonstruiert
        st.subheader("Blockvergleich: Original vs. Rekonstruiert")

        def _block_to_zoomed_img(block_matrix, size=128):
            arr = np.array(block_matrix, dtype=np.int32).T
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr, mode="L")
            return img.resize((size, size), Image.NEAREST)

        col_orig, col_recon, col_diff = st.columns(3)
        with col_orig:
            st.image(_block_to_zoomed_img(block.matrix), caption="Original-Block (8x8 → 128x128)", width="stretch")
        with col_recon:
            st.image(_block_to_zoomed_img(reconstructed.matrix), caption="Rekonstruierter Block", width="stretch")
        with col_diff:
            diff_arr = np.abs(np.array(block.matrix, dtype=np.int32) - np.array(reconstructed.matrix, dtype=np.int32)).T
            diff_arr = np.clip(diff_arr * 4, 0, 255).astype(np.uint8)
            diff_img = Image.fromarray(diff_arr, mode="L").resize((128, 128), Image.NEAREST)
            st.image(diff_img, caption="Differenz (verstaerkt 4x)", width="stretch")

        max_diff = max(abs(block.matrix[x][y] - reconstructed.matrix[x][y]) for x in range(8) for y in range(8))
        st.info(f"Maximaler Pixel-Fehler: {max_diff} (bei Qualitaet {p.q_faktor})")

    elif step == 4:
        # Zick-Zack
        st.header("Schritt 4: Zick-Zack-Scan")
        block = img.get_marked_block()
        dct = block.get_dct()
        quant = dct.get_quantisiert(p.q_matrix_lum)
        vec = quant.get_zig_zag_scan()

        st.write("**Zick-Zack-geordnete Koeffizienten (64 Werte):**")
        st.code(" ".join(str(v) for v in vec.werte), language="text")

        st.image(vec.paint_bar(600, 200, (255, 0, 0)), caption="Balkendiagramm der Zick-Zack-Werte", width="stretch")

        st.markdown("""
        Der Zick-Zack-Scan ordnet die 8x8-Koeffizienten so an, dass niedrige Frequenzen (oben links) zuerst kommen.
        Dadurch entstehen lange Nullfolgen am Ende, die sich gut mit RLE komprimieren lassen.
        """)

    elif step == 5:
        # DPCM + RLE
        st.header("Schritt 5: DPCM- und RLE-Kodierung")
        block = img.get_marked_block()
        dct = block.get_dct()
        quant = dct.get_quantisiert(p.q_matrix_lum)
        vec = quant.get_zig_zag_scan()
        rle = vec.get_rle_compressed()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("DC-Wert (DPCM)")
            st.metric("DC-Wert dieses Blocks", rle.dc_value)
            st.markdown("Der DC-Wert wird differentiell kodiert (DPCM): nur die Differenz zum vorherigen Block wird gespeichert.")
        with c2:
            st.subheader("AC-Werte (RLE)")
            st.write("RLE-Symbole (Run-Length-Encoding):")
            symbols_text = []
            for sym in rle.rle_folge.symbols:
                if hasattr(sym, 'amplitude'):
                    symbols_text.append(f"Amplitude: {sym.amplitude}")
                else:
                    if sym.zero_count == 0 and sym.size_non_zero == 0:
                        symbols_text.append("EOB (End of Block)")
                    else:
                        symbols_text.append(f"({sym.zero_count} Nullen, Groesse {sym.size_non_zero})")
            st.code("\n".join(symbols_text), language="text")

        # RLE Visualisierung
        st.subheader("RLE-Kodierung Visualisierung")
        
        # Zig-Zag Vektor als farbige Tabelle
        st.write("**Zick-Zack-Scan mit Null-Markierung:**")
        zigzag_colors = []
        zigzag_vals = []
        for i, val in enumerate(vec.werte):
            zigzag_vals.append(str(val))
            if val == 0:
                zigzag_colors.append("background-color: #ffcccc")
            elif i == 0:
                zigzag_colors.append("background-color: #ccccff")
            else:
                zigzag_colors.append("background-color: #ccffcc")
        
        html_rows = []
        for row_start in range(0, 64, 8):
            row_html = "<tr>"
            for i in range(row_start, min(row_start + 8, 64)):
                row_html += f'<td style="{zigzag_colors[i]}; text-align:center; padding:8px; border:1px solid #999; font-family:monospace;">{zigzag_vals[i]}</td>'
            row_html += "</tr>"
            html_rows.append(row_html)
        
        st.markdown(
            f'<table style="border-collapse:collapse; margin:10px 0;">{"".join(html_rows)}</table>'
            f'<div><span style="background:#ccccff; padding:2px 8px;">DC (Blau)</span> '
            f'<span style="background:#ccffcc; padding:2px 8px; margin-left:10px;">AC ≠ 0 (Gruen)</span> '
            f'<span style="background:#ffcccc; padding:2px 8px; margin-left:10px;">AC = 0 (Rot)</span></div>',
            unsafe_allow_html=True
        )

        # RLE-Dekodierung als Schritte
        st.write("**RLE-Dekodierung Schritt-fuer-Schritt:**")
        
        rle_steps = []
        pos = 1
        for sym_idx, sym in enumerate(rle.rle_folge.symbols):
            if hasattr(sym, 'zero_count'):
                if sym.zero_count == 0 and sym.size_non_zero == 0:
                    rle_steps.append({
                        "Schritt": sym_idx + 1,
                        "Symbol": "EOB",
                        "Bedeutung": "End of Block",
                        "Positionen": f"{pos}-63",
                        "Werte": "Rest mit 0 auffuellen"
                    })
                    break
                else:
                    next_pos = pos + sym.zero_count + 1
                    rle_steps.append({
                        "Schritt": sym_idx + 1,
                        "Symbol": f"({sym.zero_count}, {sym.size_non_zero})",
                        "Bedeutung": f"{sym.zero_count} Nullen + 1 Nicht-Null-Wert",
                        "Positionen": f"{pos}-{next_pos-1}" if sym.zero_count > 0 else str(pos),
                        "Werte": f"{'0, ' * sym.zero_count}X" if sym.zero_count > 0 else "X"
                    })
                    pos = next_pos
        
        if rle_steps:
            st.table(rle_steps)
        
        # Grafische Darstellung der Lauflaengen
        st.write("**Grafische Darstellung der RLE-Lauflaengen:**")
        
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 3))
        
        current_x = 0
        colors_map = {'zero': '#ff6b6b', 'value': '#4ecdc4', 'eob': '#ffe66d'}
        legend_entries = []
        
        for sym in rle.rle_folge.symbols:
            if hasattr(sym, 'zero_count'):
                if sym.zero_count == 0 and sym.size_non_zero == 0:
                    ax.barh(0, 64 - current_x, left=current_x, color=colors_map['eob'], edgecolor='black', height=0.5)
                    if 'eob' not in [e[0] for e in legend_entries]:
                        legend_entries.append(('eob', 'EOB (Rest = 0)'))
                    break
                else:
                    if sym.zero_count > 0:
                        ax.barh(0, sym.zero_count, left=current_x, color=colors_map['zero'], edgecolor='black', height=0.5)
                        current_x += sym.zero_count
                        if 'zero' not in [e[0] for e in legend_entries]:
                            legend_entries.append(('zero', 'Nullen'))
                    
                    ax.barh(0, 1, left=current_x, color=colors_map['value'], edgecolor='black', height=0.5)
                    current_x += 1
                    if 'value' not in [e[0] for e in legend_entries]:
                        legend_entries.append(('value', 'Nicht-Null-Wert'))
        
        ax.set_xlim(0, 64)
        ax.set_xlabel("Position im Zick-Zack-Vektor (0-63)")
        ax.set_yticks([])
        ax.set_title("RLE-Kodierung: Null-Laeufen (Rot) und Nicht-Null-Werte (Tuerkis)")
        
        if legend_entries:
            legend_patches = [plt.Rectangle((0,0),1,1, facecolor=colors_map[k], edgecolor='black') for k, _ in legend_entries]
            legend_labels = [label for _, label in legend_entries]
            ax.legend(legend_patches, legend_labels, loc='upper right')
        
        st.pyplot(fig)
        plt.close()

        st.markdown("""
        **Erklaerung:**
        - **DPCM**: Der DC-Koeffizient (erster Wert) wird als Differenz zum vorherigen Block kodiert.
        - **RLE**: Die AC-Koeffizienten (Rest) werden als (Anzahl_Nullen, Groesse_NichtNull)-Paare kodiert.
        - **VLI**: Die Nicht-Null-Werte werden mit variabler Laenge kodiert.
        """)

    elif step == 6:
        # Entropie
        st.header("Schritt 6: Entropie-Kodierung (Huffman)")
        st.markdown("""
        Die Entropie-Kodierung ordnet den Symbolen variable Bitlaengen nach ihrer Haeufigkeit zu:
        - Haeufige Symbole erhalten kurze Codes
        - Seltene Symbole erhalten laengere Codes
        """)

        with st.spinner("Berechne Huffman-Statistiken..."):
            dc_lum, dc_chrom, ac_lum, ac_chrom, total_bits = img.get_huffman_stats(p)

        original_bits = 192 * 144 * 3 * 8
        compression_ratio = original_bits / total_bits if total_bits > 0 else 0
        bpp = total_bits / (192 * 144)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Huffman-codierte Bits", f"{total_bits:,}")
        with m2:
            st.metric("Kompressionsrate", f"{compression_ratio:.1f}:1")
        with m3:
            st.metric("Bits pro Pixel", f"{bpp:.2f} bpp")

        st.subheader("Huffman-Tabellen")

        def _huffman_table_to_df(table, title):
            entries = []
            for i in range(len(table.lengths)):
                if table.lengths[i] != -1:
                    code_str = bin(table.symbols[i])[2:].zfill(table.lengths[i])
                    entries.append({"Symbol": i, "Laenge": table.lengths[i], "Code": code_str})
            entries.sort(key=lambda x: (x["Laenge"], x["Symbol"]))
            return entries

        col_dc, col_ac = st.columns(2)
        with col_dc:
            st.write("**DC Luminanz (Y)**")
            dc_lum_entries = _huffman_table_to_df(dc_lum, "DC Luminanz")
            if dc_lum_entries:
                st.dataframe(dc_lum_entries, width="stretch", hide_index=True)
            st.write("**DC Chrominanz (I/Q)**")
            dc_chrom_entries = _huffman_table_to_df(dc_chrom, "DC Chrominanz")
            if dc_chrom_entries:
                st.dataframe(dc_chrom_entries, width="stretch", hide_index=True)
        with col_ac:
            st.write("**AC Luminanz (Y)**")
            ac_lum_entries = _huffman_table_to_df(ac_lum, "AC Luminanz")
            if ac_lum_entries:
                st.dataframe(ac_lum_entries[:20], width="stretch", hide_index=True)
                if len(ac_lum_entries) > 20:
                    st.caption(f"... und {len(ac_lum_entries) - 20} weitere")
            st.write("**AC Chrominanz (I/Q)**")
            ac_chrom_entries = _huffman_table_to_df(ac_chrom, "AC Chrominanz")
            if ac_chrom_entries:
                st.dataframe(ac_chrom_entries[:20], width="stretch", hide_index=True)
                if len(ac_chrom_entries) > 20:
                    st.caption(f"... und {len(ac_chrom_entries) - 20} weitere")

        st.subheader("Bitlaengen-Verteilung")
        st.markdown("Verteilung der Codewort-Laengen: kuerzere Codes fuer haeufigere Symbole.")

        dc_lum_histo = dc_lum.get_histogramm()
        ac_lum_histo = ac_lum.get_histogramm()
        dc_chrom_histo = dc_chrom.get_histogramm()
        ac_chrom_histo = ac_chrom.get_histogramm()

        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(12, 6))

        for ax, histo, title in [
            (axes[0, 0], dc_lum_histo, "DC Luminanz"),
            (axes[0, 1], dc_chrom_histo, "DC Chrominanz"),
            (axes[1, 0], ac_lum_histo, "AC Luminanz"),
            (axes[1, 1], ac_chrom_histo, "AC Chrominanz"),
        ]:
            lengths = list(range(len(histo.werte)))
            counts = histo.werte
            nonzero = [(l, c) for l, c in zip(lengths, counts) if c > 0]
            if nonzero:
                ls, cs = zip(*nonzero)
                ax.bar(ls, cs, color="steelblue", edgecolor="black")
                ax.set_xlabel("Bit-Laenge")
                ax.set_ylabel("Anzahl Symbole")
                ax.set_title(title)
            else:
                ax.text(0.5, 0.5, "Keine Daten", ha="center", va="center", transform=ax.transAxes)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.subheader("Erklaerung")
        st.markdown("""
        **JPEG Huffman-Codierung:**
        - Es gibt 4 Tabellen: DC Luminanz, DC Chrominanz, AC Luminanz, AC Chrominanz
        - Die Tabellen werden adaptiv aus der Haeufigkeitsverteilung des aktuellen Bildes berechnet
        - DC-Symbole: Kategorie des Differenzwertes (0-15)
        - AC-Symbole: (Run, Size) Paare, z.B. (0,3) = 3 Nullen gefolgt von einem Wert mit 3 Bits
        - EOB (End of Block) wird als spezielles Symbol kodiert
        """)


if __name__ == "__main__":
    run_app()
