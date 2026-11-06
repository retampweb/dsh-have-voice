# Security and data handling

**Audio stays on the machine.** The daemon writes wav files under `out/cache/` and plays them
through `pw-play`. Nothing is uploaded, and there is no telemetry.

**Network is used twice, by choice:**

1. `install.sh` / `fetch-model.sh` download the Kokoro weights (311 MB + 27 MB) from one GitHub
   release. After that the daemon runs offline.
2. Kokoro's phonemizer uses espeak-ng locally. No text leaves the process.

**The MCP server and the HTTP daemon listen on `127.0.0.1` only.** Any local process can POST
`/say`; there is no authentication. Run it on a single-user machine, or bind nothing else.

**What the model says is what gets spoken.** The daemon renders the text it receives; it does not
read files, environment variables, or the session log. If an agent puts a secret in a `narrate`
call, it will be spoken aloud and cached on disk — the tool description tells agents to keep
updates short and never quote credentials.

**Caching.** `out/cache/*.wav` contains every spoken line, keyed by its text. Delete the directory
to clear it.

Report issues at https://github.com/retampweb/dsh-have-voice/issues.
