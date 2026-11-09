# OKF Bundle File Format

Each file in `okf_bundle/` is a Markdown file with a YAML frontmatter block.

## File Naming

The filename (minus `.md`, underscores replaced with spaces) is the primary match key. A question containing `"flydubai flight"` will match `flydubai_flight.md`.

## Frontmatter Fields

```yaml
---
verified: true          # bool — was this content manually verified?
stale_after: 2027-12-31 # date — file is ignored after this date (ISO 8601)
keywords:               # list — extra match terms beyond the filename
  - aircraft
  - altitude
  - co-pilot
---
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verified` | bool | no | Whether the content has been human-verified. Returned alongside the body so callers can trust-weight accordingly. |
| `stale_after` | date | no | After this date `query_okf` returns `(None, "STALE")` for this file. Use for time-sensitive facts. |
| `keywords` | list\[str\] | no | Additional match terms. Any keyword that appears (case-insensitive) in the question triggers a match. |

## Body

Everything after the closing `---` is the knowledge body. It is returned verbatim as the context string passed to the LLM.

## Example

```markdown
---
verified: true
stale_after: 2027-12-31
keywords: [aircraft, altitude, descent, co-pilot, incident]
---

FlyDubai flight FZ 1073 from Dubai to Tel Aviv was involved in a serious
incident where the captain stabbed the co-pilot in an apparent attempt to
crash the aircraft. The aircraft descended from 33,000 feet to 17,000 feet
in about a minute before other crew members intervened. The flight made an
emergency landing in Tabuk, Saudi Arabia.
```

## Matching Logic (`okf.py`)

```
for each .md file in okf_bundle/:
    parse YAML frontmatter
    if stale_after < today:  skip (return STALE)
    concept = filename without .md, underscores → spaces
    if concept in question.lower()
       OR any keyword in question.lower():
        return (body, verified)
return (None, None)   ← no match
```

## Adding a New Bundle File

1. Create `okf_bundle/<topic_slug>.md`
2. Add frontmatter with at minimum `verified` and `stale_after`
3. Add `keywords` covering terms a user might ask about this topic
4. Write the knowledge body — keep it factual and sourced

The body is passed directly to the LLM as context, so precision matters more than length.
