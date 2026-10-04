# RUNBOOK — San Francisco housing stock & development activity tracker

**Purpose of this file.** Load it into any future session (Claude or another assistant) together with `SF_Housing_Stock_and_Pipeline_YYYY-MM.xlsx`, `SF_Housing_Brief_YYYY-MM.html`, and the `build_scripts/` folder. It contains everything needed to update those two deliverables without re-deriving the brief: what the task is, the decisions already made, where the data comes from and how it was accessed, how rows were built, and the exact update procedure. It is not a summary of findings; findings live in the HTML and the workbook.

Owner: Paul (RaaP, raap.builders). First built: 2026-09-09. Last data snapshot: SF Planning Pipeline Report 2026 Q2; Housing Inventory 2025 (published April 2026); MOHCD Affordable Housing Pipeline modified 2026-02-05.

---

## 1. Task definition

Produce and maintain a summary of San Francisco's housing stock and housing development activity (approved, under construction, delivered), delivered as three artifacts:

1. **HTML brief** — standalone downloadable `.html` with inline SVG charts and tables (no external data dependencies; Google Fonts link is optional with system fallback). Delivered as a file, not published.
2. **Excel workbook** — the data store with row-level source links so it can be refreshed later.
3. **This runbook** — task, methodology, update process.

### Decisions already made by the owner (do not re-ask)

| Question | Decision |
|---|---|
| Format | HTML brief + Markdown runbook + Excel data file with source links |
| Pipeline depth | Citywide totals in the brief; rows tagged with neighborhood and affordability wherever the source provides it |
| Delivered window | 3-year trend, 2023–2025, plus 2026 year-to-date; project-level detail for completions 2023 through 2026 |
| Modular/FBH lens | None. Plain market summary |
| Size buckets | ≤4, 5–10, 11–20, 21–50, 51–250, 251+ total units (owner wrote "=<4, =<10, =<20, =<50, =<250, >250") |
| Stock detail | Product type (building type) and age of stock |
| Policy context | None (no RHNA/Housing Element narrative; RHNA appears only as a single data row) |
| Project types | All housing: residential, mixed-use, senior, student, group housing, hotel-to-housing, SRO, rehab/preservation |
| Project-level fields | developer, contractor, architect, project name, address, project cost, equity partners + equity $, lenders + loan $, affordable units, affordability mix with unit counts and AMI levels |
| Project threshold | All projects available in pipeline data (see §4 coverage caveat) |
| Research depth | Research capital-stack details on larger projects before delivering |
| Market benchmarks | None (no cost/unit, rent, or price benchmarks) |
| ADUs | Fold into totals; do not break out |
| Supervisor District | Not required; captured where MOHCD provides it |
| Workbook structure | One row per project on a single `Projects` tab |
| Source links | Both: row-level URL column plus a `Sources` tab with dataset info and retrieval date |
| Affordability mix | Single text cell, e.g. `20 @ 50% AMI; 15 @ 80% AMI` |
| Equity/lenders | Separate columns: Equity Partners, Equity $, Lenders, Loan $ |
| Unpopulated fields | Leave blank (no "not found" markers) |
| Summary formulas | `Summary` tab with COUNTIFS/SUMIFS that recalc from `Projects` |
| Status | Both a raw status column (source wording) and a normalized status column |
| Update playbook | Yes, `How_to_update` tab in workbook (mirrored and expanded in §6 here) |
| HTML vs Markdown | HTML is a standalone brief with charts and tables; Markdown is this runbook |
| HTML delivery | Downloadable `.html` file |

---

## 2. Deliverable specifications

### 2.1 Workbook `SF_Housing_Stock_and_Pipeline_YYYY-MM.xlsx`

Tabs, in order: `README`, `Summary`, `Stock`, `Trend`, `Pipeline_Q2_2026` (rename to current quarter on update), `Projects`, `Sources`, `How_to_update`. Font Arial 10 throughout; header rows navy fill `#1F3A5F`, white bold text.

**Projects tab columns (A–Z), in this exact order:**

