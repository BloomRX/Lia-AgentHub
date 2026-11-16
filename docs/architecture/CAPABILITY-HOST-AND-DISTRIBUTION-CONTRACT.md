# Capability Host & Distribution Contract

**Status:** PROPOSED (decisão) / **mecanismos IMPLEMENTADOS** (ver §15)  
**Scope:** Lia Agent Hub architecture and future host integrations  
**Initial reference consumer:** Lia Go (travel-management application)  
**Related decisions:** D-03 (formats and metadata), D-04 (dependencies), D-07 (distribution to products), D-08 (SDK/CLI), D-10 (safe updates), D-11 (third-party notices), D-17 (OS support), D-18 (risk policy), D-20 (non-redistributable resources)  
**Introduced:** 2026-11-15

---

## 1. Executive summary

The Lia Agent Hub should support two distinct classes of consumers for capabilities managed by the same ecosystem:

1. **Development Hosts** — coding agents and development environments such as Codex, Arena, and compatible tools. They consume project-scoped development capabilities, including repository instructions, engineering Skills, QA procedures, architecture guidance, and workflows.
2. **Product Runtime Hosts** — applications in the Lia family whose own assistant features may consume capabilities as part of the product experience. Lia Go is the first reference use case. Other Lia applications may become hosts later.

This proposal extends the existing Hub direction without turning the Hub into a universal runtime. The Hub remains responsible for capability authoring, discovery, curation, inspection, validation, versioning, packaging, and distribution. Each host remains responsible for loading and, where applicable, executing capabilities within its own trust, permission, credential, data, approval, and lifecycle boundaries.

The same capability ecosystem may serve both classes of host, but a capability is never assumed to be portable or compatible merely because it has a valid `SKILL.md`.

**This document records a proposed architectural direction. It does not authorize implementation, distribution, licensing acceptance, or integration into Lia Go.**

## 2. Motivation

The current Hub vision already separates capability creation/distribution from consumption and execution. This proposal makes the consumer side more explicit.

Without an explicit host model, the ecosystem risks:
- treating development-agent Skills as if they were suitable for end-user applications;
- shipping development-only instructions, scripts, or tooling inside consumer applications;
- assuming desktop filesystem conventions apply to mobile packages;
- coupling products to an installed or running Hub service;
- distributing third-party content without confirming redistribution rights;
- allowing capability changes to take effect without host-side validation and user approval;
- confusing metadata validation or package integrity with runtime safety.

Lia Go provides a concrete first use case for defining these boundaries before any product integration is attempted.

## 3. Architectural boundary

### 3.1 Lia Agent Hub — capability authoring and distribution plane

The Hub may:
- discover and catalog capabilities;
- author and edit first-party capabilities;
- inspect package contents and metadata;
- record origin, author, upstream, version, commit, license, dependencies, compatibility, declared egress, and declared permission requirements;
- validate package structure and metadata;
- calculate and verify content hashes;
- prepare exportable packages and manifests;
- record distribution profiles and host compatibility claims;
- preserve provenance and third-party notices.

The Hub must not become the mandatory runtime of consuming applications. A host must be able to validate and consume an exported package without the Hub being installed, running, or reachable.

### 3.2 Host application — consumption and runtime authority

The host application is authoritative for:
- deciding whether a capability is compatible with that host and its version;
- deciding whether the capability is allowed in the current product context;
- loading and executing capability behavior, if execution is supported;
- permission enforcement and sandboxing;
- credentials, secrets, and user data;
- network access and egress policy;
- user consent and approval of actions;
- activation, deactivation, updates, rollback, and removal;
- runtime audit logs and failure handling.

A declaration in a capability manifest is descriptive metadata, not a grant of permission. The host must independently enforce its own policies.

### 3.3 No mandatory Hub-host API

The initial distribution model should be file/package based. A host must not require a live Hub API, account, background service, or shared database to consume a package. Optional future tooling may improve discovery or synchronization, but cannot become a runtime dependency.

## 4. Host classes and distribution profiles

The proposal introduces a host-consumption model with two orthogonal dimensions:

