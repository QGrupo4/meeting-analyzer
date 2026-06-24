from dataclasses import dataclass
from typing import Optional


@dataclass
class Meeting:
    id: Optional[int] = None
    title: Optional[str] = None
    filename: str = ""
    meeting_date: Optional[str] = None
    imported_at: Optional[str] = None
    checksum: str = ""
    raw_text: str = ""
    speaker_count: int = 0


@dataclass
class Section:
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    heading: str = ""
    content: str = ""
    position: int = 0


@dataclass
class TranscriptEntry:
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    speaker: Optional[str] = None
    text: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    position: int = 0


@dataclass
class Token:
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    token: str = ""
    lemma: str = ""
    pos_tag: str = ""
    sentence_id: int = 0
    entry_id: Optional[int] = None
    position: int = 0
    is_stopword: bool = False


@dataclass
class Topic:
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    meeting_title: Optional[str] = None
    topic_label: str = ""
    keywords: str = ""
    tfidf_score: float = 0.0
    rank: int = 0


@dataclass
class ActionItem:
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    entry_id: Optional[int] = None
    text: str = ""
    confidence: float = 0.0
