# Token-Compact: Token-Efficient Prompts for LLMs

**Save 65% of your system prompt tokens with zero fidelity loss.**

A Claude Code skill and style guide for compressing documents, system prompts, CLAUDE.md files, and skill files to use fewer LLM tokens while preserving all semantic content. Based on controlled experiments with real token counts from Anthropic's API and behavioral fidelity tests across Claude model tiers.

## Quick Start

Clone this repo and the skill is automatically available in Claude Code:

```bash
# In Claude Code, use the skill:
/token-compact my_document.md
```

The skill lives at `.claude/skills/token-compact/SKILL.md` following the [Agent Skills](https://agentskills.io) standard.

For batch compression or model comparison, use the CLI tool:
```bash
pip install anthropic python-dotenv
export ANTHROPIC_API_KEY=sk-ant-...

python .claude/skills/token-compact/scripts/compress.py input.md --model opus --validate
python .claude/skills/token-compact/scripts/compress.py input.md --compare-models
```

## What It Does

```
# BEFORE (108 tokens):
The assistant must always respond in a helpful and harmless manner.
When the user asks about dangerous topics, the assistant should decline
politely and explain why it cannot help with that request.
The assistant should cite sources when making factual claims.

# AFTER (35 tokens, same fidelity):
- helpful, harmless
- decline dangerous + explain
- cite factual claims
- no fabrication
- show uncertainty
- markdown ok
- concise default
```

## Key Findings

| Finding | Detail |
|---------|--------|
| **65% token savings, zero fidelity loss** | Minimal bullet-point format saves 65% of tokens vs verbose prose with identical behavioral compliance |
| **Abbreviations don't help** | Common words like `function`, `parameter`, `context` are already single tokens. Abbreviating them saves nothing. |
| **CJK is a net loss** | Chinese characters cost ~1.5 tokens each on Claude's tokenizer — worse than English despite higher visual density |
| **Math Unicode is catastrophic** | Unicode symbols like `∀ ∃ ∈` cost 2 tokens each — never use them in prompts |
| **XML: it depends on the model** | Sonnet goes from 62% to 100% compliance with XML; Opus only gains 4%. Use XML for Sonnet, telegraphic for Opus. |
| **All Claude models share one tokenizer** | Haiku, Sonnet, and Opus produce identical token counts |

## Style Guide

See [STYLE_GUIDE.md](STYLE_GUIDE.md) for the complete, actionable guide to writing token-efficient prompts.

**The short version:**
1. Drop articles, pronouns, copulas, filler phrases
2. Use telegraphic English — every word carries meaning
3. Use `→` or `->` for flows (both 1 token)
4. Use `- item` bullets, not numbered lists (+87% vs +140% overhead)
5. Use `key: value` notation for structured data
6. Use brace expansion: `src/{controllers,services,repos}`
7. Don't abbreviate technical terms — they're already single tokens
8. Don't use CJK, emoji, or Unicode math symbols

## Project Structure

```
token-compact/
├── README.md                          # This file
├── STYLE_GUIDE.md                     # Actionable guide for writing efficient prompts
└── .claude/skills/token-compact/
    ├── SKILL.md                       # Compression skill (auto-available when cloned)
    └── scripts/compress.py            # CLI compression tool
```

## License

MIT
