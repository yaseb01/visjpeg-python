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
from PIL import Image, ImageDraw
import streamlit as st
import numpy as np

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


def get_state():
    if "parameter" not in st.session_state:
        st.session_state.parameter = JPEGParameter()
        st.session_state.our_image = None
        st.session_state.marker_x = 0
        st.session_state.marker_y = 0
        st.session_state.differenzbild = False
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
    """Wandelt eine 8x8 int-Matrix in ein Graustufen-PIL Image um."""
    img = Image.new("L", (8, 8))
    max_val = max(max(abs(matrix[x][y]) for y in range(8)) for x in range(8))
    max_val = max(max_val, 1)
    for y in range(8):
        for x in range(8):
            val = int((abs(matrix[x][y]) / max_val) * 255)
            img.putpixel((x, y), val)
    return img.resize((size, size), Image.NEAREST)


def block_navigator(img, state, key_suffix=""):
    """Zeigt das markierte Bild und Pfeil-Buttons zur Block-Navigation."""
    marked = img.get_marked_y_image()

    # Bild in der Mitte
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(marked, caption=f"Y-Komponente – Block ({state.marker_x}, {state.marker_y})", width="stretch")

    # Steuerkreuz (D-Pad) darunter
    st.markdown("**Block auswaehlen:**")

    def move(dx, dy):
        new_x = max(0, min(184, state.marker_x + dx))
        new_y = max(0, min(136, state.marker_y + dy))
        if new_x != state.marker_x or new_y != state.marker_y:
            state.marker_x = new_x
            state.marker_y = new_y
            state.our_image.set_marker(state.marker_x, state.marker_y)
            st.rerun()

    # Zeile 1: leer, ▲, leer
    r1 = st.columns([1, 1, 1])
    with r1[1]:
        if st.button("▲", key=f"up_{key_suffix}", use_container_width=True):
            move(0, -8)

    # Zeile 2: ◄, Mitte, ►
    r2 = st.columns([1, 1, 1])
    with r2[0]:
        if st.button("◄", key=f"left_{key_suffix}", use_container_width=True):
            move(-8, 0)
    with r2[1]:
        st.markdown(
            f"<div style='text-align:center; padding-top:6px; font-family:monospace; font-size:14px;'>"
            f"x={state.marker_x}<br>y={state.marker_y}"
            f"</div>",
            unsafe_allow_html=True
        )
    with r2[2]:
        if st.button("►", key=f"right_{key_suffix}", use_container_width=True):
            move(8, 0)

    # Zeile 3: leer, ▼, leer
    r3 = st.columns([1, 1, 1])
    with r3[1]:
        if st.button("▼", key=f"down_{key_suffix}", use_container_width=True):
            move(0, 8)


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

        if state.our_image is None or state.parameter.filename != path:
            real_path = get_image_or_placeholder(path)
            if real_path:
                init_image(real_path)
            else:
                st.warning(f"Bild nicht gefunden: {path}")
                return

        # Eigenes Bild hochladen
        uploaded = st.file_uploader("Eigenes Bild", type=["jpg", "jpeg", "png", "gif", "bmp"])
        if uploaded is not None:
            img = Image.open(uploaded).convert("RGB")
            tmp_path = "/tmp/visjpeg_upload.png"
            img.save(tmp_path)
            init_image(tmp_path)

        # Subsampling
        st.subheader("Subsampling")
        subsample = st.selectbox("Cr/Cb Subsampling", ["4:4:4 (kein Subsampling)", "4:2:2", "4:2:0", "4:1:1"], index=2)
        if subsample == "4:4:4 (kein Subsampling)":
            state.parameter.h_subsample = 1
            state.parameter.v_subsample = 1
        elif subsample == "4:2:2":
            state.parameter.h_subsample = 2
            state.parameter.v_subsample = 1
        elif subsample == "4:2:0":
            state.parameter.h_subsample = 2
            state.parameter.v_subsample = 2
        else:
            state.parameter.h_subsample = 4
            state.parameter.v_subsample = 2
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

        # Blockauswahl-Info (keine Slider mehr)
        st.subheader("8x8 Block-Auswahl")
        st.info(f"Aktueller Block: ({state.marker_x}, {state.marker_y})")
        st.markdown("Verwende die Pfeile im DCT-Tab, um den Block zu verschieben.")

        # Ansicht
        st.subheader("Ansicht")
        state.differenzbild = st.checkbox("Differenzbild", value=state.differenzbild)

    if state.our_image is None:
        st.info("Bitte waehle ein Bild in der Seitenleiste aus.")
        return

    # Hauptbereich: Tabs
    tabs = st.tabs([
        "Uebersicht",
        "1. Farbraum",
        "2. DCT",
        "3. Quantisierung",
        "4. Zick-Zack",
        "5. DPCM + RLE",
        "6. Entropie"
    ])

    img = state.our_image
    p = state.parameter

    # Tab 0: Uebersicht
    with tabs[0]:
        st.header("Original vs. Komprimiert")
        orig = img.get_image()
        if state.differenzbild:
            comp = img.get_difference_image(p)
        else:
            comp = img.get_decompressed_jpeg_image(p)
        show_image_pair(orig, comp, "Originalbild", "JPEG-komprimiert" if not state.differenzbild else "Differenzbild")

        # PSNR anzeigen
        psnr = img.get_psnr(p)
        if psnr == float('inf'):
            psnr_text = "∞ (verlustfrei)"
        else:
            psnr_text = f"{psnr:.2f} dB"
        st.metric("PSNR (Peak Signal-to-Noise Ratio)", psnr_text,
                  help="Hoehere PSNR = bessere Qualitaet. Typisch: >40 dB = sehr gut, 30-40 dB = gut, <30 dB = sichtbare Artefakte.")

    # Tab 1: Farbraum
    with tabs[1]:
        st.header("Schritt 1: Farbraumkonvertierung")
        st.markdown("Konvertierung von RGB nach YIQ (bzw. YCrCb) mit optionalem Subsampling der Chrominanz-Kanaele.")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.image(img.get_r_image(), caption="Rotkanal", width="stretch")
            st.image(img.get_g_image(), caption="Gruenkanal", width="stretch")
            st.image(img.get_b_image(), caption="Blaukanal", width="stretch")
        with c2:
            st.image(img.get_y_image(), caption="Y-Kanal (Helligkeit)", width="stretch")
        with c3:
            st.image(img.get_i_image(p.h_subsample, p.v_subsample), caption="Cr-Kanal (Farbabweichung)", width="stretch")
            st.image(img.get_q_image(p.h_subsample, p.v_subsample), caption="Cb-Kanal (Farbabweichung)", width="stretch")

    # Tab 2: DCT
    with tabs[2]:
        st.header("Schritt 2: Diskrete Cosinus-Transformation (DCT)")

        # Block-Navigator mit Bild + Pfeilen
        block_navigator(img, state, key_suffix="dct")

        block = img.get_marked_block()
        dct_block = block.get_dct()

        c1, c2 = st.columns(2)
        with c1:
            show_matrix(block.matrix, "Originalwerte (8x8 Block)")
            st.image(block.paint_bar3d(300, 200, (0, 0, 255)), caption="3D-Visualisierung Original", width="stretch")
        with c2:
            show_matrix([[round(v, 1) for v in row] for row in dct_block.matrix], "DCT-transformierte Werte")
            st.image(dct_block.paint_bar3d(300, 200, (0, 0, 255)), caption="3D-Visualisierung DCT", width="stretch")

    # Tab 3: Quantisierung
    with tabs[3]:
        st.header("Schritt 3: Quantisierung")
        block = img.get_marked_block()
        dct = block.get_dct()
        quant = dct.get_quantisiert(p.q_matrix_lum)
        dequant = quant.get_dequantisiert(p.q_matrix_lum)

        c1, c2, c3 = st.columns(3)
        with c1:
            show_matrix(p.q_matrix_lum.matrix, "Quantisierungsmatrix")
            st.image(matrix_to_image(p.q_matrix_lum.matrix), caption="Quantisierungsmatrix (Visual)", width="stretch")
        with c2:
            show_matrix(quant.matrix, "Quantisierte Werte")
            st.image(quant.paint_bar3d(300, 200, (0, 128, 0)), caption="3D-Visualisierung quantisiert", width="stretch")
        with c3:
            show_matrix([[round(v) for v in row] for row in dequant.matrix], "Dequantisierte Werte")
            st.image(dequant.paint_bar3d(300, 200, (0, 128, 0)), caption="3D-Visualisierung dequantisiert", width="stretch")

    # Tab 4: Zick-Zack
    with tabs[4]:
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

    # Tab 5: DPCM + RLE
    with tabs[5]:
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

        # NEU: RLE Visualisierung
        st.subheader("RLE-Kodierung Visualisierung")
        
        # 1. Zig-Zag Vektor als farbige Tabelle
        st.write("**Zick-Zack-Scan mit Null-Markierung:**")
        zigzag_colors = []
        zigzag_vals = []
        for i, val in enumerate(vec.werte):
            zigzag_vals.append(str(val))
            if val == 0:
                zigzag_colors.append("background-color: #ffcccc")  # rot = Null
            elif i == 0:
                zigzag_colors.append("background-color: #ccccff")  # blau = DC
            else:
                zigzag_colors.append("background-color: #ccffcc")  # grün = Nicht-Null AC
        
        # HTML-Tabelle für farbige Darstellung
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
            f'<span style="background:#ccffcc; padding:2px 8px; margin-left:10px;">AC ≠ 0 (Grün)</span> '
            f'<span style="background:#ffcccc; padding:2px 8px; margin-left:10px;">AC = 0 (Rot)</span></div>',
            unsafe_allow_html=True
        )

        # 2. RLE-Dekodierung als Schritte
        st.write("**RLE-Dekodierung Schritt-fuer-Schritt:**")
        
        rle_steps = []
        pos = 1  # Nach DC
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
        
        # 3. Grafische Darstellung der Lauflängen
        st.write("**Grafische Darstellung der RLE-Lauflängen:**")
        
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 3))
        
        current_x = 0
        colors_map = {'zero': '#ff6b6b', 'value': '#4ecdc4', 'eob': '#ffe66d'}
        legend_entries = []
        
        for sym in rle.rle_folge.symbols:
            if hasattr(sym, 'zero_count'):
                if sym.zero_count == 0 and sym.size_non_zero == 0:
                    # EOB
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
        
        # Legende
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

    # Tab 6: Entropie
    with tabs[6]:
        st.header("Schritt 6: Entropie-Kodierung (Huffman)")
        st.markdown("""
        Die Entropie-Kodierung ordnet den Symbolen variable Bitlaengen nach ihrer Haeufigkeit zu:
        - Haeufige Symbole erhalten kurze Codes
        - Seltene Symbole erhalten laengere Codes
        """)

        with st.spinner("Berechne Huffman-Statistiken..."):
            dc_lum, dc_chrom, ac_lum, ac_chrom, total_bits = img.get_huffman_stats(p)

        st.metric("Gesamtanzahl codierte Bits", f"{total_bits:,}")

        st.subheader("Huffman-Tabellen")

        def show_huffman_table(table, title, max_entries=16):
            st.write(f"**{title}**")
            entries = []
            for i in range(len(table.lengths)):
                if table.lengths[i] != -1:
                    code_str = bin(table.symbols[i])[2:].zfill(table.lengths[i])
                    entries.append((i, table.lengths[i], code_str))
            # Nach Codewortlaenge sortieren
            entries.sort(key=lambda x: (x[1], x[0]))
            for idx, length, code in entries[:max_entries]:
                st.code(f"Symbol {idx:3d}: Laenge {length:2d}, Code {code}", language="text")
            if len(entries) > max_entries:
                st.caption(f"... und {len(entries) - max_entries} weitere Symbole")

        c1, c2 = st.columns(2)
        with c1:
            show_huffman_table(dc_lum, "DC Luminanz (Y)")
            show_huffman_table(ac_lum, "AC Luminanz (Y)")
        with c2:
            show_huffman_table(dc_chrom, "DC Chrominanz (I/Q)")
            show_huffman_table(ac_chrom, "AC Chrominanz (I/Q)")

        st.subheader("Erklaerung")
        st.markdown("""
        **JPEG Huffman-Codierung:**
        - Es gibt 4 Tabellen: DC Luminanz, DC Chrominanz, AC Luminanz, AC Chrominanz
        - Die Tabellen werden adaptiv aus der Haeufigkeitsverteilung des aktuellen Bildes berechnet
        - DC-Symbole: Kategorie des Differenzwertes (0-15)
        - AC-Symbole: (Run, Size) Paare, z.B. (0,3) = 3 Nullen gefolgt von einem Wert mit 3 Bits
        - EOB (End of Block) wird als spezielles Symbol kodiert
        """)


def main():
    import sys
    import subprocess
    app_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        app_path,
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ]
    print("Starte VisJPEG Streamlit-App...")
    print("Oeffne deinen Browser unter: http://localhost:8501")
    subprocess.run(cmd)


if __name__ == "__main__":
    run_app()
