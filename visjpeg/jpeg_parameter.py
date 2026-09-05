"""
VisJPEG Python - JPEG Parameter
Equivalent to Java JPEGParameter.java and GUIParameter.java
"""

from .matrix import Matrix


class GUIParameter:
    DIAG_RATIO_Y = 0.33
    DIAG_RATIO_XY = 0.5
    DIAG_WIDTH = 0.75
    DIAG_HEIGHT = 0.75
    LARGE_FONT = ("SansSerif", 14, "bold")
    MEDIUM_FONT = ("SansSerif", 12, "normal")
    SMALL_FONT = ("SansSerif", 9, "normal")
    FONT_COLOR = "black"
    ACTIVE_BACKGROUND = "white"
    INACTIVE_BACKGROUND = (211, 211, 211)  # light gray


class JPEGParameter:
    HUFFMAN_STANDARD = 1
    HUFFMAN_ADAPTIVE = 2
    ARITHMETIC = 3

    # Standard matrices initialized in module level below
    STANDARD_QMATRIX_LUM = None
    STANDARD_QMATRIX_CHROM = None
    UNIFORM_QMATRIX = None
    NONUNIFORM_QMATRIX = None

    def __init__(self):
        self.h_subsample = 2
        self.v_subsample = 2
        self.q_faktor = 50
        self.q_matrix_lum = JPEGParameter.STANDARD_QMATRIX_LUM.clone()
        self.q_matrix_lum.scale(self.q_faktor)
        self.q_matrix_chrom = JPEGParameter.STANDARD_QMATRIX_CHROM.clone()
        self.q_matrix_chrom.scale(self.q_faktor)
        self.compression_type = self.HUFFMAN_STANDARD
        self.filename = "test2.gif"
        self.skalierungs_qualitaet = 1
        self.x_shift = 0
        self.y_shift = 0

    def clone(self):
        parameter = JPEGParameter()
        parameter.h_subsample = self.h_subsample
        parameter.v_subsample = self.v_subsample
        parameter.q_faktor = self.q_faktor
        parameter.compression_type = self.compression_type
        parameter.q_matrix_lum = self.q_matrix_lum.clone()
        parameter.q_matrix_chrom = self.q_matrix_chrom.clone()
        parameter.filename = self.filename
        parameter.skalierungs_qualitaet = self.skalierungs_qualitaet
        parameter.x_shift = self.x_shift
        parameter.y_shift = self.y_shift
        return parameter

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, JPEGParameter):
            return False
        return (self.h_subsample == other.h_subsample and
                self.v_subsample == other.v_subsample and
                self.q_faktor == other.q_faktor and
                self.compression_type == other.compression_type and
                self.q_matrix_lum == other.q_matrix_lum and
                self.q_matrix_chrom == other.q_matrix_chrom and
                self.filename == other.filename and
                self.skalierungs_qualitaet == other.skalierungs_qualitaet and
                self.x_shift == other.x_shift and
                self.y_shift == other.y_shift)


def _init_standard_matrices():
    JPEGParameter.STANDARD_QMATRIX_LUM = Matrix()
    lum_vals = [
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99]
    ]
    for i in range(8):
        for j in range(8):
            JPEGParameter.STANDARD_QMATRIX_LUM.matrix[i][j] = lum_vals[j][i]

    JPEGParameter.STANDARD_QMATRIX_CHROM = Matrix()
    for i in range(8):
        for j in range(8):
            JPEGParameter.STANDARD_QMATRIX_CHROM.matrix[i][j] = 99
    chrom_vals = [
        [17, 18, 24, 47],
        [18, 21, 26, 66],
        [24, 26, 56, 0],
        [47, 66, 0, 0]
    ]
    for i in range(4):
        for j in range(4):
            if chrom_vals[j][i] != 0:
                JPEGParameter.STANDARD_QMATRIX_CHROM.matrix[i][j] = chrom_vals[j][i]

    JPEGParameter.UNIFORM_QMATRIX = Matrix()
    for i in range(8):
        for j in range(8):
            JPEGParameter.UNIFORM_QMATRIX.matrix[i][j] = 50

    JPEGParameter.NONUNIFORM_QMATRIX = Matrix()
    for i in range(8):
        for j in range(8):
            JPEGParameter.NONUNIFORM_QMATRIX.matrix[i][j] = 20 + 5 * i + 5 * j


_init_standard_matrices()
