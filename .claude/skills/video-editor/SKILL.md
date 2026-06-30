---
name: video-editor
description: Edit video with OpenCut — the free, open-source, MIT-licensed CapCut alternative — driven from Claude Code. Use when the user wants to trim, cut, split, reorder, caption, overlay, or render/export video clips. Connects to OpenCut's local MCP server (headless) when available, and falls back to ffmpeg for batch/headless edits so it works today. Everything stays local: no upload, no watermark, no account.
---

# Video Editor (OpenCut)

A "video editor agent": drive real, non-destructive video edits from Claude Code.
Backed by **[OpenCut](https://github.com/OpenCut-app/OpenCut)** — the open-source
CapCut alternative (MIT licensed, ~55k★). Files are processed **locally** — nothing
is uploaded, watermarked, or shared, and there's no account or paywall.

> Why OpenCut and not CapCut: CapCut paywalls the basics and is owned by ByteDance.
> OpenCut is MIT-licensed, runs locally, and — critically for us — its rewrite ships
> a **headless mode + MCP server**, so Claude Code can edit on autopilot.

## When to use

Invoke with `/video-editor` (or just ask) when the user wants to:

- Trim / cut / split a clip, or top-and-tail dead air
- Reorder or concatenate multiple clips into one timeline
- Add captions / text overlays / a watermark or logo
- Change speed, scale/crop (e.g. 16:9 → 9:16 reel), or extract audio
- Render / export a finished video

## Two backends — pick what's available

This skill has two engines. **Prefer OpenCut MCP** when it's running; otherwise use
the **ffmpeg fallback**, which works today with zero OpenCut setup.

### A. OpenCut MCP server (timeline editing, on autopilot)

OpenCut's rewrite exposes a headless renderer + an MCP server so an agent can build a
real timeline (import clips, trim, reorder, caption, render) and iterate.

One-time setup (run on the machine that holds the media):

```bash
# 1. Get OpenCut (the rewrite carries the MCP server / headless mode)
git clone https://github.com/OpenCut-app/OpenCut.git && cd OpenCut

# 2. Toolchain + deps, then start the headless API
proto use            # installs bun + moon
bun install
moon run api:dev     # headless API on http://localhost:8787
moon run web:dev     # optional UI to watch/verify on http://localhost:5173
```

Register the MCP server with Claude Code, then restart the session:

```bash
# Confirm the exact server entrypoint against OpenCut's current docs — the rewrite
# is live at new.opencut.app and the command name may move. This is the shape:
claude mcp add opencut -- bun run --cwd /path/to/OpenCut mcp
# (or the HTTP transport, if that's what the build exposes:)
# claude mcp add --transport http opencut http://localhost:8787/mcp
```

Then drive it through the MCP tools (names per OpenCut's MCP schema — discover them
at runtime): create/open a project → import media → trim/split/reorder → add
captions/overlays → **render/export**. Show the user the output path when done.

> Status: OpenCut's MCP server + headless rendering land with the ground-up rewrite
> (`new.opencut.app`); `opencut.app` still serves the classic web build. If
> `claude mcp add` / the tool schema don't match yet, fall back to ffmpeg below and
> tell the user the MCP path needs OpenCut's rewrite build.

### B. ffmpeg fallback (works today, no OpenCut needed)

For headless batch edits, ffmpeg covers the common asks. Verify `ffmpeg -version`
first; if it's missing, `pip install imageio-ffmpeg` provides a static binary.

```bash
# Trim 00:05 → 00:20 (stream-copy, no re-encode = fast & lossless)
ffmpeg -ss 00:00:05 -to 00:00:20 -i in.mp4 -c copy out.mp4

# Concatenate clips (same codec/resolution) via a list file
printf "file '%s'\n" a.mp4 b.mp4 c.mp4 > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4

# Burn in a caption
ffmpeg -i in.mp4 -vf "drawtext=text='Hello':fontcolor=white:fontsize=48:x=(w-tw)/2:y=h-120" out.mp4

# 16:9 → 9:16 vertical reel (crop to centre)
ffmpeg -i in.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" -c:a copy out.mp4

# Speed up 2x (video + audio) / extract audio
ffmpeg -i in.mp4 -filter:v "setpts=0.5*PTS" -filter:a "atempo=2.0" out.mp4
ffmpeg -i in.mp4 -vn -acodec libmp3lame audio.mp3
```

## Procedure

1. **Locate the inputs.** Get the source file path(s) and the desired output
   (format, aspect ratio, what edit). Ask only if genuinely ambiguous.
2. **Pick the backend.** Is the OpenCut MCP server registered/running? Use it for
   anything timeline-shaped (multi-clip, captions, iterative edits). Otherwise use
   the ffmpeg fallback.
3. **Make the edit non-destructively.** Never overwrite the source — always write a
   new output file.
4. **Verify.** Probe the result (`ffprobe`/`ffmpeg -i out.mp4`) — confirm duration,
   resolution, and that audio/video streams are present. For visual checks, extract
   a frame (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 frame.png`) and inspect it.
5. **Report** the output path and what changed. Offer to send the file back.

## Notes

- **Local-only by design.** Don't upload media to third-party services for editing;
  the whole point of OpenCut is that nothing leaves the machine.
- **Non-destructive.** Always produce a new file; keep the originals untouched.
- Stream-copy (`-c copy`) whenever you're only cutting on keyframes — it's instant
  and lossless. Re-encode only when filters (captions, scaling, speed) require it.
