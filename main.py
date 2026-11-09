from rich.table import Table
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor
import rag, okf, hybrid, evaluator, config, json, datetime

console = Console()

TEST_QUESTIONS = [
    # ── Times of India, Delhi — November 7, 2026 ──
    {
        "question": "What was the average Air Quality Index recorded at 4 pm on Friday in New Delhi?",
        "gold_answer": "The average AQI was 382 at 4 pm on Friday."
    },
    {
        "question": "Which two areas in New Delhi recorded the highest AQI of 455 under GRAP III?",
        "gold_answer": "The two areas that recorded an AQI of 455 were Punjabi Bagh and DTU."
    },
    {
        "question": "What restriction on vehicles was imposed under GRAP III in Delhi?",
        "gold_answer": "GRAP III includes restrictions on BS-III petrol and BS-IV diesel cars in Delhi and five high-vehicle-density NCR districts."
    },
    {
        "question": "How long did it take to control the fire at Puri Plaza in Gaffar Market?",
        "gold_answer": "The fire took nearly 12 hours to be brought under control, with operations continuing till 1 pm."
    },
    {
        "question": "How many fire tenders were deployed at the Gaffar Market blaze?",
        "gold_answer": "The deployment was increased to 25 fire tenders as the blaze intensified."
    },
    {
        "question": "Who suggested that overheating phone batteries triggered the Gaffar Market fire?",
        "gold_answer": "DCP (Central) Rohit Rajbir Singh said the fire could have been triggered by overheating or over-charging of phone batteries."
    },
    {
        "question": "Which German trust was identified by the ED as the source of the $1 million fund transferred to India?",
        "gold_answer": "Dr Matthias Karl Vogt Trust of Germany was identified as the actual source of the $1 million fund."
    },
    {
        "question": "What is the name of the Lithuanian entity the German trust transferred funds to first?",
        "gold_answer": "The German trust first transferred the funds to XBase Digital UAB in Lithuania."
    },
    {
        "question": "How many labourers were working at the collapsed four-storey building in Chawri Bazar?",
        "gold_answer": "Five labourers were working at the building: Kishori Sah, Sanjeet, Laxman Mukhiya, Vipin Ram, and Shantun."
    },
    {
        "question": "In which district of Bihar did labourer Kishori Sah's family live?",
        "gold_answer": "Kishori Sah's family lived in Khagaria district in Bihar."
    },
]

def run():
    rag.build_index(config.DOCUMENTS_DIR)
    results = []

    for item in TEST_QUESTIONS:
        q    = item["question"]
        gold = item["gold_answer"]

        # Retrieve contexts
        rag_ctx = rag.query_rag(q)
        okf_ctx, _ = okf.query_okf(q, config.OKF_BUNDLE_DIR)
        hyb_ctx, hyb_backend, _ = hybrid.query_hybrid(q, config.OKF_BUNDLE_DIR)

        # Parallel answer generation
        with ThreadPoolExecutor(max_workers=3) as ex:
            rag_f = ex.submit(evaluator.get_answer, q, rag_ctx)
            okf_f = ex.submit(evaluator.get_answer, q, okf_ctx) if okf_ctx else None
            hyb_f = ex.submit(evaluator.get_answer, q, hyb_ctx) if hyb_ctx else None

        rag_ans = rag_f.result()
        okf_ans = okf_f.result() if okf_f else "Not in bundle"
        hyb_ans = hyb_f.result() if hyb_f else "No context"

        # Parallel scoring
        with ThreadPoolExecutor(max_workers=3) as ex:
            rag_sf = ex.submit(evaluator.score_answer, q, rag_ans, gold)
            okf_sf = ex.submit(evaluator.score_answer, q, okf_ans, gold) if okf_ctx else None
            hyb_sf = ex.submit(evaluator.score_answer, q, hyb_ans, gold) if hyb_ctx else None

        rag_score = rag_sf.result()
        okf_score = okf_sf.result() if okf_sf else 0
        hyb_score = hyb_sf.result() if hyb_sf else 0

        rag_p,  rag_r,  rag_f1  = evaluator.token_metrics(rag_ans, gold)
        okf_p,  okf_r,  okf_f1  = evaluator.token_metrics(okf_ans, gold) if okf_ctx else (0, 0, 0)
        hyb_p,  hyb_r,  hyb_f1  = evaluator.token_metrics(hyb_ans, gold) if hyb_ctx else (0, 0, 0)

        results.append({
            "question":     q,
            "rag_ctx":      rag_ctx,
            "okf_ctx":      okf_ctx,
            "hyb_ctx":      hyb_ctx,
            "rag_score":    rag_score,  "rag_precision":  rag_p,  "rag_f1":  rag_f1,
            "okf_score":    okf_score,  "okf_precision":  okf_p,  "okf_f1":  okf_f1,
            "hybrid_score": hyb_score,  "hyb_precision":  hyb_p,  "hyb_f1":  hyb_f1,
            "hybrid_used":  hyb_backend,
        })

    # ── PRINT TABLE ──────────────────────────────────────────
    t = Table(title="RAG vs OKF vs Hybrid — Accuracy Tracker")
    t.add_column("Question",        style="cyan",   max_width=28)
    t.add_column("RAG\nLLM/P/F1",  style="blue",   justify="center")
    t.add_column("OKF\nLLM/P/F1",  style="green",  justify="center")
    t.add_column("Hybrid\nLLM/P/F1",style="red",   justify="center")
    t.add_column("Used",            style="yellow", justify="center")

    for r in results:
        t.add_row(
            r["question"],
            f"{r['rag_score']}/10  {r['rag_precision']:.2f}  {r['rag_f1']:.2f}",
            f"{r['okf_score']}/10  {r['okf_precision']:.2f}  {r['okf_f1']:.2f}",
            f"{r['hybrid_score']}/10  {r['hyb_precision']:.2f}  {r['hyb_f1']:.2f}",
            r["hybrid_used"],
        )

    console.print(t)

    # ── AVERAGES (exclude no-match rows so zeros don't skew) ─
    def avg(key, ctx_key):
        matched = [r[key] for r in results if r[ctx_key]]
        return sum(matched) / len(matched) if matched else 0.0

    console.print(
        f"\n[bold]Averages[/bold]\n"
        f"  RAG    — LLM {avg('rag_score','rag_ctx'):.1f}/10  |  Precision {avg('rag_precision','rag_ctx'):.3f}  |  F1 {avg('rag_f1','rag_ctx'):.3f}\n"
        f"  OKF    — LLM {avg('okf_score','okf_ctx'):.1f}/10  |  Precision {avg('okf_precision','okf_ctx'):.3f}  |  F1 {avg('okf_f1','okf_ctx'):.3f}\n"
        f"  Hybrid — LLM {avg('hybrid_score','hyb_ctx'):.1f}/10  |  Precision {avg('hyb_precision','hyb_ctx'):.3f}  |  F1 {avg('hyb_f1','hyb_ctx'):.3f}"
    )

    # ── SAVE TO JSON ─────────────────────────────────────────
    fname = f"results_{datetime.date.today()}.json"
    export = [{k: v for k, v in r.items() if k not in ("rag_ctx", "okf_ctx", "hyb_ctx")} for r in results]
    with open(fname, "w") as f:
        json.dump(export, f, indent=2)
    console.print(f"\nSaved to [bold]{fname}[/bold]")

if __name__ == "__main__":
    run()