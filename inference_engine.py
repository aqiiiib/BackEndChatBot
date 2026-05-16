# This file is the "Inference Engine" (Tier 2). It's the brain of the chatbot.
# It uses Natural Language Processing (NLP) techniques to understand user intent.
"""
Inference Engine — NLP pipeline:
1. Preprocessing: lowercase, tokenize, remove stopwords, stem
2. Intent detection: keyword matching with confidence scoring
3. Entity extraction: destination, package name, price range
4. Fallback: cosine similarity against all known keywords
5. Self-learning: unknown queries saved to DB
"""

import re
import math
from knowledge_base import (
    get_all_static_responses,
    get_all_packages,
    search_packages,
    save_unknown_query,
    get_learned_response,
)

# --- Manual stemming (Porter-lite suffix stripping) ---
# Stemming reduces words to their root form (e.g. "packages" -> "package")
# so that the bot can understand different variations of the same word.
SUFFIXES = ["ing", "tion", "ed", "er", "est", "ly", "ness", "ment", "s"]

def stem(word):
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) > 2:
            return word[: -len(suffix)]
    return word


# --- Stopwords ---
# Stopwords are common words (like "is", "the", "and") that don't add
# much meaning to the sentence. We remove them to focus on the important keywords.
STOPWORDS = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "into", "about", "this", "that",
    "what", "which", "who", "how", "when", "where", "can", "tell", "show",
    "give", "get", "want", "need", "like", "please", "know", "any", "some",
    "there", "their", "here", "just", "also", "very", "so", "then", "than",
    "more", "much", "many", "most", "other", "up", "out", "if", "no", "not",
    "off", "on", "over", "under", "again", "further", "then", "once"
}


def preprocess(text):
    """Lowercase, tokenize, remove stopwords, stem."""
    # NLP Preprocessing step. Converts to lowercase and removes punctuation.
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    
    # Tokenization - splitting the sentence into individual words (tokens)
    tokens = text.split()
    
    # Applying stemming and removing stopwords from the tokens
    tokens = [stem(t) for t in tokens if t not in STOPWORDS and len(t) > 1]
    return tokens


def tokenize_keywords(keyword_str):
    """Split comma-separated keyword string into stemmed tokens."""
    tokens = set()
    for kw in keyword_str.split(","):
        for t in preprocess(kw.strip()):
            tokens.add(t)
    return tokens


def cosine_similarity(tokens_a, tokens_b):
    """Simple cosine similarity between two token lists."""
    # Intent Recognition technique. Compares user input tokens with
    # our predefined keyword tokens to calculate a mathematical similarity score.
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    intersection = len(set_a & set_b)
    if intersection == 0:
        return 0.0
    return intersection / (math.sqrt(len(set_a)) * math.sqrt(len(set_b)))


# --- Package intent keywords ---
PACKAGE_TRIGGERS = {
    stem(w) for w in [
        "package", "packages", "tour", "tours", "trip", "trips", "offer",
        "offers", "deal", "deals", "plan", "plans", "holiday", "holidays",
        "vacation", "booking", "book", "available", "option", "options",
    ]
}

PRICE_TRIGGERS = {
    stem(w) for w in [
        "price", "prices", "cost", "costs", "cheap", "cheapest", "expensive",
        "budget", "afford", "rate", "rates", "how much", "fee",
    ]
}

LIST_TRIGGERS = {
    stem(w) for w in [
        "list", "show", "all", "available", "what", "which", "have",
    ]
}


def extract_price_range(text):
    """Extract a max budget from user input e.g. 'under 700', 'less than 800'."""
    text = text.lower()
    match = re.search(r"(?:under|less than|below|max|maximum|up to|upto)\s*\$?\s*(\d+)", text)
    if match:
        return float(match.group(1))
    match = re.search(r"\$\s*(\d+)", text)
    if match:
        return float(match.group(1))
    return None


def format_packages(packages):
    if not packages:
        return "I couldn't find any packages matching that criteria. Try asking for 'all packages' or a specific destination like 'beach' or 'safari'."
    lines = []
    for p in packages:
        lines.append(
            f"<b>{p['name']}</b><br>"
            f"Destinations: {p['destination']}<br>"
            f"Duration: {p['duration']} | Price: <b>USD {p['price_usd']:.0f}/person</b><br>"
            f"Highlights: {p['highlights']}<br>"
            f"{p['description']}"
        )
    return "<br><br>".join(lines)


