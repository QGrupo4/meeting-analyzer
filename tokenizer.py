import re
from typing import List, Optional

from models import Token


STOPWORDS = set()
_WN_LEMMATIZER = None


def _get_stopwords():
    global STOPWORDS
    if not STOPWORDS:
        try:
            from nltk.corpus import stopwords
            STOPWORDS = set(stopwords.words("english"))
        except LookupError:
            import nltk
            nltk.download("stopwords", quiet=True)
            from nltk.corpus import stopwords
            STOPWORDS = set(stopwords.words("english"))
    return STOPWORDS


def _get_lemmatizer():
    global _WN_LEMMATIZER
    if _WN_LEMMATIZER is None:
        try:
            from nltk.stem import WordNetLemmatizer
            _WN_LEMMATIZER = WordNetLemmatizer()
        except LookupError:
            import nltk
            nltk.download("wordnet", quiet=True)
            from nltk.stem import WordNetLemmatizer
            _WN_LEMMATIZER = WordNetLemmatizer()
    return _WN_LEMMATIZER


def _get_pos(word: str) -> str:
    try:
        from nltk import pos_tag
        return pos_tag([word])[0][1]
    except LookupError:
        import nltk
        nltk.download("averaged_perceptron_tagger", quiet=True)
        from nltk import pos_tag
        return pos_tag([word])[0][1]


def _is_punctuation(word: str) -> bool:
    return bool(re.match(r'^[^\w]+$', word))


def sentence_tokenize(text: str) -> List[str]:
    try:
        from nltk.tokenize import sent_tokenize
        return sent_tokenize(text)
    except LookupError:
        import nltk
        nltk.download("punkt", quiet=True)
        from nltk.tokenize import sent_tokenize
        return sent_tokenize(text)


def word_tokenize(text: str) -> List[str]:
    try:
        from nltk.tokenize import word_tokenize
        return word_tokenize(text)
    except LookupError:
        import nltk
        nltk.download("punkt", quiet=True)
        from nltk.tokenize import word_tokenize
        return word_tokenize(text)


def tokenize_transcript_entries(
    meeting_id: int,
    entries: List,
) -> List[Token]:
    stopwords_set = _get_stopwords()
    lemmatizer = _get_lemmatizer()
    tokens: List[Token] = []
    sentence_id = 0
    token_pos = 0

    for entry in entries:
        sentences = sentence_tokenize(entry.text)
        for sent_text in sentences:
            words = word_tokenize(sent_text)
            for word in words:
                if _is_punctuation(word) or word.isdigit():
                    continue
                lower = word.lower()
                pos_tag = _get_pos(word)
                lemma = lemmatizer.lemmatize(lower)
                is_stop = lower in stopwords_set

                tokens.append(Token(
                    meeting_id=meeting_id,
                    token=lower,
                    lemma=lemma,
                    pos_tag=pos_tag,
                    sentence_id=sentence_id,
                    entry_id=entry.id,
                    position=token_pos,
                    is_stopword=is_stop,
                ))
                token_pos += 1
            sentence_id += 1

    return tokens

