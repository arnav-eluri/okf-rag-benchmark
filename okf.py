import os, yaml, datetime

def query_okf(question, bundle_dir):  # function accepting the question and the directory of the OKF bundle
    question_lower = question.lower()
    for fname in os.listdir(bundle_dir):
        if not fname.endswith(".md"): # file specified 
            continue
        path = os.path.join(bundle_dir, fname)
        with open(path, encoding='utf-8') as f:
            content = f.read()

        # parse YAML frontmatter
        parts = content.split("---")
        meta = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
        body = parts[2].strip() if len(parts) >= 3 else content

        # check staleness
        stale = meta.get("stale_after")
        if stale and datetime.date.today() > stale:
            continue

        # match on filename concept or any declared keyword
        concept_name = fname.replace(".md", "").replace("_", " ")
        keywords = meta.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        if concept_name in question_lower or any(str(kw).lower() in question_lower for kw in keywords):
            return body, meta.get("verified", False)

    return None, None  # not found