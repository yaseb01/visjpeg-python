"""
VisJPEG Python - Block classes
Equivalent to Java Block.java, FloatBlock.java, BlockVektor.java
"""

import math
from PIL import Image, ImageDraw
import numpy as np
from .matrix import Matrix

# Pre-compute DCT coefficient matrix for numpy fast path
_DCT_COEFF = np.zeros((8, 8), dtype=np.float64)
for j in range(8):
    for i in range(8):
        _DCT_COEFF[i, j] = math.cos((2 * i + 1) * j * math.pi / 16)

_SQ2 = 1 / (2 * math.sqrt(2))
_SQ2_INV = 1 / math.sqrt(2)

# Build full 8x8 DCT transform matrix
_DCT_MATRIX = np.zeros((8, 8), dtype=np.float64)
for u in range(8):
    cu = _SQ2 if u == 0 else 1.0
    for x in range(8):
        _DCT_MATRIX[u, x] = (cu / 2) * math.cos((2 * x + 1) * u * math.pi / 16)

# Inverse DCT matrix
_IDCT_MATRIX = _DCT_MATRIX.T


class BlockVektor:
    def __init__(self, werte=None):
        if werte is None:
            self.werte = [0] * 64
        else:
            self.werte = list(werte)

    def get_rle_compressed(self):
        from .rle import RLESymbolfolge, RLESymbol1, RLESymbol2, SymbolBlock
        folge = RLESymbolfolge()
        num_symbol1 = 0
        num_symbol2 = 0
        i = 1  # beginnt bei 1, nur AC Komponenten

        while i < 64:
            num_zeros = 0
            while i < 64 and self.werte[i] == 0:
                i += 1
                num_zeros += 1

            if i == 64:
                symb = RLESymbol1()
                symb.zero_count = 0
                symb.size_non_zero = 0
                folge.add_element(symb)
                num_symbol1 += 1
            else:
                while num_zeros >= 16:
                    num_zeros -= 16
                    symb = RLESymbol1()
                    symb.zero_count = 15
                    symb.size_non_zero = 0
                    folge.add_element(symb)
                    num_symbol1 += 1

                symb = RLESymbol1()
                symb.zero_count = num_zeros
                symb.size_non_zero = 1
                folge.add_element(symb)
                num_symbol1 += 1

                symb = RLESymbol2()
                symb.amplitude = self.werte[i]
                folge.add_element(symb)
                num_symbol2 += 1
                i += 1

        return SymbolBlock(self.werte[0], folge)

    def paint_bar(self, width, height, color):
        balken_breite_relativ = 1
        max_value = 0
        for i in range(64):
            if abs(self.werte[i]) > max_value:
                max_value = abs(self.werte[i])

        if max_value > 0:
            faktor = (height - 10) / max_value
        else:
            faktor = 0

        zwischenraum_breite = width / (64 * balken_breite_relativ + 63)
        balken_breite = zwischenraum_breite * balken_breite_relativ

        image = Image.new("RGB", (width, height), (211, 211, 211))
        draw = ImageDraw.Draw(image)

        for i in range(64):
            x_pos = i * (balken_breite + zwischenraum_breite)
            top = height - 5 - abs(self.werte[i]) * faktor
            draw.rectangle(
                [x_pos, top, x_pos + balken_breite, height - 5],
                fill=color,
                outline=(0, 0, 0)
            )

        return image


class FloatBlock:
    def __init__(self):
        self.matrix = [[0.0 for _ in range(8)] for _ in range(8)]

    def get_quantisiert(self, q_matrix):
        blk = Block()
        for i in range(8):
            for j in range(8):
                blk.matrix[i][j] = round(self.matrix[i][j] / q_matrix.matrix[i][j])
        return blk

    def to_int_block(self):
        block = Block()
        for x in range(8):
            for y in range(8):
                block.matrix[x][y] = round(self.matrix[x][y])
        return block

    def paint_bar3d(self, width, height, color):
        return self.to_int_block().paint_bar3d(width, height, color)


