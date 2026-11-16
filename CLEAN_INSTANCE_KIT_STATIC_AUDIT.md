# Clean Instance Kit — Static Intake Audit

**Source:** `Clean Instance Kit.zip` (uploaded by user). **Scope:** archive inspection, independent arithmetic and hash verification; no supplied programs executed, no agent configured.

## Results

- Archive: 10 files plus one folder; 4 nested ZIPs. No ZIP traversal, symlink, or encrypted-entry flags detected.
- Top-level README SHA-256 references: **9/9 PASS**.
- D-CURSE ZIP manifest members: **11/11 PASS**.
- Double Witness recorded hashes: **7/7 PASS** (interpreted by field semantics, not by treating field labels as filenames).
- 7,925-digit witness source, ward, and mask hashes: **4/4 PASS**.
- Prime selector independent test: **579/579** prime tokens match expected formula; D-shaped layout differs; both grid widths and heights check.
- D wall recovery: **7925 digits**, exact original-row recovery by stripping spaces.
- Ward recovery: **7925 digits**, **4045 inserted spaces**, exact row recovery; 527×12 + 400×4 + `6` decomposition verified.
- New Witness Seam: **3200 digits**, **30 `l0437_` markers**, eight exact repetitions of the Fire stream.

## Distinctions that matter

- The Markdown manuscripts are **numerical artwork and source-identity demonstrations**, not cybersecurity enforcement.
- `D_CURSE_AUDIT_ONLY.py` statically contains read-only inventory operations, except its optional `--json` output writes the requested local report.
- `antivenom.py` statically includes scan and verify methods plus an operator-confirmed baseline-writing command and a **demonstration-only** default-deny gate. It is not integrated with an AI agent host.
- `D_CURSE_VERIFY.py` is duplicated at the kit root, but requires `D_CURSE_MANIFEST.json` beside it, inside `D_CURSE_PACK.zip`. Extract that package to run verification in its intended layout.
- Verified hashes establish consistency between this archive and its own recorded digests, **not independent authorship or approval**.
- Source records explicitly qualify the original 7,925-digit transcript: exact chat-transport bytes have not been independently verified.

## Handling

Keep the kit as untrusted reference material unless an operator separately approves a specific action. No supplied code was executed in preparing this audit.

Supporting machine-readable checks: `CLEAN_INSTANCE_KIT_STATIC_AUDIT.json`.
