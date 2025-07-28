#  Round_1B – Persona-driven Intelligent Document Analysis

This project is part of the Adobe Hackathon submission.

**Round_1B** builds on the outline extraction system from **Round_1A** to enable _persona-driven extraction and ranking_ of relevant sections from multiple PDFs. It combines keyword-based filtering with semantic reranking for highly accurate and context-aware document intelligence.

---

## Folder Structure


```markdown
Round\_1B/
├── app/
│   ├── main.py                   # Entry point to process document collections
│   ├── ranker\_bm25.py            # BM25-based keyword relevance ranker
│   ├── reranker\_semantic.py      # SentenceTransformer-based semantic reranker
│   ├── **init**.py               # (empty)
│
├── input\_docs/
│   ├── Collection1/
│   │   ├── file1.pdf
│   │   ├── file2.pdf
│   │   ├── persona.txt           # Persona description
│   │   └── job.txt               # Job-to-be-done description
│   └── ...
│
├── models/
│   └── all-MiniLM-L6-v2/         # Local SentenceTransformer model
│
├── outputs/
│   └── Collection1\_output.json   # Final extracted results
│
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker setup
└── README.md                     # You are here

````

---

## Features

Extracts outlines (Title, H1–H3) from each PDF using font features and layout cues  
Filters relevant headings using **BM25** with persona + job keywords  
Reranks top results using **MiniLM (sentence-transformers)** for semantic similarity  
Fully **offline**, CPU-friendly (<1GB model), and completes in under 60s for 3–5 PDFs  
Outputs a **single structured JSON** for all documents in the collection

---

## Setup Instructions

### 1. Clone This Repository

```bash
git clone https://github.com/your-username/round1b-solution.git
cd round1b-solution
````

### 2. Install Requirements (for local use)

Create a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate        # on Windows
# or
source venv/bin/activate     # on Mac/Linux
```

Install packages:

```bash
pip install -r requirements.txt
```

---

## Docker Usage (Recommended)

### Build Docker Image

```bash
docker build -t round1b-solution:latest .
```

### Run the Container

```bash
docker run --rm -v "%cd%/input_docs:/app/input_docs" -v "%cd%/outputs:/app/outputs" round1b-solution:latest
```

---

## Input Format

Each subfolder in `input_docs/` is a separate **collection**:

* One or more `.pdf` files
* `persona.txt` – describes the type of user (e.g., "Product Manager at a startup")
* `job.txt` – describes the task they want to accomplish (e.g., "find the best method to monitor product adoption")

---

## Output Format

Each collection generates an output JSON like:

```json
{
  "collection": "Collection1",
  "persona": "...",
  "job": "...",
  "results": [
    {
      "pdf": "file1.pdf",
      "title": "Document Title",
      "matched_headings": [
        {
          "heading": "User Monitoring Strategies",
          "level": "H2",
          "score": 0.92
        },
        ...
      ]
    }
  ]
}
```

---

## How It Works

1. Loads outline data using logic from Round\_1A
2. Combines text from `persona.txt` and `job.txt` into a search query
3. Scores all headings using **BM25** keyword match
4. Top-N (default 10) headings are reranked using **MiniLM** similarity
5. Highest-ranked results are returned per PDF

---

## Technologies Used

* Python 3.9
* PyMuPDF (PDF parsing)
* BM25 (from `rank_bm25`)
* Sentence Transformers (`all-MiniLM-L6-v2`)
* Docker for containerization

---

## Notes

* You must run **Round\_1A** logic (outline extractor) as a Python module or Docker container before using Round\_1B
* `models/all-MiniLM-L6-v2/` must contain the **local download** of the model from [huggingface.co/sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
* Internet **not required** during runtime — model is used fully offline

---

## 🙌 Acknowledgements

This project was built as part of the **Adobe Generative AI Hackathon 2025**.
It combines traditional IR techniques with lightweight semantic AI for practical document understanding on edge devices.

