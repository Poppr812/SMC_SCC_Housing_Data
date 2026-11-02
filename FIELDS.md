# FIELDS: v1 record field list

Drafted and approved by Paul 2026-11-02. Every field below holds one or more **claims**, each with its source(s), per PLAN.md §0. Fields marked **[category]** use a fixed list of labels; each label has a definition. Everything else is a number, date, name, or text.

**Minimum to create a record:** name, at least one parcel, product type, status, and one source.

---

## 1. Basics

| Field | Kind | Notes |
|---|---|---|
| Record ID | auto | `SMC-000001`; permanent |
| Name | text | Project or property name; address if no name |
| Product type | [category] | See labels below |
| Status | [category] | See labels below; set from the latest event |
| Population served | [category], multi | See labels below; blank = general |
| Images | 1–5 | Safe images only; else "copyrighted image exists" or "no image available" |

**Product type labels**
- **Apartments:** multifamily rental, 5+ units, one owner
- **Condominiums:** multifamily units sold individually
- **Townhomes:** attached homes with their own ground-level entry, for sale or rent
- **Single-family:** detached homes, including small-lot detached
- **Mixed product:** a project combining two or more of the above (e.g., Clearview: townhomes + detached)

**Status labels**
- **Proposed:** application filed or publicly announced; not yet approved
- **Approved:** entitlements granted; no building permit yet
- **Permitted:** building permit issued; construction not started
- **Under construction:** construction started
- **Lease-up / selling:** complete, now leasing or selling initial units
- **Existing:** built and stabilized; the record tracks sales and refinancings
- **Inactive:** withdrawn, denied, expired, or stalled (reason in notes)

**Population served labels**
- **Senior:** age-restricted (55+ or 62+)
- **Student:** built or leased for students
- **Workforce / educator:** targeted to employees or a profession (e.g., Azara)
- **Farmworker:** units set aside for agricultural workers
- **Supportive:** permanent supportive housing (formerly homeless, services on site)
- **Family:** affordable family housing (e.g., CTCAC "large family")

## 2. Location

| Field | Kind | Notes |
|---|---|---|
| Parcel(s) (APN) | list, dated | Verified in County GIS; dated because parcels merge and split |
| Address(es) | list | Main address first |
| Jurisdiction | [category] | The 20 cities + Unincorporated San Mateo County |
| Community / area | text | e.g., Moss Beach, Broadway-Valdez; keyword-searchable |
| Site area | number | acres |
| Latitude / longitude | auto | From the parcel outline |

## 3. Units & building

| Field | Kind | Notes |
|---|---|---|
| Total units | number | Includes manager units |
| Unit mix | numbers | Studio · 1BR · 2BR · 3BR · 4BR+ counts |
| Average unit size | number | sq ft |
| Residential area | number | sq ft |
| Commercial area | number | sq ft (retail, office) |
| Stories | number | |
| Parking spaces | number | |
| Year built | number | For existing buildings |
| Construction notes | text, sourced | Construction type, framing, podium, Type V/III/I, modular, etc. Keyword-searchable. No categories. |

## 4. Affordability

| Field | Kind | Notes |
|---|---|---|
| Affordability type | [category] | See labels below |
| Restricted units by income | list | `count @ % AMI`, e.g., `14 @ 30%` |
| Market-rate units | number | |
| Restriction term | number | years, if stated |

**Affordability type labels**
- **Market-rate:** no deed-restricted units
- **Mixed-income:** some deed-restricted units (inclusionary or density bonus)
- **100% affordable:** all units deed-restricted except manager units
- **Below-market (unrestricted):** below-market rents by owner policy, no deed restriction (e.g., Azara)

## 5. Approvals & timeline

| Field | Kind | Notes |
|---|---|---|
| Approval type | [category], multi | See labels below |
| Planning file / case number | text | |
| Events | list | Each event has a date and source(s); the timeline on the record page |

