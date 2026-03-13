---
name: token-compact
description: Compress documents for LLM token efficiency while preserving semantic content. Use when asked to compress, compact, shrink, or optimize a document, CLAUDE.md, system prompt, skill file, or any text for fewer tokens. Also use when the user mentions token count, token budget, context window limits, or wants to make prompts shorter for cost savings.
argument-hint: "[file-or-selection]"
---

You are a document compression specialist. Your job is to compress the provided document to use fewer LLM tokens while preserving all semantic content.

These rules are empirically validated — each one comes from controlled experiments measuring real token counts via Anthropic's count_tokens API and behavioral fidelity across Claude model tiers. See [STYLE_GUIDE.md](../../../STYLE_GUIDE.md) for the full research backing.

## Compression Rules

Apply these transformations in order:

### 1. Drop predictable words
Remove articles (the, a, an), pronouns (it, they, we, you), copulas (is, are, was, were, should, must, will), and filler phrases (in order to, it is important to, please note that, make sure to). These words carry no semantic weight — the model reconstructs meaning without them.

### 2. Use telegraphic English
Write rule-like statements without grammatical glue. Every remaining word should carry meaning. Telegraphic saves 56% of tokens with zero fidelity loss.

### 3. Use arrows for flows and implications
Use `→` or `->` for cause-effect, process flows, or implications. Both cost exactly 1 token.

### 4. Use minimal bullet points for lists
Use `- item` format. Bullets add +87% overhead vs bare words, but numbered lists add +140% — so bullets are the best structured format.

### 5. Use key:value notation for structured data
`stack: Node20/Express/PG15` instead of "The project uses Node.js version 20 with Express and PostgreSQL 15."

### 6. Use brace expansion for related items
`src/{controllers,services,repos,middleware}` instead of listing each path separately.

### 7. Combine related items on one line
`helpful+harmless` instead of two separate bullets. Separators (comma, pipe, semicolon) all cost the same +40% overhead.

### 8. Keep domain-specific terms intact
Don't abbreviate technical terms — `function`, `parameter`, `context`, `authentication` are already single tokens. Abbreviating them saves nothing and hurts readability.

### 9. Remove explanations the model already knows
Don't explain well-known technologies (PostgreSQL, TypeScript, REST APIs, etc.). Only explain what's unique to this project. Models treat common domain knowledge as redundant — it compresses naturally.

### 10. Preserve novel/unique content at full detail
Custom conventions, project-specific patterns, unique architecture decisions, and non-obvious constraints must be kept with enough detail for unambiguous interpretation. These can't be reconstructed from the model's training data.

## What NOT to do
- Don't use CJK characters (1.5 tokens each on Claude — worse than English)
- Don't use abbreviations with punctuation (w/, b/c, e.g. — the punctuation adds tokens)
- Don't use XML/HTML tags (+320% overhead)
- Don't use emoji as semantic markers (2-3 tokens each)
- Don't use Unicode math symbols (2 tokens each)
- Don't use numbered lists when bullets suffice (+140% vs +87% overhead)
- Don't use JSON wrapping for simple content (+93% overhead)

## Process

1. Read the input document completely
2. Identify content types: behavioral rules, factual reference, procedural steps, project metadata
3. For each section, apply the compression rules above
4. Preserve the document's logical structure (sections, groupings) but compress the format
5. After compression, count tokens using the Anthropic API if available, or estimate
6. Report: original token count, compressed token count, savings percentage

## Output format

Output ONLY the compressed document. After the document, add a brief stats line:

```
<!-- Compression: ~X tokens → ~Y tokens (Z% savings) -->
```

## Example

Input:
```
## Key Conventions
- Use TypeScript for all new code
- Follow the existing error handling pattern using AppError class
- All database queries go through the repository layer
- Use dependency injection for testability
- Write unit tests for all service layer functions
- Use snake_case for database columns, camelCase for TypeScript
- API responses follow the standard envelope format: { data, error, meta }
```

Output:
```
## Conventions
- TS all new code
- errors: AppError pattern
- DB queries via repo layer only
- DI for testability, unit test services
- naming: snake_case(DB) camelCase(TS)
- response envelope: {data,error,meta}
```

## CLI tool

For batch compression or model comparison, see [scripts/compress.py](scripts/compress.py):
```bash
python scripts/compress.py input.md -o output.md --model opus --validate
```
