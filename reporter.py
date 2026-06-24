import json
from typing import List, Optional

from models import Meeting, Topic, ActionItem, TranscriptEntry, Section


def print_meeting_summary(meeting: Meeting, sections: List[Section], entries: List[TranscriptEntry]):
    print(f"\n{'='*60}")
    print(f"  Meeting: {meeting.title or 'Untitled'}")
    print(f"  File: {meeting.filename}")
    if meeting.meeting_date:
        print(f"  Date: {meeting.meeting_date}")
    print(f"  Speakers: {meeting.speaker_count}")
    print(f"{'='*60}")

    if sections:
        print(f"\n  Sections:")
        for s in sections:
            print(f"    [{s.position + 1}] {s.heading}")

    speaker_texts = {}
    for e in entries:
        if e.speaker:
            speaker_texts.setdefault(e.speaker, []).append(e.text)

    if speaker_texts:
        print(f"\n  Speakers ({len(speaker_texts)}):")
        for speaker, texts in speaker_texts.items():
            word_count = sum(len(t.split()) for t in texts)
            print(f"    - {speaker}: {len(texts)} lines, ~{word_count} words")

    print(f"\n  Total entries: {len(entries)}")


def print_topics(topics: List[Topic]):
    if not topics:
        print("  No topics extracted.")
        return
    print(f"\n  Topics:")
    for t in topics:
        print(f"    {t.rank}. {t.topic_label} (score: {t.tfidf_score})  [{t.keywords}]")


def print_action_items(items: List[ActionItem]):
    if not items:
        print("  No action items detected.")
        return
    print(f"\n  Action Items:")
    for i, a in enumerate(items, start=1):
        print(f"    {i}. [conf: {a.confidence}] {a.text[:120]}{'...' if len(a.text) > 120 else ''}")


def print_meeting_list(meetings: List[Meeting]):
    if not meetings:
        print("No meetings found in database.")
        return
    print(f"{'ID':<5} {'Title':<30} {'Date':<15} {'Speakers':<10}")
    print("-" * 60)
    for m in meetings:
        print(f"{m.id:<5} {(m.title or 'Untitled')[:29]:<30} {(m.meeting_date or '')[:14]:<15} {m.speaker_count:<10}")


def print_search_results(meetings: List[Meeting], query: str):
    if not meetings:
        print(f"No results for '{query}'.")
        return
    print(f"\nSearch results for '{query}':")
    for m in meetings:
        snippet = ""
        if m.raw_text:
            idx = m.raw_text.lower().find(query.lower())
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(m.raw_text), idx + len(query) + 40)
                snippet = m.raw_text[start:end].replace("\n", " ")
                if start > 0:
                    snippet = "..." + snippet
                if end < len(m.raw_text):
                    snippet = snippet + "..."
        print(f"\n  [{m.id}] {m.title or m.filename}")
        print(f"  Snippet: {snippet}")