**Approval type labels**
- **Discretionary:** standard city or county review and approval
- **Streamlined / ministerial:** by-right state streamlining (SB 35, SB 423, AB 2011, etc.; the law cited goes in notes)
- **Builder's remedy:** filed under the Housing Accountability Act builder's remedy
- **Density bonus:** uses the state density bonus law (can combine with others)
- **Specific / master plan:** approved under an area plan or development agreement

**Event types:** application filed · approved · permit issued · construction start · completion (TCO/CO) · lease-up start · stabilized · sale · refinance · other

## 6. Parties

Each party entry has: **company name** · **contact name** · **contact's public LinkedIn page** (if one exists). Each is sourced like any other fact.

Why this section matters: people researching comparable projects want to know who designed them, who built them, who financed them, and who brokered them. The parties list should make those questions easy to answer and search (e.g., "every project Pyatok designed").

| Field | Kind | Notes |
|---|---|---|
| Developer / sponsor | name(s) | |
| Co-developer / partner | name(s) | |
| Recorded owner | name | Entity on title (County GIS / recorder) |
| General contractor | name | |
| Architect | name | |
| Structural engineer | name | |
| Civil engineer | name | |
| Landscape architect | name | |
| Interior designer | name | |
| Other parties | list, light | One line per company: **company name · role** (free text, e.g., "fire sprinklers", "environmental consultant") · source. Company name only; no contact or LinkedIn. Keyword-searchable. |
| Property manager | name | |
| Lender(s) | name(s) | Linked to the loan below |
| Equity partner(s) | name(s) | |
| Buyer / seller | names | For sale events |
| Broker | name(s) | For sale events |

## 7. Financing & transactions

| Field | Kind | Notes |
|---|---|---|
| Total development cost | $ | Pipeline projects |
| Cost per unit / per sq ft | calculated | Shows the math |
| Sale price | $ | Per sale event |
| Price per unit / per sq ft | calculated | |
| Cap rate / GRM | number | Per sale event, if published |
| Financing sources | list | One line per source: provider · **source type** [category] · program name (text) · amount · date · terms if stated (rate, term) |
| Operating / rental subsidy | list | Provider · program (e.g., project-based vouchers, LOSP) · units covered · term |

**Source type labels** (program names like MHP, AHSC, Serna, NPLH, HOME go in the program-name text, keyword-searchable)
- **Predevelopment loan:** early-stage loan for design, entitlements, site control
- **Acquisition loan:** loan to buy land or an existing building
- **Construction loan:** short-term loan during construction
- **Permanent loan:** long-term first mortgage after completion (incl. FHA/HUD, Fannie, Freddie)
- **Bridge loan:** short-term loan between other financing events
- **Tax-exempt bonds:** private activity bonds (CDLAC allocation) or other tax-exempt issues
- **Taxable bonds:** taxable bond tranches (e.g., taxable tail, subordinate series)
- **Tax-credit equity (4%):** LIHTC equity from the 4% (bond-financed) program
- **Tax-credit equity (9%):** LIHTC equity from the competitive 9% program
- **State tax-credit equity:** California state LIHTC equity
- **State soft loan:** HCD and other state programs (MHP, AHSC, IIG, Serna, NPLH, VHHP, etc.), often residual-receipts
- **Local soft loan:** city or county gap financing (e.g., county affordable housing funds), often residual-receipts
- **Federal grant / loan:** HOME, CDBG, and similar federal pass-through funds
- **FHLB AHP:** Federal Home Loan Bank Affordable Housing Program
- **Seller financing:** seller carryback or land-lease structures
- **Deferred developer fee:** developer fee left in the deal as a source
- **Sponsor / GP equity:** cash equity from the developer or general partner
- **Private equity:** investor or joint-venture equity (market-rate deals)
- **Other:** anything else; described in program name

## 8. Sources & history (every record)

- **Sources list:** title, publisher, date, type, link, retrieval date, Wayback snapshot, saved-copy location (public or private archive), fingerprint
- **Edit history:** who entered each fact, when, and how

---

## Open questions for Paul
1. Should rents / sale prices by unit type be a field? Useful for competitive research, but listing data is often copyrighted; it would need a public source.
2. Is anything missing that you compare on when sizing up a competing project?
