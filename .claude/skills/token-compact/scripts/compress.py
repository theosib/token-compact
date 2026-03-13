#!/usr/bin/env python3
"""
Document compression tool using LLM-guided semantic compression.

Compresses documents using empirically validated strategies:
- Telegraphic English (drop articles, pronouns, copulas)
- Minimal bullet points
- Key:value notation for structured data
- Brace expansion for lists
- Arrow notation for flows

Supports multiple models for cost optimization:
  --model haiku   (cheapest, ~$0.001/doc)
  --model sonnet  (default, ~$0.01/doc)
  --model opus    (highest quality, ~$0.10/doc)

Usage:
  python compress.py input.md                    # Compress with Sonnet
  python compress.py input.md -o output.md       # Write to file
  python compress.py input.md --model haiku      # Use Haiku (cheapest)
  python compress.py input.md --validate         # Compress + validate fidelity
  python compress.py input.md --compare-models   # Compare all 3 models
"""

import argparse
import json
import os
import sys
import time

# Add project src/ to path for token_counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from dotenv import load_dotenv

# Walk up from script directory to find .env (handles nested skill paths)
_dir = os.path.dirname(os.path.abspath(__file__))
while _dir != os.path.dirname(_dir):
    _env = os.path.join(_dir, '.env')
    if os.path.exists(_env):
        load_dotenv(_env)
        break
    _dir = os.path.dirname(_dir)

import anthropic

MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-6",
}

OVERHEAD = 7  # message framing tokens

client = anthropic.Anthropic()

COMPRESS_PROMPT = """Compress the following document to use fewer LLM tokens while preserving ALL semantic content.

Rules:
1. Drop articles (the/a/an), pronouns, copulas (is/are/should/must), filler phrases
2. Use telegraphic English — every word must carry meaning
3. Use → for implications/flows (1 token). Use + to combine related items
4. Use minimal bullets (- item) for lists. No numbering unless order matters
5. Use key:value for structured data. Use brace expansion for related items: src/{{a,b,c}}
6. Keep domain-specific terms intact — don't abbreviate (function, parameter, etc. are already 1 token)
7. Remove explanations for well-known concepts (the model already knows what PostgreSQL is)
8. Preserve novel/unique content at full detail — project-specific patterns, custom conventions, non-obvious constraints
9. Do NOT use: CJK, emoji, math Unicode, XML tags, abbreviations with punctuation (w/, b/c, e.g.)
10. Preserve logical structure (sections, groupings) but compress format

Output ONLY the compressed document. No preamble, no explanation.

Document:
---
{document}
---"""


def count_tokens(text, model="claude-sonnet-4-20250514"):
    r = client.messages.count_tokens(
        model=model,
        messages=[{"role": "user", "content": text}]
    )
    return r.input_tokens - OVERHEAD


def compress(text, model_name="sonnet"):
    """Compress a document using the specified model."""
    model_id = MODELS[model_name]
    response = client.messages.create(
        model=model_id,
        max_tokens=8192,
        temperature=0.0,
        messages=[{"role": "user", "content": COMPRESS_PROMPT.format(document=text)}],
    )
    return response.content[0].text.strip()


def validate_fidelity(original, compressed, model_name="sonnet"):
    """Ask a model to identify what information was lost in compression."""
    model_id = MODELS[model_name]
    response = client.messages.create(
        model=model_id,
        max_tokens=2048,
        temperature=0.0,
        messages=[{"role": "user", "content": f"""Compare these two documents. The second is a compressed version of the first.

ORIGINAL:
---
{original[:6000]}
---

COMPRESSED:
---
{compressed[:6000]}
---

List ONLY information that was LOST or CHANGED in compression.
If nothing was lost, say "No information loss detected."
For each lost item, rate severity: CRITICAL (meaning changed), MINOR (detail dropped), or OK (redundancy removed).
Be precise — do not flag items that are merely rephrased."""}],
    )
    return response.content[0].text.strip()


def compare_models(text):
    """Compress with all three models and compare results."""
    orig_tokens = count_tokens(text)
    print(f"Original: {len(text)} chars, {orig_tokens} tokens\n")

    results = {}
    for name in ["haiku", "sonnet", "opus"]:
        print(f"Compressing with {name}...", end=" ", flush=True)
        start = time.time()
        compressed = compress(text, name)
        elapsed = time.time() - start
        comp_tokens = count_tokens(compressed)
        savings = (1 - comp_tokens / orig_tokens) * 100
        results[name] = {
            "compressed": compressed,
            "tokens": comp_tokens,
            "savings": savings,
            "time": elapsed,
            "chars": len(compressed),
        }
        print(f"{comp_tokens} tokens ({savings:+.1f}%), {elapsed:.1f}s")

    # Show diffs
    print(f"\n{'Model':<10} {'Tokens':>8} {'Savings':>9} {'Chars':>7} {'Time':>6}")
    print(f"{'-'*10} {'-'*8} {'-'*9} {'-'*7} {'-'*6}")
    for name, r in results.items():
        print(f"{name:<10} {r['tokens']:>8} {r['savings']:>+8.1f}% {r['chars']:>7} {r['time']:>5.1f}s")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Compress documents for token efficiency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="Input file to compress")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("-m", "--model", choices=["haiku", "sonnet", "opus"],
                        default="sonnet", help="Model to use (default: sonnet)")
    parser.add_argument("--validate", action="store_true",
                        help="Validate compression fidelity after compressing")
    parser.add_argument("--compare-models", action="store_true",
                        help="Compare compression across all three models")
    parser.add_argument("--stats-only", action="store_true",
                        help="Only show token count stats, don't compress")

    args = parser.parse_args()

    with open(args.input) as f:
        text = f.read()

    if args.stats_only:
        tokens = count_tokens(text)
        print(f"File: {args.input}")
        print(f"Chars: {len(text)}")
        print(f"Tokens: {tokens}")
        print(f"Chars/token: {len(text)/tokens:.2f}")
        return

    if args.compare_models:
        results = compare_models(text)
        return

    # Compress
    orig_tokens = count_tokens(text)
    compressed = compress(text, args.model)
    comp_tokens = count_tokens(compressed)
    savings = (1 - comp_tokens / orig_tokens) * 100

    if args.output:
        with open(args.output, 'w') as f:
            f.write(compressed)
            f.write(f"\n\n<!-- Compression: {orig_tokens} tokens → {comp_tokens} tokens ({savings:+.1f}%) -->\n")
        print(f"Written to {args.output}")
        print(f"  Original:   {orig_tokens} tokens")
        print(f"  Compressed: {comp_tokens} tokens ({savings:+.1f}%)")
    else:
        print(compressed)
        print(f"\n<!-- Compression: {orig_tokens} tokens → {comp_tokens} tokens ({savings:+.1f}%) -->")

    if args.validate:
        print("\n--- Fidelity Validation ---")
        validation = validate_fidelity(text, compressed, args.model)
        print(validation)


if __name__ == "__main__":
    main()
