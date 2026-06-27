# Grounded mode — NotebookLM

Use this mode when answers must stay **anchored to a specific, fixed set of sources** — a spec,
a bundle of papers, a folder of internal docs, a set of URLs — with citations and as little
hallucination as possible. NotebookLM ingests the corpus and answers *only* from it, returning
DOM-level citations back to the source passages.

Web-sweep is for "what does the open web say"; grounded mode is for "what do *these specific
sources* say, exactly, with receipts".

## When to use grounded versus web-sweep

| | Grounded (NotebookLM) | Web sweep |
|---|---|---|
| Source set | Fixed, curated, known | Open web, discovered as you go |
| Strength | Citations tight to passages, low hallucination | Breadth, freshness, finding the unknown |
| Use for | Reasoning over a spec/paper-set/internal docs | Prior art, "is this true", surveying options |

A common chain: **web-sweep to find the best sources → load them into NotebookLM → grounded question-and-answer**
for citation-tight answers.

## Bridges (no official API — use a community bridge)

NotebookLM has no first-party public API, so access is via a community MCP server or CLI that
drives a real browser session. As of this writing, the maintained options:

- **[jacob-bd/notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli)** — CLI + MCP
  server + agent skills, ~39 tools, explicitly built for Claude Code. Toggle it off when not in
  use to save context.
- **[roomi-fields/notebooklm-mcp](https://github.com/roomi-fields/notebooklm-mcp)** — MCP + a
  33-endpoint REST API; bulk source import, Studio generation (audio/video/report), multi-account
  rotation with auto re-auth.
- **[PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp)** — MCP server
  driving a stealth Chrome; ingest sources, grounded chat, read citations.
- **[teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py)** — unofficial Python API
  + agentic skill, exposes some features the web UI doesn't.

These are third-party tools that automate a logged-in Google session — review before installing,
and treat them as you would any tool with access to your Google account.

## Setup

1. Install one bridge (see its README) and complete Google auth — typically a one-time browser
   login the bridge persists.
2. If it's an MCP server, register it with Claude Code (`.mcp.json` / `claude mcp add`). Its tools
   then appear as `mcp__<server>__*` and are discoverable via ToolSearch.
3. Confirm reachability (list notebooks) before relying on it.

## Flow

1. **Create / select a notebook** for this research question.
2. **Ingest sources** — bulk-import the URLs, PDFs, docs, or YouTube links that make up the
   corpus. This is the step that makes answers grounded; curate it deliberately.
3. **Query** — ask the question against the notebook. Answers come back with citations into the
   ingested sources.
4. **Extract** — pull the grounded answers + citations into the research brief. Every claim from
   this mode should carry its source citation; that's the whole point of using it.

## Fallback

If no bridge is configured or Google sign-in isn't available (for example, a headless or sandbox session),
**fall back to web-sweep** over the same source URLs and **state in the brief that grounded mode
was unavailable** — so the user knows the citations are web-fetched, not NotebookLM-grounded.
Don't silently substitute.