- **Host class:** the kind of consumer and its responsibilities.
- **Distribution profile:** the intended delivery channel/lifecycle of a capability.

### 4.1 Host classes

| Host class | Examples | Typical capability use |
|---|---|---|
| `development-host` | Codex, Arena, compatible coding agents and IDE environments | Repository-scoped instructions, engineering workflows, QA, architecture, security, development tools |
| `product-runtime-host` | Lia Go and future Lia applications | Product assistant capabilities intentionally designed and approved for end-user application use |

Host compatibility must be explicit and may include host identifier, host version range, operating system, architecture, runtime capabilities, and supported capability/package format.

### 4.2 Distribution profiles

| Profile | Meaning | Expected handling |
|---|---|---|
| `development-only` | Intended only for development hosts and development workflows | Must not be included in product application bundles |
| `app-bundled` | Intentionally shipped as part of a product application release | Versioned and reviewed with the application; host validates package and declared compatibility |
| `user-installed` | Optional capability installed by the user after product installation | Explicit user choice, host-side validation, consent, and controlled lifecycle |

These are proposed distribution profiles, not installation states. A host should separately track lifecycle states such as discovered, available, installed, pending approval, active, disabled, update available, failed, and removed.

A capability may declare more than one permitted distribution profile only when each profile is independently justified and compatible with its license, package contents, and host behavior. `development-only` must never be inferred to be product-compatible.

## 5. Complementary manifest: `.lia/capability.json`

### 5.1 Purpose

Evaluate a Lia-specific complementary manifest at:

`.lia/capability.json`

It would carry distribution and host metadata without changing standardized Agent Skills frontmatter or the contents/semantics of `SKILL.md`.

The absence of this file must not invalidate an otherwise valid standard Agent Skill. Such a resource may remain catalogable as a generic or unclassified capability, but it must not be treated as approved for Product Runtime Host distribution by default.

### 5.2 Proposed metadata groups

The exact schema is OPEN and requires a separate specification. Candidate groups:

- `schema_version`: version of the complementary manifest schema;
- `capability_id`: stable identifier, distinct from display name;
- `distribution_profiles`: one or more of `development-only`, `app-bundled`, `user-installed`;
- `hosts`: explicit host identifiers, supported versions, and host classes;
- `platforms`: operating systems, architectures, and platform-specific constraints;
- `requirements`: runtime, tool, network, storage, model, or service requirements;
- `permissions_declared`: descriptive declarations of required capabilities such as filesystem access, network access, or external tools;
- `egress_declared`: destinations or categories of external communication, when known;
- `provenance`: source repository, upstream, author, version, commit, and derivation relationship;
- `license`: SPDX identifier where confidently identified, license file reference, notices, and redistribution conditions;
- `integrity`: hashes for the exact package files or canonical package representation;
- `entrypoints` or resource references: descriptive pointers only, never permission to execute automatically.

This list is a design inventory, not a finalized JSON schema. Field names, requiredness, canonicalization, and validation rules remain to be specified.

### 5.3 Compatibility with Agent Skills

- Do not modify standardized `SKILL.md` frontmatter to introduce Lia-only distribution semantics.
- Do not require the complementary manifest for generic Agent Skills discovery or basic inspection.
- Preserve unknown metadata and original files when importing/exporting, where format and license permit.
- Do not claim universal compatibility from format recognition alone.
- Define behavior for malformed, unsupported, or newer manifest schema versions.

## 6. Mobile and platform-specific profiles

Capabilities intended for mobile applications require explicit platform compatibility declarations.

Do not assume that:
- Windows paths or environment variables exist inside an Android APK;
- Codex/Arena directory conventions are available to a mobile host;
- desktop CLIs, shell scripts, local servers, or filesystem permissions are available on mobile;
- a capability compatible with Lia Go desktop is automatically compatible with Lia Go Android/iOS.

A mobile-compatible capability should declare its platform requirements, supported runtime interfaces, network assumptions, storage model, permissions, and any platform-specific package assets. The host must reject or disable unsupported capabilities rather than silently approximating their behavior.

