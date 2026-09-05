"""
VisJPEG Python - Block classes
Equivalent to Java Block.java, FloatBlock.java, BlockVektor.java
"""

import math
from PIL import Image, ImageDraw
from .matrix import Matrix


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
        sq2 = 1 / (2 * math.sqrt(2))

        # process rows
        for y in range(8):
            t0 = self.matrix[0][y] - 128
            t1 = self.matrix[1][y] - 128
            t2 = self.matrix[2][y] - 128
            t3 = self.matrix[3][y] - 128
            t4 = self.matrix[4][y] - 128
            t5 = self.matrix[5][y] - 128
            t6 = self.matrix[6][y] - 128
            t7 = self.matrix[7][y] - 128

            self.blk.matrix[0][y] = sq2 * (t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7)
            for x in range(1, 8):
                self.blk.matrix[x][y] = (
                    t0 * self.dct_coeff[0][x] +
                    t1 * self.dct_coeff[1][x] +
                    t2 * self.dct_coeff[2][x] +
                    t3 * self.dct_coeff[3][x] +
                    t4 * self.dct_coeff[4][x] +
                    t5 * self.dct_coeff[5][x] +
                    t6 * self.dct_coeff[6][x] +
                    t7 * self.dct_coeff[7][x]
                ) / 2

        # process columns
        for x in range(8):
            t0 = self.blk.matrix[x][0]
            t1 = self.blk.matrix[x][1]
            t2 = self.blk.matrix[x][2]
            t3 = self.blk.matrix[x][3]
            t4 = self.blk.matrix[x][4]
            t5 = self.blk.matrix[x][5]
            t6 = self.blk.matrix[x][6]
            t7 = self.blk.matrix[x][7]

            self.blk.matrix[x][0] = sq2 * (t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7)
            for y in range(1, 8):
                self.blk.matrix[x][y] = (
                    t0 * self.dct_coeff[0][y] +
                    t1 * self.dct_coeff[1][y] +
                    t2 * self.dct_coeff[2][y] +
                    t3 * self.dct_coeff[3][y] +
                    t4 * self.dct_coeff[4][y] +
                    t5 * self.dct_coeff[5][y] +
                    t6 * self.dct_coeff[6][y] +
                    t7 * self.dct_coeff[7][y]
                ) / 2

        return self.blk

    def get_idct(self):
        sq2 = 1 / math.sqrt(2)

        # process rows
        for y in range(8):
            t0 = self.matrix[0][y]
            t1 = self.matrix[1][y]
            t2 = self.matrix[2][y]
            t3 = self.matrix[3][y]
            t4 = self.matrix[4][y]
            t5 = self.matrix[5][y]
            t6 = self.matrix[6][y]
            t7 = self.matrix[7][y]

            for x in range(8):
                self.blk.matrix[x][y] = (
                    t0 * self.dct_coeff[x][0] * sq2 +
                    t1 * self.dct_coeff[x][1] +
                    t2 * self.dct_coeff[x][2] +
                    t3 * self.dct_coeff[x][3] +
                    t4 * self.dct_coeff[x][4] +
                    t5 * self.dct_coeff[x][5] +
                    t6 * self.dct_coeff[x][6] +
                    t7 * self.dct_coeff[x][7]
                ) / 2

        # process columns
        for x in range(8):
            t0 = self.blk.matrix[x][0]
            t1 = self.blk.matrix[x][1]
            t2 = self.blk.matrix[x][2]
            t3 = self.blk.matrix[x][3]
            t4 = self.blk.matrix[x][4]
            t5 = self.blk.matrix[x][5]
            t6 = self.blk.matrix[x][6]
            t7 = self.blk.matrix[x][7]

            for y in range(8):
                self.blk.matrix[x][y] = (
                    t0 * self.dct_coeff[y][0] * sq2 +
                    t1 * self.dct_coeff[y][1] +
                    t2 * self.dct_coeff[y][2] +
                    t3 * self.dct_coeff[y][3] +
                    t4 * self.dct_coeff[y][4] +
                    t5 * self.dct_coeff[y][5] +
                    t6 * self.dct_coeff[y][6] +
                    t7 * self.dct_coeff[y][7]
                ) / 2 + 128

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
