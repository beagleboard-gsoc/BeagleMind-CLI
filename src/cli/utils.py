"""
Utility functions for BeagleMind CLI.
"""

import re


def clean_llm_response_text(response: str) -> str:
    """Remove chain-of-thought style content and leave the final answer.

    Heuristics:
    - Strip <think>/<thinking> blocks if present
    - Drop leading paragraphs that look like internal planning ("I should...", "Let's...", etc.)
    """
    if not response:
        return response

    try:
        # Remove explicit thought tags
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Split into paragraphs and filter obvious meta-thought before first real paragraph
        paras = re.split(r'\n{2,}', cleaned.strip())
        meta_patterns = [
            r"\bI (should|need to|will|am going to|must)\b",
            r"\bLet's\b",
            r"\bPlan:?\b",
            r"\bReasoning:?\b",
            r"\bThinking:?\b",
            r"\bTime to\b",
            r"\bAlright\b",
            r"\bI'll\b",
            r"\bI need to make sure\b",
        ]
        meta_re = re.compile("|".join(meta_patterns), re.IGNORECASE)
        filtered = []
        non_meta_seen = False
        for p in paras:
            if not non_meta_seen and meta_re.search(p):
                # skip meta planning paragraphs at the start
                continue
            p2 = re.sub(r'^(?:Note:|Meta:).*$', '', p, flags=re.IGNORECASE | re.MULTILINE).strip()
            if p2:
                filtered.append(p2)
                non_meta_seen = True
        cleaned = "\n\n".join(filtered) if filtered else cleaned.strip()

        # Normalize whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        return cleaned
    except Exception:
        return response