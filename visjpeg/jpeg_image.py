"""
VisJPEG Python - JPEG Image processing
Equivalent to Java JPEGImage.java (simplified)
"""

import math
import os
from PIL import Image, ImageDraw
import numpy as np

from .block import Block, BlockVektor
from .jpeg_parameter import JPEGParameter, GUIParameter
from .rle import SymbBlockFolge
from .huffman import HuffmanWriter, OurHuffmanTable, Histogramm


class JPEGImage:
    def __init__(self, file_or_url, scrolling_enabled=False):
        self.scrolling_enabled = scrolling_enabled
        self.first_act_line = 0
        self.last_act_line = 143
        self.first_act_col = 0
        self.last_act_col = 191
        self.marker_x = 0
        self.marker_y = 0

        # Caches
        self._r_image = None
        self._g_image = None
        self._b_image = None
        self._y_image = None
        self._i_image = None
        self._q_image = None
        self._subsampled_i_image = None
        self._subsampled_q_image = None
        self._markered_image = None
        self._decompr_rgb_image = None
        self._diff_image = None

        self.i_image_last_params = JPEGParameter()
        self.q_image_last_params = JPEGParameter()
        self.difference_image_parameter = None
        self.jpeg_image_parameter = None
        self.quant_bloecke_erzeugen_params = None
        self.symbole_erzeugen_params = None
        self.symbole_codieren_params = None
        self._huffman_stats_cache = None
        self._huffman_stats_params = None

        self.coded_size = 0
        self.length_huffman_coded = 0
        self.h_writer = None
        self.quant_y_bloecke = []
        self.quant_i_bloecke = []
        self.quant_q_bloecke = []
        self.de_mcu_order = []
        self.dc_lum_werte = []
        self.dc_chrom_werte = []
        self.ac_lum_huffman_table = None
        self.ac_chrom_huffman_table = None
        self.dc_lum_huffman_table = None
        self.dc_chrom_huffman_table = None
        self.y_block_folge = None
        self.cr_block_folge = None
        self.cb_block_folge = None
        self.index_aktueller_block = 0

        self.roh_image = None
        self.image = None

        if isinstance(file_or_url, str):
            self._load_from_file(file_or_url)
        else:
            self._load_from_url(file_or_url)

    def _load_from_file(self, filename):
        try:
            self.roh_image = Image.open(filename).convert("RGB")
        except Exception:
            self.image = Image.new("RGB", (192, 144), (0, 0, 0))
            draw = ImageDraw.Draw(self.image)
            draw.text((5, 48), "Bild kann nicht geladen werden!", fill=(255, 255, 255))
            draw.text((5, 96), "Image cannot be loaded!", fill=(255, 255, 255))
            self.roh_image = self.image.copy()
            return

        self._rebuild_from_raw(self.scrolling_enabled, 0, 0)

    def _load_from_url(self, url):
        # Simplified - same as file for now
        self._load_from_file(url)

    def set_image_shift(self, x_shift, y_shift):
        new_x_shift = self.parameter.x_shift - x_shift if hasattr(self, 'parameter') else -x_shift
        new_y_shift = self.parameter.y_shift - self.parameter.y_shift if hasattr(self, 'parameter') else -y_shift
        roh_width = self.roh_image.width
        roh_height = self.roh_image.height

        if new_x_shift > roh_width - 192:
            new_x_shift = roh_width - 192
        if new_y_shift > roh_height - 144:
            new_y_shift = roh_height - 144
        if new_x_shift < 0:
            new_x_shift = 0
        if new_y_shift < 0:
            new_y_shift = 0

        if hasattr(self, 'parameter'):
            self.parameter.x_shift = new_x_shift
            self.parameter.y_shift = new_y_shift
        self._rebuild_from_raw(True, new_x_shift, new_y_shift)

    def get_roh_width(self):
        return self.roh_image.width

    def get_roh_height(self):
        return self.roh_image.height

    def invalidate(self):
        self._r_image = None
        self._g_image = None
        self._b_image = None
        self._y_image = None
        self._i_image = None
        self._q_image = None
        self._subsampled_i_image = None
        self._subsampled_q_image = None
        self._markered_image = None
        self._decompr_rgb_image = None
        self._diff_image = None
        self.difference_image_parameter = None
        self.jpeg_image_parameter = None
        self.quant_bloecke_erzeugen_params = None
        self.symbole_erzeugen_params = None
        self.symbole_codieren_params = None
        self._huffman_stats_cache = None
        self._huffman_stats_params = None

    def _rebuild_from_raw(self, scrolling_enabled, x_shift, y_shift):
        if scrolling_enabled:
            if self.roh_image.width < 192 or self.roh_image.height < 144:
                if self.roh_image.width > 192:
                    self.first_act_col = 0
                    self.last_act_col = 191
                    x_draw_pos = 0
                    draw_width = 192
                else:
                    self.first_act_col = (192 - self.roh_image.width) // 2
                    self.last_act_col = self.first_act_col + self.roh_image.width - 1
                    x_draw_pos = self.first_act_col
                    draw_width = self.roh_image.width
                if self.roh_image.height > 144:
                    self.first_act_line = 0
                    self.last_act_line = 143
                    y_draw_pos = 0
                    draw_height = 144
                else:
                    self.first_act_line = (144 - self.roh_image.height) // 2
                    self.last_act_line = self.first_act_line + self.roh_image.height - 1
                    y_draw_pos = self.first_act_line
                    draw_height = self.roh_image.height
                self.image = Image.new("RGB", (192, 144), (0, 0, 0))
                sub = self.roh_image.crop((x_shift, y_shift, x_shift + draw_width, y_shift + draw_height))
                self.image.paste(sub, (x_draw_pos, y_draw_pos))
            else:
                self.image = self.roh_image.crop((x_shift, y_shift, x_shift + 192, y_shift + 144))
                self.first_act_col = 0
                self.first_act_line = 0
                self.last_act_col = 191
                self.last_act_line = 143
        else:
            self.image = self.roh_image.copy()
            if self.roh_image.width != 192 or self.roh_image.height != 144:
                self.image = self.image.resize((192, 144), Image.LANCZOS)
                self.first_act_col = 0
                self.first_act_line = 0
                self.last_act_col = 191
                self.last_act_line = 143
            else:
                self.first_act_col = 0
                self.first_act_line = 0
                self.last_act_col = 191
                self.last_act_line = 143

    def get_image(self):
        return self.image

    def get_r_image(self):
        if self._r_image is None:
            self._split_to_rgb()
        return self._r_image

    def get_g_image(self):
        if self._g_image is None:
            self._split_to_rgb()
        return self._g_image

    def get_b_image(self):
        if self._b_image is None:
            self._split_to_rgb()
        return self._b_image

    def get_y_image(self):
        if self._y_image is None:
            self._split_to_yiq()
        return self._y_image

    def get_marked_y_image(self):
        if self._markered_image is None:
            if self._y_image is None:
                self._split_to_yiq()
            self._markered_image = self._mark_block(self._y_image)
        return self._markered_image

    def get_i_image(self, h_subsample, v_subsample):
        if self._i_image is None:
            self._split_to_yiq()
        if self._subsampled_i_image is None or self.i_image_last_params.h_subsample != h_subsample or self.i_image_last_params.v_subsample != v_subsample:
            self._subsampled_i_image = self._subsample(self._i_image, h_subsample, v_subsample)
            # clone params
            self.i_image_last_params = JPEGParameter()
            self.i_image_last_params.h_subsample = h_subsample
            self.i_image_last_params.v_subsample = v_subsample
        return self._subsampled_i_image

    def get_q_image(self, h_subsample, v_subsample):
        if self._q_image is None:
            self._split_to_yiq()
        if self._subsampled_q_image is None or self.q_image_last_params.h_subsample != h_subsample or self.q_image_last_params.v_subsample != v_subsample:
            self._subsampled_q_image = self._subsample(self._q_image, h_subsample, v_subsample)
            self.q_image_last_params = JPEGParameter()
            self.q_image_last_params.h_subsample = h_subsample
            self.q_image_last_params.v_subsample = v_subsample
        return self._subsampled_q_image

    def set_marker(self, x, y):
        self.marker_x = (x // 8) * 8
        self.marker_y = (y // 8) * 8
        self._markered_image = None

    def _split_to_rgb(self):
        r_img = Image.new("RGB", (192, 144))
        g_img = Image.new("RGB", (192, 144))
        b_img = Image.new("RGB", (192, 144))
        for x in range(192):
            for y in range(144):
                r, g, b = self.image.getpixel((x, y))
                r_img.putpixel((x, y), (r, 0, 0))
                g_img.putpixel((x, y), (0, g, 0))
                b_img.putpixel((x, y), (0, 0, b))
        self._r_image = r_img
        self._g_image = g_img
        self._b_image = b_img

    def _split_to_yiq(self):
        y_img = Image.new("L", (192, 144))
        i_img = Image.new("L", (192, 144))
        q_img = Image.new("L", (192, 144))
        for x in range(192):
            for y in range(144):
                r, g, b = self.image.getpixel((x, y))
                y_val = int(0.299 * r + 0.587 * g + 0.114 * b)
                i_val = 128 + int(-0.1687 * r - 0.3313 * g + 0.5 * b)
                q_val = 128 + int(0.5 * r - 0.4187 * g - 0.0813 * b)
                y_img.putpixel((x, y), y_val)
                i_img.putpixel((x, y), i_val)
                q_img.putpixel((x, y), q_val)
        self._y_image = y_img
        self._i_image = i_img
        self._q_image = q_img

    def _mark_block(self, image):
        new_image = image.copy().convert("RGB")
        draw = ImageDraw.Draw(new_image)
        draw.rectangle([self.marker_x, self.marker_y, self.marker_x + 7, self.marker_y + 7], outline=(255, 255, 0))
        return new_image

    def _subsample(self, image, h_subsample, v_subsample):
        if h_subsample == 1 and v_subsample == 1:
            return image.copy()
        new_width = image.width // h_subsample
        new_height = image.height // v_subsample
        # BOX = echter Mittelwert ueber jedes h x v Block (JPEG-Subsampling),
        # kein Weichzeichnen wie bei LANCZOS -> reduzierte Aufloesung bleibt sichtbar
        return image.resize((new_width, new_height), Image.BOX)

    def _supersample(self, image):
        new_width = 192
        new_height = 144
        if new_width == image.width and new_height == image.height:
            return image.copy()
        return image.resize((new_width, new_height), Image.LANCZOS)

    def get_marked_block(self):
        return self.get_y_block(self.marker_x, self.marker_y)

    def get_y_block(self, block_x, block_y):
        if self._y_image is None:
            self._split_to_yiq()
        return self._get_block(self._y_image, block_x, block_y)

    def get_i_block(self, block_x, block_y, h_subsample, v_subsample):
        subsampled = self.get_i_image(h_subsample, v_subsample)
        return self._get_block(subsampled, block_x, block_y)

    def get_q_block(self, block_x, block_y, h_subsample, v_subsample):
        subsampled = self.get_q_image(h_subsample, v_subsample)
        return self._get_block(subsampled, block_x, block_y)

    def _get_block(self, image, block_x, block_y):
        block = Block()
        for x in range(8):
            for y in range(8):
                px = block_x + x
                py = block_y + y
                if px < image.width and py < image.height:
                    val = image.getpixel((px, py))
                    if isinstance(val, tuple):
                        val = val[0]
                    block.matrix[x][y] = val
                else:
                    block.matrix[x][y] = 0
        return block

    def _process_channel(self, channel_img, q_matrix, width, height):
        """Wendet DCT, Quantisierung und iDCT auf einen Kanal an."""
        result = Image.new("L", (width, height))
        for by in range(0, height, 8):
            for bx in range(0, width, 8):
                # Block extrahieren
                block = Block()
                for x in range(8):
                    for y in range(8):
                        px = bx + x
                        py = by + y
                        if px < channel_img.width and py < channel_img.height:
                            val = channel_img.getpixel((px, py))
                            if isinstance(val, tuple):
                                val = val[0]
                            block.matrix[x][y] = val
                        else:
                            block.matrix[x][y] = 0

                # DCT -> Quantisierung -> iDCT
                dct = block.get_dct()
                quant = dct.get_quantisiert(q_matrix)
                dequant = quant.get_dequantisiert(q_matrix)
                reconstructed = dequant.get_idct()

                # Zurueckschreiben
                for x in range(8):
                    for y in range(8):
                        px = bx + x
                        py = by + y
                        if px < width and py < height:
                            val = int(reconstructed.matrix[x][y])
                            val = max(0, min(255, val))
                            result.putpixel((px, py), val)
        return result

    def get_decompressed_jpeg_image(self, parameter):
        if self.jpeg_image_parameter is not None and self.jpeg_image_parameter == parameter and self._decompr_rgb_image is not None:
            return self._decompr_rgb_image

        self.jpeg_image_parameter = parameter.clone() if hasattr(parameter, 'clone') else parameter

        # Y-Kanal verarbeiten (mit Quantisierung)
        y_img = self.get_y_image()
        y_processed = self._process_channel(y_img, parameter.q_matrix_lum, 192, 144)

        # I/Q-Kanaele verarbeiten (mit Chrominanz-Quantisierung)
        i_img_raw = self.get_i_image(parameter.h_subsample, parameter.v_subsample)
        q_img_raw = self.get_q_image(parameter.h_subsample, parameter.v_subsample)
        i_processed = self._process_channel(i_img_raw, parameter.q_matrix_chrom, i_img_raw.width, i_img_raw.height)
        q_processed = self._process_channel(q_img_raw, parameter.q_matrix_chrom, q_img_raw.width, q_img_raw.height)

        # Supersample
        i_processed = i_processed.resize((192, 144), Image.NEAREST)
        q_processed = q_processed.resize((192, 144), Image.NEAREST)

        # YIQ -> RGB
        result = Image.new("RGB", (192, 144))
        for x in range(192):
            for y in range(144):
                y_val = y_processed.getpixel((x, y))
                i_val = i_processed.getpixel((x, y)) - 128
                q_val = q_processed.getpixel((x, y)) - 128

                red = int(y_val + 1.402 * q_val)
                green = int(y_val - 0.34414 * i_val - 0.71414 * q_val)
                blue = int(y_val + 1.772 * i_val)

                red = max(0, min(255, red))
                green = max(0, min(255, green))
                blue = max(0, min(255, blue))

                result.putpixel((x, y), (red, green, blue))

        self._decompr_rgb_image = result
        return result

    def get_difference_image(self, parameter):
        if self.difference_image_parameter is not None and self.difference_image_parameter == parameter and self._diff_image is not None:
            return self._diff_image

        orig = self.image
        comp = self.get_decompressed_jpeg_image(parameter)
        diff = Image.new("RGB", (192, 144))
        for x in range(192):
            for y in range(144):
                r1, g1, b1 = orig.getpixel((x, y))
                r2, g2, b2 = comp.getpixel((x, y))
                diff.putpixel((x, y), (abs(r1 - r2) * 4, abs(g1 - g2) * 4, abs(b1 - b2) * 4))

        self.difference_image_parameter = parameter.clone() if hasattr(parameter, 'clone') else parameter
        self._diff_image = diff
        return diff

    def get_psnr(self, parameter):
        """Berechnet die PSNR (Peak Signal-to-Noise Ratio) zwischen Original und komprimiertem Bild."""
        import math
        orig = self.image
        comp = self.get_decompressed_jpeg_image(parameter)
        mse = 0.0
        for x in range(192):
            for y in range(144):
                r1, g1, b1 = orig.getpixel((x, y))
                r2, g2, b2 = comp.getpixel((x, y))
                mse += (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2
        mse /= (192 * 144 * 3)
        if mse == 0:
            return float('inf')
        return 20 * math.log10(255.0 / math.sqrt(mse))

    def write_to_file(self, filename):
        try:
            self.image.save(filename)
            return True
        except Exception:
            return False

    def x_blocks(self, resampling_ratio):
        return (self.image.width - 1) // (8 * resampling_ratio) + 1

    def y_blocks(self, resampling_ratio):
        return (self.image.height - 1) // (8 * resampling_ratio) + 1

    def _get_category(self, value):
        """VLI-Kategorie fuer einen Wert (JPEG-Standard)."""
        if value == 0:
            return 0
        abs_val = abs(value)
        cat = 0
        while abs_val > 0:
            abs_val >>= 1
            cat += 1
        return cat

    def _build_symbol_histogram(self, parameter):
        """Erzeugt Histogramme fuer DC- und AC-Symbole des gesamten Bildes.
        Nutzt NumPy fuer schnelle Block-Extraktion."""
        h = parameter.h_subsample
        v = parameter.v_subsample
        w, h_img = self.image.width, self.image.height

        # Bild als NumPy-Array laden (schneller als getpixel)
        rgb = np.array(self.image)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        # YIQ-Kanaele als NumPy-Arrays (Y direkt; I/Q uber die gecachten,
        # subsampelten PIL-Bilder fuer Konsistenz mit der Dekompression)
        y_arr = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.int32)

        dc_lum_histo = Histogramm(17)
        dc_chrom_histo = Histogramm(17)
        ac_lum_histo = Histogramm(256)
        ac_chrom_histo = Histogramm(256)

        prev_dc_y = 0
        prev_dc_i = 0
        prev_dc_q = 0

        def process_blocks(arr, q_matrix, dc_histo, ac_histo, prev_dc_ref):
            """Hilfsfunktion: verarbeitet alle 8x8-Bloecke eines Kanals."""
            prev_dc = prev_dc_ref[0]
            rows, cols = arr.shape
            x_blocks = (cols - 1) // 8 + 1
            y_blocks = (rows - 1) // 8 + 1
            for by in range(y_blocks):
                for bx in range(x_blocks):
                    block = Block()
                    y0, x0 = by * 8, bx * 8
                    for yy in range(8):
                        for xx in range(8):
                            py = y0 + yy
                            px = x0 + xx
                            if py < rows and px < cols:
                                block.matrix[xx][yy] = int(arr[py, px])
                            else:
                                block.matrix[xx][yy] = 0
                    dct = block.get_dct()
                    quant = dct.get_quantisiert(q_matrix)
                    vec = quant.get_zig_zag_scan()
                    rle = vec.get_rle_compressed()

                    dc_diff = rle.dc_value - prev_dc
                    prev_dc = rle.dc_value
                    dc_cat = self._get_category(dc_diff)
                    dc_histo.werte[dc_cat] += 1

                    for sym in rle.rle_folge.symbols:
                        if hasattr(sym, 'zero_count'):
                            if sym.zero_count == 0 and sym.size_non_zero == 0:
                                ac_histo.werte[0] += 1
                            else:
                                symbol_val = (sym.zero_count << 4) | sym.size_non_zero
                                ac_histo.werte[symbol_val] += 1
            prev_dc_ref[0] = prev_dc

        # Y-Kanal
        process_blocks(y_arr, parameter.q_matrix_lum, dc_lum_histo, ac_lum_histo, [prev_dc_y])

        # I- und Q-Kanaele: nutzen die gleichen subsampelten Bilder wie die
        # Dekompression (BOX-Mittelung), damit alles konsistent ist
        i_sub = np.array(self.get_i_image(h, v), dtype=np.int32)
        q_sub = np.array(self.get_q_image(h, v), dtype=np.int32)

        process_blocks(i_sub, parameter.q_matrix_chrom, dc_chrom_histo, ac_chrom_histo, [prev_dc_i])
        process_blocks(q_sub, parameter.q_matrix_chrom, dc_chrom_histo, ac_chrom_histo, [prev_dc_q])

        return dc_lum_histo, dc_chrom_histo, ac_lum_histo, ac_chrom_histo

    def get_huffman_stats(self, parameter):
        """Berechnet Huffman-Statistiken fuer das aktuelle Bild.
        Gibt zurueck: (dc_lum_table, dc_chrom_table, ac_lum_table, ac_chrom_table, total_bits)"""
        if self._huffman_stats_cache is not None and self._huffman_stats_params == parameter:
            return self._huffman_stats_cache

        dc_lum_histo, dc_chrom_histo, ac_lum_histo, ac_chrom_histo = self._build_symbol_histogram(parameter)

        dc_lum_table = dc_lum_histo.build_huffman_table()
        dc_chrom_table = dc_chrom_histo.build_huffman_table()
        ac_lum_table = ac_lum_histo.build_huffman_table()
        ac_chrom_table = ac_chrom_histo.build_huffman_table()

        # Gesamtanzahl Bits berechnen
        total_bits = 0
        for i in range(17):
            if dc_lum_table.lengths[i] != -1:
                total_bits += dc_lum_table.lengths[i] * dc_lum_histo.werte[i]
        for i in range(17):
            if dc_chrom_table.lengths[i] != -1:
                total_bits += dc_chrom_table.lengths[i] * dc_chrom_histo.werte[i]
        for i in range(256):
            if ac_lum_table.lengths[i] != -1:
                total_bits += ac_lum_table.lengths[i] * ac_lum_histo.werte[i]
        for i in range(256):
            if ac_chrom_table.lengths[i] != -1:
                total_bits += ac_chrom_table.lengths[i] * ac_chrom_histo.werte[i]

        result = (dc_lum_table, dc_chrom_table, ac_lum_table, ac_chrom_table, total_bits)
        self._huffman_stats_cache = result
        self._huffman_stats_params = parameter.clone() if hasattr(parameter, 'clone') else parameter
        return result

    def paint_dpcm_bar(self, width, height, color1, color2, color3):
        img = Image.new("RGB", (width, height), GUIParameter.INACTIVE_BACKGROUND)
        draw = ImageDraw.Draw(img)
        return img

    def paint_huffman_sizes(self, width, height, c1, c2, c3, c4):
        img = Image.new("RGB", (width, height), GUIParameter.INACTIVE_BACKGROUND)
        draw = ImageDraw.Draw(img)
        return img
