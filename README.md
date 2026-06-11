# Dec & Sam · WC26 War Room

Live dashboard for the Jeff Keen Charity Challenge World Cup 2026 pool.

## What's here
- index.html  — the whole dashboard (no build step, works anywhere)
- data.json   — leaderboard + fixtures + model data (refreshed by the robot)
- update_data.py — fetches Jeff's leaderboard, rewrites data.json
- .github/workflows/update.yml — runs the robot every 20 minutes, free, on GitHub

## Deploy in 10 minutes (GitHub Pages)
1. Create a new GitHub repo (e.g. `wc-warroom`), upload these files keeping the folder structure.
2. Repo Settings → Pages → Source: "Deploy from a branch" → branch `main`, folder `/ (root)` → Save.
3. Repo Settings → Actions → General → Workflow permissions → "Read and write" → Save.
4. Actions tab → "Update leaderboard" → Run workflow (first manual run). It then runs itself every 20 min.
5. Custom domain: in your DNS (where berkeleyhome.co.uk lives) add a CNAME record
   `wc` → `YOURUSERNAME.github.io`, then in repo Settings → Pages set custom domain `wc.berkeleyhome.co.uk` and tick Enforce HTTPS.

Done: https://wc.berkeleyhome.co.uk updates itself for the whole tournament.

## Optional: live odds + automatic Venn updates (Claude)
Add a repo secret named ANTHROPIC_API_KEY (Settings → Secrets and variables → Actions).
The "Daily odds & Venn refresh" workflow then runs each morning: Claude searches the
latest results, flips the Venn condition statuses, and nudges the prize-odds estimates.
Costs roughly pennies per day. Without the secret, the job skips harmlessly.