| Col | Header | Notes |
|---|---|---|
| A | Project ID | Prefix scheme: `C23-`/`C24-`/`C25-`/`C26-` completions by year; `U-` under construction; `PM-` permitted; `A-` approved; `F-` filed/pre-development; `MP-` multi-phase remainder |
| B | Project Name | Common name + address hint |
| C | Project Address | |
| D | Analysis Neighborhood | SF Planning 41 Analysis Neighborhoods (MOHCD "City Analysis Neighborhood" / pipeline `NHOOD41`) |
| E | Supervisor District | text "1"–"11" |
| F | Status (raw, source) | Source wording + date, e.g. `Construction - FCD issued Jun 2025 (MOHCD)` or `Approved Oct 8, 2025 (HI 2025 A-3)` |
| G | Status (normalized) | One of exactly: `Complete`, `Under Construction`, `Permitted`, `Approved`, `Under Review`, `Major Multi-Phase (remaining)` — Summary formulas match on these strings |
| H | Project Type | free text: 100% Affordable (family/senior/PSH), Mixed-Income, Mixed-Use, Residential High-Rise, Group Housing, SRO, Adaptive Reuse, Rehab, Student Housing, Major Multi-Phase, etc. |
| I | Tenure | Rental / Ownership / Mixed / blank |
| J | Total Units | integer; includes manager units |
| K | Affordable Units | integer; excludes manager units (MOHCD convention); blank if unknown |
| L | Affordability mix (units @ AMI) | text `n @ x% AMI; ...`; for Housing Inventory rows use the four HI bands (Ext. Low ≤30, Very Low ≤50, Low ≤80, Moderate ≤120) |
| M | Size Bucket | **formula**, do not type: `=IF(J="","",IF(J<=4,"≤4",IF(J<=10,"5–10",IF(J<=20,"11–20",IF(J<=50,"21–50",IF(J<=250,"51–250","251+"))))))` — the last label must not start with `>` (SUMIFS reads it as an operator) |
| N | Developer / Sponsor | MOHCD "Project Lead Sponsor"; pipeline `SPONSOR`; press |
| O | Co-developer / Partner | |
| P | General Contractor | |
| Q | Architect | |
| R | Total Project Cost ($) | number, `$#,##0`; yellow fill if analyst estimate |
| S | Equity Partners | LIHTC investor/syndicator, JV equity, philanthropic funds |
| T | Equity $ | number |
| U | Lenders | construction/perm lenders, city/state loans, bond issuer/purchaser |
| V | Loan $ | number (largest single loan or bond cap; describe in Notes if multiple) |
| W | Est./Actual Completion | text (month/year) |
| X | Year Completed | integer, only for Complete rows (Summary section E sums on this) |
| Y | Notes / Milestones | approvals, authorizations, prior unit counts, caveats |
| Z | Source URL | one URL per row; hyperlinked |

Freeze panes at C2; autofilter on the header row; wrap text.

**Summary tab sections** (all formulas use whole-column refs so appended rows are picked up automatically):
- A. Official citywide figures (hard-coded from reports, with "as of" and source columns) — 19 rows.
- B. Tracked projects by normalized status: `COUNTIFS(Projects!G:G, status)`, `SUMIFS(Projects!J:J, ...)`, `SUMIFS(Projects!K:K, ...)`, share.
- C. Units by size bucket × status: `SUMIFS(Projects!J:J, Projects!M:M, bucket, Projects!G:G, status)`.
- D. Project counts by size bucket × status: `COUNTIFS`.
- E. Completions tracked by Year Completed vs official HI figures (2023: 2,059 new-construction / 946 affordable; 2024: 1,457 / 1,115; 2025: 2,406 / 1,758; 2026 H1: 405 / —).
- F. Non-complete units by Supervisor District.

**Stock tab:** A) citywide stock by building type, 2024 restated and 2025 (HI 2025 Table 1), with superseded 2023/2024 rows from HI 2024 kept for reference; B) tenure, vacancy, age (HUD CMAR + ACS), SRO rooms, condos, ADUs; C) 41 Analysis Neighborhoods × building type, 2025 total, 2025 net gain, 2025 new-construction units (HI 2025 Tables 27–28) with a citywide SUM check row.

