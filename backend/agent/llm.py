import os
import json
import re
import time
from typing import Optional
from groq import Groq, RateLimitError
from agent.tools import TOOL_SCHEMAS, execute_tool

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# FIX: same issue as agent/tools.py — constructing Groq() at import time
# means importing this module crashes if GROQ_API_KEY isn't already in the
# environment (e.g. mcp_server/server.py, which never calls load_dotenv()).
# Lazy singleton defers this to first actual API call.
_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


MAX_RETRIES = 3


def _seconds_from_rate_limit_error(err: RateLimitError) -> float:
    """
    Groq's 429 body includes the exact wait time, e.g. "Please try again
    in 8.865s". Parsing it out lets us wait almost exactly as long as
    needed instead of guessing with a fixed/exponential backoff, which
    would either under-wait (retry fails again) or over-wait (slower than
    necessary) relative to what Groq actually tells us.
    Falls back to a flat 5s if the message format ever changes.
    """
    try:
        match = re.search(r"try again in ([\d.]+)s", str(err))
        if match:
            return float(match.group(1)) + 0.5  # small buffer
    except Exception:
        pass
    return 5.0


def _create_with_retry(client: Groq, **kwargs):
    """
    Wraps client.chat.completions.create with automatic retry on 429
    (rate limit) errors. Without this, a single burst of testing/demo
    traffic on the free tier surfaces a raw Groq error string straight to
    the UI ("Rate limit reached... code: rate_limit_exceeded") instead of
    the agent just completing a beat later — which looks like the app is
    broken to anyone trying the live demo, even though the fix is just
    "wait a few seconds and try the same call again."
    """
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as e:
            last_err = e
            if attempt == MAX_RETRIES - 1:
                raise
            wait = _seconds_from_rate_limit_error(e)
            time.sleep(wait)
    raise last_err


def run_with_tools(prompt: str, system: str = None) -> tuple:
    """
    Run the LLM with tool-calling in an agentic loop.
    Returns (final_text, tool_log) where tool_log is a list of
    {"tool": name, "args": {...}, "result": str} dicts.
    """
    sys_content = system or "You are a helpful AI assistant. Use the available tools to complete the task."
    sys_msgs = [{"role": "system", "content": sys_content}]
    loop_messages = [{"role": "user", "content": prompt}]
    tool_log = []
    max_iterations = 10
    client = _get_client()

    for _ in range(max_iterations):
        resp = _create_with_retry(
            client,
            model=MODEL,
            messages=sys_msgs + loop_messages,
            tools=[{
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": {
                        "type": "object",
                        "properties": t["input_schema"].get("properties", {}),
                        "required": t["input_schema"].get("required", []),
                    },
                }
            } for t in TOOL_SCHEMAS],
            tool_choice="auto",
            # FIX: was 2000. The tool-calling loop runs multiple times per
            # agent request (research -> profile -> news -> jobs -> tech),
            # and each call's max_tokens counts fully against the account's
            # tokens-per-minute cap even when the actual response is much
            # shorter. Trimming this reduces how fast a single agent run
            # burns through the free-tier 8000 TPM budget, so fewer runs
            # hit the 429 in the first place.
            max_tokens=1200,
        )

        msg = resp.choices[0].message

        # No tool calls — LLM is done, return final text
        if not msg.tool_calls:
            return (msg.content or "", tool_log)

        # Add assistant message with tool calls to history
        loop_messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in msg.tool_calls
            ]
        })

        # Execute each tool call
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments)
            except Exception:
                tool_args = {}

            try:
                tool_result = execute_tool(tool_name, tool_args)
                result_str = json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
            except Exception as e:
                result_str = json.dumps({"error": str(e)})

            # Log this tool call for graph.py to parse
            tool_log.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result_str,
            })

            # Add tool result to message history
            loop_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

    return ("Max iterations reached.", tool_log)


def chat(messages: list, system: str = None) -> str:
    """
    Simple chat without tools.
    Accepts a messages list and optional system prompt string.
    Returns the assistant's reply as a string.
    """
    sys_msgs = []
    if system:
        sys_msgs = [{"role": "system", "content": system}]

    resp = _create_with_retry(
        _get_client(),
        model=MODEL,
        messages=sys_msgs + messages,
        # FIX (regression): an earlier version of this trimmed max_tokens to
        # 800 to reduce TPM pressure, but openai/gpt-oss-120b is a reasoning
        # model — it spends tokens on internal chain-of-thought BEFORE
        # writing the visible answer, and those reasoning tokens count
        # against max_tokens too. At 800 the model was exhausting its whole
        # budget mid-reasoning on the detailed node_email prompt and
        # returning an empty message.content with no error (the API call
        # still "succeeds"), which is why the email panel came back blank
        # with no exception anywhere in the trace. Restored to 1500, which
        # is still far below run_with_tools' iteration cost and leaves
        # enough headroom for reasoning + a <150-word email.
        max_tokens=1500,
    )
    return resp.choices[0].message.content or ""


# Alias for backward compatibility
simple_chat = chat