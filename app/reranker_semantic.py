import os
from sentence_transformers import SentenceTransformer, util
current_script_dir = os.path.dirname(os.path.abspath(__file__))

LOCAL_MODEL_PATH = os.path.join(current_script_dir, "..", "models", "paraphrase-MiniLM-L6-v2")

try:
    model = SentenceTransformer(LOCAL_MODEL_PATH)
except Exception as e:
    print(f"Error loading model from local path: {LOCAL_MODEL_PATH}. Error: {e}")
    print("Ensure the model is downloaded to this path and all files are present.")
    raise 

def rerank_semantic(top_headings, query, top_k=5):
    candidates = [h["heading"] for h in top_headings]
    query_emb = model.encode(query, convert_to_tensor=True)
    cand_embs = model.encode(candidates, convert_to_tensor=True)

    similarities = util.cos_sim(query_emb, cand_embs)[0]

    scored = []
    for i, score in enumerate(similarities):
        h = top_headings[i].copy()
        h["semantic_score"] = float(score)
        scored.append(h)

    return sorted(scored, key=lambda x: -x["semantic_score"])[:top_k]
