# PLAN — SMC/SCC Housing Data

Planning log. Decisions are recorded here as they are made; open questions stay marked until answered.

Rollout: San Mateo County → Santa Clara County → San Francisco → full Peninsula.

## Vision

**Thesis (draft, 2026-11-02):** Developing, selling, buying, or investing in real estate in these counties? See what recent projects have been entitled, designed, built, financed, and sold, and who the players are, all from public records.

**Audience = the parties (2026-11-02):** every role in the Parties section is a potential user: developers, owners, architects, engineers, landscape architects, interior designers, contractors, property managers, lenders, equity investors, buyers, sellers, brokers. They'd use it to find comparable projects, see who's active, find business, and see (and help correct) their own projects' records.

**Value proposition (2026-11-02):** It's about people. The database is useful, and can eventually make money, to the extent it helps people do their work: find work for themselves, and make their projects and themselves successful. The data serves that end. (How it makes money is undecided; the data itself stays free and open under ODbL.)

**Marketing theme (draft, 2026-11-02):** "Find your next project and the people behind every deal. If you develop, design, build, finance, buy, sell, or broker real estate in San Mateo and Santa Clara Counties, see who's doing what, from public records." Marketing language, separate from the README's plain description.

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

## Mockup feedback (SMC_Housing_mockup.html, built 2026-10-03)

