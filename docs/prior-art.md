# Prior art: public well-log datasets for the ROGII TVT competition

Research scope: public well-log / petrophysics datasets relevant to **predicting log
continuation** in the ROGII *Wellbore Geology Prediction* competition — i.e. predicting
**TVT (True Vertical Thickness, ft)** along a horizontal lateral from a **gamma-ray (GR)
log** plus a vertical **typewell** reference (see `docs/competition-overview.md`).

The competition is fundamentally a **GR-vs-depth sequence task** with a typewell↔lateral
correlation flavour. So the question for every external dataset is: *does it give us GR
logs (ideally with stratigraphic/formation-top labels) from analogous basins that we can
legally use to pretrain or warm-start a sequence model?*

> Kaggle rules note (from issue #5 / competition rules): external data is permitted —
> "freely & publicly available external data ... including pre-trained models" — *provided
> we cite it and stay within its license*. So pretraining is allowed; the binding
> constraint is **license compatibility**, not the rules themselves.

---

## Comparison table

| Dataset | Content (logs) | # wells / region | License | Pretraining relevance to TVT task |
|---|---|---|---|---|
| **FORCE 2020 (Xeek / NPD lithology)** | GR + DTC/DTS, NEU, DENS, RHOB, resistivity, PEF, SP, caliper; **lithofacies labels** + NPD lithostratigraphy + well X/Y | ~98 train + ~30 hidden (≈118–128) / **Norwegian North Sea & Norwegian Sea** | **Labels CC-BY-4.0; underlying logs NLOD 2.0** (Norwegian License for Open Government Data). Both permissive w/ attribution. *Permissive — usable.* | **Highest.** Curated, consistently-interpreted GR + explicit stratigraphy on a depth axis — the closest public analogue to the ROGII GR→geology task. Stratigraphic labels enable a GR→formation pretraining objective transferable to TVT. |
| **Equinor Volve** | Full field: petrophysical + drilling well logs (incl. GR), seismic, production, geomodels | ~24 wells (single field) / **central North Sea (Norway)** | **Modified CC-BY** — attribution required; **restrictions on resale and on data elements not covered by copyright.** *Usable with care — verify resale/redistribution clause.* | Medium. Real GR logs, but a *single field* → narrow geological diversity; better for validation / sanity-checking distributions than broad pretraining. |
| **Geolink Open North Sea** | LAS logs incl. **GR**; ~21,676 NPD stratigraphic picks (formation tops) | ~221–227 LAS files / **North Sea (Norwegian Continental Shelf)** | **CC-BY-SA-4.0** (attribution to Geolink, https://www.geolink-s2.com/). *Usable but **ShareAlike/copyleft** — see caveat.* | High. Largest well count with GR **and** stratigraphic picks → strong pretraining corpus for GR↕depth↔formation alignment. Copyleft is the catch (below). |
| **NLOG (TNO Dutch Subsurface DB)** | Borehole well logs (incl. GR), formation tops, production | Many hundreds / **Netherlands + Dutch continental shelf** | Public mining-law data, released **after a statutory confidentiality term**; reuse/redistribution (incl. via OSDU) permitted but **not under a single uniform CC license** — terms vary per file. *VERIFY per-file before redistribution.* | Medium. Good GR + tops volume and a *different* basin (good for robustness), but heterogeneous formats and license-per-file friction. |
| **Teapot Dome / RMOTC (DOE)** | LAS well logs, formation tops, correlation markers, core photos, 3-D seismic, production | ~1,000+ wells / **Wyoming, USA (onshore)** | US DOE / RMOTC release; data is **non-proprietary, intended for research/testing**. Effectively public-domain US-gov data. *Verify any resale/redistribution restriction.* | Low–Medium. Onshore US, different log suites & geology from the North-Sea-flavoured ROGII data → weaker domain match, but a large clean labelled set for generic GR-sequence pretraining. |
| **USGS well-log data / National Geologic Map** | Scanned + some digital logs, formation tops, stratigraphy | Many (US) / **USA** | US Gov work — **public domain** (no copyright). *Permissive.* | Low. Mostly raster/scanned, US geology; not a turnkey digital GR corpus. Reference, not pretraining. |
| **OSDU (Open Subsurface Data Universe)** | *Platform / data standard*, not a dataset | n/a | Platform is open; **hosted data carries its own per-source license.** | n/a for pretraining — it's an *access mechanism* for the datasets above (e.g. NLOG via OSDU), not a corpus itself. |
| **Kaggle "well log" datasets** (e.g. re-hosts of FORCE 2020) | Varies; many are re-uploads of the above | Varies | **Inherits the original license** — re-hosting does **not** relax CC/NLOD terms. *VERIFY provenance; cite the original.* | Use only as a convenient mirror of an already-permitted dataset; never as a license-laundering path. |

---

## Narrative

The ROGII task is, at its core, **GR-conditioned geological-position regression along
depth**, anchored to a vertical typewell. The public corpora that matter are the ones
that pair **GR logs** with **stratigraphic structure** (formation tops / lithofacies /
picks) on a depth axis, ideally from **North Sea / Norwegian Continental Shelf** basins —
the same geological family the ROGII data appears to come from (Austin Chalk / Buda /
Eagle Ford-style names like `BUDA`, `EGFDU/L` suggest a Gulf-Coast analogue, so treat
*all* external basins as domain-shifted — see caveats).

Three datasets stand out for **GR + stratigraphy**: **FORCE 2020**, **Geolink**, and
**NLOG**. **Volve** is real but single-field (good for validation, weak for pretraining
breadth). **Teapot Dome** and **USGS** are clean/large but onshore-US and log-suite
mismatched.

The decisive axis is **license cleanliness for a Kaggle submission**:

- **FORCE 2020** is the cleanest: labels **CC-BY-4.0** + logs **NLOD 2.0**, both plain
  attribution licenses with no copyleft and no resale entanglement. It is also already
  framed as an ML competition corpus, so it is pre-cleaned and consistently interpreted.
- **Geolink** is larger and has formation picks, but is **CC-BY-SA-4.0**. ShareAlike
  (copyleft) means derivative works *built from it* may need to be shared under the same
  license — fine for an open Kaggle notebook, but a snag if any downstream/commercial
  reuse is intended. Pretrained-model weights derived from a ShareAlike corpus sit in a
  legally grey area; **flag for verification** before relying on it in a submission.
- **NLOG / Teapot Dome / Volve** carry per-file or modified-license friction that costs
  time to clear for marginal added domain-relevance.

### Transfer-learning constraints (apply to ALL external data)

1. **Basin mismatch.** ROGII formation names (`BUDA`, `EGFD*`) read as Gulf-Coast /
   Cretaceous carbonates-and-shales, while FORCE/Geolink/Volve are North Sea
   siliciclastics. GR *response* and shale/sand cyclicity differ → pretrain for
   **representation** (GR texture, depth-sequence priors), not for transferable absolute
   TVT values.
2. **Log-type mismatch.** Many external sets have rich multi-log suites; ROGII gives
   essentially **GR only**. Pretrain on **GR-only subsets** to avoid a feature-distribution
   shift the competition model can't reproduce.
3. **Geometry mismatch.** External corpora are dominated by **vertical** wells; ROGII's
   target is **horizontal/lateral TVT continuation**. The typewell (vertical) ↔ lateral
   correlation structure is *unique to ROGII* and cannot be pretrained from vertical-only
   public data — it must be learned in-competition.
4. **Sampling / units.** Watch sampling interval (ROGII ≈ 1 ft steps) and GR API
   calibration; resample/normalise external GR before any joint training.

---

## TOP 1–2 pretraining recommendations

**1. FORCE 2020 (primary).** Best license cleanliness (CC-BY-4.0 labels + NLOD 2.0 logs,
no copyleft, no resale snag), pre-cleaned, consistently-interpreted GR with explicit
stratigraphy. Use it for **self-supervised / GR→lithofacies pretraining** of a
depth-sequence encoder, then fine-tune on ROGII. Lowest legal risk for a Kaggle
submission and the most directly analogous public corpus.

**2. Geolink (secondary, conditional).** Adds the largest GR + formation-pick volume for
broader pretraining diversity. **Conditional on clearing the CC-BY-SA-4.0 ShareAlike
implication** for pretrained weights used in a competition context — if that copyleft
question can't be resolved cleanly, **skip it and stay on FORCE 2020 alone**.

**Skip / de-prioritise:** Volve (single-field, low diversity), Teapot Dome & USGS
(onshore-US domain mismatch, raster-heavy), NLOG (per-file license friction). Keep
**Volve** only as a *validation/distribution-sanity* set, not a pretraining corpus.

---

## License caveats that could block competition use

- **Geolink ShareAlike (CC-BY-SA-4.0):** copyleft may attach to models/derivatives.
  **VERIFY** before relying on Geolink-pretrained weights in a submission.
- **Volve "modified CC-BY":** resale + non-copyright-element restrictions. Attribution-only
  use in an open notebook is likely fine; **verify** the exact clause if redistributing.
- **NLOG:** mining-law confidentiality terms + non-uniform per-file licensing → **VERIFY
  each file** before redistribution; safest accessed read-only, not re-hosted.
- **Kaggle re-hosts:** re-uploaded copies **inherit the original license** — always cite
  the original (Zenodo/SODIR for FORCE 2020, Data Underground for Geolink), never the
  mirror, and never treat a re-host as license relaxation.
- **General:** Kaggle rules require external data be *publicly available* and *cited*. All
  recommended datasets meet "publicly available"; cleanest citation path is **FORCE 2020**.

---

## Sources

- FORCE 2020 dataset (canonical, citable) — Zenodo: <https://zenodo.org/records/4351156>
  (license: CC-BY-4.0 labels; underlying logs NLOD 2.0); SODIR technical retrospective:
  <https://www.sodir.no/4ace9a/globalassets/2-force/2020/seminars/contest-machine-learning/technical_retrospective_force-2020-lithofacies-competition.pdf>
- Equinor Volve open dataset: <https://www.equinor.com/energy/volve-data-sharing> and
  <https://www.equinor.com/news/archive/14jun2018-disclosing-volve-data>
- Geolink Open North Sea — Data Underground: <https://dataunderground.org/dataset/geolink>;
  analysis repo (Lukas Mosser): <https://github.com/LukasMosser/geolink_dataset>
  (license: CC-BY-SA-4.0, attribution to https://www.geolink-s2.com/)
- NLOG (TNO Geological Survey of the Netherlands): <https://www.nlog.nl/en/boreholes>,
  <https://www.nlog.nl/en/data-supply>
- Teapot Dome / RMOTC (DOE) — SEG Open data wiki: <https://wiki.seg.org/wiki/Open_data>;
  Data Underground: <https://dataunderground.org/dataset/teapot-dome>
- USGS well-log data: <https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/well-log-data>
- OSDU (Open Subsurface Data Universe): platform/standard, hosts per-source-licensed data.
- Transfer-learning context — well-log foundation models / cross-well generalization:
  e.g. ScienceDirect S2096249524000115 (deep lithofacies classification),
  S2666544122000077 (GR-attribute lithofacies for limited-log boreholes).

> Accuracy note: where a license could not be confirmed to a single unambiguous term
> (NLOG per-file terms; Volve modified-CC-BY exact clause; Geolink ShareAlike implication
> for model weights), this doc says **"verify"** rather than asserting. All datasets named
> above are real and publicly documented at the cited URLs.
