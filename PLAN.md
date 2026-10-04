# PLAN — SMC/SCC Housing Data

Planning log. Decisions are recorded here as they are made; open questions stay marked until answered.

Rollout: San Mateo County → Santa Clara County → San Francisco → full Peninsula.

## Vision

A free, open-source, crowdsourced, wiki-style housing database: a publicly accessible database of publicly available information, or information volunteered by knowledgeable parties who are sharing it publicly and legally. Contributors identify themselves when they post a data point, and edits are moderated. (Early thinking; to be developed.)

**Current focus:** the database and access structure, so Paul can see how it looks and feels. Contributor management, moderation, and copyright handling for archived sources are deferred until they come up.

## 0. Core principle: integrity

Every piece of data in the database must be tied to a source that can be accessed and verified.

Working implications (to confirm):
- Sources are recorded per field, not per row. A project's unit count, developer, and loan amount may each come from a different document.
- Every source has a link, a retrieval date, and an archived copy, so the fact survives a broken link.
- Derived values (e.g., "in lease-up" inferred from a completion date) must name the facts and rule they were derived from.
- **Decided:** When sources disagree, keep every claim with its source and flag one as the best value; never silently overwrite. Outputs may show the best value alone, or a range with footnotes to each source, depending on format.
- No unsourced analyst estimates.
- **Decided:** No paid or non-redistributable data, in the database or in the workflow.

## Structure (version 1)

**Anchor (decided): the parcel.** Every record is anchored to county parcels (APN + mapped boundary). Parcels exist for all land, including vacant sites with no address yet.

**Record ID (decided):** county code + six-digit sequence, e.g. `SMC-000001` (later `SCC-`, `SF-`). Permanent; never changes as parcels merge, split, or get new APNs.

**Core record: the Housing Record.** It links to:
- **Parcels**: one or many APNs (a group when a project spans several). Links are dated, because lot mergers and splits change APNs over time.
- **Addresses**: one or many (main address, secondary addresses, unit numbers), attached to the record as details, not as the anchor.
- **Facts**: units, unit mix, sizes, etc. Each fact has its own source(s) per §0.
- **Events over time**: entitlement, permit, construction start, completion, lease-up, sale, refinance.
- **Parties with roles**: owner, developer, contractor, architect, lender, equity partner.
- **Sources**: every article, web posting, and public document about the property.

Pipeline and transactions are two views of the same Housing Records, not separate databases.

**Growth model (decided):** Built organically, one verified record at a time. No bulk ingestion or comprehensive research. Paul provides a source; Claude adds or updates the record from it. No history cutoff; coverage is whatever has been sourced.

**Visibility (decided):** Public from the first record, so Paul can share it and get feedback.

**Access (decided):** A public website with a map, plus a downloadable spreadsheet.

**User flow (v1, as described by Paul):**
1. **Link.** Someone receives a shared link and opens it.
2. **Filter.** Property types: drop-down with checkboxes. Area: drop-down of cities or the whole county, or a checkbox for a radius around a specific address.
3. **Map.** An icon for each matching record. Hovering shows a thumbnail popup; clicking it opens the record page.
4. **Record page.** Photo if available, parcel numbers, addresses, and every development fact. Each fact has a clickable link to verify it: the source website, the email of the person who posted it, or a note that it was calculated. Calculated example: one source gives units and total cost, so cost per unit is derived; another gives units and cost per unit, so total cost is derived. The calculation names its inputs.
5. **Record PDF.** Download a PDF of the single record, links included.
6. **Export.** Export the filtered selection in one of three options:
   - Standard: the most common fields
   - Comprehensive: every field
   - Custom: pick categories of fields
   Formats: CSV, Excel, or Google Sheet.
7. **Save (account).** Create a username and password to save searches and custom export field selections.

**Contribution flow (separate workflow, as described by Paul):**
1. The contributor chooses: add a source link, or type information in directly.
2. **Source link** (publicly accessible): can be submitted anonymously.
3. **Typed-in information**: requires registration (email, username, password). The contributor chooses to show their username or an alias. The moderator/owner can verify who they are.

**Owner entries (decided):** Paul, as owner and programmer, feeds the base information. His entries are held to the same accountability: every fact records who entered it (a contributor field), including Paul.

