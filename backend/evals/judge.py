"""
LLM-as-judge scorer for SalesAgent eval harness.
"""
import os
import json
import re
from groq import Groq

JUDGE_MODEL = os.getenv("GROQ_JUDGE_MODEL", "llama-3.1-8b-instant")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

JUDGE_SYSTEM = """You are a strict QA evaluator for a B2B cold-email generation agent.
You will be given:
1. The agent's output (lead profile, lead score, generated email)
2. A set of pass/fail criteria for that test case

Score each criterion honestly. Do not be lenient. If information is missing or generic
(e.g. "your company" instead of a real company name), mark it as failed.

Return ONLY valid JSON in this exact shape, nothing else:
{
  "personalization_score": <1-5 int, how specific/non-generic is the email>,
  "correctness_score": <1-5 int, does profile/company info look plausible and non-hallucinated>,
  "structure_score": <1-5 int, does it follow subject/greeting/body/CTA format under word limit>,
  "criteria_results": {
    "min_score_met": <true/false>,
    "mentions_company": <true/false>,
    "has_specific_hook": <true/false>,
    "under_word_limit": <true/false>,
    "no_forbidden_placeholders": <true/false>
  },
  "reasoning": "<2-3 sentence explanation of the score, specifically noting any failures>"
}

Do NOT compute overall_pass yourself - just report the criteria_results honestly."""


def _word_count(text: str) -> int:
    return len(text.split())


def _check_expected_pass(judge_result: dict, test_case: dict) -> bool:
    """Compare actual criteria_results against what THIS test case expects,
    instead of assuming every criterion must be true. Some test cases
    (e.g. deliberately low-signal profiles) expect certain fields to be False."""
    criteria = test_case["criteria"]
    actual = judge_result.get("criteria_results", {})

    expected_map = {
        "mentions_company": criteria.get("must_mention_company"),
        "has_specific_hook": criteria.get("must_have_specific_hook"),
    }

    for key, expected in expected_map.items():
        if expected is not None and actual.get(key) != expected:
            return False

    # These are always required regardless of test case
    if not actual.get("under_word_limit", False):
        return False
    if not actual.get("no_forbidden_placeholders", False):
        return False
    if not actual.get("min_score_met", False):
        return False

    return True


def judge_output(agent_result: dict, test_case: dict) -> dict:
    """
    agent_result: dict with keys profile, score, email, deal_id, followup (from run_agent's final event)
    test_case: one entry from golden_set.json
    """
    criteria = test_case["criteria"]
    email = agent_result.get("email") or ""
    profile = agent_result.get("profile") or {}
    lead_score = agent_result.get("score")

    word_count = _word_count(email)
    under_limit = word_count <= criteria.get("max_word_count", 999)
    forbidden = criteria.get("must_not_contain", [])
    found_forbidden = [f for f in forbidden if f.lower() in email.lower()]
    no_forbidden = len(found_forbidden) == 0
    min_score_met = (lead_score or 0) >= criteria.get("min_score", 0)

    prompt = f"""TEST CASE ID: {test_case['id']}
NOTES: {test_case.get('notes', 'n/a')}

AGENT OUTPUT:
Profile: {json.dumps(profile)}
Lead Score: {lead_score}
Generated Email:
---
{email}
---

CRITERIA TO CHECK:
- must_mention_company: {criteria.get('must_mention_company')}
- must_have_specific_hook (references a real, specific company event/signal, not generic filler): {criteria.get('must_have_specific_hook')}

OBJECTIVE CHECKS ALREADY COMPUTED (use these, don't recompute):
- word_count: {word_count}, under_limit: {under_limit}
- forbidden_placeholders_found: {found_forbidden}
- min_score_met: {min_score_met}

Score personalization, correctness, and structure. Fill criteria_results using the objective
checks above for word limit / forbidden placeholders / min score, and your own judgment for
mentions_company and has_specific_hook."""

    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        max_tokens=600,
        temperature=0,
    )

    raw = resp.choices[0].message.content or "{}"
    raw = re.sub(r"^```json\s*|\s*```$", "", raw.strip())

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "personalization_score": 0,
            "correctness_score": 0,
            "structure_score": 0,
            "criteria_results": {},
            "reasoning": f"JUDGE_PARSE_ERROR: raw output was: {raw[:300]}",
        }

    result.setdefault("criteria_results", {})
    result["criteria_results"]["under_word_limit"] = under_limit
    result["criteria_results"]["no_forbidden_placeholders"] = no_forbidden
    result["criteria_results"]["min_score_met"] = min_score_met
    result["word_count"] = word_count
    result["forbidden_found"] = found_forbidden

    # Compute overall_pass ourselves based on THIS test case's expectations,
    # instead of trusting the judge model to assume all criteria must be true.
    result["overall_pass"] = _check_expected_pass(result, test_case)

    return result
