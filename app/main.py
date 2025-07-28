import os
import sys
import json
from datetime import datetime
from importlib.util import spec_from_file_location, module_from_spec

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

round1a_app_path = os.path.join(base_dir, 'Round_1A', 'app')
if round1a_app_path not in sys.path:
    sys.path.insert(0, round1a_app_path)

_outline_extractor_path = os.path.join(round1a_app_path, 'outline_extractor.py')
print(f"Attempting to load outline_extractor from: {_outline_extractor_path}")
try:
    _spec = spec_from_file_location("_outline_extractor_module", _outline_extractor_path)
    _outline_extractor_module = module_from_spec(_spec)
    _spec.loader.exec_module(_outline_extractor_module)
    print("outline_extractor module loaded successfully.")
except Exception as e:
    print(f"Error loading outline_extractor module: {e}")
    sys.exit(1) 

from app.ranker_bm25 import rank_bm25
from app.reranker_semantic import rerank_semantic

CURRENT_ROUND_DIR = os.path.dirname(os.path.abspath(__file__)) 
INPUT_DIR = os.path.join(CURRENT_ROUND_DIR, "..", "input_docs")
OUTPUT_DIR = os.path.join(CURRENT_ROUND_DIR, "..", "outputs")
TEMP_HEADINGS_FILE_NAME = ".temp_headings.json" 
TOP_K = 5

def read_txt(file_path):
    """Reads content from a text file, returns empty string on error."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: File not found - {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def process_collection(collection_path):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdfs = [f for f in os.listdir(collection_path) if f.lower().endswith(".pdf")]
    
    if not pdfs:
        return

    persona = read_txt(os.path.join(collection_path, "persona.txt"))
    job = read_txt(os.path.join(collection_path, "job.txt"))
    
    if not persona and not job:
        query = ""
    elif not persona:
        query = f"As a user, {job}"
    elif not job:
        query = f"As a {persona}, perform a task."
    else:
        query = f"As a {persona}, {job}"
    
    if not query:
        print(f"No valid query could be formed for {collection_path}. Cannot rank headings.")

    all_headings = []
    span_map = {} 

    for pdf in pdfs:
        pdf_path = os.path.join(collection_path, pdf)
        print(f"  - Extracting outline from: {pdf_path}")
        
        try:
            outline_result = _outline_extractor_module.extract_outline(
                pdf_path, pdf, include_content=True
            )
            headings = outline_result["outline"]
            spans = outline_result.get("spans", [])
            span_map[pdf] = spans
            for h in headings:
                h["source"] = pdf
                all_headings.append(h)
        except Exception as e:
            print(f"    - Error extracting outline from {pdf}: {e}")

    if not all_headings:
        print(f"No headings found in any PDF in {collection_path}. Skipping ranking and output for this collection.")
        return
    temp_headings_file_path = os.path.join(collection_path, TEMP_HEADINGS_FILE_NAME)
    
    try:
        with open(temp_headings_file_path, "w", encoding="utf-8") as f:
            json.dump(all_headings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  - Error saving temporary headings file: {e}")

    if query:
        def is_valid_heading(h):
            heading = h.get("text") or h.get("section_title", "")
            try:
                level = int(h.get("level", 1)) 
            except (ValueError, TypeError):
                level = 1
            return len(heading.split()) >= 4 and level <= 2

        filtered_headings = [h for h in all_headings if is_valid_heading(h)]
        top_bm25 = rank_bm25(filtered_headings, query)

        top_20 = top_bm25[:20] 

        print(f"  - Reranking semantically (top {TOP_K})...")
        reranked = rerank_semantic(top_20, query, top_k=TOP_K)
    else:
        print("  - Skipping ranking due to no valid query. Using all extracted headings.")
        reranked = filtered_headings[:TOP_K] 
        for item in reranked:
            item["semantic_score"] = 0.0 

    result = {
        "collection_name": os.path.basename(collection_path),
        "metadata": {
            "input_documents": pdfs,
            "persona": persona,
            "job_to_be_done": job,
            "query_used": query, 
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }

    for i, item in enumerate(reranked, 1):
        doc_source = item.get("source", "unknown_document")
        section_title = item.get("text") or item.get("section_title", "Untitled Section")
        page_num = item.get("page", -1) 
        result["extracted_sections"].append({
            "document": doc_source,
            "section_title": section_title,
            "importance_rank": i,
            "page_number": page_num,
        })

        spans = span_map.get(doc_source)
        page_text = ""
        if spans:
            page_spans = [s for s in spans if s.get("page") == page_num] 
            page_spans.sort(key=lambda s: (s.get("y", 0), s.get("x", 0)))
            page_text = " ".join(s.get("text", "") for s in page_spans).strip()
        if not page_text:
            print(f"    - Warning: No page text found for {doc_source}, page {page_num}, section '{section_title}'")

        result["subsection_analysis"].append({
            "document": doc_source,
            "refined_text": page_text,
            "page_number": page_num
        })

    collection_output_filename = f"{os.path.basename(collection_path)}.json"
    output_path = os.path.join(OUTPUT_DIR, collection_output_filename)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving final result for {os.path.basename(collection_path)}: {e}")


def main():
    collections = [os.path.join(INPUT_DIR, folder) 
                   for folder in os.listdir(INPUT_DIR)
                   if os.path.isdir(os.path.join(INPUT_DIR, folder))]

    if not collections:
        return

    for collection in collections:
        process_collection(collection)

    for collection in collections:
        temp_file_to_clean = os.path.join(collection, TEMP_HEADINGS_FILE_NAME)
        if os.path.exists(temp_file_to_clean):
            try:
                os.remove(temp_file_to_clean)
            except Exception as e:
                print(f"Error removing temporary file {temp_file_to_clean}: {e}")
        else:
            print(f"  - No temporary file found in {collection}")


if __name__ == "__main__":
    main()