- 2026-11-02: Graphics and layout approved ("fantastic"). Keep the overall look: filter bar, map with parcel outlines, side list, pop-up record page.
- 2026-11-02: Record page approved: summary sheet layout, sources grouped at the bottom, short S1/S2 tags next to each fact. Pop-up stays; each record keeps its own shareable link.
- 2026-11-02: **Conflicts must be understated, not alarming.** No yellow box, no "under review" or "check flagged" language. The page should read as factual, not as a task list of unfinished work. Display inline, plain text, e.g.: "Lender: possibly Wells Fargo [S3] or U.S. Bank [S1]. See sources below." Same principle for other flags (e.g., Azara's funding-vs-price gap).
  - **Resolution flow:** a viewer who clicks through is asked the specific clarifying question (e.g., "Which bank provided the construction loan?"). If answered and verified, the display updates to e.g. "U.S. Bank [S1], verified by Happy Giraffe on Nov 2. Other sources indicate Wells Fargo involvement [S3]." Contributor answers are stage 2 (accounts/moderation); v1 can route answers by email or GitHub.
  - **A contributor's answer is another claim, not a ruling.** The database collects and presents what each source says; it does not declare a definitive answer. A verified contributor answer is shown alongside the other claims with its attribution, not as the final word.
- 2026-11-02: Image placeholders approved as-is (size, position at top, purple "copyrighted image exists" vs gray "no image available").
- 2026-11-02: Filters: keep the current bar, and add an **advanced filter** that lets people filter on any field however they want. Design to be worked out (open).
- 2026-11-02: **Excel export must open ready to read**, with no reformatting by the user: column widths sized to content, styled and frozen header row, autofilter, wrapped text, number and currency formats, clickable links, and a Sources tab formatted the same way. (Mockup used SheetJS, which can't style; switch to a library that can, e.g. ExcelJS.) Updated mockup with ExcelJS approved 2026-11-02 ("opened well").
- 2026-11-02: Standard export columns (18): record ID, name, housing type, record kind, status, jurisdiction, address, APNs, total units, restricted units, recorded owner, developer, cost-or-price basis, total cost / sale price, per unit (calculated), main lender, latest event date, record link. Loan amounts and the full financing breakdown stay in the comprehensive export.
- 2026-11-02: **Exports carry no per-fact source references** (an Excel cell holds only one link, and the website's S1/S2 labels are per-record, so they'd be wrong in a multi-record sheet). The Sources tab lists every source used with a "Used by" column of record IDs. Revisit later.
- 2026-11-02: **Show menu = filter + color key + counts** (map legend removed). Development pipeline (parent checkbox) with Proposed, Approved, Permitted, Under construction, Lease-up / selling, Inactive; then Sales & refinancings (one checkbox; covers Existing). Counts reflect the other active filters. **Colors** (phase-based, per Paul's milestone sheet): Inactive gray, Proposed yellow, Approved orange, Permitted pink, Under construction green, Lease-up / selling blue, Sales & refinancings purple. Open: a future "Site acquired" status for Paul's phase 1 (land PSA / close).
- 2026-11-02: **Area menu = county > cities tree**, like the Show menu: counties listed only once they have data; caret opens all 20 cities plus "Unincorporated (Community)" entries; county checkbox shows partial when some cities are off; counts beside each. Unincorporated records must name a community from schema.UNINCORPORATED.
- 2026-11-03: **Pipeline Report** (button in the filter bar, free, works with any search boundary or filter): units by stage, expected delivery by year, product type, project list with distance, inactive projects listed outside the totals, and a coverage statement per jurisdiction (schema.COVERAGE; anything unlisted reads as partial). Delivery uses only dates a source states. Shareable with &rep=1. Also fixed record links (#r=), which were lost when the page rewrote its URL on load. Same day: Paul ruled out modeled delivery dates, and the by-year delivery roll-up came out too. Delivery is one more field in the project list, blank unless a source states it; users verify and enter their own in the Excel download's "Your delivery date" column.
- 2026-11-03: **Both counties, state data as the backbone.** Santa Clara County added (SCC- IDs, ###-##-### APNs, county parcel dataset). scripts/import_apr.py merges the state Annual Progress Report rows (Tables A and A2, 2018-2025) into projects of 5+ units and imports those whose parcel checks out against county GIS, with status taken only from what the report states. Doubtful ones go to reference/apr_import_review.csv rather than the database. Each imported record carries a note that it hasn't been checked against the city's list until research clears it. scripts/apply_batch.py applies researched additions and corrections from city lists, funding reports and news. First pass the same night: 841 records. Cities mistype APNs in the state report, so the importer now requires a parcel's situs to match the project address. Records confirmed against a city list lose the "not yet checked" note; schema.COVERAGE names the cities checked. Blocked lists (403) were not worked around.
- 2026-11-04: **Address labels.** Each record has one main address, optional other addresses (real different street addresses), and under each one the other ways sources wrote it ("Also written"). Those variants stay in the data, search and Excel. Numbers one digit apart on the same street are flagged "possibly a typo", not merged. scripts/addresses.py applies this and reruns safely; apply_batch.py and import_apr.py call it.
- 2026-11-04: **One Search area menu** (replaces Search by jurisdiction and Search by boundary). Order: Jurisdiction (expanding row), Draw a radius, Draw a fence, Type an address, Use my location, Clear boundary. Pick a radius merged into Draw a radius: a click gives the default, a drag sets the size. Default radius 1 mile. The radius handle shows its size. A jurisdiction and a boundary stay separate: a boundary pauses jurisdiction picks.
- 2026-11-04: **Archive scope.** The archive backs up facts; it is not a document library. Paul: no whole drawing sets, no downloading everything, storage size matters. scripts/archive.py now skips any document over 25 MB and the source stays cited by its link. The five oversized copies were removed (SRC-000109, 000213, 000217, 001001, 001086); each source now carries `no_copy` with the reason.
- 2026-11-08: **Affordability from the state report; Advanced filters (Paul).** Restricted means deed-restricted at any income level; unrestricted is market, including units a city reports as low or moderate income without a restriction. scripts/apr_affordability.py reads the APR income breakdown (application, entitlement, permit and completion rows; the stage with the most deed-restricted units) and fills restricted_by_ami and affordability_type only where a record has none. "Market (state report)" when no row reports a restricted unit, with a note that a later source overrides it. Not stated fell from 413 to 119 (active projects 148 to 41). Income bands: Low (80% AMI and below), Moderate (81-120%), Workforce (121-200%). Advanced filters panel after Search area, live with a record count: Market/Affordable (synced with the main menu), market inclusionary any/has/none and its bands, affordable income bands (any-of) and tax credits/bonds, product types and stages (synced), units min/max, last movement, delivery year (source-stated, with a no-date toggle), filed or approved since. Search logging waits until the panel closes.
- 2026-11-08: **Market vs Affordable (Paul).** Two buckets, because users look for market comps or affordable comps. Market: up to 25% of units deed-restricted (inclusionary or density bonus), labeled "Market, with inclusionary" when some are. Affordable: more than 25% deed-restricted or applying for tax credits (TCAC source or tax-credit equity); "Affordable, 100%" when only managers' units (3 or fewer) are unrestricted, else the share. "TC/bonds" tag for tax credits or tax-exempt bonds. No "mixed income" label. Stored affordability_type values are unchanged; build.py derives the bucket, using the state report's deed-restricted count when no income breakdown exists. Product types menu leads with Market rate / Affordable / Affordability not stated (413 records). Shown in the report list, summary, Excel and sidebar.
- 2026-11-08: **Archive retest and history rewrite.** All 428 saved copies retested with the honest download: 422 passed, 6 from therealdeal.com refused (403) and were removed (sources keep `no_copy`). Archive history rewritten to drop those 6 and the 5 oversized copies; pack went from 1.18 GB to 465 MB. Backup bundle of the old history: Documents\GitHub\SMC_SCC_Housing_Archive_backup_2026-11-08.bundle. Report files now save as "<4 letters of place> <search> Housing Comps YYYY.MM.DD" (e.g. "Midd 1MR Housing Comps 2026.11.08").
- 2026-11-08: **Update routine.** When Paul says "update it," check everything since the last records commit: the HLC weekly digest (Gmail; leads only, cite the original articles), SF YIMBY, the city project lists in COVERAGE, local news (Almanac, RWC Pulse, Palo Alto Online, Coastside News, SJ Spotlight, Real Deal, SVBJ; Daily Journal and Mercury News block us), and CTCAC/CDLAC awards. Match to existing records first, batch with `--check`, apply, archive new copyrighted sources, build, push. First run: HLC digest Oct 30 to Nov 6 updated 1580 Maple (SMC-000246), Willow Park (SMC-000003), 990 El Camino San Bruno (SMC-000265, now Approved) and 555 Kelly (SMC-000008, preliminary Measure Q count).
- 2026-11-08: **Pipeline report leads with an executive summary.** Order: summary (request, results, product, affordability share of units, bedroom mix where known, sale prices only when 3+ projects have one, then one plain takeaway sentence), a map with numbered pins matching the list and the search area outlined, the project list, inactive projects (not in totals or on the map), and coverage notes. Prices mean recorded sale transactions only. The stage and type tables were folded into the summary.
- 2026-11-04: **Archive honesty.** scripts/archive.py had identified itself as Chrome since 2026-11-02 and fell back to a headless browser when a site refused the download. Both removed: it now names itself, a site that refuses (401, 403, 429, 451) gets no retry and no other route, and pages are printed from the copy already downloaded, fully offline (2026-11-08: no images or scripts fetched; text-first PDFs, smaller and faster). Sites that refuse stay cited by link. Copies saved under the old behavior have not been reviewed.
- 2026-11-03: **San Mateo city is the first complete submarket test.** Every housing project on the city's Current Development Projects list is now a record: 42 pipeline records, 7,397 stated units, up from 10 and 2,609. "Complete" means against that list as of 2026-11-03. The list excludes permit-only work and projects completed or inactive for over five years, and hasn't yet been checked against state housing reports. Weakest record: Peninsula Heights (SMC-000097), where the state's 290 units and YIMBY's 156 units for The Heights aren't linked by any source. Two Fremont records have no unit count (the Daily Journal couldn't be read).
- 2026-11-03: **Image policy: a deliberate exception to "no non-redistributable material", Paul's call.** Project renderings may be shown wherever they were found (city pages, plan sets, press, project sites), because they originate with the developer or architect for publicity. Each is credited to its creator and source and logged like a source, and is removed the same day on request; the site gets a visible "send a better image or ask us to remove it" link. Photographs taken by news outlets, YIMBY, or professional and stock photographers stay link-only unless permission is given. Paul's own photos, permissioned images and free-licensed images are fine. Accepted risk: rights can sit with an architect or rendering studio, so an IP attorney review is still advised.
- 2026-11-03: **Email links work in any browser.** Sign-in switched from PKCE to implicit flow: PKCE links only worked in the browser that requested them, and failed silently elsewhere (phone mail apps). Expired links now show a message; new passwords use a form instead of a browser prompt.
- 2026-11-03: **Weekly report (Admin > Weekly report).** Paul reviews it himself for a while, then hands the routine to an agent. Last 7 days vs the 7 before, excluding admin sessions and local testing: to-review list, traffic, referrers, popular records, addresses, keywords, jurisdictions, no-result searches, every search, exports; database counts, source age, data gaps, quiet records; leads parsed from INTAKE.md at build. No scheduled email yet: that needs a server-side job holding the Supabase secret key.
- 2026-11-03: **Pipeline labels are for comps research, not legal status.** Inactive pipeline (white dot) = a source says withdrawn or denied, or a Proposed/Approved/Permitted record has no recorded movement for over 5 years (applied automatically at build; record shows "No recorded movement since"). Paused or expired approvals stay in the pipeline, because they're still useful competition: Willow Village returns to Approved with a paused note. Existing housing stock (gray dot) = Existing records with no sale or refinance.
- 2026-11-03: **Private archive filled** (scripts/archive.py): 119 copyrighted sources captured to SMC_SCC_Housing_Archive (PDF, HTML, text, meta); PDF fingerprint (sha256) written to each public source. Sites that block automated browsers are printed from the saved page; PDF sources are kept as is; files over 95 MB stay local only (Clearview plan set SRC-000109). Wayback lookups: 136 of 283 sources now have a saved copy date. **Record review:** Belmont Family Apartments to Lease-up / selling (City of Belmont completion post, SRC-001000); 1700 S El Camino parcel confirmed from developer plan set (SRC-001001); 111 Independence listing event reworded, headline-only $13.5M dropped. Open for Paul: Oak Gardens (MidPen page reads as occupied, no announcement), Broadway Meadows (paywalled 2026 article may contradict 2025 permit date), 24 Baytree (only listings; deed search not free online), 1700 S El Camino planning file number (PA-2026-0013 vs -0025).
- 2026-11-02: **Live services set up.** Supabase project housing-comps (org Montara Ventures, free): schema run, Auth URLs (Site URL = GitHub Pages address; redirects for localhost:8781 and Pages), Paul admin. Email: Resend (domain montarav.com verified via DNS records at Network Solutions/Globat: TXT resend._domainkey, CNAME send and rsend), Supabase custom SMTP smtp.resend.com:465 from "Housing Comps <noreply@montarav.com>". Password-reset email tested OK.
- 2026-11-02: **Accounts build (Supabase project housing-comps).** scripts/supabase.sql holds the schema: profiles, saved_searches, contributions, activity; row-level security (users see only their own; activity and all contributions readable only by is_admin); sign-up trigger copies name/alias/company/role into profiles. Site: Sign in / Create account (email + password, sign-in link, password reset), privacy note (footer + sign-up checkbox), saved searches in the account (old browser-saved ones move in once), "Add or correct info" (header, record page, Know more?) into a review queue, export limits for signed-out visitors, activity log (visit, search, record view, export, save, contribute, sign in/out; visitors by random browser ID), Admin view for Paul (KPIs, contributions with status, accounts with usage counts, activity, Excel download).
- 2026-11-02: **Public name: Housing Comps.** Site title, header, export file names (housing_comps_...) and workbook creator use it. Supabase: organization "Montara" (Company), project "housing-comps". Repo name unchanged for now.
- 2026-11-02: **Accounts and capture (next build, Supabase free tier).** Two tiers: anyone browses free; an account (email or Google, optional public alias) is needed to save searches and contribute. Contributions (source link, free-text facts, contributor identity, "public and mine to share" checkbox) go to a moderation queue; Paul approves before anything becomes a claim. Activity log for Paul only: logins, records viewed, searches and areas run, exports. Privacy notice at sign-up. **Export limits without an account:** Standard comp table up to 20 records; Comprehensive/Custom (with source references) up to 5 records; above that, sign in. (The data stays open under ODbL; the limit is a sign-up prompt, not a lock.)
- 2026-11-02: **Standard export = clean comp table**: Name (links to the record), Units, Value per unit, Value basis (Sale price / Dev. cost), Pipeline status (pipeline records), Transaction + Transaction date (latest sale or refinance), Distance (mi) from the search-area center when a radius is set (sorted nearest first). Bottom rows: Average, Minimum, Maximum as live Excel formulas; a note names the distance center. CSV gets the same summary rows as values.
- 2026-11-02: "Select area" renamed **Search area**. Menu order: Pick a point (click the map) / type an address or coordinates + radius + Go / Use my location / Draw a radius / Draw a fence / Clear search area. The miles box sets the radius for pick, address and GPS.
- 2026-11-02: Show menu: "Sales & refinancings" becomes **Transactions** with two sub-checks, **Sales** and **Refinancings** (from Sale / Refinance events). Exports: money facts with one value (or a flagged best) and all calculated values are plain dollar numbers usable in formulas; each per-unit / per-sf column sits right after its total (cost after Total development cost, price after Sale price).
- 2026-11-02: **Coordinates and GPS** in Select area: the address box also takes lat/long (`37.5630, -122.3255`, or a pasted Google Maps link with `@lat,long`); "Use my location" centers the radius on the device GPS (browser asks permission); the radius center is a draggable pin; the button and menu show the center coordinates (4 decimals) next to the address.
- 2026-11-02 (supersedes the map toolbar below): **"Select area" dropdown** in the top bar, Photoshop-style: (1) From an address: address box, "Pick point on map" (fills the address by reverse lookup), miles (default 10); (2) Draw a radius: press at the center and drag outward; (3) Draw a fence: click points, close on the first point or double-click; Clear. Button shows what's active ("10 mi from …", "2.5 mi radius", "Fence (4 points)"). The on-map toolbar is removed; right-click shortcuts stay. **Any selected area replaces the Area picks:** while active, the Area menu is greyed with a note and reads "Paused (selected area)"; Clear restores the city picks.
- 2026-11-02: **Map tools** (standard navigation untouched: drag pans, scroll/pinch/double-click zoom): toolbar under +/− with ◯ Radius (click a point; miles box sets size, default 10; drag center to move, edge to resize), ⬠ Draw boundary (click points; click first point or double-click to close), ✕ Clear. Right-click shortcut: "10-mile radius here", "Start a boundary here". Esc cancels. Radius-from-address box feeds the same radius. Shapes are saved in links and saved searches. Future: default to a radius when the database is large.
- 2026-11-02: Product types menu shows counts under the current selection; short display names (Condos, Mixed) in the menu, button, and list; data labels unchanged. Results header shows total units, e.g. "24 records match (11,177–11,717 units)": a range when sources disagree on some unit counts; records with no unit count are left out of the total.
- 2026-11-02: Map hover card approved as-is (image box, name, place, units, status).
- 2026-11-02: **Mockup phase complete.** Next: parcel data, then record fields.
- 2026-11-02: Map shows only parcels that have records (as in the mockup); no county-wide parcel layer. **Purpose clarified:** the site is for researching related product types and competitive projects, not for retrieving parcel maps. Parcels anchor records; they aren't a product feature.
- 2026-11-02: Empty field wording: "No current report logged".
- 2026-11-02: Calculated values approved: small "calculated" tag plus the math on one gray line. Drop the "Inputs are sourced above" sentence.

## v1 build (started 2026-11-02)

- `data/records/SMC-######.json`: one file per record, per FIELDS.md
- `data/sources/SRC-######.json`: one file per source; records cite these IDs; each record page renumbers them S1, S2…
- `scripts/schema.py`: field registry (labels and definitions); `scripts/template.html`: the site; `scripts/build.py`: validates every record and writes `docs/`
- Run `python scripts/build.py` after any data change; it stops with a list of problems if a record breaks the rules (missing source, undefined label, bad APN, etc.). Stdlib only, no pandas.
- GitHub Pages serves `docs/` from `main`. Excel export is built in the browser (ExcelJS).
- Conflicting financing entries share a `group` (with a clarifying question); conflicting facts have multiple claims and optional `best`; complementary claims use `combine`.
- "Reported financing total" excludes short-term loans (construction, bridge, predevelopment) so construction and permanent money isn't double-counted.

## Fields

- **2026-11-02: Categories with defined labels, plus project notes.** Records use categories (starting with core product types), and each label needs a written definition. Terms like wrap vs. flat vs. podium mean different things to different people, and those projects still compete, so construction details (wood frame, metal stud, podium, Type V / III / I, etc.) are not categories. They go in a **Construction notes** section on the project, sourced, and keyword-searchable.

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
