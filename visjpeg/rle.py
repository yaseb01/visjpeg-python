"""
VisJPEG Python - RLE Symbol classes
Equivalent to Java RLESymbol.java, RLESymbol1.java, RLESymbol2.java,
RLESymbolfolge.java, SymbolBlock.java, SymbBlockFolge.java
"""


class RLESymbol:
    pass


class RLESymbol1(RLESymbol):
    def __init__(self):
        self.zero_count = 0
        self.size_non_zero = 0


class RLESymbol2(RLESymbol):
    def __init__(self):
        self.amplitude = 0


class RLESymbolfolge:
    def __init__(self):
        self.symbols = []

    def add_element(self, symbol):
        self.symbols.append(symbol)


class SymbolBlock:
    def __init__(self, dc_value, rle_folge):
        self.dc_value = dc_value
        self.rle_folge = rle_folge


class SymbBlockFolge:
    def __init__(self):
        self.blocks = []

    def add_element(self, block):
        self.blocks.append(block)