**What the public sees (decided):** A fact backed by a public document shows the document as its source, not who entered it or that Claude extracted it; that would be noise. A fact typed in directly (no document) shows its contributor, because the contributor is the source.

**Edit history (decided):** A deeper layer records the full chain of provenance for everything: who entered each source and each fact, when, and how (e.g., "Paul via Claude"). It is not shown on the record page by default but is kept for every change. Fidelity to everything.

**Build stages (decided):**
- **v1 (stage 1): everything in GitHub, $0, no logins.** Data as JSON text files (`data/records/`, `data/sources/`), PDFs in `archive/`, Python build scripts in `scripts/`, generated site on GitHub Pages with OpenStreetMap. Includes: filters, map, record pages with source links, single-record PDF, export (standard / comprehensive / custom) as CSV or Excel, git edit history, owner data entry via Claude.
  - **Saved searches in v1 without accounts:** (1) every filter and custom-field selection is encoded in the URL, so a link can be bookmarked or shared; (2) a "My saved searches" list stored in the user's browser (that device only).
- **Stage 2: accounts and contributions.** Adds a hosted service (e.g., Supabase) for logins, cross-device saved searches, the public contribution form, moderation, and direct Google Sheet export. Passwords and emails live in that service, never in the repo.

**Source archive and copyright (decided):** Must withstand legal scrutiny; no republishing of copyrighted material.
- Public-domain documents (government records, public agency PDFs): archived copy may be public in `archive/`.
- Copyrighted material (news articles, paywalled content): the public record holds only the link, retrieval date, a short quote, a Wayback Machine snapshot link where available, and a digital fingerprint (SHA-256 hash) of the saved file. The full PDF is stored privately, outside the public repo, for Paul's verification.
- **Decided:** the private archive lives in a separate private GitHub repo (proposed name `SMC_SCC_Housing_Archive`), cloned to `C:\Users\Paul Ring\Documents\GitHub\`.

**Web address (decided):** v1 uses the free GitHub Pages address, `poppr812.github.io/SMC_SCC_Housing_Data`. A custom domain can come later.

**Licenses (decided):** Data under ODbL (Open Database License), so anyone who builds on it must keep their improvements open. Code (website, scripts) under MIT. License files to be added to the repo at build time.

**Property types (decided):** The structure covers all housing types (apartments, condos, townhomes, single-family, etc.). v1 includes a sample record of each type to prove the structure, then goes deep on apartments first. Each type has its own public sources.

## Field ideas (parked until the fields discussion)

Captured as they come up; not a final list.
- Housing type (apartment, condo, townhome, single-family, etc.)
- Affordability: deed-restricted units and their AMI levels, as part of the unit mix
- Population served: senior, student, family, farmworker, educator/workforce, supportive housing, etc.
- Approval type: e.g., by-right/ministerial (SB 35 / SB 423), builder's remedy, density bonus, standard discretionary, specific plan
- Images: 1 to 5 per record, each with its source and credit like any other fact. Clip images from articles as they're processed. **Decided:** news images stay in the private archive; the public site shows only safe images (own photos, public agency documents, developer press kits, openly licensed). Idea: when no safe image exists, show our own rough massing sketch, labeled illustrative. Open: how the sketch is made (see copyright note in chat: derive from public facts, not by tracing a copyrighted photo).
- **Decided:** stick to what's legal for now; no blurred or traced copyrighted images. Frosted-glass styling and massing sketches to be revisited once Paul sees examples.
- **Decided:** image placeholders distinguish two cases: (1) "copyrighted image exists" icon, linking to the source where it can be viewed; (2) "no image available."

## 1. Users and use cases

**First user:** Paul.

**First question:** "Give me the apartment development pipeline for San Mateo County, and separately, sales and refinancings of existing apartments."

This defines two datasets from day one:

| Dataset | What it holds | Stages / event types |
|---|---|---|
| A. Development pipeline | New apartment projects | Approved → Building permit issued → Under construction → In active lease-up |
| B. Existing-asset transactions | Existing apartment buildings | Sale, Refinance |

Open:
- Minimum project size
- Whether condos / for-sale and 100% affordable projects are included
- Lease-up definition
- How far back the transaction history goes
