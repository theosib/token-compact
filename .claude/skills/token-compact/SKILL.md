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
Don't explain well-known technologies (PostgreSQL, TypeScript, REST APIs, etc.). Only explain what's unique to this project. Models treat common domain knowledge as redundant — it compresses naturally. **Caveat**: If the compressed document will be used across different model families, keep domain facts explicit — different models have different training data, so what one model "knows" another may not.

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

## Large Document Strategy (1000+ tokens)

For documents over ~1000 tokens, apply a top-down pass before word-level compression:

1. **Triage sections by information density**: Sections containing novel/project-specific content get full compression treatment. Sections restating well-known domain concepts can be reduced to a one-line reference or dropped.
2. **Preserve structural skeleton**: Keep headings and section boundaries — they cost few tokens but aid navigation. Flatten nested structure where possible (3 levels → 2).
3. **Compress proportionally**: Larger documents typically contain more redundancy. A 1K-token doc may compress to 50%; a 10K-token doc may reach 30-40% of original.
4. **Use cross-references instead of repetition**: If the same concept appears in multiple sections, state it once and reference it elsewhere (`(see above)` or `(→ §Config)`).

## Compression Loss Caveats

Compression can introduce errors. These categories are ordered by severity:

1. **Meaning inversions** (critical): Telegraphic rewriting can accidentally flip the meaning. Example: "The synchronizer adds 2 cycles of latency; bypass it for fast protocols" compressed to "sync bypass: 2-cycle latency" inverts who adds the latency. Always re-read compressed text to check that cause-effect and subject-object relationships are preserved.
2. **Numeric specifics dropped**: Concrete figures ("~4 billion transfers", "10+ cycles of jitter", "~20% faster") are high-value reference data. Treat them like novel content — preserve at full detail.
3. **Decision criteria lost**: Sections explaining WHEN to use something (not just HOW) are guidance, not redundant explanation. "When DMA Is Needed: continuous streaming, CPU not blocked, circular buffers" is actionable and should survive compression.
4. **Code comments stripped**: Comments explaining WHY (not WHAT) are novel content. `// DMA paced by producer's RX FIFO DREQ` is a critical implementation detail, not a redundant label.
5. **Derivation context lost**: `Baud = SM_clock / 80` is correct but `SM_clock / (8 * 10)` shows the reasoning (8 cycles/bit × 10 bits). Preserve derivations when the formula isn't self-explanatory.

## Verification

After compressing, verify the result before delivering:

1. **Inversion scan**: Re-read each compressed rule/statement and check that the subject, action, and object match the original. Meaning inversions are the most dangerous compression error — they silently teach the model the wrong behavior.
2. **Fact spot-check**: Pick 5-10 specific facts from the original (especially numeric values, conditional logic, and cause-effect statements) and confirm they survive in the compressed version.
3. **If the document is a skill or system prompt**: Spawn a subagent with only the compressed text and a test prompt. Verify it interprets the instructions correctly. This catches ambiguities and inversions that a manual read might miss.

## Process

1. Read the input document completely
2. For large documents (1000+ tokens), apply the Large Document Strategy first
3. Identify content types: behavioral rules, factual reference, procedural steps, project metadata
4. For each section, apply the compression rules above
5. Preserve the document's logical structure (sections, groupings) but compress the format
6. **Verify**: scan for meaning inversions, check numeric specifics, confirm decision criteria survived
7. After compression, count tokens using the Anthropic API if available, or estimate
8. Report: original token count, compressed token count, savings percentage

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
