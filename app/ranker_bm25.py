from rank_bm25 import BM25Okapi
import re

def simple_tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())

def rank_bm25(all_headings, query):
    filtered = [
        (h, h.get("text") or h.get("section_title", ""))
        for h in all_headings
        if len((h.get("text") or h.get("section_title", "")).split()) >= 4
    ]
    
    if not filtered:
        return []

    headings_only = [t for _, t in filtered]
    tokenized_corpus = [simple_tokenize(t) for t in headings_only]
    bm25 = BM25Okapi(tokenized_corpus)

    query_tokens = simple_tokenize(query)
    scores = bm25.get_scores(query_tokens)

    results = []
    for i, (h, _) in enumerate(filtered):
        h_copy = h.copy()
        h_copy["bm25_score"] = float(scores[i])
        h_copy["heading"] = h.get("text", h.get("section_title", ""))
        results.append(h_copy)

    return sorted(results, key=lambda x: -x["bm25_score"])