The mobile profile and exact platform matrix remain OPEN until Lia Go's target platforms and assistant architecture are specified.

## 7. Package, integrity, and lifecycle requirements

### 7.1 Package independence

- Exported packages must be self-describing enough for a host to inspect them without contacting the Hub.
- A host must not require the Hub's local database or application to validate package structure and declared metadata.
- Package contents must distinguish instructions, references, assets, scripts, and executable components.
- Dependencies must be explicit; hidden downloads or undeclared runtime dependencies are not acceptable.
- Packages must preserve license texts, notices, attribution, and upstream references required for redistribution.

### 7.2 Integrity and authenticity

- Record hashes over a precisely defined package/file representation.
- Specify canonicalization and exactly which files are covered.
- Recalculate hashes at import and before activation/update where appropriate.
- A mismatch must be visible and must prevent activation unless a separately approved recovery process exists.
- Hashes establish content identity/integrity relative to a trusted expected value; they do not establish author identity, publisher authenticity, or safety.
- Digital signatures and publisher identity are separate future design questions; do not imply that unsigned hashes provide signature guarantees.

### 7.3 Import, activation, and update

The host should:
1. inspect the package and manifest;
2. validate schema and host/platform compatibility;
3. verify hashes and package completeness;
4. show provenance, version changes, license, declared requirements, permissions, and egress;
5. obtain explicit user/administrator approval appropriate to the product;
6. install into a host-controlled location;
7. activate only after host policy checks;
8. retain enough prior state for a controlled rollback where feasible.

No silent installation, activation, or update is permitted. An update that changes content, permissions, egress, dependencies, or license metadata must be surfaced for renewed review. Failure must not leave a partially active capability.

### 7.4 Quarantine is not approval

Importing a package into a quarantine or review area is distinct from approving or activating it. A package with an integrity mismatch, unknown license, unsupported host profile, or unresolved critical risk must not become active merely because it was successfully imported.

## 8. Licensing and redistribution policy

The Hub must distinguish:
- cataloging a reference from copying its content;
- local use from redistribution;
- source-code license from documentation/content/assets/model/data licenses;
- permission to modify from permission to redistribute;
- upstream license obligations from obligations introduced by bundled dependencies.

For `app-bundled`, redistribution rights must be documented for every included third-party component and relevant content. If redistribution rights are unknown or insufficient, the package must not be bundled. A link/reference or user-directed acquisition flow may be considered only after separate review.

For `user-installed`, the host still must not assume that user choice resolves all license or redistribution obligations. The exact legal treatment depends on the distribution model and applicable license.

This document is not legal advice and does not approve any third-party license or package.

## 9. Security and trust model

- All imported capability content is untrusted until inspected.
- Metadata declarations are claims, not enforcement.
- Host permissions must be granted by host policy, never by the capability itself.
- Secrets and credentials must remain in the host's credential boundary.
- Egress declarations must be reviewed and enforced by the host where technically possible.
- Static inspection is not a guarantee of benign behavior.
- Product Runtime Hosts must not execute development-only scripts or instructions as a side effect of package import.
- The Hub must not remotely activate, update, or revoke runtime behavior in a host.
- The host must maintain its own audit trail for installation, approval, activation, update, disablement, and removal.

A future runtime capability may be pure instructions/data, invoke host-provided tools, or include executable components. These are materially different risk classes and must be represented explicitly in future contracts. This proposal does not authorize executable plugin support.

## 10. Lia Go as the first reference host

Lia Go is a travel-management application and the first candidate Product Runtime Host.

The initial work should be limited to documenting its potential host requirements:
- target platforms and packaging constraints;
- assistant architecture and capability invocation model;
- product-owned tools and APIs;
- data boundaries for itineraries, reservations, user preferences, and other travel context;
- network and egress requirements;
- permission and confirmation requirements for consequential actions;
- offline behavior and capability availability;
- capability update and rollback UX.

Do not assume Lia Go already has an approved AI slice or runtime interface. Do not implement Hub integration in Lia Go until that slice and the host contract are approved.

The first integration should be a narrow, low-risk proof of compatibility using a first-party capability, not a general third-party plugin execution system.

