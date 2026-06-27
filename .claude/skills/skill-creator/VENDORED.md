# Provenance

This `skill-creator` is vendored from Anthropic's public example skills
(`anthropics/skills`, the `skill-creator` example), licensed under Apache License 2.0.
See `LICENSE.txt` in this directory.

## Local modification

The **"Interview and Research"** step in `SKILL.md` has been extended to invoke the
companion **`research`** skill (`.claude/skills/research/`) once a skill's goal is captured
and before drafting — so prior art, the real interface, known gotchas, and competing
approaches are surfaced before the first draft. If the `research` skill is absent, the step
falls back to the original behavior.

No other behavior was changed. To pull upstream improvements, re-vendor the upstream
`skill-creator` and re-apply that one edit (search for the `research` skill reference in the
"Interview and Research" section).
