import argparse
import hashlib
import json
import re
import sys

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List

# --------------------------

try:
    import fitz  #PyMuPDF
except Exception:
    fitz = None

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except Exception:
    pdfminer_extract_text = None

# --------------------------


def read_binary(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# -------------------------- Extração de texto


def extract_with_pymupdf(pdf_path: Path) -> List[str]:
    pages: List[str] = []
    doc = fitz.open(pdf_path.as_posix())
    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))
        page_buf: List[str] = []
        for b in blocks:
            text = b[4]
            if text:
                page_buf.append(text)
        pages.append("\n".join(page_buf))
    doc.close()
    return pages


def extract_with_pdfminer(pdf_path: Path) -> List[str]:
    full = pdfminer_extract_text(pdf_path.as_posix())
    raw_pages = full.split("\f")
    raw_pages = [p for p in raw_pages if p.strip()]
    return raw_pages


def extract_text_pages(pdf_path: Path, prefer="pymupdf") -> List[str]:
    if prefer == "pymupdf" and fitz:
        try:
            pages = extract_with_pymupdf(pdf_path)
            if any(p.strip() for p in pages):
                return pages
        except Exception:
            pass

    if pdfminer_extract_text:
        try:
            pages = extract_with_pdfminer(pdf_path)
            if any(p.strip() for p in pages):
                return pages
        except Exception:
            pass

    return []


# -------------------------- Limpeza/reconstrução

_hyphen_linebreak = re.compile(r"(\w)-\n(\w)")
_newline_in_para = re.compile(r"(?<!\n)\n(?!\n)")
_multi_newlines = re.compile(r"\n{3,}")
_multi_spaces = re.compile(r"[ \t]{2,}")
_trailing_spaces = re.compile(r"[ \t]+\n")
_whitespace = re.compile(r"[ \t]+")


def dehyphenate(text: str) -> str:
    while True:
        new = _hyphen_linebreak.sub(r"\1\2", text)
        if new == text:
            break
        text = new
    return text


def join_single_newlines(text: str) -> str:
    return _newline_in_para.sub(" ", text)


def normalize_spaces(text: str) -> str:
    text = _trailing_spaces.sub("\n", text)
    text = _multi_spaces.sub(" ", text)
    text = _multi_newlines.sub("\n\n", text)
    return _whitespace.sub(" ", text).strip()


def remove_repeat_headers_footers(pages: List[str]) -> List[str]:
    n = len(pages)
    if n < 3:
        return pages

    top_lines = []
    bottom_lines = []
    for p in pages:
        lines = [ln.strip() for ln in p.splitlines() if ln.strip()]
        if not lines:
            top_lines.append("")
            bottom_lines.append("")
            continue
        top_lines.append(lines[0])
        bottom_lines.append(lines[-1])

    top_counter = Counter(top_lines)
    bottom_counter = Counter(bottom_lines)

    threshold = max(3, int(n * 0.7))

    top_rep = {ln for ln, c in top_counter.items() if ln and c >= threshold}
    bot_rep = {ln for ln, c in bottom_counter.items() if ln and c >= threshold}

    cleaned = []
    for p in pages:
        lines = [ln for ln in p.splitlines()]
        if lines and lines[0].strip() in top_rep:
            lines = lines[1:]
        if lines and lines[-1].strip() in bot_rep:
            lines = lines[:-1]
        cleaned.append("\n".join(lines))
    return cleaned


def clean_and_format_pages(pages: List[str]) -> List[str]:
    cleaned_pages = []
    for p in pages:
        t = p
        t = dehyphenate(t)
        t = join_single_newlines(t)
        t = normalize_spaces(t)
        cleaned_pages.append(t)
    cleaned_pages = remove_repeat_headers_footers(cleaned_pages)
    return cleaned_pages


# -------------------------- Chunks

_sentence_splitter = re.compile(r"([.!?。！？]+)(\s+)")


def split_into_sentences(text: str) -> List[str]:
    parts = _sentence_splitter.split(text)
    if len(parts) <= 1:
        return [text.strip()] if text.strip() else []

    out = []
    buf = []
    for i in range(0, len(parts), 3):
        seg = parts[i]
        punct = parts[i + 1] if i + 1 < len(parts) else ""
        space = parts[i + 2] if i + 2 < len(parts) else ""
        full = (seg + punct).strip()
        if full:
            buf.append(full)
        out.append(" ".join(buf).strip())
        buf = []
    if buf:
        out.append(" ".join(buf).strip())
    return [s for s in out if s]


def make_chunks(
    text: str,
    max_chars: int = 1200,
    min_chars: int = 400,
    overlap: int = 150,
) -> List[str]:
    sentences = split_into_sentences(text)
    chunks: List[str] = []
    buf: List[str] = []
    buf_len = 0

    def flush(force=False):
        nonlocal buf, buf_len
        if not buf:
            return
        joined = " ".join(buf).strip()
        if force or len(joined) >= min_chars or not chunks:
            chunks.append(joined)
            if overlap > 0:
                start = max(0, len(joined) - overlap)
                tail = joined[start:]
                space_pos = tail.find(" ")
                if space_pos > 0 and space_pos < len(tail) - 1:
                    tail = tail[space_pos + 1 :]
                tail = tail.lstrip()
                buf = [tail] if tail else []
                buf_len = len(tail)
            else:
                buf = []
                buf_len = 0

    for s in sentences:
        if not s:
            continue
        if buf_len + len(s) + 1 <= max_chars:
            buf.append(s)
            buf_len += len(s) + 1
        else:
            flush(force=True)
            buf = [s]
            buf_len = len(s)
    flush(force=True)
    chunks = [c.strip() for c in chunks if c.strip()]
    return chunks