## 11. Non-goals and explicit constraints

This proposal does not:
- turn the Hub into a universal agent runtime;
- create a mandatory Hub-host API or cloud service;
- move execution, permissions, credentials, user data, or action approvals into the Hub;
- distribute development Skills inside consumer applications;
- permit silent installation, activation, or updates;
- authorize execution of imported scripts or arbitrary code;
- guarantee that all Agent Skills formats are portable across hosts;
- approve redistribution of any third-party capability;
- define a final mobile runtime or APK integration;
- authorize implementation in Lia Go or the Hub.

## 12. Proposed decision sequence

1. Complete the current Skills and third-party license research.
2. Review this host/distribution proposal with Architecture/Security.
3. Define host identity and compatibility semantics.
4. Specify the `.lia/capability.json` schema and versioning policy.
5. Specify portable package layout, canonical hashing, notices, and validation behavior.
6. Define host-side lifecycle and consent requirements.
7. Document Lia Go's actual target platforms and proposed AI host boundary.
8. Approve a narrow first-party capability pilot.
9. Only then authorize implementation and integration work.

## 13. Open questions

- Should host classes and distribution profiles be separate schema fields or a normalized compatibility matrix?
- Can one capability have multiple distribution profiles, and under what review rules?
- What is the canonical package format and hash boundary?
- How are nested dependencies represented and locked?
- How should a host handle unknown manifest schema versions?
- Which capability classes are allowed in Product Runtime Hosts: instructions/data only, host-tool calls, or executable extensions?
- How are permissions and egress declared in a portable but enforceable way?
- What is the minimum metadata required for `app-bundled` redistribution approval?
- How will desktop and mobile host profiles differ?
- What is the smallest safe first-party Lia Go pilot?

## 14. Acceptance criteria for a future specification

A subsequent implementation-ready specification should demonstrate that:
- generic Agent Skills remain valid without Lia-specific metadata;
- development-only capabilities cannot be accidentally selected for product bundling;
- host compatibility is explicit and independently validated by the host;
- a package can be inspected and validated without a running Hub;
- package hashes cover a precisely specified representation;
- integrity failures prevent activation;
- license and notice obligations are preserved and reviewed before bundling;
- declared permissions and egress never grant themselves;
- the host owns credentials, user data, approvals, execution, and lifecycle;
- mobile compatibility is explicit rather than inferred from desktop support;
- updates are reviewable, consent-based, and recoverable;
- the initial Lia Go integration remains out of scope until its AI host slice is approved.

---

## Evidence and status discipline

This document records a proposal received from the Lia Go workstream and expanded into a Hub-level architectural design. The requirements have not yet been implemented or validated in a running host.

- **PROPOSED:** two host classes and three distribution profiles.
- **PROPOSED:** complementary manifest at `.lia/capability.json`.
- **PROPOSED:** package-independent host validation and host-owned runtime authority.
- **NOT IMPLEMENTED:** manifest schema, package format, host SDK, distribution tooling, or Lia Go integration.
- **NOT VALIDATED:** compatibility with a real Lia Go assistant runtime or mobile package.
- **HUMAN DECISION REQUIRED:** approval of the architecture, schema, distribution policy, legal review process, and implementation scope.


---

## 15. Implementation status (added 2026-11-15)

This document is a **proposal for the decision** about how hosts integrate — that
decision is still `PROPOSED`, and nothing here approves a global license or a
product rollout. But the *technical mechanisms* described in §5–§10 are no
longer hypothetical: they exist, they are tested, and the tests are organized
by consuming project. This section records exactly what a host can rely on
today and what remains a decision.

### 15.1 What exists and is verified

Each row is backed by tests in `tests/integration/test_host_contracts.py`,
one class per host. A row is here only if a test would fail without it.