**Trend tab:** HI 2025 Table 2 (2006–2025: authorized, new construction, demolished, alterations, net) + 2026 H1 row + 10-yr average formulas; Table 13 (new units by building type 2021–25); Table 23 (affordable by income level 2021–25, with share formula); Table 24 (affordable by source); Table 4 (authorized by building type); Table 3 (filed/approved).

**Pipeline tab:** seven stage rows + total + affordable, share formulas; 14 multi-phase projects with remaining units and master developer; density-bonus note.

**Sources tab:** ID, source, publisher, URL (hyperlinked), retrieved date, covers, refresh cadence. IDs S1–S21 as of first build.

### 2.2 HTML brief `SF_Housing_Brief_YYYY-MM.html`

Single file, inline CSS and SVG, no JavaScript. Generated by `build_scripts/build_html.py` from the same `data.py` plus hard-coded citywide series. Structure and content:

1. Kicker line (snapshot dates) and a one-sentence headline stating stock, last-year net add, pipeline total, and under-construction count.
2. Lede paragraph: last full-year completions vs 10-yr average, affordable share, current-year H1 completions, under-construction trend (vs 5 years earlier), entitled-unpermitted count.
3. **Housing stock**: stat strip (total units, renter share, median year built, vacancy, SRO rooms); two charts — units by building type (horizontal bars with share) and age of stock; short paragraph incl. condos and ADUs.
4. **Production trend**: grouped vertical bars 2006–latest (new construction vs net change); table 2023–current H1 (new construction, net, affordable + share, authorized, approved); stacked bars affordable vs market-rate 2021–latest with share labels; top-10 neighborhoods by net gain (horizontal bars).
5. **Pipeline**: paragraph; horizontal bars by stage with share (darker = permits in hand); multi-phase remaining-units bars; tracked-projects-by-size-bucket bars.
6. Table: largest projects under construction (≥60 units) with developer/partner, GC, architect, total cost, equity/lenders, est. completion.
7. Table: largest approved projects without permits (≥300 units, excluding multi-phase rows).
8. Table: all tracked completions 2023–current, sorted by year desc then units.
9. "What to watch" paragraph (financing of entitled units, pending policy that changes economics, MOHCD affordable UC count) and companion-file note.

Design tokens: ink `#1C2430`, navy `#17304F` (market-rate/total), gold `#D9A21B` (affordable), teal `#1B7F8C` (secondary), gray `#8A93A0`, rule `#DDE3EA`, background `#F6F7F4`; IBM Plex Serif for headings, IBM Plex Sans for body (Google Fonts, with system fallback). Charts are built by three Python helpers in `build_html.py`: `bars_vertical`, `hbars`, `stacked`.

### 2.3 Build scripts (`build_scripts/`)

- `data.py` — the 265 project rows as a Python list `R` (helper `P(...)` with keyword args), the 14 multi-phase tuples `MP`, source URL constants, and the column list `COLS`. **This is the master copy of the project data.** Edit here, then rebuild both files. If a future session only has the xlsx, treat the `Projects` tab as master and regenerate `data.py` from it (read with openpyxl, `data_only=True` after recalculation).
- `build_xlsx.py` — writes the workbook (openpyxl), then run `recalc.py` (LibreOffice) to compute formulas; must report `total_errors: 0`. If LibreOffice is unavailable, skip recalc — Excel recalculates on open.
- `build_html.py` — writes the HTML; hard-coded citywide series in this file (`years`, `comp`, `net`, stock bars, age bars, `pipe`, affordable stacked series, neighborhood top-10) must be updated by hand when the Housing Inventory or Pipeline Report changes.

Run order (from the `build_scripts` folder; scripts write to `/mnt/user-data/outputs/` — change the output paths at the bottom of each script to your local folder): `python3 build_xlsx.py && python3 build_html.py`. Requires `openpyxl`.

---

## 3. Data sources and access notes

