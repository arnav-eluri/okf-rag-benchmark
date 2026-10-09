import os, yaml, datetime

def query_okf(question, bundle_dir):  # function accepting the question and the directory of the OKF bundle
    question_lower = question.lower()
    for fname in os.listdir(bundle_dir):
        if not fname.endswith(".md"): # file specified 
            continue
        path = os.path.join(bundle_dir, fname)
        with open(path) as f:
            content = f.read()      # reads the file 

        # parse YAML frontmatter
        parts = content.split("---")
        meta = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
        body = parts[2].strip() if len(parts) >= 3 else content

        # check staleness
        stale = meta.get("stale_after")
        if stale and datetime.date.today() > stale:
            return None, "STALE"

        # simple keyword match (swap for a classifier later)
        concept_name = fname.replace(".md", "").replace("_", " ")
        if concept_name in question_lower:
            return body, meta.get("verified", False)

    return None, None  # not found