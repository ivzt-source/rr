# Content Machine

A system for turning high-performing content into repeatable formats.

## How it's organized

```
content-machine/
├── post-types/    # Reusable formats — structure, script template, production specs
└── examples/      # Real assets dissected scene-by-scene (the source material for post-types)
```

**Post types** are the machine part: a brand-agnostic, fill-in-the-blanks
structure that anyone (founder, creator, editor) can execute against a brief
without re-deriving the strategy each time. Each one specifies:

- The psychological job of each beat and its timing
- A script template with placeholders
- Shooting and editing specs
- Distribution/cutdown notes

**Examples** are annotated breakdowns of real videos or posts — the evidence
for *why* the post type is shaped the way it is. When a new asset performs
well (ours or a competitor's), dissect it into `examples/`, then either
extract a new post type or refine an existing one.

## Workflow

1. Find a winning asset → break it down in `examples/` (hook, beats, timings,
   transcript, strategist + videographer notes).
2. Extract the repeatable skeleton → create or update a file in `post-types/`.
3. Brief creators using the post type, not the example — the example is for
   study, the post type is for execution.
4. When a produced asset outperforms, feed it back in as a new example and
   tighten the post type.

## Current post types

| Post type | Funnel stage | Best for |
|---|---|---|
| [UGC Comment-Reply Testimonial](post-types/ugc-comment-reply-testimonial.md) | MOFU/BOFU | Products with an "I don't need this" objection from experienced users |
