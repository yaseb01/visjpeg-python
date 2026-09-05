"""
VisJPEG Python - Matrix class
Equivalent to Java Matrix.java
"""

import copy


class Matrix:
    """Kapselt ein 8x8 int-Array."""

    def __init__(self, data=None):
        if data is None:
            self.matrix = [[1 for _ in range(8)] for _ in range(8)]
        else:
            self.matrix = [[0 for _ in range(8)] for _ in range(8)]
            for i in range(8):
                for j in range(8):
                    val = data[i][j]
                    if val <= 0:
                        val = 1
                    if val > 255:
                        val = 255
                    self.matrix[i][j] = val

    def clone(self):
        new_matrix = Matrix(self.matrix)
        return new_matrix

    def scale(self, qual_faktor):
        if qual_faktor < 50:
            qual_faktor2 = 5000 // qual_faktor
        else:
            qual_faktor2 = 200 - qual_faktor * 2

        for i in range(8):
            for j in range(8):
                temp = (self.matrix[i][j] * qual_faktor2 + 50) // 100
                if temp <= 0:
                    temp = 1
                if temp > 255:
                    temp = 255
                self.matrix[i][j] = temp

    def get_zig_zag_ordered(self):
        matrix_neu = [[0 for _ in range(8)] for _ in range(8)]
        x, y = 0, 0
        i, j = 0, 0
        richtung = 1  # 1 = nach rechts oben, 0 = nach links unten

        while x < 8 and y < 8:
            matrix_neu[i][j] = self.matrix[x][y]

            if richtung == 1:
                if y == 0:
                    richtung = 0
                    if x == 7:
                        y += 1
                    else:
                        x += 1
                elif x == 7:
                    richtung = 0
                    y += 1
                else:
                    x += 1
                    y -= 1
            else:
                if x == 0:
                    richtung = 1
                    if y == 7:
                        x += 1
                    else:
                        y += 1
                elif y == 7:
                    x += 1
                    richtung = 1
                else:
                    x -= 1
                    y += 1

            if i == 7:
                i = 0
                j += 1
            else:
                i += 1

        return Matrix(matrix_neu)

    def __eq__(self, other):
        if not isinstance(other, Matrix):
            return False
        for i in range(8):
            for j in range(8):
                if self.matrix[i][j] != other.matrix[i][j]:
                    return False
        return True

    def __repr__(self):
        return "Matrix(" + repr(self.matrix) + ")"
