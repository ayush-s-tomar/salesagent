"""
Eval runner for SalesAgent.

Usage:
    cd backend
    python -m evals.run_evals
"""
import os
import sys
import json
import time
import asyncio
import statistics
import numpy as np
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import run_agent
from evals.judge import judge_output

EVALS_DIR = Path(__file__).parent
GOLDEN_SET_PATH = EVALS_DIR / "golden_set.json"
RUNS_DIR = EVALS_DIR / "runs"
RUNS_DIR.mkdir(exist_ok=True)


def json_safe(obj):
    """Convert numpy types to native Python types so json.dumps doesn't choke."""
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


async def run_single_case(test_case: dict) -> dict:
    start = time.time()
    final_data = {}
    error = None

    try:
        async for event in run_agent(linkedin_url=test_case["linkedin_url"]):
            if event.get("step") == "complete":
                final_data = event.get("data", {})
    except Exception as e:
        error = str(e)

    latency = round(time.time() - start, 2)

    if error:
        return {
            "id": test_case["id"],
            "linkedin_url": test_case["linkedin_url"],
            "latency_sec": latency,
            "error": error,
            "judge": {
                "overall_pass": False,
                "personalization_score": 0,
                "correctness_score": 0,
                "structure_score": 0,
                "reasoning": f"AGENT_ERROR: {error}",
            },
        }

    judge_result = judge_output(final_data, test_case)

    return {
        "id": test_case["id"],
        "linkedin_url": test_case["linkedin_url"],
        "latency_sec": latency,
        "lead_score": final_data.get("score"),
        "email_preview": (final_data.get("email") or "")[:200],
        "error": None,
        "judge": judge_result,
    }


async def run_all():
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found. Check your .env file exists in backend/ and has GROQ_API_KEY set.")
        return
    if not os.getenv("TAVILY_API_KEY"):
        print("ERROR: TAVILY_API_KEY not found. Check your .env file exists in backend/ and has TAVILY_API_KEY set.")
        return

    golden_set = json.loads(GOLDEN_SET_PATH.read_text())
    print(f"Running {len(golden_set)} eval cases against live agent...\n")

    results = []
    for i, case in enumerate(golden_set, 1):
        print(f"[{i}/{len(golden_set)}] {case['id']} - {case['linkedin_url']}")
        result = await run_single_case(case)
        results.append(result)
        status = "PASS" if result["judge"].get("overall_pass") else "FAIL"
        print(f"    -> {status} | latency={result['latency_sec']}s | avg_score="
              f"{_avg_score(result['judge']):.1f}/5\n")

    summary = build_summary(results)
    save_run(results, summary)
    print_summary(summary)
    print_diff_vs_previous(summary)


def _avg_score(judge: dict) -> float:
    scores = [
        judge.get("personalization_score", 0),
        judge.get("correctness_score", 0),
        judge.get("structure_score", 0),
    ]
    return statistics.mean(scores) if scores else 0.0


def build_summary(results: list) -> dict:
    n = len(results)
    passed = sum(1 for r in results if r["judge"].get("overall_pass"))
    avg_scores = [_avg_score(r["judge"]) for r in results]
    latencies = [r["latency_sec"] for r in results]
    errors = [r for r in results if r["error"]]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_cases": n,
        "passed": passed,
        "pass_rate": round(passed / n, 3) if n else 0,
        "avg_quality_score": round(statistics.mean(avg_scores), 2) if avg_scores else 0,
        "avg_latency_sec": round(statistics.mean(latencies), 2) if latencies else 0,
        "error_count": len(errors),
        "failing_ids": [r["id"] for r in results if not r["judge"].get("overall_pass")],
    }


def save_run(results: list, summary: dict):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = RUNS_DIR / f"run_{ts}.json"
    out_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2, default=json_safe))
    print(f"Saved run log -> {out_path}\n")


def print_summary(summary: dict):
    print("=" * 50)
    print("EVAL SUMMARY")
    print("=" * 50)
    print(f"Pass rate:         {summary['passed']}/{summary['total_cases']} "
          f"({summary['pass_rate']*100:.0f}%)")
    print(f"Avg quality score: {summary['avg_quality_score']}/5")
    print(f"Avg latency:       {summary['avg_latency_sec']}s")
    print(f"Errors:            {summary['error_count']}")
    if summary["failing_ids"]:
        print(f"Failing cases:     {', '.join(summary['failing_ids'])}")
    print("=" * 50)


def print_diff_vs_previous(current: dict):
    prior_runs = sorted(RUNS_DIR.glob("run_*.json"))
    if len(prior_runs) < 2:
        print("\n(No previous run to compare against - this is your baseline.)")
        return

    prev_path = prior_runs[-2]
    prev = json.loads(prev_path.read_text())["summary"]

    delta_pass = current["pass_rate"] - prev["pass_rate"]
    delta_quality = current["avg_quality_score"] - prev["avg_quality_score"]
    delta_latency = current["avg_latency_sec"] - prev["avg_latency_sec"]

    print(f"\nDIFF vs previous run ({prev_path.name}):")
    print(f"  Pass rate:  {delta_pass:+.1%}")
    print(f"  Quality:    {delta_quality:+.2f}")
    print(f"  Latency:    {delta_latency:+.2f}s")

    if delta_pass < 0 or delta_quality < -0.3:
        print("  REGRESSION DETECTED vs previous run.")
    else:
        print("  OK - no regression.")


if __name__ == "__main__":
    asyncio.run(run_all())