| ID | Source | URL | What it gives | Access notes / gotchas |
|---|---|---|---|---|
| S1 | SF Planning **Housing Inventory** (annual, ~April 1) | https://sfplanning.org/project/housing-inventory ; 2025 PDF: https://sfplanning.org/sites/default/files/resources/2026-04/2025_Housing_Inventory.pdf | Stock by building type (Table 1), 20-yr trend (Table 2), filings/approvals (T3), authorizations by type (T4), ADUs (T9), new units by type (T13), condos (T16), SROs (T20), affordable by AMI (T23) and by source (T24), neighborhood production (T27) and stock (T28); Appendix A-1 (market-rate completions ≥10 units, with inclusionary count), A-2 (affordable completions ≥20 units with AMI bands), A-3 (approvals ≥20 units with case descriptions), A-4 (filings), A-5 (authorized ≥10 units), A-6 (density bonus), A-7 (MOHCD pipeline) | PDF is ~90 pages; text extraction works. Appendices start ~page 57. Each new report restates prior years (2024 stock was 417,824 in HI 2024, 420,289 in HI 2025) — always take the whole series from the newest report. Building-type split was re-based in HI 2024 (Census 2020 + ACS ratios); HI 2023 single-family figure (122,816) is not comparable. |
| S2/S3 | HI 2024, HI 2023 | https://sfplanning.org/sites/default/files/resources/2025-04/2024_Housing%20Inventory.pdf ; https://sfplanning.org/sites/default/files/resources/2024-04/2023_Housing_Inventory.pdf | 2024 and 2023 A-1/A-2 completion lists, A-3, A-5 | Already harvested into `data.py`; only needed if re-verifying. |
| S5 | SF Planning **Pipeline Report** (quarterly) | https://sfplanning.org/project/pipeline-report ; 2026 Q2 PDF: https://sfplanning.org/sites/default/files/documents/reports/Housing_Production_Development_Pipeline-2026Q2.pdf | Stage totals (7 buckets), affordable total, list of 14 major multi-phase projects with remaining units | Page text has the summary; PDF has the same plus charts. Definitions: "Construction" = full BP issued OR site permit + approved first construction document; "BP Issued" = site permit only (not RHNA-countable). |
| S6 | DataSF **San Francisco Development Pipeline** (dataset `6jgi-cpb4`, replaces `k55i-dnjd`) | https://data.sf.gov/d/6jgi-cpb4 ; CSV: https://data.sf.gov/api/v3/views/6jgi-cpb4/export.csv?accessType=DOWNLOAD ; data dictionary: https://sfplanninggis.s3.amazonaws.com/SF+Quarterly+Developement+Pipeline+Data+Definition+12212023.xlsx | Row-level pipeline: `NAMEADDR`, `current status` (PL Filed / PL Approved / BP Filed / BP Approved / BP BP Issued / Construction), `net pipeline units`, `pipeline affordable units`, `bmr units ex low/very low/low/moderate`, `affordability type`, `tenure type`, `case no`, `SPONSOR`, `CONTACT`, `NHOOD41`, `SD22`, `zoning district`, `planning area`, lat/long | **Large** (thousands of rows, most non-residential or 0 net units; ~20 MB with descriptions). Could not be pulled through the assistant's fetch tool in the first build — download locally, filter `net pipeline units > 0`, then paste/append. Snapshot updates quarterly (2026 Q2 posted 2026-08-28). Previous quarters are retired from the portal; request from ken.qi@sfgov.org. |
| S7 | DataSF **MOHCD/OCII Affordable Housing Pipeline** (`aaxw-2cb8`) | https://data.sfgov.org/Housing-and-Buildings/Affordable-Housing-Pipeline/aaxw-2cb8 ; CSV: https://data.sfgov.org/api/views/aaxw-2cb8/rows.csv?accessType=DOWNLOAD | ~300 rows: Project ID, name, Project Status, Construction Status (0–5), address, SD, Analysis Neighborhood, lead agency, program, multiphase name, project type, tenure, NTP/BP/FCD/start/completion dates, Lead Sponsor, Co-Sponsor, Owner, planning case, entitlement date, Section 415 declaration, total units, MOHCD affordable units, bedroom mix, population set-asides (senior, TAY, homeless, LOSP, public-housing replacement), unit counts at 20/30/40/50/55/60/80/90/100/105/110/120/130/150% AMI and undeclared | CSV is small enough to fetch (~170 rows captured in first build before truncation; re-pull fully). Construction status codes: (0) Multiphase before predevelopment, (1) Preliminary, (2) Predevelopment Feasibility, (3) Design with Entitlements Approved, (4) Site Work Permit Issued, (5) First Construction Document Issued. Est. completion dates are frequently stale — flag when in the past. |
| S8 | SF Planning **Housing Dashboard** (Power BI) | https://sfplanning.org/san-francisco-housing-dashboard | Completed units since 2005 and active pipeline by geography/affordability/project type; year-to-date completions | Not machine-readable via fetch; read visually or use S9. |
| S9 | DataSF **Dwelling Unit Completion Counts by Building Permit** (`j67f-aayr`) | https://data.sfgov.org/Housing-and-Buildings/Dwelling-Unit-Completion-Counts-by-Building-Permit/j67f-aayr | Monthly completions by permit/address | Use for current-year YTD completions and to confirm 2026 rows. |
| S10 | The Frisc, "SF Has Built Only 400 Homes This Year…" (Jul 2026) | https://thefrisc.com/sf-has-built-only-400-homes-this-year-tens-of-thousands-more-are-waiting/ | 405 units H1 2026; UC 3,300 vs 4,545 five years ago; permits-not-yet-filed 9,477 vs 448; MOHCD ~2,000 affordable UC, 1,139 due 2026 | Journalism; replace with dashboard numbers when possible. |
| S11 | SF Chronicle, "More homes are entering S.F.'s pipeline" (Apr 2026) | https://www.sfchronicle.com/realestate/article/sf-homes-built-22208676.php | 2025 filings context | |
| S12 | HUD **Comprehensive Housing Market Analysis**, SF-Redwood City-SSF (2024) | https://www.huduser.gov/portal/publications/pdf/CMARtables_SanFranciscoRedwoodCitySouthSanFranciscoCA_24.pdf | Inventory 420,800; occupied 380,400; owner 32.6% / renter 67.4%; vacant 40,450 (SF submarket, "current") | Irregular publication. |
| S13 | Census ACS (5-year), San Francisco County | https://data.census.gov (table DP04); secondary views used: https://censusreporter.org/profiles/16000US0667000-san-francisco-ca , Social Explorer, NeighborhoodScout | Median year built 1944; pre-1940 45.4%, 1940–69 24.7%, 1970–99 16.3%, 2000+ 13.6%; single-unit 30.9% / multi-unit 68.9%; for-rent 26.5% / for-sale 2.5% of vacant | First build used secondary compilations; replace with DP04 directly (ACS 1-year, released ~September; 5-year ~December). |
| S14 | **CTCAC/CDLAC staff reports** | https://www.treasurer.ca.gov/ctcac/ (meeting → staff reports by project number) | Federal/state LIHTC annual credit, tax-exempt bond cap, applicant LP, developer, bond issuer, private-placement purchaser (lender), investor/consultant, unit/AMI mix, construction dates | Search pattern: `"<address>" CTCAC staff report` or `treasurer.ca.gov ctcac "<project name>"`. Examples harvested: CA-23-567 (Transbay 2W), CA-23-638 (Transbay 2E), CA-24-535 (1515 SVN), CA-24-670 (Balboa E). |
| S15 | **MOHCD Citywide Affordable Housing Loan Committee** agendas and loan evaluations | https://www.sf.gov (search "Citywide Affordable Housing Loan Committee meeting <month year>") | City gap/predevelopment/permanent loans, LOSP contracts, TDC, sponsor, GC when named | Monthly meetings; evaluation PDFs give full sources & uses. |
| S16 | **CalHFA Mixed-Income Program** staff reports | https://www.calhfa.ca.gov/multifamily/mixedincome/approved/ | Conduit bond amounts, borrower, developer for mixed-income deals (e.g., 1101 Sutter) | |
| S17 | **SF YIMBY** | https://sfyimby.com (search address) | Architect, GC, cost estimates from permits, unit mix, milestones | Best single source for GC/architect on market-rate projects. |
| S18 | **SF.gov press releases** (groundbreakings/openings) | https://www.sf.gov/news | TDC, lenders, partners, AMI ranges for affordable projects | Search `site sf.gov "<address>" groundbreaking`. |
| S19–21 | CoStar (Quincy), SF Chronicle (300 De Haro), Chinatown CDC "In Development" page | https://www.costar.com/article/147377327 ; https://www.sfchronicle.com/realestate/article/sf-housing-affordable-apartments-20816373.php ; https://www.chinatowncdc.org/our-housing/in-development | Developer, lease-up, cost/unit, GC/architect/TDC | Nonprofit developer websites (CCDC, TNDC, Mercy, MEDA, BRIDGE, MidPen) list GC/architect/TDC for their projects. |

