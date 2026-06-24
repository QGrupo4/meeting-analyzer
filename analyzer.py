from typing import List, Optional
from collections import Counter
import re

from models import Topic, ActionItem, Meeting, TranscriptEntry

STOPWORDS = set()
_NLTK_READY = False


def _ensure_nltk():
    global _NLTK_READY
    if _NLTK_READY:
        return
    try:
        from nltk.corpus import stopwords
        global STOPWORDS
        STOPWORDS = set(stopwords.words("english"))
    except LookupError:
        import nltk
        nltk.download("stopwords", quiet=True)
        from nltk.corpus import stopwords
        STOPWORDS = set(stopwords.words("english"))
    _NLTK_READY = True


def extract_topics_tfidf(meeting_id: int, meeting_title: str, all_meeting_texts: dict) -> List[Topic]:
    _ensure_nltk()

    meeting_text = all_meeting_texts.get(meeting_id, "")
    if not meeting_text or len(all_meeting_texts) < 2:
        return _fallback_keywords(meeting_id, meeting_title, meeting_text)

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        return _fallback_keywords(meeting_id, meeting_title, meeting_text)

    doc_ids = list(all_meeting_texts.keys())
    docs = [all_meeting_texts[did] for did in doc_ids]

    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words=list(STOPWORDS),
        ngram_range=(1, 2),
        max_df=0.85,
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(docs)

    if meeting_id not in doc_ids:
        return _fallback_keywords(meeting_id, meeting_title, meeting_text)

    idx = doc_ids.index(meeting_id)
    feature_names = vectorizer.get_feature_names_out()
    row = tfidf_matrix[idx].toarray()[0]

    scored = [(feature_names[i], row[i]) for i in range(len(feature_names)) if row[i] > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    topics = []
    for rank, (kw, score) in enumerate(scored[:10], start=1):
        topics.append(Topic(
            meeting_id=meeting_id,
            meeting_title=meeting_title,
            topic_label=kw,
            keywords=kw,
            tfidf_score=round(score, 4),
            rank=rank,
        ))
    return topics


def _fallback_keywords(meeting_id: int, meeting_title: str, text: str) -> List[Topic]:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    words = [w for w in words if w not in STOPWORDS]
    counter = Counter(words)
    top_val = max(counter.values(), default=1)
    topics = []
    for rank, (kw, count) in enumerate(counter.most_common(10), start=1):
        topics.append(Topic(
            meeting_id=meeting_id,
            meeting_title=meeting_title,
            topic_label=kw,
            keywords=kw,
            tfidf_score=round(count / top_val, 4),
            rank=rank,
        ))
    return topics


def extract_action_items(meeting_id: int, entries: List[TranscriptEntry]) -> List[ActionItem]:
    _ensure_nltk()
    items = []
    action_patterns = re.compile(
        r'\b(action\s+item|to[\s-]do|follow[\s-]up|assign|owner|responsible|'
        r'action\s+required|'
        r'will\s+(take|do|send|prepare|create|update|review|check|fix|complete|'
        r'set\s+up|draft|investigate|reconvene|implement|migrate|deploy|write)|'
        r'(needs?\s+to|must\s+|please\s+))\b',
        re.IGNORECASE,
    )

    for entry in entries:
        if not entry.text:
            continue
        if action_patterns.search(entry.text):
            confidence = min(0.5 + 0.1 * 1, 1.0)
            items.append(ActionItem(
                meeting_id=meeting_id,
                entry_id=entry.id,
                text=entry.text[:500],
                confidence=round(confidence, 2),
            ))

    return items
