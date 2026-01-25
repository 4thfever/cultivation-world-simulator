---
name: spec-interview
description: Conduct an in-depth interview to gather requirements and write a detailed spec
---

## Overview

Conduct a thorough interview using `AskUserQuestion` to deeply understand a feature, system, or idea before writing a specification document.

## Core Principles

1. **Use your judgment** - Adapt question depth and focus based on the topic. A small UI change needs different questions than a new authentication system.

2. **Ask non-obvious questions** - Skip surface-level questions. Probe for:
   - Hidden assumptions the user hasn't articulated
   - Edge cases they haven't considered
   - Tradeoffs they're implicitly making
   - Constraints they forgot to mention
   - Failure modes and recovery paths

3. **Follow interesting threads** - When an answer reveals complexity or uncertainty, dig deeper before moving on.

4. **Challenge gently** - Ask "what if X fails?" or "why not Y instead?" to stress-test the design.

5. **Know when to stop** - End the interview when you have enough clarity to write a useful spec. Not every topic needs exhaustive coverage.

## Question Areas (use as needed, not as a checklist)

- **Problem & motivation**: Why now? What's the cost of not doing this?
- **Technical design**: Data model, state, APIs, performance, migrations
- **User experience**: Error states, loading, edge cases, accessibility
- **Integration**: What else does this touch? Security? Observability?
- **Tradeoffs**: What are you NOT building? What debt are you accepting?
- **Risks**: What assumptions could be wrong? What would make this a failure?

## Interview Flow

1. Start with 2-4 questions per round via `AskUserQuestion`.
2. Synthesize answers and follow up on gaps or ambiguities.
3. Periodically summarize to confirm understanding.
4. When sufficiently complete, confirm with the user and write the spec.

## Output

Write the spec to `docs/specs/<feature-name>.md` (or ask user for preferred path). Include whatever sections are relevant — don't force a rigid template.

## Invocation

```
/spec-interview [topic]
```
