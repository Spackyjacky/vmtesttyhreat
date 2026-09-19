# KQL Hunt Range

A browser-based KQL (Kusto Query Language) practice range, built to accompany playing
[KC7](https://www.kc7cyber.com/) games and get back into writing KQL against a
Defender-XDR-style log schema. Every piece of KQL syntax and semantics it teaches is
grounded in [Microsoft Learn's Kusto Query Language documentation](https://learn.microsoft.com/en-us/kusto/query/) —
nothing here is guessed.

It ships 52 investigation scenarios (50 single-step + 2 multi-step chains) across three
skill tiers, each tagged to a real [MITRE ATT&CK](https://attack.mitre.org/) technique, plus:

- A **Detection Lab** for building and testing detections against the synthetic dataset.
- **Learning Paths** — curated scenario sequences for different tracks (including a
  SOC Tier 1 path).
- A **Coverage heatmap** showing which MITRE tactics/techniques you've exercised.
- A **Learning Matrix** mapping scenarios to the KQL operators and cyber-analyst skills
  they teach.
- A **Badges** system, a **Shift Queue** of triage alerts, and **War Room** notes
  (saved locally in your browser).

## No backend

Everything runs client-side, in the browser:

- The KQL engine is a hand-written interpreter of a practical subset of KQL (tokenizer,
  parser, and evaluator covering `where`, the `project` family, `extend`, `summarize`,
  `make-series`, `sort`/`order`, `top`, `take`/`limit`, `distinct`, `count`, `join`,
  `union`, `render`, the scalar expression language, and the aggregation functions).
- The "Fabrikam" dataset — `DeviceProcessEvents`, `DeviceNetworkEvents`,
  `DeviceFileEvents`, `DeviceLogonEvents`, `EmailEvents`, `AlertInfo`, `AlertEvidence`,
  `SigninLogs`, `AuditLogs`, `NetworkAccessTraffic` — is generated deterministically in
  the browser at load time, so the same dataset (and the same correct answers) come up
  every time.
- Grading, scenario state, and War Room notes are all handled client-side, with
  `localStorage` used only for small per-viewer conveniences (theme choice, War Room
  notes, badge progress).

There is no server, no database, and no data ever leaves your browser.

## Running locally

Because the page loads its JavaScript as separate `<script src>` files, opening
`index.html` directly via `file://` can be blocked by the browser's CORS rules for local
script loads (this varies by browser). The reliable way to run it is with any static file
server from the repo root, for example:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Any other static server works too (`npx serve`, VS Code's Live Server, etc.) — there is
no build step, no `npm install`, and no bundler involved.

## Repo structure

```
kql-hunt-range-repo/
  index.html          Page shell: <head> (CDN CodeMirror + Google Fonts, css/style.css),
                       the body markup (topbar, sidebar, mission panel, modals, War Room
                       drawer), then the script tags that load everything below in order.
  css/
    style.css         All page styling: CSS custom properties for the light/dark theme,
                       and every component's styles (including CodeMirror's own CSS).
  src/
    kql-engine.js      The KQL interpreter (tokenizer, parser, evaluator). Exposes
                        `KQL` (`KQL.run`, `KQL.tokenize`, `KQL.KqlError`) globally.
    dataset.js          The synthetic Fabrikam dataset generator. Exposes
                         `FabrikamData` (`FabrikamData.buildDataset`, `.NOW`,
                         `.SCHEMA_COLUMNS`) globally.
    scenarios.js         The scenario bank — the 52-mission `SCENARIOS` array (prompts,
                          hints, solution queries, MITRE technique tags, facts, etc.).
                          Exposes `KQL_SCENARIOS` globally.
    app.js                Everything else: CodeMirror editor wiring, the sidebar and
                           mission panel, results rendering, grading, the Detection Lab,
                           Coverage/Learning Matrix/Learning Paths/Badges modals, the
                           Shift Queue, War Room notes, theme toggle, and mobile layout.
  README.md
  .gitignore
```

Each `src/*.js` file is a plain script (not an ES module) that attaches its API to the
global scope, exactly as the original single-file version did — `index.html` loads them
in dependency order (`kql-engine.js` → `dataset.js` → `scenarios.js` → `app.js`) so each
later file can use the globals the earlier ones defined.

## Credits

- The code editor is [CodeMirror 5](https://codemirror.net/5/), loaded from cdnjs
  (core + the `simple` mode, `show-hint`, `matchbrackets`, and `active-line` addons).
- Fonts are [JetBrains Mono](https://www.jetbrains.com/lp/mono/) and
  [Manrope](https://fonts.google.com/specimen/Manrope), loaded from Google Fonts.
- All KQL syntax, operators, and semantics are grounded in
  [Microsoft Learn's Kusto Query Language documentation](https://learn.microsoft.com/en-us/kusto/query/).
- MITRE ATT&CK technique references are grounded in [attack.mitre.org](https://attack.mitre.org/).

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages**.
3. Under **Source**, choose **Deploy from a branch**.
4. Set **Branch** to `main` and the folder to **`/ (root)`**.
5. Save. GitHub Pages will publish `index.html` at your repo's Pages URL within a minute
   or two.
