from rich.table import Table
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor
import rag, okf, hybrid, evaluator, config, json, datetime

console = Console()

TEST_QUESTIONS = [
    {
        "question": "Who was stabbed on the flydubai flight from Dubai to Tel Aviv?",
        "gold_answer": "The co-pilot was stabbed by the captain in an apparent attempt to crash the aircraft."
    },
    {
        "question": "What altitude did the aircraft descend to during the incident?",
        "gold_answer": "The aircraft descended from 33,000 feet to 17,000 feet in about a minute."
    },
    {
        "question": "Where did the flydubai flight FZ 1073 make an emergency landing?",
        "gold_answer": "The flight made an emergency landing in Tabuk, Saudi Arabia."
    },
    {
        "question": "What was the name of the Indian pilot on the flydubai flight?",
        "gold_answer": "Captain Smit Machchhar was the Indian pilot who sustained serious injuries."
    },
    {
        "question": "How much drugs were seized in the Arabian Sea operation?",
        "gold_answer": "526 kg of drugs were seized in the Arabian Sea, with five people held."
    },
    {
        "question": "What is the India-EFTA partnership about?",
        "gold_answer": "The India-EFTA deal is a partnership that can deliver across multiple sectors."
    },
    {
        "question": "Which militant organization's commander was killed in Budgam, J&K?",
        "gold_answer": "A Lashkar-e-Taiba (LeT) commander active in the Pir Panjal Valley and south Kashmir was killed."
    },
    {
        "question": "What did Iran indicate it received on Wednesday?",
        "gold_answer": "Iran said it received an official U.S. response to Tehran's proposal to end the war."
    },
    {
        "question": "How many people were on the flydubai flight FZ 1073?",
        "gold_answer": "The flight was carrying 174 people, including dozens of Israelis."
    },
    {
        "question": "What new norms has the Centre tightened?",
        "gold_answer": "The Centre has tightened norms for passenger vehicles through the CAFE-III notification."
    },
]

def run():
    rag.build_index(config.DOCUMENTS_DIR)
    results = []

    for item in TEST_QUESTIONS:
        q    = item["question"]
        gold = item["gold_answer"]

        # Retrieve contexts (local, fast)
        rag_ctx            = rag.query_rag(q)
        okf_ctx, _         = okf.query_okf(q, config.OKF_BUNDLE_DIR)
        hyb_ctx, backend, _ = hybrid.query_hybrid(q, config.OKF_BUNDLE_DIR)
        hyb_reuses_okf     = (backend == "OKF" and okf_ctx is not None)

        # Parallel answer generation; skip hybrid if it reuses OKF context
        with ThreadPoolExecutor(max_workers=3) as ex:
            rag_f = ex.submit(evaluator.get_answer, q, rag_ctx)
            okf_f = ex.submit(evaluator.get_answer, q, okf_ctx) if okf_ctx else None
            hyb_f = None if hyb_reuses_okf else ex.submit(evaluator.get_answer, q, hyb_ctx)

        rag_ans = rag_f.result()
        okf_ans = okf_f.result() if okf_f else "Not in bundle"
        hyb_ans = okf_ans if hyb_reuses_okf else hyb_f.result()

        # Parallel scoring; skip hybrid if answer is reused
        with ThreadPoolExecutor(max_workers=3) as ex:
            rag_sf = ex.submit(evaluator.score_answer, q, rag_ans, gold)
            okf_sf = ex.submit(evaluator.score_answer, q, okf_ans, gold) if okf_ctx else None
            hyb_sf = None if hyb_reuses_okf else ex.submit(evaluator.score_answer, q, hyb_ans, gold)

        rag_score = rag_sf.result()
        okf_score = okf_sf.result() if okf_sf else 0
        hyb_score = okf_score if hyb_reuses_okf else (hyb_sf.result() if hyb_sf else 0)

        results.append({
            "question":    q,
            "rag_score":   rag_score,
            "okf_score":   okf_score,
            "hyb_score":   hyb_score,
            "hyb_backend": backend,
        })

    # ── PRINT TABLE ──────────────────────────────────────────
    t = Table(title="RAG vs OKF vs Hybrid — Accuracy Tracker")
    t.add_column("Question",       style="cyan",  max_width=30)
    t.add_column("RAG Score",      style="blue",  justify="center")
    t.add_column("OKF Score",      style="green", justify="center")
    t.add_column("Hybrid Score",   style="red",   justify="center")
    t.add_column("Hybrid Used",    style="yellow",justify="center")

    for r in results:
        t.add_row(
            r["question"],
            f"{r['rag_score']}/10",
            f"{r['okf_score']}/10",
            f"{r['hyb_score']}/10",
            r["hyb_backend"],
        )

    console.print(t)

    # ── AVERAGES ─────────────────────────────────────────────
    avg = lambda key: sum(r[key] for r in results) / len(results)
    console.print(f"\n[bold]Averages:[/bold]  RAG {avg('rag_score'):.1f}  |  "
                  f"OKF {avg('okf_score'):.1f}  |  Hybrid {avg('hyb_score'):.1f}")

    # ── SAVE TO JSON ─────────────────────────────────────────
    fname = f"results_{datetime.date.today()}.json"
    with open(fname, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"\nSaved to [bold]{fname}[/bold]")

if __name__ == "__main__":
    run()