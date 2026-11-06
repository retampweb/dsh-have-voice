# Three ways to give an agent a voice

The daemon in this repo is the "how". This note is the "when" — three patterns that compose around
the same `vox say`, and what each one costs.

| Pattern | Who decides what to say | First sound | Fits |
|---|---|---|---|
| **A. Tool** | the working agent | ~1 s | any chat, zero new moving parts |
| **B. Narrator subagent** | a separate agent watching the session | ~1 s, never blocks the main one | long autonomous runs, "what is it doing?" |
| **C. Scheduled digest** | a cron/reminder job + a human yes/no | instant if pre-rendered | reports, monitoring, morning briefs |

All three call the same endpoint, so they can be mixed in one session.

## A. Tool — the default

The agent finishes its thought, then speaks one or two sentences. The text carries the detail;
the voice carries the tone. `/say` returns in ~2 ms and the daemon synthesizes in the background,
so the agent's turn never waits on audio.

Cost: the human hears the answer *after* reading it. Right for "say it out loud", wrong for a
conversation.

## B. Narrator subagent

A subagent forked with the session context, told to be a narrator: it receives short progress
lines and speaks them.

```
subagent(prompt: "You are the voice. For every message I send, speak at most 2 short
sentences with `vox say`. Never explain, never ask questions, keep it under 6 seconds.")
```

The parent then sends one line a minute: `send_message(narrator, "tests are red, fixing auth")`.

**What works and what does not.** A forked subagent sees a *snapshot* of the session, not the live
turns — there is no event stream into a child. So "broadcast" is really the parent pushing
one-line summaries. That is the honest version, and it is enough for narration.

Why it helps: narration runs in its own agent turn, so the main agent never waits on synthesis,
and the narrator only sees the summary — it cannot ramble for forty seconds.

## C. Scheduled digest

For bots that work with a schedule: the job produces text, the human gets an offer, audio is
rendered only after "yes". Because the cache is keyed on `sha1(text, voice)`, pre-rendering on
job completion makes the answer instant.

```bash
0 9 * * *  vox say "Morning. Three things today: the release, the invoice, the call at four."
```

## Ears (optional)

`vox listen` records from PipeWire, runs Underdog Bark 3.0 (0.6B, 163 MB) and prints text. The
loop is: mic → Bark → the human or a bridge sends the text → agent → Kokoro → speaker. Until
STT is installed there is only a mouth, no ears.

## Notes on the implementation

- **One worker, one lock.** Kokoro is a single-pass model; parallel sentences would fight over
  the same ONNX session. The daemon serializes synthesis and keeps the model warm instead.
- **Cache first, always.** Openers are pre-rendered at boot, so the most common first word is
  already a file. Everything else is `sha1(text, voice)`.
- **Player thread, not per-call processes.** `pw-play` is blocking; a queue keeps lines in order
  and prevents two answers from overlapping.
- **fp32, not int8.** Measured: int8 is 2.4× slower on CPUs without AVX-512 VNNI. See the README
  benchmark table.