Other useful but not yet used: SF Business Times (lenders on market-rate deals, paywalled); MOHCD Affordable Housing Pipeline flyer (https://sfplanning.org/sites/default/files/documents/citywide/ahlc-pipeline-flyer-2025.pdf); OCII project pages for Transbay/Mission Bay/Shipyard; CTCAC "project status" reports for placed-in-service dates.

---

## 4. Methodology

### 4.1 Coverage rule for the Projects tab
Include: every project ≥10 units in HI Appendices A-1/A-2 (completed), A-3 (approved), A-4 (filed), A-5 (authorized) for 2023–2025; every row in the MOHCD Affordable Housing Pipeline (100% affordable, inclusionary, OCII, rehab/preservation); named market-rate projects with public coverage; the 14 multi-phase master plans as single "remaining units" rows. Small projects and ADUs are intentionally excluded from itemization (they are folded into citywide totals from HI) — the DataSF pipeline CSV is the path to add them (§6 step 4).

### 4.2 Deduplication
One row per project regardless of how many milestones it hit. When a project appears in multiple years/tables (e.g., 730 Stanyan: authorized 2023, approved 2024, completed 2025), keep the most advanced status, put earlier milestones in Notes, and use the latest unit count. Match on address (normalize "ST/St", "AVE/Av") and planning case number. Multi-year TCOs: HI credits partial units per year (e.g., 921 Howard 195 of 203 in 2023); the row carries the full project unit count and Year Completed = year of first substantial TCO; note the split.

### 4.3 Status normalization

| Source status | Normalized |
|---|---|
| HI A-1/A-2 listed; MOHCD "Completed"; TCO/CFC issued | Complete |
| MOHCD (5) First Construction Document Issued; pipeline `Construction`; HI A-5 authorized with confirmed start | Under Construction |
| MOHCD (4) Site Work Permit Issued; pipeline `BP BP Issued` | Permitted |
| MOHCD (3) Design with Entitlements Approved; pipeline `PL Approved`, `BP Filed`, `BP Approved`; HI A-3 approved | Approved |
| MOHCD (0)–(2); pipeline `PL Filed`; HI A-4 filed | Under Review |
| Pipeline Report multi-phase list | Major Multi-Phase (remaining) |

Priority when sources conflict: MOHCD construction status (most current for affordable) > DataSF pipeline `current status` > HI appendix > press. Record the source used in column F.

### 4.4 Unit counts and affordability
- Total Units = gross units incl. manager units. Affordable Units = deed-restricted units excl. manager units. For HI market-rate rows, Affordable = inclusionary on-site units from A-1.
- Affordability mix cell: MOHCD AMI columns → `n @ x% AMI` joined with `; `, drop zeros, append set-asides (`; 40 LOSP`, `; 30 PSH units`) when material. HI rows: four bands. Inclusionary projects that have not declared method: leave mix as "Inclusionary TBD".
- Density-bonus and revised projects: use the latest approved count; put prior counts in Notes.

### 4.5 Capital stack research recipe (per project, larger projects first)
1. `"<address>" CTCAC staff report` → LIHTC $/yr, bond cap, bond issuer, private-placement purchaser (= lender), investor/consultant, developer LP.
2. `"<address>" loan committee sf.gov` → city loans (predevelopment, gap, construction, perm), LOSP, TDC, GC if named.
3. `"<address>" sfyimby` → architect, GC, permit cost estimate, milestones.
4. `site:sf.gov "<address>" groundbreaking OR opens` → TDC, construction lender (e.g., "Bank of America"), partners.
5. For mixed-income/market-rate: `"<address>" CalHFA` (MIP), `"<address>" construction loan` (Business Times/Real Deal/Bisnow), developer website.
6. Enter dollar figures as numbers; put descriptions in the text columns; leave blank if nothing found. Mark analyst estimates (e.g., cost derived from a stated $/unit) with yellow fill and say so in Notes.

### 4.6 Citywide figures
Never computed from the Projects tab. Always hard-coded from HI (stock, trend, affordable) and the Pipeline Report (stages), with "as of" and source columns. The Projects-tab totals are a tracked subset and are labeled as such.

---

## 5. State at last build (so a future session knows what exists)

- Projects tab: 265 rows. By normalized status: Complete 44 rows / 6,022 units (2023: 15 rows; 2024: 8; 2025: 21; 2026 H1: 2 scheduled — verify); Under Construction 35 / 3,544; Permitted 36 / 3,127; Approved 100 / 29,126; Under Review 36 / 9,229; Multi-phase 14 / 40,479 (multi-phase rows total 40,479 vs Pipeline Report 37,577 because `data.MP` was entered from the report but Summary also counts three master-plan rows in Approved; do not double count when quoting).
- Capital stack populated for: 300 De Haro, 1101 Sutter, Transbay 2 East and 2 West, 1515 South Van Ness, Balboa Reservoir E and A, 730 Stanyan, 1633 Valencia, 850 Turk (partial), 88 Bluxome (site history), Quincy/555 Bryant (developer/architect/land price). All other rows: developer/sponsor from MOHCD or HI where available; GC/architect/cost/equity/lender blank.
- Known gaps to fill on next pass: 2024 completions' developers (400 China Basin, 4840 Mission co-dev confirm); market-rate lenders generally; 2026 H1 project-level completions (only two MOHCD-scheduled rows entered); DataSF pipeline small projects; 15 Marina Blvd approval status (Chronicle reported approval Apr 2026; HI 2025 lists as filed).
- Official series entered: HI 2025 Tables 1–4, 9, 13, 16, 20, 23, 24, 27, 28; Pipeline Report 2026 Q2 stages and multi-phase list; HUD CMAR 2024; ACS 5-yr (secondary).

---

## 6. Update procedure

Perform in this order. Each step names the tab/file it changes.

**Step 0 — Load.** Read this runbook, open the xlsx (`Projects` tab is the master row store if `build_scripts/data.py` is missing), and the HTML. Note the last snapshot dates in the kicker line and in `Sources!Retrieved`.

**Step 1 — Quarterly: Pipeline Report.** Fetch https://sfplanning.org/project/pipeline-report. Update `Pipeline_Q2_2026` tab (rename to the new quarter): seven stage values, total, affordable units, the 14 multi-phase remaining counts (add/remove projects if the list changed). Update `Summary` section A rows for pipeline. In `build_html.py` update `pipe`, `data.MP`, the pipeline paragraph numbers, the headline, the lede, and the kicker date.

**Step 2 — Quarterly: DataSF pipeline row-level (`6jgi-cpb4`).** Download CSV locally (too large for in-chat fetch). Filter `net pipeline units > 0`. Map `current status` per §4.3. For rows already in Projects (match on address / case no), update columns F, G, J, K, L, N. For new rows, append with next ID in the appropriate prefix series. This is also the only source for sub-10-unit projects if the owner wants them itemized.

**Step 3 — When modified: MOHCD Affordable Housing Pipeline (`aaxw-2cb8`).** Check "Last Updated" on the dataset page. Download CSV (fits in fetch). Key on `Project ID` (kept in Notes/Source where used) or address. Update construction status (0–5 → normalized), FCD/completion dates, sponsor/co-sponsor, AMI mix (rewrite column L), set-asides. Any project with status (5) and an estimated completion in the past → check S9/S8; if completed, set G = Complete, X = year, move ID to `C<yy>-` series.

**Step 4 — Annual (April): Housing Inventory.** Download the new PDF from S4. Replace the entire series in `Stock` A (Table 1, both years), `Stock` C (Tables 27–28), `Trend` (Tables 2, 3, 4, 13, 23, 24), `Stock` B rows for SROs (T20), condos (T16), ADUs (T9). Update `Summary` A rows (total units, net added, new construction, authorized, approved, filed, affordable, RHNA). Add completion rows from A-1 (≥10 units, with inclusionary count) and A-2 (≥20 units, AMI bands) as `C<yy>-nn`, Status Complete, Year Completed = report year; merge with existing rows where the project was already tracked. Add A-3 approvals and A-4 filings ≥20 units not already present. Update `Summary` E official figures for the new year. In `build_html.py` extend `years/comp/net`, the stacked affordable series, the neighborhood top-10, stock and age bars, the 3-year table (drop the oldest year so the table stays 3 full years + current H1), and all prose numbers.

**Step 5 — Monthly: current-year completions.** From S9 (or S8), sum units completed YTD; update `Summary` A "Units completed <year> H1/YTD", `Trend` current-year row, and the HTML lede/table. Add ≥10-unit completions as `C<yy>-` rows.

**Step 6 — Per milestone: capital stack.** For any row that changes to Under Construction, or any Approved row ≥100 units, run §4.5 and fill R–V. Priority order: largest units first.

**Step 7 — Annual (September/December): ACS/HUD.** Replace `Stock` B tenure/vacancy/age values from data.census.gov DP04 (ACS 1-year, San Francisco County) and any newer HUD CMAR. Update HTML stat strip and age chart.

**Step 8 — Rebuild and verify.** If using the scripts: edit `data.py` (or regenerate it from the Projects tab), run `build_xlsx.py`, run `recalc.py` if LibreOffice is available and confirm `total_errors: 0` and that Summary B totals equal the Projects row count; run `build_html.py`; render a couple of SVGs to PNG (cairosvg) to eyeball. If not using scripts: edit the xlsx directly (column M formula copies down automatically only if pasted — re-fill it for new rows), and edit the HTML tables by hand. Bump file names to the new `YYYY-MM`, update `Sources!Retrieved`, update the HTML kicker, and update §5 of this runbook.

**Step 9 — Sanity checks before delivering.**
- `Summary` B total rows = number of Projects rows.
- `Stock` C citywide check row equals `Stock` A 2025 (or newer) total.
- No normalized status outside the six allowed strings (filter column G).
- Size-bucket column has no blanks where Total Units is present.
- Every row has a Source URL.
- Multi-phase units are not also counted inside Approved rows when quoting a single total.

---

## 7. Conventions and pitfalls learned in the first build

- The Housing Inventory PDF text is ~60k tokens; fetch with a token limit high enough to reach Appendix A (appendices start around 55k tokens in). The 2025 report's A-5/A-7 tables were beyond the fetch limit and were reconstructed from MOHCD data instead.
- The DataSF full pipeline CSV cannot be pulled through an assistant fetch tool (multi-MB, mostly non-residential); the MOHCD CSV can, but was truncated around row 170 at a 90k-token limit — pull it in two passes or locally.
- SUMIFS/COUNTIFS criteria starting with `>`/`<`/`=` are parsed as operators; bucket labels therefore use `251+` not `>250`, and `≤4` (unicode) is safe.
- Keep whole-column references in Summary formulas so appended rows count automatically.
- HI restates prior years every edition; never mix editions in one series.
- MOHCD estimated completion dates lag reality; a (5) status with a past completion date usually means completed — verify before promoting.
- "Under construction" in SF Planning's definition means authorized, not necessarily active; say so in the brief.
- The Pipeline Report's multi-phase bucket contains only un-permitted phases; permitted phases of the same master plans are inside the stage buckets — avoid adding master-plan totals to stage totals.
