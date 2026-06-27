#!/usr/bin/env python3
"""
council.py — run a Karpathy-style "LLM Council" over multiple models via one OpenRouter key.

Three stages:
  1. Independent answers   — every member answers the question on its own.
  2. Anonymized peer review — each member ranks the others' answers, identities stripped
                              (labeled "Response A", "Response B", and so on), so nobody
                              favors their own family.
  3. Chairman synthesis     — one model fuses answers + reviews into the final answer.

Why OpenRouter: one API key and one bill for all vendors. A ChatGPT/Gemini *subscription* is a
UI product and does NOT grant API access, so it cannot be used here. See references/providers.md.
For the no-key, no-cost alternative, run the council as Claude subagents instead (the default in
SKILL.md) — this script is only for real cross-vendor diversity.

Uses only the Python standard library (no pip install needed).

Usage:
  export OPENROUTER_API_KEY=sk-or-...
  python council.py \
      --question "Should we use approach X or Y given our constraints?" \
      --context-file ./session-context.md \
      --members openai/gpt-5 google/gemini-2.5-pro anthropic/claude-opus-4-8 \
      --chairman anthropic/claude-opus-4-8 \
      --out council-result.md

Notes:
  - Model IDs change over time. Check https://openrouter.ai/models for current ones rather than
    trusting the examples above.
  - To use a different OpenAI-compatible gateway or a direct vendor, override --base-url and the
    API key env var (--key-env).
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_model(base_url, api_key, model, messages, temperature=0.7, timeout=180):
    """One chat-completion call against an OpenAI-compatible endpoint. Returns the text."""
    payload = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature}
    ).encode("utf-8")
    req = urllib.request.Request(base_url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    # OpenRouter likes these but they're harmless elsewhere.
    req.add_header("HTTP-Referer", "https://localhost/research-skill")
    req.add_header("X-Title", "research-skill council")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"{model}: HTTP {e.code}: {body}") from e
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"{model}: {e}") from e


def label(i):
    """0 -> 'A', 1 -> 'B', ..."""
    return chr(ord("A") + i)


def stage1_answers(base_url, key, members, question, context):
    """Each member answers independently."""
    answers = {}
    sys_msg = (
        "You are one member of an expert council answering a question. Answer thoroughly and "
        "honestly on your own. Be concrete; state assumptions; flag what you're unsure about."
    )
    user = f"# Question\n{question}\n"
    if context:
        user += f"\n# Context / constraints\n{context}\n"
    for m in members:
        print(f"  [stage 1] querying {m} ...", file=sys.stderr)
        answers[m] = call_model(
            base_url, key, m,
            [{"role": "system", "content": sys_msg},
             {"role": "user", "content": user}],
        )
    return answers


def stage2_reviews(base_url, key, members, question, answers):
    """Each member reviews the *anonymized* set of all answers."""
    ordered = list(answers.items())  # [(model, text), ...]
    anon_block = "\n\n".join(
        f"## Response {label(i)}\n{text}" for i, (_, text) in enumerate(ordered)
    )
    sys_msg = (
        "You are a member of an expert council. Below are anonymized responses to the question "
        "(yours may be among them — you can't tell which). Critique each on accuracy, "
        "completeness, and reasoning, then rank them best-to-worst by label. Be impartial; you "
        "do not know which response is whose."
    )
    reviews = {}
    for m in members:
        print(f"  [stage 2] {m} reviewing (blind) ...", file=sys.stderr)
        user = f"# Question\n{question}\n\n# Anonymized responses\n{anon_block}\n"
        reviews[m] = call_model(
            base_url, key, m,
            [{"role": "system", "content": sys_msg},
             {"role": "user", "content": user}],
            temperature=0.4,
        )
    return reviews, [m for m, _ in ordered]


def stage3_chairman(base_url, key, chairman, question, context, answers, reviews):
    """Chairman fuses everything into the final answer."""
    answers_block = "\n\n".join(f"## {m}\n{t}" for m, t in answers.items())
    reviews_block = "\n\n".join(f"## Review by {m}\n{t}" for m, t in reviews.items())
    sys_msg = (
        "You are the Chairman of an expert council. You receive every member's answer and every "
        "member's peer review. Produce ONE final answer for the user. Where members disagreed, "
        "resolve it explicitly and say why — do not just average. Be decisive, cite reasoning, "
        "and call out remaining uncertainty."
    )
    user = f"# Question\n{question}\n"
    if context:
        user += f"\n# Context / constraints\n{context}\n"
    user += f"\n# Member answers\n{answers_block}\n\n# Peer reviews\n{reviews_block}\n"
    print(f"  [stage 3] chairman {chairman} synthesizing ...", file=sys.stderr)
    return call_model(
        base_url, key, chairman,
        [{"role": "system", "content": sys_msg},
         {"role": "user", "content": user}],
        temperature=0.3,
    )


def main():
    p = argparse.ArgumentParser(description="Run an LLM council via OpenRouter.")
    p.add_argument("--question", required=True)
    p.add_argument("--context-file", help="Path to a file with session goal/context.")
    p.add_argument("--members", nargs="+", required=True, help="Model IDs for council members.")
    p.add_argument("--chairman", help="Model ID for synthesis (default: first member).")
    p.add_argument("--out", default="council-result.md", help="Markdown output path.")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL,
                   help="OpenAI-compatible chat-completions URL.")
    p.add_argument("--key-env", default="OPENROUTER_API_KEY",
                   help="Env var holding the API key.")
    args = p.parse_args()

    key = os.environ.get(args.key_env)
    if not key:
        sys.exit(
            f"No API key in ${args.key_env}. Set it (see references/providers.md), or run the "
            f"council as Claude subagents instead — no key needed (see references/council.md)."
        )

    context = ""
    if args.context_file:
        with open(args.context_file, encoding="utf-8") as f:
            context = f.read().strip()

    chairman = args.chairman or args.members[0]

    print(f"Council: {len(args.members)} members, chairman={chairman}", file=sys.stderr)
    answers = stage1_answers(args.base_url, key, args.members, args.question, context)
    reviews, order = stage2_reviews(args.base_url, key, args.members, args.question, answers)
    final = stage3_chairman(
        args.base_url, key, chairman, args.question, context, answers, reviews
    )

    # Write the human-readable report.
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"# Council result\n\n**Question:** {args.question}\n\n")
        f.write(f"**Members:** {', '.join(args.members)}  \n**Chairman:** {chairman}\n\n")
        f.write("## Final answer (chairman synthesis)\n\n")
        f.write(final + "\n\n")
        f.write("## Anonymization key\n\n")
        for i, m in enumerate(order):
            f.write(f"- Response {label(i)} = {m}\n")
        f.write("\n## Stage 1 — independent answers\n\n")
        for m, t in answers.items():
            f.write(f"### {m}\n\n{t}\n\n")
        f.write("## Stage 2 — anonymized peer reviews\n\n")
        for m, t in reviews.items():
            f.write(f"### Review by {m}\n\n{t}\n\n")

    # Also dump raw JSON next to it for programmatic use.
    raw_path = os.path.splitext(args.out)[0] + ".json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(
            {"question": args.question, "members": args.members, "chairman": chairman,
             "answers": answers, "reviews": reviews, "final": final},
            f, indent=2,
        )

    print(f"\nWrote {args.out} and {raw_path}", file=sys.stderr)
    print(final)


if __name__ == "__main__":
    main()
