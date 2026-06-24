import re
from pathlib import Path
from typing import List, Tuple

from models import Meeting, Section, TranscriptEntry


def parse_file(filepath: Path, raw_text: str, checksum: str) -> Tuple[Meeting, List[Section], List[TranscriptEntry]]:
    if filepath.suffix.lower() == ".vtt":
        return parse_vtt(filepath, raw_text, checksum)
    return parse_txt(filepath, raw_text, checksum)


def parse_txt(filepath: Path, raw_text: str, checksum: str) -> Tuple[Meeting, List[Section], List[TranscriptEntry]]:
    meeting = Meeting(
        filename=filepath.name,
        title=filepath.stem,
        checksum=checksum,
        raw_text=raw_text,
        meeting_date=extract_date_from_text(raw_text),
    )

    sections = []
    entries = []
    lines = raw_text.splitlines()
    current_heading = None
    current_content = []
    pos = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if re.match(r'^#{1,3}\s+', stripped):
            if current_heading:
                sections.append(Section(
                    heading=current_heading,
                    content="\n".join(current_content),
                    position=pos,
                ))
                pos += 1
                current_content = []
            current_heading = re.sub(r'^#+\s+', '', stripped)
        elif re.match(r'^[A-Z][A-Z\s]+:$', stripped):
            sections.append(Section(
                heading=stripped.rstrip(":"),
                content="",
                position=pos,
            ))
            pos += 1
        else:
            if current_heading:
                current_content.append(stripped)
            entries.append(TranscriptEntry(
                text=stripped,
                position=len(entries),
            ))

    if current_heading:
        sections.append(Section(
            heading=current_heading,
            content="\n".join(current_content),
            position=pos,
        ))

    return meeting, sections, entries


def parse_vtt(filepath: Path, raw_text: str, checksum: str) -> Tuple[Meeting, List[Section], List[TranscriptEntry]]:
    title = extract_vtt_title(raw_text) or filepath.stem
    meeting_date = extract_date_from_text(raw_text)

    meeting = Meeting(
        filename=filepath.name,
        title=title,
        checksum=checksum,
        raw_text=raw_text,
        meeting_date=meeting_date,
    )

    entries = []
    sections = []
    speakers_seen = set()
    block_pattern = re.compile(
        r'(\d+)\n(\d{2}:\d{2}:\d{2}\.\d{3})\s-->\s(\d{2}:\d{2}:\d{2}\.\d{3})\n(.+?)(?=\n\n|\Z)',
        re.DOTALL,
    )

    for match in block_pattern.finditer(raw_text):
        start = match.group(2)
        end = match.group(3)
        text_block = match.group(4).strip()

        speaker_line = text_block.split("\n")[0]
        speaker = None
        text = text_block

        speaker_match = re.match(r'^(.+?):\s*(.*)', speaker_line)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip()
            speakers_seen.add(speaker)

        entries.append(TranscriptEntry(
            speaker=speaker,
            text=text,
            start_time=start,
            end_time=end,
            position=len(entries),
        ))

    meeting.speaker_count = len(speakers_seen)

    header_match = re.search(
        r'(?:Agenda|Topics|Sections?|Discussion):(.+?)(?=\n\n|\Z)',
        raw_text,
        re.IGNORECASE | re.DOTALL,
    )
    if header_match:
        for i, h in enumerate(header_match.group(1).strip().split("\n")):
            h = h.strip().lstrip("-* ")
            if h:
                sections.append(Section(heading=h, content="", position=i))

    return meeting, sections, entries


def extract_date_from_text(text: str) -> str:
    patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}/\d{2}/\d{4})',
        r'(Date:?\s*(.+?))[\r\n]',
        r'(Meeting Date:?\s*(.+?))[\r\n]',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            date_str = m.group(1) if m.lastindex == 1 else m.group(2)
            date_str = date_str.strip().rstrip(",")
            return date_str
    return ""


def extract_vtt_title(text: str) -> str:
    m = re.search(r'^(.+)\n', text)
    if m:
        title = m.group(1).strip()
        if title.upper() != "WEBVTT":
            return title
    return ""
