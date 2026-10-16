# AGENTS.md

## Overview

Educational JPEG-compression visualizer (Streamlit web app), ported from Java VisJPEG 2.0. Small single-package repo (~2k lines). All UI strings, docstrings, and README are German — keep new user-facing text German.

- Core pipeline is GUI-independent: `jpeg_image.py` (loading, YIQ, subsampling, DCT, quantization, PSNR), `block.py` (8x8 DCT/iDCT, zig-zag), `matrix.py`, `jpeg_parameter.py`, `huffman.py`, `rle.py`.
- `streamlit_app.py` is presentation only; all UI state lives in `get_state()` / `st.session_state`.

## Commands

- Install + run: `pip install -e .` then `visjpeg` (or `python -m visjpeg`, `python run.py`). Port is auto-picked from 8501 upward; force with `visjpeg --server.port 8502`.
- Tests: `pytest tests/ -v`. Core suite (`test_pipeline.py`) needs only `pytest`, `numpy`, `Pillow`. `test_step_navigation.py` (Streamlit AppTest) additionally needs `streamlit`, `plotly`, `matplotlib` and skips automatically when they are missing (`pip install -e ".[dev]"` does not pull them).
- No lint, formatter, typecheck, or CI config exists in this repo — don't invent such commands.

## Golden tests pin the numerics — intentionally

`tests/test_pipeline.py` asserts exact PSNR values (±0.05) and Huffman bit counts for sample images. Changing DCT, quantization, zig-zag, or RLE numerics breaks these tests **by design** — the goal is parity with the original Java implementation (see commit "Fix DCT/iDCT NumPy implementation to match original Java algorithm exactly"). Only regenerate expected values as a deliberate, documented decision.

Regeneration history: 2026-10-16 the 3 `total_bits` values (21393 / 33591 / 16267) were regenerated after fixing the AC RLE encoder to emit real VLI categories instead of hardcoded `size_non_zero = 1` (user-approved). PSNR values were unaffected.

## Matrix indexing is transposed: `[x][y]`

- `Matrix.matrix` is indexed `[x][y]` (column-major, kept from the Java port). Row-ordered data must be transposed when loading: `m.matrix[x][y] = vals[y][x]` — see `_init_standard_matrices()` in `jpeg_parameter.py` and the test fixtures.
- `Matrix` clamps all values into `[1, 255]` (both constructor and `scale()`); a default `Matrix()` is all 1s, not 0s.

## Mutable shared state gotchas

- `JPEGParameter.STANDARD_QMATRIX_*` are class-level and shared. `scale()` mutates in place — always `clone()` first, never scale the class-level matrices.
- `JPEGImage` caches derived images/stats keyed by `JPEGParameter.__eq__` (e.g. `_huffman_stats_cache`, `*_last_params`). If you add a field to `JPEGParameter` that affects pipeline output, add it to `__eq__` too, or caches return stale results. After raw-image changes call `invalidate()`.

## Streamlit widget gotchas

- Never pass `index=` to a keyless widget whose value changes at runtime: `index` is part of the auto-generated widget ID, so every value change re-creates the widget and real-browser clicks can be dropped (symptom: clicks must be repeated). Control such widgets via an explicit stable `key` + `st.session_state[key]` set *before* `st.rerun()` — see the `schritt_nav` radio in `streamlit_app.py`. Note: `streamlit.testing.v1.AppTest` does NOT reproduce this bug (it bypasses widget-ID handling), so AppTest passing is not proof against it.
- UI strings use the modern `width="stretch"` parameter, not the removed `use_container_width` (deprecated 2025-12-31).
- Keep all user-facing strings German.

## Sample images are runtime data

Sample images live inside `visjpeg/` and are loaded by paths relative to the module dir (`_MODULE_DIR`); tests read them from there as well (not from `tests/`). Don't relocate them. `JPEGImage` silently falls back to a black 192×144 error image on load failure; the pipeline canvas is fixed at 192×144.
