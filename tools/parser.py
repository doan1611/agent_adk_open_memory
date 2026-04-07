"""
Parse Gauss / text responses for ADK-style tool_calls JSON.
"""

import json
import re


def extract_tool_calls(text):
    """
    Extract all tool_calls JSON from text using bracket counting.
    """
    if not text:
        return None
    all_calls = []
    search_start = 0

    while True:
        key_index = text.find('"tool_calls"', search_start)
        if key_index == -1:
            break

        list_start = text.find("[", key_index)
        if list_start == -1:
            break

        balance = 0
        list_end = -1

        for i in range(list_start, len(text)):
            if text[i] == "[":
                balance += 1
            elif text[i] == "]":
                balance -= 1

            if balance == 0:
                list_end = i + 1
                break

        if list_end != -1:
            json_str = text[list_start:list_end]
            try:
                parsed_list = json.loads(json_str)
                if isinstance(parsed_list, list):
                    all_calls.extend(parsed_list)
            except json.JSONDecodeError:
                pass

            search_start = list_end
        else:
            search_start = list_start + 1

    return all_calls if all_calls else None


def strip_json_code_fence(text: str) -> str:
    """Remove optional ```json ... ``` wrapping from model output."""
    if not text:
        return text
    s = text.strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", s, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def first_function_call_from_text(text: str) -> dict | None:
    """
    Return {"name": str, "parameters": dict} for the first tool call in text, or None.
    """
    cleaned = strip_json_code_fence(text)
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and "tool_calls" in obj:
            tcs = obj["tool_calls"]
            if isinstance(tcs, list) and tcs:
                first = tcs[0]
                if isinstance(first, dict) and "name" in first and "parameters" in first:
                    return {"name": first["name"], "parameters": first["parameters"]}
    except json.JSONDecodeError:
        pass

    extracted = extract_tool_calls(cleaned)
    if extracted:
        first = extracted[0]
        if isinstance(first, dict) and "name" in first and "parameters" in first:
            return {"name": first["name"], "parameters": first["parameters"]}
    return None
