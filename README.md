# OKF - Ontology Knowledge Framework Evaluation

A framework for comparing three question-answering approaches: RAG (Retrieval Augmented Generation), OKF (Ontology Knowledge Framework), and a Hybrid routing strategy.

**Author:** Arnav Eluri 
**License:** MIT

## Project Structure

### Core Modules

- **main.py** - Entry point that runs the evaluation suite against test questions and generates a comparison report with accuracy scores
- **evaluator.py** - LLM-powered evaluation that generates answers from context and scores responses against gold standard answers using Groq API
- **rag.py** - RAG implementation using sentence-transformers and Chroma vector database for semantic search over documents
- **okf.py** - OKF approach that performs keyword matching on markdown files with YAML frontmatter, respects staleness metadata
- **hybrid.py** - Router that selects between OKF and RAG based on question keywords, falls back to RAG when OKF has no match
- **config.py** - Centralized configuration loading environment variables for API keys and directory paths

### Configuration Files

- **.env** - Environment variables for API keys and paths (not committed to git)
- **.gitignore** - Git ignore patterns for Python, virtual environments, and sensitive files
- **requirements.txt** - Python package dependencies

### Data Directories (User-Created)

- **documents/** - Text files indexed by RAG for semantic search
- **okf_bundle/** - Markdown files with YAML frontmatter for OKF queries

## What The Code Does

### Workflow

1. **Index Building** - RAG builds a vector index from documents in the documents directory
2. **Test Execution** - For each test question:
   - RAG: Semantic search retrieves relevant documents, LLM generates answer
   - OKF: Keyword matching in markdown files, returns structured content if found
   - Hybrid: Routes to OKF or RAG based on question keywords, falls back intelligently
3. **Scoring** - LLM evaluates each answer against a gold standard and assigns a 0-10 accuracy score
4. **Reporting** - Results table displays scores for all three approaches, calculates averages, saves to JSON

### Key Features

- OKF staleness checking: Returns no context if YAML stale_after date has passed
- OKF verification metadata: Tracks whether OKF content is human-verified
- Hybrid routing: Keyword-based router reduces unnecessary LLM calls for structured queries
- Extensible test suite: Add questions to TEST_QUESTIONS array in main.py

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Groq API key (get from https://console.groq.com)

### Step 1: Clone and Install

```bash
cd okf
pip install -r requirements.txt
```

### Step 2: Configure API Key

1. Get a Groq API key from https://console.groq.com
2. Edit .env file and add:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Step 3: Prepare Data

Create the required directories and add your content:

```bash
mkdir documents okf_bundle
```

- Add .txt files to `documents/` for RAG to index
- Add .md files to `okf_bundle/` for OKF queries (with optional YAML frontmatter)

### Step 4: Define Test Questions

Edit TEST_QUESTIONS in main.py and add your test cases:

```python
TEST_QUESTIONS = [
    {
        "question": "Your question here?",
        "gold_answer": "Expected answer here."
    },
]
```

### Step 5: Run Evaluation

```bash
python main.py
```

The script will generate a comparison table and save results to `results_YYYY-MM-DD.json`.

## OKF Markdown Format

Create markdown files in okf_bundle/ with this structure:

```markdown
---
verified: true
stale_after: 2026-12-31
---

Your knowledge content here.
```

The OKF router matches against the filename (with underscores converted to spaces) in lowercase question text.

## Hybrid Routing Keywords

The hybrid router checks for these keywords to decide between OKF and RAG:

- policy
- definition
- what is
- procedure
- rule

Questions containing these keywords route to OKF first, falling back to RAG if no match.

## Model Configuration

The evaluator uses Groq's `llama-3.3-70b-versatile` model for:
- Generating answers from context
- Scoring answer accuracy

Available Free Groq Models:
- llama-3.3-70b-versatile (production)
- llama-3.1-8b-instant (production)
- openai/gpt-oss-120b (production)
- openai/gpt-oss-20b (production)

## Extensibility

To add a fourth approach:

1. Create a new query function in a new module
2. Call it in main.py's run() function
3. Add its score column to the results table
4. Include it in average calculations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
