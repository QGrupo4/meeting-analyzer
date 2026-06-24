import sqlite3
from typing import List, Optional
from models import Meeting, Section, TranscriptEntry, Token, Topic, ActionItem


DB_PATH = "meetings.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            filename TEXT NOT NULL,
            meeting_date TEXT,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checksum TEXT NOT NULL,
            raw_text TEXT,
            speaker_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
            heading TEXT,
            content TEXT,
            position INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS transcript_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
            speaker TEXT,
            text TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            position INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
            token TEXT NOT NULL,
            lemma TEXT,
            pos_tag TEXT,
            sentence_id INTEGER DEFAULT 0,
            entry_id INTEGER REFERENCES transcript_entries(id) ON DELETE SET NULL,
            position INTEGER DEFAULT 0,
            is_stopword INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
            meeting_title TEXT,
            topic_label TEXT NOT NULL,
            keywords TEXT,
            tfidf_score REAL DEFAULT 0.0,
            rank INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
            entry_id INTEGER REFERENCES transcript_entries(id) ON DELETE SET NULL,
            text TEXT NOT NULL,
            confidence REAL DEFAULT 0.0
        );

        CREATE INDEX IF NOT EXISTS idx_meetings_checksum ON meetings(checksum);
        CREATE INDEX IF NOT EXISTS idx_tokens_meeting ON tokens(meeting_id);
        CREATE INDEX IF NOT EXISTS idx_tokens_token ON tokens(token);
        CREATE INDEX IF NOT EXISTS idx_entries_meeting ON transcript_entries(meeting_id);
        CREATE INDEX IF NOT EXISTS idx_topics_meeting ON topics(meeting_id);
        CREATE INDEX IF NOT EXISTS idx_actions_meeting ON action_items(meeting_id);
    """)
    conn.commit()
    conn.close()


def meeting_exists_by_checksum(checksum: str) -> Optional[int]:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM meetings WHERE checksum = ?", (checksum,)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def insert_meeting(meeting: Meeting) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO meetings (title, filename, meeting_date, checksum, raw_text, speaker_count)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (meeting.title, meeting.filename, meeting.meeting_date,
         meeting.checksum, meeting.raw_text, meeting.speaker_count),
    )
    meeting_id = cur.lastrowid
    conn.commit()
    conn.close()
    return meeting_id


def update_meeting(meeting: Meeting):
    conn = get_connection()
    conn.execute(
        """UPDATE meetings SET title=?, filename=?, meeting_date=?, checksum=?,
           raw_text=?, speaker_count=?, imported_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (meeting.title, meeting.filename, meeting.meeting_date,
         meeting.checksum, meeting.raw_text, meeting.speaker_count, meeting.id),
    )
    conn.commit()
    conn.close()


def delete_meeting_sections(meeting_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM sections WHERE meeting_id = ?", (meeting_id,))
    conn.commit()
    conn.close()


def insert_section(section: Section) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO sections (meeting_id, heading, content, position) VALUES (?, ?, ?, ?)",
        (section.meeting_id, section.heading, section.content, section.position),
    )
    section_id = cur.lastrowid
    conn.commit()
    conn.close()
    return section_id


def insert_entries(entries: List[TranscriptEntry]):
    conn = get_connection()
    conn.executemany(
        "INSERT INTO transcript_entries (meeting_id, speaker, text, start_time, end_time, position) VALUES (?, ?, ?, ?, ?, ?)",
        [(e.meeting_id, e.speaker, e.text, e.start_time, e.end_time, e.position) for e in entries],
    )
    conn.commit()
    conn.close()


def insert_tokens(tokens: List[Token]):
    conn = get_connection()
    conn.executemany(
        "INSERT INTO tokens (meeting_id, token, lemma, pos_tag, sentence_id, entry_id, position, is_stopword) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(t.meeting_id, t.token, t.lemma, t.pos_tag, t.sentence_id, t.entry_id, t.position, int(t.is_stopword)) for t in tokens],
    )
    conn.commit()
    conn.close()


def insert_topics(topics: List[Topic]):
    conn = get_connection()
    conn.executemany(
        "INSERT INTO topics (meeting_id, meeting_title, topic_label, keywords, tfidf_score, rank) VALUES (?, ?, ?, ?, ?, ?)",
        [(t.meeting_id, t.meeting_title, t.topic_label, t.keywords, t.tfidf_score, t.rank) for t in topics],
    )
    conn.commit()
    conn.close()


def insert_action_items(items: List[ActionItem]):
    conn = get_connection()
    conn.executemany(
        "INSERT INTO action_items (meeting_id, entry_id, text, confidence) VALUES (?, ?, ?, ?)",
        [(i.meeting_id, i.entry_id, i.text, i.confidence) for i in items],
    )
    conn.commit()
    conn.close()


def get_all_meetings() -> List[Meeting]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM meetings ORDER BY imported_at DESC").fetchall()
    conn.close()
    return [Meeting(**dict(r)) for r in rows]


def get_meeting(meeting_id: int) -> Optional[Meeting]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    conn.close()
    return Meeting(**dict(row)) if row else None


def get_entries(meeting_id: int) -> List[TranscriptEntry]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transcript_entries WHERE meeting_id = ? ORDER BY position",
        (meeting_id,),
    ).fetchall()
    conn.close()
    return [TranscriptEntry(**dict(r)) for r in rows]


def get_sections(meeting_id: int) -> List[Section]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sections WHERE meeting_id = ? ORDER BY position",
        (meeting_id,),
    ).fetchall()
    conn.close()
    return [Section(**dict(r)) for r in rows]


def search_meetings(query: str) -> List[Meeting]:
    conn = get_connection()
    pattern = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM meetings WHERE raw_text LIKE ? ORDER BY imported_at DESC",
        (pattern,),
    ).fetchall()
    conn.close()
    return [Meeting(**dict(r)) for r in rows]


def get_topics(meeting_id: Optional[int] = None) -> List[Topic]:
    conn = get_connection()
    if meeting_id:
        rows = conn.execute(
            "SELECT * FROM topics WHERE meeting_id = ? ORDER BY rank",
            (meeting_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM topics ORDER BY meeting_id, rank"
        ).fetchall()
    conn.close()
    return [Topic(**dict(r)) for r in rows]


def get_action_items(meeting_id: Optional[int] = None) -> List[ActionItem]:
    conn = get_connection()
    if meeting_id:
        rows = conn.execute(
            "SELECT * FROM action_items WHERE meeting_id = ?",
            (meeting_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM action_items").fetchall()
    conn.close()
    return [ActionItem(**dict(r)) for r in rows]


def export_meeting_json(meeting_id: int) -> dict:
    meeting = get_meeting(meeting_id)
    if not meeting:
        return {}
    sections = get_sections(meeting_id)
    entries = get_entries(meeting_id)
    topics = get_topics(meeting_id)
    actions = get_action_items(meeting_id)
    return {
        "meeting": {
            "id": meeting.id,
            "title": meeting.title,
            "filename": meeting.filename,
            "date": meeting.meeting_date,
            "speaker_count": meeting.speaker_count,
        },
        "sections": [
            {"heading": s.heading, "content": s.content, "position": s.position}
            for s in sections
        ],
        "entries": [
            {"speaker": e.speaker, "text": e.text, "time": f"{e.start_time} -> {e.end_time}" if e.start_time else None}
            for e in entries
        ],
        "topics": [
            {"topic": t.topic_label, "keywords": t.keywords, "score": t.tfidf_score}
            for t in topics
        ],
        "action_items": [{"text": a.text} for a in actions],
    }
