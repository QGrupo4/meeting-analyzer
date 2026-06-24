import argparse
import sys
from pathlib import Path

from database import (
    init_db, insert_meeting, insert_section, insert_entries,
    insert_tokens, insert_topics, insert_action_items,
    get_all_meetings, get_meeting, get_entries, get_sections,
    search_meetings, get_topics, get_action_items,
    delete_meeting_sections, update_meeting, export_meeting_json, meeting_exists_by_checksum,
)
from models import Meeting
from scanner import scan_folder, compute_checksum, read_file
from parser import parse_file
from tokenizer import tokenize_transcript_entries
from analyzer import extract_topics_tfidf, extract_action_items
import json
from reporter import (
    print_meeting_summary, print_topics, print_action_items,
    print_meeting_list, print_search_results,
)


def cmd_ingest(args):
    folder = args.folder
    new_files, modified_files = scan_folder(folder)

    if modified_files:
        for f in modified_files:
            print(f"  Skipping (already imported): {f.name}")

    if not new_files:
        if not modified_files:
            print(f"No new transcript files found in '{folder}'.")
        return

    # Collect all meeting texts for TF-IDF across meetings
    all_texts = {}
    existing = get_all_meetings()
    for m in existing:
        all_texts[m.id] = m.raw_text

    print(f"Found {len(new_files)} new transcript(s) in '{folder}':")
    for f in new_files:
        print(f"  Importing: {f.name}")

    for filepath in new_files:
        print(f"\n--- Processing {filepath.name} ---")
        raw_text = read_file(filepath)
        checksum = compute_checksum(filepath)

        meeting, sections, entries = parse_file(filepath, raw_text, checksum)

        meeting_id = insert_meeting(meeting)
        meeting.id = meeting_id

        for s in sections:
            s.meeting_id = meeting_id
            insert_section(s)

        for e in entries:
            e.meeting_id = meeting_id
        insert_entries(entries)

        tokens = tokenize_transcript_entries(meeting_id, entries)
        insert_tokens(tokens)

        all_texts[meeting_id] = ' '.join(e.text for e in entries)

        topics = extract_topics_tfidf(meeting_id, meeting.title or meeting.filename, all_texts)
        insert_topics(topics)

        actions = extract_action_items(meeting_id, entries)
        insert_action_items(actions)

        print(f"  Done: {len(entries)} entries, {len(tokens)} tokens, {len(topics)} topics, {len(actions)} action items")

    print("\nIngest complete.")


def cmd_list(args):
    meetings = get_all_meetings()
    print_meeting_list(meetings)


def cmd_info(args):
    meeting = get_meeting(args.id)
    if not meeting:
        print(f"Meeting with id {args.id} not found.")
        return
    sections = get_sections(args.id)
    entries = get_entries(args.id)
    print_meeting_summary(meeting, sections, entries)

    topics = get_topics(args.id)
    print_topics(topics)

    actions = get_action_items(args.id)
    print_action_items(actions)


def cmd_search(args):
    meetings = search_meetings(args.query)
    print_search_results(meetings, args.query)


def cmd_topics(args):
    if args.all:
        topics = get_topics()
    else:
        topics = get_topics(args.id) if args.id else get_topics()
    if not topics:
        print("No topics found.")
        return
    current_mid = None
    for t in topics:
        if t.meeting_id != current_mid:
            current_mid = t.meeting_id
            print(f"\nMeeting [{t.meeting_id}]: {t.meeting_title or ''}")
        print(f"  {t.rank}. {t.topic_label} ({t.tfidf_score})")


def cmd_actions(args):
    items = get_action_items(args.id) if args.id else get_action_items()
    print_action_items(items)
    if items:
        print(f"\nTotal: {len(items)} action item(s)")


def cmd_export(args):
    data = export_meeting_json(args.id)
    if not data:
        print(f"Meeting with id {args.id} not found.")
        return
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Meeting Transcript Parser & Analyzer")
    parser.set_defaults(func=None)

    sub = parser.add_subparsers(title="commands")

    p_ingest = sub.add_parser("ingest", help="Import transcripts from a folder")
    p_ingest.add_argument("folder", help="Path to folder containing .txt/.vtt files")
    p_ingest.set_defaults(func=cmd_ingest)

    p_list = sub.add_parser("list", help="List all meetings")
    p_list.set_defaults(func=cmd_list)

    p_info = sub.add_parser("info", help="Show meeting details")
    p_info.add_argument("--id", "-i", type=int, required=True, help="Meeting ID")
    p_info.set_defaults(func=cmd_info)

    p_search = sub.add_parser("search", help="Full-text search transcripts")
    p_search.add_argument("query", help="Search term")
    p_search.set_defaults(func=cmd_search)

    p_topics = sub.add_parser("topics", help="Show extracted topics")
    p_topics.add_argument("--id", "-i", type=int, help="Meeting ID")
    p_topics.add_argument("--all", action="store_true", help="Show topics for all meetings")
    p_topics.set_defaults(func=cmd_topics)

    p_actions = sub.add_parser("actions", help="Show action items")
    p_actions.add_argument("--id", "-i", type=int, help="Meeting ID")
    p_actions.set_defaults(func=cmd_actions)

    p_export = sub.add_parser("export", help="Export meeting as JSON")
    p_export.add_argument("--id", "-i", type=int, required=True, help="Meeting ID")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    if args.func is None:
        parser.print_help()
        sys.exit(1)

    init_db()
    args.func(args)


if __name__ == "__main__":
    main()


