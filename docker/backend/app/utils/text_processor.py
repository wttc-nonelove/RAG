import re


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[　]+", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 128) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):
            last_period = chunk.rfind("。")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)
            if break_point > chunk_size // 2:
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - chunk_overlap
        if start >= len(text):
            break

    return chunks


def _section_title(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    patterns = [
        r"^#{1,6}\s+(.+)$",
        r"^(第[一二三四五六七八九十百千万\d]+[章节条款].*)$",
        r"^([一二三四五六七八九十]+[、.．].{2,60})$",
        r"^(\d+(\.\d+){0,3}[、.．\s].{2,60})$",
    ]
    for pattern in patterns:
        match = re.match(pattern, stripped)
        if match:
            return match.group(1).strip()
    return None


def chunk_text_with_metadata(text: str, chunk_size: int = 512, chunk_overlap: int = 128) -> list[dict]:
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return []

    section_markers = []
    current = ""
    offset = 0
    for line in text.splitlines(True):
        title = _section_title(line)
        if title:
            current = title
        section_markers.append((offset, current))
        offset += len(line)

    enriched = []
    search_start = 0
    for index, chunk in enumerate(chunks):
        start = text.find(chunk[:80], search_start)
        if start < 0:
            start = search_start
        search_start = max(start + len(chunk) - chunk_overlap, start + 1)

        section_path = ""
        for marker_offset, marker_title in section_markers:
            if marker_offset <= start and marker_title:
                section_path = marker_title
            elif marker_offset > start:
                break

        enriched.append({
            "text": chunk,
            "chunk_index": index,
            "section_path": section_path or "正文",
            "start_char": start,
            "end_char": start + len(chunk),
        })
    return enriched
