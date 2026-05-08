# External intel log

Append-only. External observations (posts, articles, talks) that bear on the modeling
task or on ROGII as a domain authority. One entry per source, dated. Keep raw
captured content separate from "relevance here" so future readers don't
over-extrapolate.

## 2026-05-07 — ROGII LinkedIn: StarLite ROP Heat Map

- **Source:** <https://www.linkedin.com/posts/drilling-drillingengineer-geologists-ugcPost-7457537199279054849-feUh>
- **Author:** ROGII (company account, ~15.1k followers)
- **Topic:** StarLite product feature — ROP (Rate of Penetration) heat map built from offset wells.

### Captured content

- Contrast headline: 380 ft/hr vs 139 ft/hr drilling rates within the *same* target window.
- Heat map is constructed by aggregating offset-well ROP, indexed by TVD.
- UI affords hovering at any TVD to read the **median** expected ROP at that depth.
- Pitched as decision support for steering *before* hitting slower formations.
- Hashtags: `#Drilling #DrillingEngineer #Geologists`.
- Comment from Carlos Cabrera questions whether software-side ROP gains are
  meaningful versus tuning mechanical drilling parameters (WOB, RPM, mud
  hydraulics). Worth flagging — it's a real-world skeptic prior on
  "model-driven optimization in drilling."

### Relevance to the TVT prediction task

The post is about **ROP** (drilling speed), not **TVT** (geological position) —
do not transfer claims directly. What *is* transferable is the method shape:

1. **Offset-well aggregation indexed by depth is ROGII's native primitive.**
   The competition data layout (typewell + horizontal-well pairs) reflects the
   same paradigm. Treating it as confirmation that per-formation, per-TVD
   distributions over offset wells are a sanctioned input for TVT models.
2. **Median over mean.** ROGII publicly uses median for its offset-well
   summary statistic. Likely chosen for outlier robustness against sparsely
   sampled, heterogeneous offsets — a useful prior for our own aggregations
   (e.g., per-formation TVT residual, per-MD-bin GR percentiles).
3. **TVD as the spatial join key.** ROP heat map is parameterized by TVD,
   not MD. Reinforces that TVD/TVT (not MD) is the comparable axis across
   wells in ROGII's worldview — relevant when designing typewell-to-lateral
   alignment features.
4. **Skeptic prior (Cabrera comment).** A real practitioner expressing
   doubt that software optimization beats mechanical tuning. Doesn't directly
   apply to TVT (which is interpretation, not actuation), but a useful
   reminder that domain experts may discount model output that contradicts
   bit-feel intuition. Frame predictions as *decision support*, not
   replacement.

### Caveats

- StarLite is a commercial product, not the competition. Nothing in the post
  is a permission, hint, or rule about the Kaggle task — treat as background.
- LinkedIn marketing posts overstate. The 380-vs-139 headline is one
  cherry-picked window; do not generalize the gain magnitude.

## 2026-05-08 — Julian Stahl LinkedIn: ROP Heatmap practitioner endorsement (StarLite + DrillSpot + StarSteer)

- **Source:** <https://www.linkedin.com/posts/stahljulian_the-rop-heatmap-in-starlite-has-been-a-game-ugcPost-7454512710932692992-zLy5>
- **Author:** Julian Stahl (drilling/geosteering practitioner, ~6.5k LinkedIn
  followers). Reshare-with-comment of a ROGII corporate post.
- **Topic:** Customer-side endorsement of the StarLite ROP Heatmap with a
  named outcome (5 days ahead of schedule, 1 bit per lateral, zero bit
  trips), and — incidentally — the first visibility we have into ROGII's
  three-tool stack rather than just the ROP-heatmap headline feature.

### Captured content

Stahl's comment: *"The ROP Heatmap in StarLite has been a game changer.
Instantly find the fastest zone in your target based on your offset wells."*

ROGII's underlying post (which Stahl reshared) describes a client case:

- **Outcomes claimed:** finished well 5 days ahead of schedule, drilled the
  full lateral with **1 bit**, zero bit trips, minimized non-productive time.
- **Demo data:** "public well data" (ROGII's framing).
- **Three-tool stack named:**
  - **StarLite** — geosteering visualization platform (already known from
    2026-05-07 entry).
  - **DrillSpot** — *new to us;* described as "drift-informed placement."
  - **StarSteer** — *new to us;* described as "formation layer avoidance."
- **Operational claim:** the ROP heatmap maps offset-well penetration-rate
  data directly onto geosteering displays, and crews "steer directly
  towards" high-performance zones.

Hashtags: `#Geosteering #Geoscience #Geology`.

### Why this is more useful than the 2026-05-07 entry

The first ROGII post was vendor headline material; this one reveals
**ROGII's own product taxonomy**, which is the more methodologically
interesting signal. Two specific implications for the TVT prediction
task:

1. **DrillSpot = "drift-informed placement"** suggests ROGII engineers
   think **wellbore drift** (the deviation of the actual lateral path
   from plan) is a load-bearing operational concern. The competition
   data has `X`, `Y`, `Z` columns per row of the lateral. Drift in 3-D
   space is implicit in the X/Y trajectory and explicit in Z. If
   ROGII's own toolchain treats drift as a first-class input, **drift
   features (cumulative dx, dy, dz from heel; deviation from a fitted
   linear path) deserve consideration as TVT covariates.**
2. **StarSteer = "formation layer avoidance"** suggests the formation-top
   columns (`ANCC`, `ASTNU`, `ASTNL`, `EGFDU`, `EGFDL`, `BUDA`) — which
   we already know are train-only — are **actuation targets in ROGII's
   workflow**, not just descriptive labels. This reinforces the prior
   note (in `competition-overview.md`) that they're "answers in
   disguise" *and* genuinely informative as auxiliary supervision
   signal. Worth using as multi-task auxiliary heads even though they
   can't be model inputs at inference.

### Practitioner-voice signal

Different signal class than the 2026-05-07 ROGII corporate post: this
one carries a named practitioner's reputation. Stahl is willing to put
"game changer" next to his real name. That's at least one independent
data point that the offset-well-aggregation methodology is *believed*
useful by working geosteerers, not only marketed by ROGII. Doesn't
upgrade the methodology to ground truth, but it does reduce the prior
that the 2026-05-07 post was pure marketing puffery.

### Caveats

- Outcomes ("5 days ahead", "1 bit", "zero bit trips") are about ROP /
  drilling efficiency, **not** about TVT prediction accuracy. The
  competition is judged on RMSE on TVT, which is geological
  interpretation; these claims do not transfer numerically.
- "Public well data" in the demo is *not* a permission, hint, or
  rule about which datasets the Kaggle entry can use. Verify
  separately against Kaggle ToS before ingesting any external well
  log.
- DrillSpot and StarSteer are commercial products. Treat as named
  evidence of methodology direction; do not infer their internal
  algorithms from the post.

### Cross-reference

- Updates the 2026-05-07 entry above by adding the DrillSpot /
  StarSteer tool taxonomy and the practitioner-voice signal. Read both
  entries together for the full picture.
