---
name: voice
description: Speak out loud on this machine with a local Kokoro-82M voice (English, ~2x real time, no cloud). Use when the user asks to hear an answer, says "voice", "скажи голосом", "озвучь", "прочитай вслух", or when a scheduled/status report should be delivered as audio. Also use to offer voice ("рассказать голосом?") and to play pre-generated digests.
---

# Voice

A local TTS daemon. Nothing leaves the machine, no API key, ~1 s from request to first sound.

## The one rule

Speak **one or two sentences**, not the answer. Details stay in the chat text. Put the
**shortest sentence first** — playback starts when the first one is synthesized, so
"Yes. Here is the short version." starts in ~2 s while the rest renders behind it.

## Say something

```bash
vox say "Yes. Report is on track. Two blockers, both mine."
vox say "..." --voice mira        # juno (default) | mira
```

`vox say` returns in milliseconds: it posts to the warm daemon (`vox serve`) and the audio
plays sentence by sentence. If the daemon is down it falls back to a one-shot run
(~5 s slower, still works). Check with `vox status`.

## Offer voice instead of dumping a report

When the user asks about status ("что по отчёту?", "как там деплой?"), answer in text **and**
end with an offer. Only speak after a yes:

> Отчёт: 3 задачи закрыты, релиз в четверг. Рассказать голосом?

Then: `vox digest report.md` (first ~45 words, spoken) or `vox say "<2 sentences>"`.

## Scheduled bots

A reminder/cron job that has a report should not speak on its own. It sends the text, then
offers: "хочешь, расскажу голосом?" — the human says yes — `vox digest`. This keeps a muted
machine from talking to an empty room.

## Narrating long work

When a task takes minutes and the human is doing something else, narrate milestones. Use the
`narrate` tool when an MCP client is connected, `vox say` otherwise.

- Write the line yourself. Never read the plan, the todo list, or a status field aloud.
- Shape: what I just did, how it went, what comes next. Two sentences at most, under eight seconds.
- Milestones only: a batch finished, tests came back, something broke, I am blocked.
- Vary the opening. Three updates in a row cannot all start with "Done" or "Okay".
- Stay quiet when nothing changed, and never narrate routine reads or small edits.

## Limits

- **English voices only.** The bundled voice pack is English; other scripts are rejected.
- Voices: `af_heart` (default), `bf_emma` (British), `af_bella`, `af_nicole`, `af_sarah`, `am_michael`.
- 2.2× real time: a 4 s line costs ~1.8 s. Keep lines short; repeats are free from cache.
- No streaming yet: audio starts after the whole line is synthesized.
- License: Kokoro-82M is Apache 2.0 (hexgrad); the voices ship with their own terms.
- Ears (`vox listen`) need Underdog Bark 3.0 + torch; see `src/stt.py`. Not installed by default.