# -------------------------- Pipeline principal

@dataclass
class ChunkRecord:
    doc_id: str
    source_path: str
    page_from: int
    page_to: int
    chunk_index: int
    text: str


def process_pdf(
    pdf_path: Path,
    prefer: str = "pymupdf",
    max_chars: int = 1200,
    min_chars: int = 400,
    overlap: int = 150,
):
    pages = extract_text_pages(pdf_path, prefer=prefer)

    if not any(p.strip() for p in pages):
        return []

    pages = clean_and_format_pages(pages)

    page_offsets = []
    buf = []
    total = 0
    for i, p in enumerate(pages, start=1):
        page_offsets.append((i, total, total + len(p)))
        buf.append(p)
        total += len(p) + 2
    full_text = "\n\n".join(buf).strip()

    chunk_texts = make_chunks(full_text, max_chars=max_chars, min_chars=min_chars, overlap=overlap)

    def page_range_for_span(start_idx: int, end_idx: int):
        start_page = 1
        end_page = len(pages)
        for (pg, a, b) in page_offsets:
            if a <= start_idx <= b:
                start_page = pg
                break
        for (pg, a, b) in page_offsets:
            if a <= end_idx <= b:
                end_page = pg
                break
        return start_page, end_page

    doc_hash = hashlib.sha1(read_binary(pdf_path)).hexdigest()

    chunk_records = []
    cursor = 0
    for idx, c in enumerate(chunk_texts):
        pos = full_text.find(c, cursor)
        if pos == -1:
            pos = full_text.find(c)
        if pos == -1:
            pf, pt = (1, len(pages))
        else:
            pf, pt = page_range_for_span(pos, pos + len(c))
            cursor = pos + len(c)

        rec = ChunkRecord(
            doc_id=doc_hash,
            source_path=pdf_path.as_posix(),
            page_from=pf,
            page_to=pt,
            chunk_index=idx,
            text=c,
        )
        chunk_records.append(rec)

    return chunk_records


def iter_pdf_files(input_path: Path):
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        yield input_path
    elif input_path.is_dir():
        for p in sorted(input_path.rglob("*.pdf")):
            if p.is_file():
                yield p


def main():
    parser = argparse.ArgumentParser(description="Extrair e chunkear PDFs para busca vetorial (gera um único JSONL).")
    parser.add_argument("--input", required=True, help="Arquivo PDF ou pasta com PDFs.")
    parser.add_argument("--out", required=True, help="Arquivo de saída JSONL (um chunk por linha).")
    parser.add_argument("--prefer", default="pymupdf", choices=["pymupdf", "pdfminer"], help="Extrator preferido.")
    parser.add_argument("--max-chars", type=int, default=1200, help="Tamanho máximo de chunk.")
    parser.add_argument("--min-chars", type=int, default=400, help="Tamanho mínimo desejado para flush do buffer.")
    parser.add_argument("--overlap", type=int, default=150, help="Overlap (em caracteres) entre chunks.")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_chunks = 0
    with open(out_path.as_posix(), "w", encoding="utf-8") as fout:
        for pdf in iter_pdf_files(input_path):
            try:
                recs = process_pdf(
                    pdf_path=pdf,
                    prefer=args.prefer,
                    max_chars=args.max_chars,
                    min_chars=args.min_chars,
                    overlap=args.overlap,
                )
                for r in recs:
                    fout.write(json.dumps(r.__dict__, ensure_ascii=False) + "\n")
                print(f"[OK] {pdf.name}: {len(recs)} chunks")
                all_chunks += len(recs)
            except Exception as e:
                print(f"[ERRO] {pdf}: {e}", file=sys.stderr)

    print(f"Concluído. Total de chunks: {all_chunks}")
    print(f"Saída: {out_path.as_posix()}")


if __name__ == "__main__":
    main()


# ---------------

"""
import fitz

class ExtractorPDF():
    def __init__(self):
        self.pdf_path = "files/Texto_Exemplo.pdf"
        self.pdf_file = fitz.open(self.pdf_path)
    
    def extract_pdf_to_text(self):
        text = ""

        for page in self.pdf_file:
            text += page.get_text("text")

            text = text.replace("\n", " ")
            text = " ".join(text.split())
            
        return text
    
    def extract_pdf_to_token(self):
        tokens = []
        initial_point = 0
        count = 0
        text = self.extract_pdf_to_text()

        for i in text:
            if i in [" ", "."]:
                token = text[initial_point:count + 1]
                initial_point = count + 1
                tokens.append(token)
            count += 1

        return tokens
    """
