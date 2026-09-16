# Racing V8.6 — diagnostic candidate

Base: b360a29c74970cf8ef29edb75410619354c9bac8 (V8.5.7).
Target: debug/motogp-pipeline-output only. No production-main promotion.

## Contract

Before the editor, build one canonical_fact_object from the source title,
summary and explicit series/feed metadata. It contains series, event, session,
riders, entities, teams, manufacturers, locations, dates, positions, numbers,
relationships, claims, modality and forbidden_inferences. Extracted facts carry
literal source evidence and offsets. Missing information stays empty. The source
hash and independent frozen copy detect source/CFO mutation during qualification.

Extraction is deterministic and conservative: it preserves claim text and explicit
relationship/modality markers rather than inventing a fully resolved knowledge
graph. Entity catalogs recognize source spellings and deny additions; they never
expand surnames into full names or infer a rider's series. Unclassified source
tokens remain explicitly unclassified. Series transfer statements and dedicated
feed metadata remain supported.

The editor receives the CFO. The initial caption and every repaired caption pass
the Entity/Number/Series Guard, Racing-QM and independent Semantic-QM. Racing-QM
mutations also cross the guard. Hashtags are source-only, including rider spellings.
The final series check no longer silently rewrites a semantically approved post.
Technical provider failures remain TECHNICAL-DEFER. Semantic-QM keeps all hard-fact
requirements and now accepts only actual JSON true values as passing flags.

Repairs return only {"patches":[{"old":"exact span","new":"replacement"}]}.
A deterministic merge requires unique, non-overlapping spans in the original,
limits patch size/count, and rejects malformed, ambiguous, cascading or whole-post
replacements atomically. There is one editor call and at most two repair calls;
there is no repair-triggered research or full-text fallback. Invalid patches retain
the old caption, consume a repair attempt and are recorded.

## Compatibility and artifacts

The existing install entry point racing_v855_hardening.install remains valid and
is idempotent. Existing five diagnostic filenames and existing JSON fields remain.
motogp-qm-results.json adds pipeline_version, canonical_fact_object, guard_errors,
guard_history and repair_history. Guard rejection reasons also reach rejection
artifacts. No Telegram, publication or production workflow was triggered.

Legacy pipeline tests were migrated from obsolete regeneration/research assertions
to bounded patch assertions. Stale PASS reset is tested at the qualification
boundary; obsolete checks for absent baseline implementation symbols were replaced
with current runtime/approval compatibility checks. Audit selftest restores its
working directory before temporary cleanup, making it work on Windows as well.

## Validation

Local Python 3.12: compileall of the downloaded repository Python sources PASS.
Five offline suites PASS:
- racing_cfo_selftest.py: 23 tests (plus parameterized regression cases).
- racing_pipeline_selftest.py.
- racing_v85_selftest.py.
- motogp_pipeline_audit_selftest.py.
- motogp_date_recovery_selftest.py.

Covers Agius -> Aras, inserted first names, Gonzalez -> Gonzales,
WorldSBK -> WorldSSP/Supersport, San Marino -> Mugello,
P1 -> championship leadership or Q1, new numbers and hashtag bypasses.
Includes real editor/Racing-QM/artifact integration with mocked LLM responses,
post-repair and post-QM guards, immutable source evidence, strict semantic failure,
technical defer and rejected patches.

The diagnostic workflow now runs all five suites before its existing read-only
live Copy-QM step (Python 3.10 in GitHub Actions).

## Remaining live proof

No live V8.6 diagnostic result is claimed by these offline tests. Dispatch
MotoGP Pipeline Diagnostic against the V8.6 debug commit and compare with V8.5.7:
PASS/reject/defer counts, repair counts and acceptance, guard rejection reasons,
semantic/language failures, and elapsed time. Source news changes over time, so
counts alone are not a controlled quality benchmark.

Lexical guards are not a universal multilingual entity recognizer or semantic
proof. They cover known entities, source spelling drift, name prefixes/subjects,
literal numeric tokens/positions, series, leadership and modality escalations.
Novel paraphrases, unknown entities, spelled-out quantities and relationship
entailment still require strict Semantic-QM. Conservative modality/name checks
may reject valid prose; inspect the new histories in Diagnostic before tuning.
Do not relax Semantic-QM or promote main merely because offline tests pass.