class Block(Matrix):
    ZICK_ZACK_X = [
        0, 1, 0, 0, 1, 2, 3, 2, 1, 0, 0,
        1, 2, 3, 4, 5, 4, 3, 2, 1, 0, 0,
        1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1, 0,
        1, 2, 3, 4, 5, 6, 7, 7, 6, 5, 4, 3, 2,
        3, 4, 5, 6, 7, 7, 6, 5, 4, 5, 6, 7,
        7, 6, 7
    ]
    ZICK_ZACK_Y = [
        0, 0, 1, 2, 1, 0, 0, 1, 2, 3, 4,
        3, 2, 1, 0, 0, 1, 2, 3, 4, 5, 6,
        5, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 5, 6, 7, 7,
        6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7, 7,
        6, 5, 4, 3, 4, 5, 6, 7, 7, 6, 5, 6, 7, 7
    ]

    def __init__(self, data=None):
        super().__init__(data)
        self.blk = FloatBlock()
        self.dct_coeff = [[0.0 for _ in range(8)] for _ in range(8)]
        for j in range(8):
            for i in range(8):
                self.dct_coeff[i][j] = math.cos((2 * i + 1) * j * math.pi / 16)

    def get_dct(self):
        # NumPy fast path – exakt gleiches Ergebnis wie Original-Loop
        arr = np.array(self.matrix, dtype=np.float64) - 128.0
        blk = np.zeros((8, 8), dtype=np.float64)

        # Row pass
        for y in range(8):
            t = arr[:, y]
            blk[0, y] = _SQ2 * np.sum(t)
            for x in range(1, 8):
                blk[x, y] = np.sum(t * _DCT_COEFF[:, x]) / 2.0

        # Column pass
        result = np.zeros((8, 8), dtype=np.float64)
        for x in range(8):
            t = blk[x, :]
            result[x, 0] = _SQ2 * np.sum(t)
            for y in range(1, 8):
                result[x, y] = np.sum(t * _DCT_COEFF[:, y]) / 2.0

        self.blk.matrix = result.tolist()
        return self.blk

    def get_idct(self):
        # NumPy fast path – exakt gleiches Ergebnis wie Original-Loop
        arr = np.array(self.matrix, dtype=np.float64)
        blk = np.zeros((8, 8), dtype=np.float64)

        # Row pass
        for y in range(8):
            t = arr[:, y]
            for x in range(8):
                blk[x, y] = (t[0] * _DCT_COEFF[x, 0] * _SQ2_INV + np.sum(t[1:] * _DCT_COEFF[x, 1:])) / 2.0

        # Column pass
        result = np.zeros((8, 8), dtype=np.float64)
        for x in range(8):
            t = blk[x, :]
            for y in range(8):
                result[x, y] = (t[0] * _DCT_COEFF[y, 0] * _SQ2_INV + np.sum(t[1:] * _DCT_COEFF[y, 1:])) / 2.0 + 128.0

        self.blk.matrix = result.tolist()
        return self.blk.to_int_block()

    def get_zig_zag_scan(self):
        bv = BlockVektor()
        for i in range(64):
            bv.werte[i] = int(self.matrix[self.ZICK_ZACK_X[i]][self.ZICK_ZACK_Y[i]])
        return bv

    def get_linear_scan(self):
        bv = BlockVektor()
        for y in range(8):
            for x in range(8):
                bv.werte[x + 8 * y] = int(self.matrix[x][y])
        return bv

    def get_dequantisiert(self, q_matrix):
        blk = Block()
        for i in range(8):
            for j in range(8):
                blk.matrix[i][j] = self.matrix[i][j] * q_matrix.matrix[i][j]
        return blk

    def paint_bar3d(self, width, height, color):
        from .jpeg_parameter import GUIParameter
        dummy = Image.new("RGB", (width, height), GUIParameter.INACTIVE_BACKGROUND)
        draw = ImageDraw.Draw(dummy)

        bbx = (width - height * GUIParameter.DIAG_RATIO_XY * GUIParameter.DIAG_RATIO_Y) / (8 / GUIParameter.DIAG_WIDTH)
        bby = (height * GUIParameter.DIAG_RATIO_Y) / (8 / GUIParameter.DIAG_HEIGHT)
        bsx = (width - height * GUIParameter.DIAG_RATIO_XY * GUIParameter.DIAG_RATIO_Y) / 8
        bsy = (height * GUIParameter.DIAG_RATIO_Y) / 8
        bsl = (height * GUIParameter.DIAG_RATIO_XY * GUIParameter.DIAG_RATIO_Y) / 8

        ratio = abs(self.matrix[0][0])
        for y in range(8):
            for x in range(8):
                if abs(self.matrix[x][y]) > ratio:
                    ratio = abs(self.matrix[x][y])

        if ratio > 0:
            ratio = (height - 8 * bsy) / ratio

        for y in range(8):
            for x in range(8):
                bh = abs(self.matrix[x][y]) * ratio
                bx = bsl * (7 - y) + bsx * x
                by = height - bsy * (7 - y)

                # Frontseite
                draw.polygon(
                    [(bx, by), (bx + bbx, by), (bx + bbx, by - bh), (bx, by - bh)],
                    fill=color, outline=(0, 0, 0)
                )
                # Oberseite
                draw.polygon(
                    [(bx, by - bh), (bx + bbx, by - bh), (bx + bbx + bsl, by - bh - bby), (bx + bsl, by - bh - bby)],
                    fill=tuple(min(255, c + 40) for c in color), outline=(0, 0, 0)
                )
                # Seitenwand
                draw.polygon(
                    [(bx + bbx, by), (bx + bbx + bsl, by - bby), (bx + bbx + bsl, by - bh - bby), (bx + bbx, by - bh)],
                    fill=tuple(max(0, c - 40) for c in color), outline=(0, 0, 0)
                )

        return dummy
