# Grounded mode — NotebookLM

Use this mode when answers must stay **anchored to a specific, fixed set of sources** — a
specification, a bundle of papers, a folder of internal documents, a set of links — with
citations and as little hallucination as possible. NotebookLM ingests the corpus and answers
*only* from it, returning page-level citations back to the source passages.

Web-sweep is for "what does the open web say"; grounded mode is for "what do *these specific
sources* say, exactly, with receipts".

## When to use grounded versus web-sweep

| | Grounded (NotebookLM) | Web sweep |
|---|---|---|
| Source set | Fixed, curated, known | Open web, discovered as you go |
| Strength | Citations tight to passages, low hallucination | Breadth, freshness, finding the unknown |
| Use for | Reasoning over a specification, paper set, or internal documents | Prior art, "is this true", surveying options |

A common chain: **web-sweep to find the best sources → load them into NotebookLM → grounded
question-and-answer** for citation-tight answers.

## Bridges (no official interface — use a community bridge)

NotebookLM has no first-party public application programming interface, so access is via a
community Model Context Protocol server or command-line interface that drives a real browser
session. As of this writing, the maintained options:

- **[jacob-bd/notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli)** — a
  command-line interface plus a Model Context Protocol server plus agent skills, roughly 39
  tools, explicitly built for Claude Code. Toggle it off when not in use to save context.
- **[roomi-fields/notebooklm-mcp](https://github.com/roomi-fields/notebooklm-mcp)** — a Model
  Context Protocol server plus a 33-endpoint web (REST) interface; bulk source import, Studio
  generation (audio/video/report), multi-account rotation with automatic re-authentication.
- **[PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp)** — a Model
  Context Protocol server driving a stealth Chrome; ingest sources, grounded chat, read citations.
- **[teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py)** — an unofficial Python
  interface plus an agentic skill, exposing some features the web user interface doesn't.

These are third-party tools that automate a logged-in Google session — review before installing,
and treat them as you would any tool with access to your Google account.

## Setup

1. Install one bridge (see its readme) and complete Google sign-in — typically a one-time browser
   login the bridge persists.
2. If it's a Model Context Protocol server, register it with Claude Code (`.mcp.json` /
   `claude mcp add`). Its tools then appear as `mcp__<server>__*` and are discoverable via ToolSearch.
3. Confirm reachability (list notebooks) before relying on it.

## Flow

1. **Create / select a notebook** for this research question.
2. **Ingest sources** — bulk-import the links, PDF files, documents, or YouTube videos that make
   up the corpus. This is the step that makes answers grounded; curate it deliberately.
3. **Query** — ask the question against the notebook. Answers come back with citations into the
   ingested sources.
4. **Extract** — pull the grounded answers and citations into the research brief. Every claim from
   this mode should carry its source citation; that's the whole point of using it.

## Fallback

If no bridge is configured or Google sign-in isn't available (for example, a headless or sandbox
session), **fall back to web-sweep** over the same source links and **state in the brief that
grounded mode was unavailable** — so the user knows the citations are web-fetched, not
NotebookLM-grounded. Don't silently substitute.
