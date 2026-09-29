"""
Golden tests – sichern die aktuelle Pipeline-Numerik vor der Performance-Refaktur.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visjpeg.jpeg_image import JPEGImage
from visjpeg.jpeg_parameter import JPEGParameter
from visjpeg.block import Block, BlockVektor
from visjpeg.matrix import Matrix

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visjpeg")


def _make_test_block():
    """Known 8x8 block for reproducible tests."""
    block = Block()
    vals = [
        [128, 130, 125, 120, 118, 115, 110, 108],
        [132, 128, 124, 119, 117, 114, 109, 107],
        [135, 131, 127, 122, 120, 117, 112, 110],
        [138, 134, 130, 125, 123, 120, 115, 113],
        [140, 136, 132, 127, 125, 122, 117, 115],
        [142, 138, 134, 129, 127, 124, 119, 117],
        [145, 141, 137, 132, 130, 127, 122, 120],
        [148, 144, 140, 135, 133, 130, 125, 123],
    ]
    for x in range(8):
        for y in range(8):
            block.matrix[x][y] = vals[y][x]
    return block


class TestDCT:
    def test_dct_dc_coefficient(self):
        block = _make_test_block()
        dct = block.get_dct()
        assert abs(dct.matrix[0][0] - (-17.5)) < 0.01

    def test_dct_ac_coefficients(self):
        block = _make_test_block()
        dct = block.get_dct()
        assert abs(dct.matrix[0][1] - (-42.84)) < 0.01
        assert abs(dct.matrix[1][0] - 64.71) < 0.01

    def test_idct_roundtrip(self):
        block = _make_test_block()
        dct = block.get_dct()
        recon = dct.to_int_block()
        idct = recon.get_idct()
        max_diff = max(
            abs(block.matrix[x][y] - idct.matrix[x][y])
            for x in range(8) for y in range(8)
        )
        assert max_diff <= 1


class TestZigZag:
    def test_zig_zag_order(self):
        block = _make_test_block()
        p = JPEGParameter()
        dct = block.get_dct()
        quant = dct.get_quantisiert(p.q_matrix_lum)
        vec = quant.get_zig_zag_scan()
        assert vec.werte[0] == -1
        assert vec.werte[1] == 6
        assert vec.werte[2] == -4
        # After coefficient 2, remaining are 0
        assert all(v == 0 for v in vec.werte[3:])


class TestRLE:
    def test_rle_dc_value(self):
        block = _make_test_block()
        p = JPEGParameter()
        dct = block.get_dct()
        quant = dct.get_quantisiert(p.q_matrix_lum)
        vec = quant.get_zig_zag_scan()
        rle = vec.get_rle_compressed()
        assert rle.dc_value == -1

    def test_rle_symbol_count(self):
        block = _make_test_block()
        p = JPEGParameter()
        dct = block.get_dct()
        quant = dct.get_quantisiert(p.q_matrix_lum)
        vec = quant.get_zig_zag_scan()
        rle = vec.get_rle_compressed()
        assert len(rle.rle_folge.symbols) == 5


class TestQuantization:
    def test_standard_matrix_q50(self):
        q50 = JPEGParameter.STANDARD_QMATRIX_LUM.clone()
        q50.scale(50)
        assert q50.matrix[0][0] == 16
        assert q50.matrix[7][7] == 99

    def test_standard_matrix_q100(self):
        q100 = JPEGParameter.STANDARD_QMATRIX_LUM.clone()
        q100.scale(100)
        # qual_faktor2 = 200 - 200 = 0, so all values become (val*0+50)//100 = 0 → clipped to 1
        assert q100.matrix[0][0] == 1
        assert q100.matrix[7][7] == 1

    def test_standard_matrix_q1(self):
        q1 = JPEGParameter.STANDARD_QMATRIX_LUM.clone()
        q1.scale(1)
        assert q1.matrix[0][0] == 255
        assert q1.matrix[7][7] == 255


class TestGoldenImagePipeline:
    """Golden values captured before numpy refactoring."""

    @pytest.mark.parametrize("img_name,expected_psnr,expected_bits", [
        ("test2.gif", 27.4549, 12816),
        ("tria.jpg", 23.3169, 19628),
        ("monument.jpg", 33.2536, 10697),
    ])
    def test_psnr_and_bits(self, img_name, expected_psnr, expected_bits):
        path = os.path.join(TESTDATA_DIR, img_name)
        img = JPEGImage(path)
        p = JPEGParameter()
        psnr = img.get_psnr(p)
        assert abs(psnr - expected_psnr) < 0.05, f"PSNR changed: {psnr} vs {expected_psnr}"
        _, _, _, _, total_bits = img.get_huffman_stats(p)
        assert total_bits == expected_bits, f"total_bits changed: {total_bits} vs {expected_bits}"

    def test_image_size_after_load(self):
        path = os.path.join(TESTDATA_DIR, "test2.gif")
        img = JPEGImage(path)
        assert img.image.size == (192, 144)

    def test_pixel_value_at_origin(self):
        path = os.path.join(TESTDATA_DIR, "test2.gif")
        img = JPEGImage(path)
        assert img.image.getpixel((0, 0)) == (57, 74, 123)
