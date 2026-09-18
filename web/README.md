# ThreatPad Web

A CyberChef-style port of ThreatPad: a static, fully client-side SOC notes
app. No backend, no accounts — everything runs in the browser and is
persisted to `localStorage` on the machine you're using. This is Phase 1 of
the web port (see the scoping notes in the session that created this): the
CyberChef-equivalent core feature set, single-user/local-only.

## Features

- Multi-tab note editor (CodeMirror 6) with autosave to `localStorage`
- IOC detection for IPv4/IPv6, domains, URLs, emails, and MD5/SHA1/SHA256
  hashes, with inline highlighting in the editor
- Defang / Refang (`hxxp[://]`, `[.]`, `[@]`, `[:]`, `[#]`)
- Extract IOCs panel with CSV/JSON/text export and click-to-copy
- Hash generation (MD5/SHA1/SHA256) and hash-type identification
- Base64 encode/decode
- Templates and snippets (editable, stored locally)
- Dark/light mode, line numbers, word wrap, font size — all persisted

## Not in this port (yet)

IOC enrichment (VirusTotal/AbuseIPDB), the training-wheels checklist,
client-contamination checks, breakglass mode, and the mileage/timer tab were
intentionally left out of Phase 1 — see the scoping discussion for why.

## Develop

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # static output in dist/, deployable anywhere (GitHub Pages, S3, nginx, or opened as a local file)
```
