"""Text normalization untuk parser rally.

Tujuan: membersihkan teks OCR/manual menjadi bentuk yang mudah diparse,
tanpa kehilangan informasi rally penting (BR vs br tetap dipertahankan).
"""

from __future__ import annotations

import re
import unicodedata


# Karakter yang sering dipakai OCR sebagai ganti karakter sebenarnya.
_OCR_FIXES = {
    "—": "-",
    "–": "-",
    "•": "-",
    "→": "->",
    "↓": "->",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    " ": " ",  # non-breaking space
}

_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
# Hapus nomor halaman OCR seperti "Hal. 2/5" yang sering muncul.
_PAGE_FOOTER = re.compile(r"(?im)^\s*(hal(aman)?\.?\s*\d+(\s*/\s*\d+)?|page\s*\d+(\s*/\s*\d+)?)\s*$")


def normalize_rally_text(raw: str) -> str:
    """Normalisasi teks rally.

    Aturan:
    - karakter unicode dinormalisasi NFKC, tetapi case dipertahankan (BR vs br penting).
    - whitespace dirapikan.
    - karakter OCR umum diganti dengan pasangannya.
    - footer halaman OCR dihapus.
    - line trailing/leading whitespace di-strip.
    """
    if not raw:
        return ""

    text = unicodedata.normalize("NFKC", raw)
    for src, dst in _OCR_FIXES.items():
        text = text.replace(src, dst)

    # Hilangkan footer halaman OCR
    text = _PAGE_FOOTER.sub("", text)

    lines = [line.rstrip() for line in text.splitlines()]
    # Strip baris kosong di awal/akhir tapi pertahankan struktur paragraph
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    text = "\n".join(lines)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def split_sub_trayek_blocks(text: str) -> list[tuple[str, str]]:
    """Memecah teks menjadi list (label, body) per Sub.

    Mendukung pola:
        SUB A: ...
        Sub B - ...
        SUB-C ...
    """
    pattern = re.compile(r"(?im)^\s*sub[\s\-]*([A-Z])\b[\s:.\-]*(.*)$")
    blocks: list[tuple[str, str]] = []
    current_label: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            if current_label is not None:
                blocks.append((current_label, "\n".join(current_lines).strip()))
            current_label = match.group(1).upper()
            tail = match.group(2).strip()
            current_lines = [tail] if tail else []
        else:
            if current_label is not None:
                current_lines.append(line)
    if current_label is not None:
        blocks.append((current_label, "\n".join(current_lines).strip()))

    return blocks