def get_response(user_input: str) -> str:
    raw = user_input.strip()
    if not raw:
        return "Please type a message so I can help you!"

    lower = raw.lower()
    input_tokens = preprocess(raw)

    # 1. Machine Learning Integration
    # Before using keywords, the bot checks if it has LEARNED this specific query from the admin.
    # 1. Check learned responses first (self-learning layer)
    learned = get_learned_response(raw)
    if learned:
        return learned

    # Check learned responses with stemmed match
    for token in input_tokens:
        learned = get_learned_response(token)
        if learned:
            return learned

    # 2. Keyword Matching & Intent Detection
    # 2. Package listing intent
    has_package_trigger = bool(PACKAGE_TRIGGERS & set(input_tokens))
    has_price_trigger = bool(PRICE_TRIGGERS & set(input_tokens))
    has_list_trigger = bool(LIST_TRIGGERS & set(input_tokens))

    if has_package_trigger or (has_list_trigger and any(
        w in lower for w in ["tour", "trip", "package", "offer", "holiday"]
    )):
        # Price filter?
        max_price = extract_price_range(lower)
        if max_price:
            all_pkgs = get_all_packages()
            filtered = [p for p in all_pkgs if p["price_usd"] <= max_price]
            return (
                f"Here are packages under USD {max_price:.0f}:<br><br>"
                + format_packages(filtered)
                if filtered
                else f"No packages found under USD {max_price:.0f}. Our most affordable option is the Budget Backpacker at USD 320."
            )
        # Destination search?
        destinations = [
            "beach", "surf", "kandy", "ella", "sigiriya", "galle", "yala",
            "safari", "wildlife", "cultural", "honeymoon", "budget", "backpack",
            "colombo", "trincomalee", "nuwara", "mirissa", "arugam",
        ]
        for dest in destinations:
            if dest in lower:
                results = search_packages(dest)
                if results:
                    return f"Here are packages related to <b>{dest.title()}</b>:<br><br>" + format_packages(results)

        # General package listing
        all_pkgs = get_all_packages()
        return (
            f"We offer <b>{len(all_pkgs)} travel packages</b> to Sri Lanka:<br><br>"
            + format_packages(all_pkgs)
        )

    # Price query without explicit package trigger
    if has_price_trigger:
        all_pkgs = get_all_packages()
        lines = [f"<b>{p['name']}</b> — USD {p['price_usd']:.0f} ({p['duration']})" for p in all_pkgs]
        return "Here's a quick price overview of our packages:<br><br>" + "<br>".join(lines) + "<br><br>Ask me about any specific package for full details!"

    # 3. Static intent matching with cosine similarity
    static_responses = get_all_static_responses()
    best_score = 0.0
    best_response = None

    for intent, keywords, response in static_responses:
        kw_tokens = list(tokenize_keywords(keywords))
        score = cosine_similarity(input_tokens, kw_tokens)
        # Boost: exact keyword word boundary match
        for kw in keywords.split(","):
            kw = kw.strip().lower()
            if kw and re.search(rf"\b{re.escape(kw)}\b", lower):
                score += 0.4
                break
        if score > best_score:
            best_score = score
            best_response = response

    CONFIDENCE_THRESHOLD = 0.15
    if best_score >= CONFIDENCE_THRESHOLD and best_response:
        return best_response

    # 4. Broad destination / activity search in package DB
    search_hits = search_packages(raw[:50])
    if search_hits:
        return (
            f"I found some packages that might match what you're looking for:<br><br>"
            + format_packages(search_hits[:3])
        )

    # Machine Learning / Self-learning trigger
    # If the bot couldn't find a match (intent failed), it saves the query to the Knowledge Base database.
    # 5. Unknown — save for self-learning
    save_unknown_query(raw)
    return (
        "I'm not sure I understood that. I've noted your question and will learn from it! "
        "You can ask me about: <b>travel packages, destinations, visa requirements, "
        "weather, currency, food, accommodation, or transport</b> in Sri Lanka."
    )
