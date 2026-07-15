import os
import json
from typing import Optional
from groq import Groq
from agent.tools import TOOL_SCHEMAS, execute_tool

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

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
        resp = client.chat.completions.create(
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
            max_tokens=2000,
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

    resp = _get_client().chat.completions.create(
        model=MODEL,
        messages=sys_msgs + messages,
        max_tokens=1500,
    )
    return resp.choices[0].message.content or ""


# Alias for backward compatibility
simple_chat = chat