| Mechanism | Contract section | Verified by |
|---|---|---|
| Publishable index with declared scope | §5.2, §7 | `TestContratoLiaGo` |
| Index never contains quarantine | §7.4 | `TestContratoLiaGo` |
| Index never claims to be signed | §7.2 | `TestContratoLiaGo` |
| Self-describing package readable without the Hub | §7.1 | `TestContratoLiaGo` |
| `dry_run` writes nothing | §7.3 | `TestContratoLiaStudio` |
| Structural error reported with its code | §7.3 | `TestContratoLiaStudio` |
| Prose content never blocks an import | §9 | `TestContratoLiaStudio` |
| Package verifiable by the receiver | §7.2 | `TestContratoLiaProject` |
| Tampering detected | §7.2 | `TestContratoLiaProject` |
| Batch export survives one failure | §7.3 | `TestContratoLiaProject` |
| Internal metadata (`.lia/`) never shipped | §7.1 | `TestContratoLiaProject` |
| Searchable description, tags, domain | §5.2 | `TestContratoLiaForge` |
| License and obligations travel with the resource | §8 | `TestContratoLiaForge` |
| Quarantine invisible to consumers | §7.4 | `TestContratoLiaForge` |
| Unknown fields survive a read/write roundtrip | §5.3 | `TestContratoModelLab` |
| Import never executes content | §9 | `TestFronteirasQueNaoPodemCeder` |
| Import never writes outside the Hub | §9 | `TestFronteirasQueNaoPodemCeder` |
| No credential *value* ever stored | §9 | `TestFronteirasQueNaoPodemCeder` |
| Trust starts unreviewed and requires a human | §9 | `TestFronteirasQueNaoPodemCeder` |

### 15.2 The stable surface a host may code against

`AgentHub` is the integration surface. These are the methods a host uses; the
rest is internal.

| Method | Returns | A host uses it to |
|---|---|---|
| `import_path(path, dry_run=)` | `ImportReport` | inspect before accepting |
| `items(query=)` | `list[dict]` | list **active** capabilities only |
| `detail(cap_id)` | `dict` | inspect one capability fully |
| `promote(cap_id)` | `dict` | the human decision to activate |
| `set_trust(cap_id, trust, decided_by=)` | `dict` | record who reviewed it |
| `set_license(cap_id, ...)` | `dict` | record the redistribution decision |
| `export(cap_id, target=, destination=)` | `dict` | produce a package |
| `verify_package(path)` | `dict` | check a received package |
| `publish_index()` / `read_index()` | `dict` | publish/consume the index |

Three properties hold on all of them, and tests enforce them:

1. **Nothing is activated implicitly.** Import lands in quarantine; `promote`
   is a separate, explicit call.
2. **Nothing is authorized implicitly.** `redistributable` is `False` unless a
   human sets it; a declared license never authorizes anything.
3. **Hashes prove integrity, never authorship.** There is no `signed` field
   that can become `True` in the MVP.

### 15.3 What a host must still decide (not technical)

These stay with the host and are out of scope for the Hub — listed so nobody
mistakes a working mechanism for a granted permission:

- whether to load a capability of a given trust level;
- whether to execute anything a capability describes;
- which credentials to supply and where;
- redistribution rights for third-party content;
- approval UX and the operational lifecycle of a running capability.

### 15.4 Known limitations

- **No exchange format for quarantine.** Only active capabilities are
  publishable. That is deliberate (§7.4), but it means two Hubs cannot mirror
  each other's unreviewed work.
- **`requirements` is not extracted from `metadata:`.** Reading declared
  dependencies from the frontmatter is P-E7, outside the authorized scope of
  this round. The field exists in the model and returns `None`; the tests
  assert that "nothing declared" reads as `None`, not as `0`.
- **Nested frontmatter is one level only.** `metadata:` with `author`,
  `domain`, `tags` works. Deeper nesting is not interpreted: keys are
  flattened onto the parent's path, so `metadata.a.b` loses its `a` level
  (`metadata.b` is kept, and no data is silently dropped — but the structure
  is). A full YAML parser was rejected as an unnecessary dependency for a
  format where no real skill in the 53-file corpus nests deeper than one
  level. Verified: `parse_frontmatter` on `metadata:\n  a:\n    b: c`
  yields `{"metadata": "", "metadata.a": "", "metadata.b": "c"}`.
