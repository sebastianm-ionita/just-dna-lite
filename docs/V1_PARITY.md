# Generation-I Module Parity Plan

This document maps every Generation-I (Gen I) Just-DNA-Seq annotation module to its port status in
the current (Gen II) `just-dna-format`, and lays out what's needed to reach full feature parity.

Gen-I modules were OakVar *postaggregators*, one `just_*` repo per module in the
[`dna-seq`](https://github.com/dna-seq) GitHub org, each shipping a small curated SQLite/TSV/txt data
file. Stage 1 (see `just_dna_pipelines.v1_port` and `data/interim/v1_port/`) reproducibly ports the
variant-backed modules from that canonical source; this plan covers the rest.

## Where they're published

The **module marketplace** (`https://module-marketplace.just-dna.life`, namespace `just-dna-seq`) is
now the primary store; publish via `pipelines marketplace publish just-dna-seq <name> <version>
data/interim/v1_port/<name>`. The HuggingFace collection (`just-dna-seq/annotators`) is **legacy** and
will be retired after the marketplace migration; it's kept in sync for now via `pipelines v1-port
publish <name>`. All six variant-backed modules are live on both at **1.0.0**.

## Status overview

| Gen-I repo | Module | Data | Ported to `v1_port/`? | Published (marketplace + HF) | Parity |
|---|---|---|---|---|---|
| `just_coronary` | coronary | `coronary.sqlite` | ✅ compiled | ✅ 1.0.0 | **full** — 27/27 rsids match HF |
| `just_vo2max` | vo2max | `vo2max.sqlite` | ✅ compiled | ✅ 1.0.0 | **full** — 13/13 match HF |
| `just_lipidmetabolism` | lipidmetabolism | `lipid_metabolism.sqlite` | ✅ compiled | ✅ 1.0.0 | **full** — 15/15 match HF |
| `just_longevitymap` | longevitymap | `longevitymap.sqlite` | ✅ compiled | ✅ 1.0.0 | **near-full** — 518/528 rsids (10 het-only rsids unresolved, below) |
| `just_thrombophilia` | thrombophilia | `thrombophilia.sqlite` | ✅ compiled | ✅ 1.0.0 | **full** — newly published (2026-07) |
| `just_superhuman` | superhuman | `superhuman.sqlite` | ✅ compiled (subset) | ✅ 1.0.0 (subset) | **🚧 WIP** — v1 subset live (2 verified in-source PMIDs); v2 (full grounding + Mar-2026 refresh) **in progress** |
| `just_lnewco` | lnewco (APOE) | `metabolic_genotype.sqlite` | ❌ | ❌ | **gap** — diplotype schema needed |
| `just_cardio` | cardio | `genes.txt` | ❌ | ❌ | **gap** — ClinVar gene-panel type |
| `just_cancer` | cancer | `genes.txt` | ❌ | ❌ | **gap** — ClinVar gene-panel type |
| `just_pathogenic` | pathogenic | (none) | ❌ | ❌ | **gap** — ClinVar pathogenicity type |
| `just_drugs` | drugs | `annotation_tab.tsv` | ❌ | ❌ | **gap** — PharmGKB domain |

The five modules previously on HuggingFace now have a **reproducible source-of-truth port**
re-derived from their Gen-I repos, and the reproduction matches the published artifacts almost exactly
— validating both the port and the legacy HF data. thrombophilia was newly added; superhuman is a WIP
(v1 subset published, v2 grounding in progress).

## Work items to reach parity

### 1. Publish `thrombophilia` — ✅ done (2026-07)
Published to `just-dna-seq/annotators/data/thrombophilia/` via `pipelines v1-port publish
thrombophilia`; `module_metadata.thrombophilia` added to `modules.yaml`. It is now auto-discovered and
part of the default module set. Re-publish (or publish other readied modules) with the same command.

### 2. Close the longevitymap het-allele gap (10 rsids)
284 `allele_weights` rows were skipped, dropping 10 rsids that appear only as heterozygous entries
whose ref/alt pair wasn't found in the Ensembl cache (novel/merged/multiallelic rsids). Options:
- query an additional/newer dbSNP build for the missing rsids, or
- carry the original module's runtime ref lookup forward.
Low value relative to effort — 518/528 already reproduced. Track, don't block.

### 3. Ground `superhuman` with real PMIDs — 🚧 v1 subset published; v2 IN PROGRESS
Most of the source's `references` are dbSNP URLs, but a subset are real PubMed links. **v1.0.0** is
published to the marketplace + HF grounded on those 2 in-source, rsid-specific, PubMed-verified
citations (APOA2 `rs5082`→17446329, APOE `rs7412`→16603077); the other 755 variants are ungrounded.
The full literature backfill (per-gene founding PMIDs) + **March 2026 refresh** is **v2, now in
progress** (separate supervised agent) — see `docs/SUPERHUMAN_REFRESH_PLAN.md` (verification-gated,
never fabricates PMIDs). When it lands, publish as `2.0.0`.

### 4. New module type: ClinVar gene-panel (`cardio`, `cancer`, `pathogenic`)
These three don't carry per-variant weights — they select ClinVar pathogenic variants (by gene list
for cardio/cancer; directly for pathogenic). Parity requires:
- a **ClinVar reference** (NCBI `clinvar.vcf.gz`, ~200 MB, GRCh38) provisioned like the Ensembl cache
  — note the Ensembl variations parquets already carry `CLIN_*` columns
  (`CLIN_pathogenic`, `CLIN_likely_pathogenic`, `CLIN_benign`, …), so a gene-panel module could be
  built as a filter over the existing cache without a separate ClinVar download;
- a **gene-panel module type** in `just-dna-format` (a module defined by a gene set + a
  pathogenicity predicate, rather than an enumerated variant table). This is a schema proposal for
  the format repo (leave a note in `just-dna-format/docs/ROADMAP.md`).

### 5. New module shape: APOE diplotype (`lnewco`)
`lnewco` keys conclusions on an APOE diplotype spanning `rs7412`+`rs429358` (e.g. `e4/e4`). The DSL's
single-rsid `VariantRow` can't express a multi-locus genotype. Parity requires a haplotype/diplotype
extension to the schema — a `just-dna-format` proposal.

### 6. PharmGKB pharmacogenomics (`drugs`)
`just_drugs` is drug-response annotation (PharmGKB `annotation_tab.tsv`) — a different domain from the
variant-weight modules and never migrated from Gen I. Parity requires a PharmGKB adapter plus likely
new fields (drug, response, evidence level). Largest effort; scope separately.

## Suggested sequencing
1. ✅ Publish `thrombophilia` (done). 2. 🚧 `superhuman` v2 PMID back-fill + Mar-2026 refresh (in
progress). 3. ClinVar gene-panel type covering `cardio`/`cancer`/`pathogenic` in one mechanism (schema
+ one adapter). 4. APOE diplotype schema for `lnewco`. 5. PharmGKB `drugs` (separate project).
