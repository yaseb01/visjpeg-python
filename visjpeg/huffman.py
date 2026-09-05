"""
VisJPEG Python - Huffman coding classes
Equivalent to Java HuffmanWriter.java, Histogramm.java, OurHuffmanTable.java
"""

import os
from PIL import Image, ImageDraw
from .jpeg_parameter import GUIParameter


class OurHuffmanTable:
    def __init__(self, huff_table=None):
        self.lengths = [-1] * 256
        self.symbols = [0] * 256
        self.coded_symbols = []
        self.coded_lengths = []

        if huff_table is not None:
            # Simplified from JPEGHuffmanTable - not fully implemented
            pass

    def __eq__(self, other):
        for i in range(len(self.lengths)):
            if self.lengths[i] != other.lengths[i]:
                return False
        return True

    def get_histogramm(self):
        histo = Histogramm(17)
        for i in range(256):
            if self.lengths[i] != -1:
                histo.werte[self.lengths[i]] += 1
        return histo


class Histogramm:
    def __init__(self, groesse):
        self.werte = [0] * groesse

    def add_histo(self, histo):
        for i in range(len(self.werte)):
            self.werte[i] += histo.werte[i]

    def build_huffman_table(self):
        huff_table = OurHuffmanTable()
        n = len(self.werte)
        freq = list(self.werte) + [0]
        freq_backup = list(freq)
        others = [-1] * (n + 1)
        codesize = [0] * (n + 1)

        while True:
            min_val = 100000
            v1 = 0
            for i in range(n + 1):
                if freq[i] > 0 and freq[i] <= min_val:
                    min_val = freq[i]
                    v1 = i
            v2 = -1
            min_val = 100000
            for i in range(n + 1):
                if freq[i] > 0 and i != v1 and freq[i] < min_val:
                    min_val = freq[i]
                    v2 = i
            if v2 == -1:
                break

            freq[v1] += freq[v2]
            freq[v2] = 0

            done = False
            while not done:
                codesize[v1] += 1
                if others[v1] == -1:
                    done = True
                else:
                    v1 = others[v1]
            others[v1] = v2

            done = False
            while not done:
                codesize[v2] += 1
                if others[v2] == -1:
                    done = True
                else:
                    v2 = others[v2]

        bits = [0] * 33
        for i in range(n):
            if codesize[i] != 0:
                bits[codesize[i]] += 1

        i = 32
        while True:
            if bits[i] > 0:
                j = i - 1
                while bits[j] == 0:
                    j -= 1
                bits[i] -= 2
                bits[i - 1] += 1
                bits[j + 1] += 2
                bits[j] -= 1
            else:
                i -= 1
                if i == 16:
                    break
        while bits[i] == 0:
            i -= 1
        bits[i] -= 1

        freq = list(freq_backup)
        freq_order = list(range(n))
        done = False
        while not done:
            done = True
            for i in range(n - 1):
                if freq[freq_order[i]] < freq[freq_order[i + 1]]:
                    freq_order[i], freq_order[i + 1] = freq_order[i + 1], freq_order[i]
                    done = False

        symb_index = 0
        for i in range(17):
            for j in range(bits[i]):
                if symb_index < n:
                    huff_table.lengths[freq_order[symb_index]] = i
                    symb_index += 1

        code = 0
        symb_index = 0
        for i in range(17):
            for j in range(bits[i]):
                if symb_index < n:
                    huff_table.symbols[freq_order[symb_index]] = code
                    code += 1
                    symb_index += 1
            code <<= 1

        huff_table.coded_lengths = [0] * 17
        for i in range(17):
            huff_table.coded_lengths[i] = bits[i]
        huff_table.coded_symbols = [0] * symb_index
        symb_index = 0
        for i in range(17):
            for j in range(bits[i]):
                if symb_index < len(huff_table.coded_symbols):
                    huff_table.coded_symbols[symb_index] = freq_order[symb_index]
                    symb_index += 1

        return huff_table

    def bitlaengen_histogramm(self, width, height, color):
        image = Image.new("RGB", (width, height), GUIParameter.INACTIVE_BACKGROUND)
        draw = ImageDraw.Draw(image)

        max_val = 0
        summe_laengen = 0
        summe_anzahl = 0
        for i in range(len(self.werte)):
            if self.werte[i] > max_val:
                max_val = self.werte[i]
            summe_laengen += self.werte[i] * i
            summe_anzahl += self.werte[i]

        durchschn_laenge = int(10 * summe_laengen / summe_anzahl) if summe_anzahl > 0 else 0

        rand_unten = 20
        rand_oben = 5

        max_prozent_str = str(int(100 * max_val / summe_anzahl)) + "%" if summe_anzahl > 0 else "0%"
        rand_linx = 5 + 2 + 5 + len(max_prozent_str) * 6
        draw.line([(rand_linx - 1, rand_oben), (rand_linx - 1, height - rand_unten)], fill=(0, 0, 0))
        draw.line([(rand_linx - 5, height - rand_unten), (rand_linx - 1, height - rand_unten)], fill=(0, 0, 0))
        draw.line([(rand_linx - 5, rand_oben), (rand_linx - 1, rand_oben)], fill=(0, 0, 0))
        draw.text((rand_linx - len("0%") * 6 - 7, height - rand_unten - 5), "0%", fill=(0, 0, 0))
        draw.text((5, rand_oben), max_prozent_str, fill=(0, 0, 0))

        laenge_str = "Bitlaenge"
        rand_rechz = len(laenge_str) * 6 + 15
        draw.polygon([(width - rand_rechz, height - rand_unten - 3),
                      (width - rand_rechz, height - rand_unten + 3),
                      (width - rand_rechz + 5, height - rand_unten)], fill=(0, 0, 0))
        draw.text((width - rand_rechz + 10, height - rand_unten - 5), laenge_str, fill=(0, 0, 0))

        faktor = (height - rand_oben - rand_unten) / max_val if max_val > 0 else 0
        balken_breite = (width - rand_linx - rand_rechz) // (2 * len(self.werte))
        luecke = balken_breite

        x = rand_linx
        for i in range(len(self.werte)):
            s = str(i)
            draw.text((x + (balken_breite - len(s) * 6) // 2, height - 15), s, fill=(0, 0, 0))
            x += balken_breite + luecke

        draw.line([(rand_linx, height - rand_unten), (width - rand_rechz - 1, height - rand_unten)], fill=(0, 0, 0))
        rand_unten += 1

        schnitt_text = f"Durchschn. Laenge: {durchschn_laenge // 10}.{durchschn_laenge % 10}"
        string_breite = len(schnitt_text) * 6
        schrift_pos = width - 5 - string_breite

        x = rand_linx
        for i in range(len(self.werte)):
            if self.werte[i] > 0:
                y_oben = height - rand_unten - int(self.werte[i] * faktor)
                draw.rectangle([x, y_oben, x + balken_breite, height - rand_unten], fill=color, outline=(0, 0, 0))
            x += balken_breite + luecke

        draw.text((schrift_pos, 10), schnitt_text, fill=(0, 0, 0))
        return image


class HuffmanWriter:
    def __init__(self):
        self.current_val = 0
        self.current_size = 0
        self.out_buffers = []
        self.max_buffer_size = 4096
        self.current_buffer = bytearray(self.max_buffer_size)
        self.out_buffers.append(self.current_buffer)
        self.current_buffer_size = 0

    def get_bits_written(self):
        return (len(self.out_buffers) - 1) * self.max_buffer_size * 8 + self.current_buffer_size * 8 + self.current_size

    def write_byte(self, b):
        if self.current_buffer_size == self.max_buffer_size:
            self.current_buffer = bytearray(self.max_buffer_size)
            self.current_buffer_size = 0
            self.out_buffers.append(self.current_buffer)
        self.current_buffer[self.current_buffer_size] = b & 0xFF
        self.current_buffer_size += 1

    def write_bytes(self, b):
        for byte in b:
            self.write_byte(byte)

    def write_bytes_length(self, b, length):
        for i in range(length):
            self.write_byte(b[i])

    def _output_code_byte(self, b):
        if b == 0xFF:
            self.write_byte(b)
            self.write_byte(0)
        else:
            self.write_byte(b)

    def write_symbol(self, size, val):
        self.current_val = val + (self.current_val << size)
        self.current_size += size
        while self.current_size >= 8:
            self.current_size -= 8
            output = self.current_val >> self.current_size
            self._output_code_byte(output)
            self.current_val -= output << self.current_size

    def flush(self):
        self.write_byte(self.current_val << (8 - self.current_size))
        self.current_val = 0
        self.current_size = 0

    def write_to_file(self, filename):
        try:
            with open(filename, 'wb') as f:
                for i in range(len(self.out_buffers) - 1):
                    f.write(self.out_buffers[i])
                f.write(self.out_buffers[-1][:self.current_buffer_size])
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
