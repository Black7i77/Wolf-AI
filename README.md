# Wolf AI Cloudflare v0.6

MIT-licensed local Ollama chat website with an optional public Cloudflare demo.
No login or personal author name. Includes emerald wolf artwork, coding mode,
code-copy buttons, and Python syntax checking without executing model output.

## Public website from your laptop

Requirements: Python 3.9+, Ollama with an installed model, and cloudflared.
No Python packages or virtual environment are required.

1. Extract the whole ZIP and open a terminal inside this folder.
2. Check `ollama list`. If Ollama is offline, run `ollama serve` separately.
3. Run:

```bash
bash start-public.sh
```

The launcher checks your installed models, starts a separate loopback demo
server on port 8780, and runs cloudflared. Share the real HTTPS
trycloudflare.com link cloudflared prints in your terminal. Leave this terminal,
Ollama and your laptop running. Ctrl+C stops the public tunnel and demo server.
No model files are downloaded or included. The script prefers installed
qwen2.5-coder:3b, then 7b, then llama3.2:latest, otherwise an installed model.

Choose another installed model or unused port explicitly:

```bash
bash start-public.sh --model qwen2.5-coder:3b --port 8781
```

If cloudflared is missing, install it from Cloudflare's official Linux download
page: https://developers.cloudflare.com/tunnel/downloads/
Cloudflare documents Quick Tunnels here:
https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/

Quick Tunnels are for testing/development, with no uptime guarantee. The public
hostname changes on restart and stops working when the tunnel stops. For a
permanent domain, configure a named Cloudflare Tunnel later. Its origin should
be this public demo server, not the unrestricted local app. Set WOLF_PUBLIC_HOST
to your exact hostname before starting a named-tunnel setup.

## Public demo limits

- One AI reply at a time; other requests receive a busy message.
- Three AI requests per visitor IP per 10 minutes.
- Twenty AI requests total per hour; limits reset when the server restarts.
- One fixed model; visitors cannot select arbitrary installed models.
- 2,000 characters per new message and at most 10 messages of context.
- Short replies capped at 512 model output tokens; unfinished code is flagged.

Allowances are basic application-level demo controls, not hardened production
abuse prevention. The host computer does the model computation. Public messages
travel through Cloudflare to the host's Ollama. Chats stay in each visitor's
browser local storage. The app does not intentionally persist or log prompts
on the server. Visitor IP addresses are hashed with a random per-run secret for
in-memory limits. Browser profiles share their own chat history. No accounts,
payments or subscriptions are active.

## Put the source on GitHub

This package contains code and artwork only, not model weights or private chat
history. Original code is MIT licensed under Wolf AI contributors; third-party
models keep their own licenses. Public GitHub ownership remains visible even
when the code and commit author do not contain a personal name.

Install GitHub CLI if needed (`sudo apt install gh` on Kali), then sign in and
publish from this extracted project folder:

```bash
gh auth login
bash upload-github.sh
```

The script creates a NEW PUBLIC `Wolf-AI` repository under the authenticated
GitHub account. It does not overwrite an existing repository. To choose a
new name: `bash upload-github.sh Wolf-AI-Website`. If `.git` already exists, it
stops to preserve that repository. If publication fails after git initialisation,
keep the terminal output so the existing Git checkout can be resumed.

After a successful upload the script saves the verified repository URL in a
local ignored file. Restart `bash start-public.sh`: the website's GitHub button
then points to that URL. You can also set WOLF_GITHUB_URL to an existing repo URL.

## Local-only use

```bash
bash start.sh
```

This uses http://127.0.0.1:8767 with the original local model choices and longer
coding replies. Do not tunnel this unrestricted local server directly.

## Checks

```bash
python3 -m unittest -q
node test_format.cjs
node --check web/app.js
```

Node is needed for developer checks only. Python code checks parse syntax,
not behaviour, dependency availability or security. Tests simulate Ollama;
real laptop inference and the actual external tunnel still require a live run.
