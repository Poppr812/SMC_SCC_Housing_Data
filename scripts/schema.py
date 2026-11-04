"""Field registry: the single definition of every record field and category label.

Mirrors FIELDS.md. build.py validates records against this and passes it to the
site template, so the record page and exports are driven from here.
"""

PRODUCT_TYPES = {
    "Apartments": "Multifamily rental, 5+ units, one owner",
    "Condominiums": "Multifamily units sold individually",
    "Townhomes": "Attached homes with their own ground-level entry, for sale or rent",
    "Single-family": "Detached homes, including small-lot detached",
    "Mixed product": "A project combining two or more of the above",
}

STATUSES = {
    "Proposed": "Application filed or publicly announced; not yet approved",
    "Approved": "Entitlements granted; no building permit yet",
    "Permitted": "Building permit issued; construction not started",
    "Under construction": "Construction started",
    "Lease-up / selling": "Complete, now leasing or selling initial units",
    "Existing": "Built and stabilized; the record tracks sales and refinancings",
    "Inactive pipeline": "Withdrawn or denied, or no recorded movement for over 5 years. A working label for comps research, not a legal status",
}

POPULATIONS = {
    "Senior": "Age-restricted (55+ or 62+)",
    "Student": "Built or leased for students",
    "Workforce / educator": "Targeted to employees or a profession",
    "Farmworker": "Units set aside for agricultural workers",
    "Supportive": "Permanent supportive housing, services on site",
    "Family": "Affordable family housing",
}

AFFORDABILITY_TYPES = {
    "Market-rate": "No deed-restricted units",
    "Mixed-income": "Some deed-restricted units (inclusionary or density bonus)",
    "100% affordable": "All units deed-restricted except manager units",
    "Below-market (unrestricted)": "Below-market rents by owner policy, no deed restriction",
}

APPROVAL_TYPES = {
    "Discretionary": "Standard city or county review and approval",
    "Streamlined / ministerial": "By-right state streamlining (SB 35, SB 423, AB 2011, etc.)",
    "Builder's remedy": "Filed under the Housing Accountability Act builder's remedy",
    "Density bonus": "Uses the state density bonus law",
    "Specific / master plan": "Approved under an area plan or development agreement",
}

SMC_CITIES = [
    "Atherton", "Belmont", "Brisbane", "Burlingame", "Colma", "Daly City",
    "East Palo Alto", "Foster City", "Half Moon Bay", "Hillsborough", "Menlo Park",
    "Millbrae", "Pacifica", "Portola Valley", "Redwood City", "San Bruno",
    "San Carlos", "San Mateo", "South San Francisco", "Woodside",
]
SCC_CITIES = [
    "Campbell", "Cupertino", "Gilroy", "Los Altos", "Los Altos Hills", "Los Gatos",
    "Milpitas", "Monte Sereno", "Morgan Hill", "Mountain View", "Palo Alto",
    "San Jose", "Santa Clara", "Saratoga", "Sunnyvale",
]
JURISDICTIONS = SMC_CITIES + SCC_CITIES + ["Unincorporated"]

# Unincorporated communities (census-designated places and named areas). A record whose
# jurisdiction is "Unincorporated" must name one of these in facts.community.
SMC_UNINCORPORATED = [
    "Broadmoor", "Burlingame Hills", "Devonshire", "El Granada", "Emerald Lake Hills",
    "Highlands-Baywood Park", "Kensington Square", "La Honda", "Ladera", "Loma Mar",
    "Montara", "Moss Beach", "North Fair Oaks", "Pescadero", "Princeton", "San Gregorio",
    "Sequoia Tract", "West Menlo Park", "Other San Mateo County",
]
SCC_UNINCORPORATED = [
    "Alum Rock", "Burbank", "Cambrian Park", "East Foothills", "Fruitdale", "Lexington Hills",
    "Loyola", "San Martin", "Stanford", "Other Santa Clara County",
]
UNINCORPORATED = SMC_UNINCORPORATED + SCC_UNINCORPORATED

# Counties with data, in display order. Area menu: county > cities + "Unincorporated (community)".
COUNTIES = {
    "San Mateo County": {"prefix": "SMC", "cities": SMC_CITIES, "unincorporated": SMC_UNINCORPORATED},
    "Santa Clara County": {"prefix": "SCC", "cities": SCC_CITIES, "unincorporated": SCC_UNINCORPORATED},
}


def area_options(county):
    c = COUNTIES[county]
    return c["cities"] + [f"Unincorporated ({u})" for u in c["unincorporated"]]


EVENT_TYPES = [
    "Application filed", "Approved", "Permit issued", "Construction start",
    "Completion", "Lease-up start", "Stabilized", "Sale", "Refinance", "Other",
]

PARTY_ROLES = [
    "Developer", "Co-developer / partner", "Recorded owner", "General contractor",
    "Architect", "Structural engineer", "Civil engineer", "Landscape architect",
    "Interior designer", "Property manager", "Lender", "Equity partner",
    "Buyer", "Seller", "Broker", "Other",
]

FINANCING_TYPES = {
    "Predevelopment loan": "Early-stage loan for design, entitlements, site control",
    "Acquisition loan": "Loan to buy land or an existing building",
    "Construction loan": "Short-term loan during construction",
    "Permanent loan": "Long-term first mortgage after completion",
    "Bridge loan": "Short-term loan between other financing events",
    "Tax-exempt bonds": "Private activity bonds or other tax-exempt issues",
    "Taxable bonds": "Taxable bond tranches",
    "Tax-credit equity (4%)": "LIHTC equity from the 4% program",
    "Tax-credit equity (9%)": "LIHTC equity from the competitive 9% program",
    "State tax-credit equity": "California state LIHTC equity",
    "State soft loan": "HCD and other state programs",
    "Local soft loan": "City or county gap financing",
    "Federal grant / loan": "HOME, CDBG, and similar federal funds",
    "FHLB AHP": "Federal Home Loan Bank Affordable Housing Program",
    "Seller financing": "Seller carryback or land-lease structures",
    "Deferred developer fee": "Developer fee left in the deal as a source",
    "Sponsor / GP equity": "Cash equity from the developer or general partner",
    "Private equity": "Investor or joint-venture equity",
    "Other": "Anything else; described in the program name",
}
DEBT_TYPES = {
    "Predevelopment loan", "Acquisition loan", "Construction loan", "Permanent loan",
    "Bridge loan", "Tax-exempt bonds", "Taxable bonds", "Seller financing",
}

SOURCE_TYPES = [
    "Government document", "Government web page", "Government press release", "Government dataset",
    "Application document", "Developer press release", "Developer web page", "News article",
    "Trade publication", "Trade listing",
]

# Facts: key -> (section, label, kind, options). kind: cat, catmulti, text, int, num, money, mix, ami
SECTIONS = ["Basics", "Location", "Units & building", "Affordability",
            "Approvals & timeline", "Parties", "Financing & transactions"]

FACTS = {
    "product_type":      ("Basics", "Product type", "cat", PRODUCT_TYPES),
    "status":            ("Basics", "Status", "cat", STATUSES),
    "population":        ("Basics", "Population served", "catmulti", POPULATIONS),
    "jurisdiction":      ("Location", "Jurisdiction", "cat", {j: "" for j in JURISDICTIONS}),
    "community":         ("Location", "Community / area", "text", None),
    "site_area_acres":   ("Location", "Site area (acres)", "num", None),
    "total_units":       ("Units & building", "Total units", "int", None),
    "unit_mix":          ("Units & building", "Unit mix", "mix", None),
    "avg_unit_sf":       ("Units & building", "Average unit size (sq ft)", "int", None),
    "residential_sf":    ("Units & building", "Residential area (sq ft)", "int", None),
    "commercial_sf":     ("Units & building", "Commercial area (sq ft)", "int", None),
    "stories":           ("Units & building", "Stories", "int", None),
    "parking_spaces":    ("Units & building", "Parking spaces", "int", None),
    "year_built":        ("Units & building", "Year built", "int", None),
    "affordability_type": ("Affordability", "Affordability type", "cat", AFFORDABILITY_TYPES),
    "restricted_by_ami": ("Affordability", "Restricted units by income", "ami", None),
    "market_rate_units": ("Affordability", "Market-rate units", "int", None),
    "restriction_term_years": ("Affordability", "Restriction term (years)", "int", None),
    "affordability_notes": ("Affordability", "Affordability notes", "text", None),
    "approval_type":     ("Approvals & timeline", "Approval type", "catmulti", APPROVAL_TYPES),
    "planning_file":     ("Approvals & timeline", "Planning file / case number", "text", None),
    "total_development_cost": ("Financing & transactions", "Total development cost", "money", None),
    "sale_price":        ("Financing & transactions", "Sale price", "money", None),
    "cap_rate":          ("Financing & transactions", "Cap rate (%)", "num", None),
    "grm":               ("Financing & transactions", "Gross rent multiplier", "num", None),
}

MIX_KEYS = ["studio", "1br", "2br", "3br", "4br+"]

# Calculated facts: shown with a "calculated" tag and the math. Computed in build.py.
CALCS = {
    "cost_per_unit":  ("Financing & transactions", "Cost per unit"),
    "cost_per_sf":    ("Financing & transactions", "Cost per sq ft"),
    "price_per_unit": ("Financing & transactions", "Price per unit"),
    "price_per_sf":   ("Financing & transactions", "Price per sq ft"),
    "financing_total": ("Financing & transactions", "Reported financing total"),
}

# Fields required before a record can be created (PLAN/FIELDS minimum).
REQUIRED_FACTS = ["product_type", "status"]


# Jurisdictions whose pipeline has been checked against an official list. Anything else is partial.
COVERAGE = {
    "San Mateo": "complete against the City of San Mateo's Current Development Projects list as of 2026-11-03. "
                 "That list leaves out permit-only work and projects completed or inactive for over five years.",
}
_CHECKED = ("checked against the city's published project list on 2026-11-03. The list may leave out permit-only work, "
            "and a few listed projects are missing because no county parcel could be matched.")
COVERAGE.update({j: _CHECKED for j in [
    "Burlingame", "Campbell", "Cupertino", "Daly City", "East Palo Alto", "Foster City", "Gilroy", "Half Moon Bay",
    "Los Gatos", "Menlo Park", "Millbrae", "Morgan Hill", "Redwood City", "San Bruno", "San Carlos", "Saratoga",
    "South San Francisco",
]})


def registry():
    """JSON-serializable registry for the site template."""
    return {
        "sections": SECTIONS,
        "facts": {k: {"section": s, "label": l, "kind": kd,
                      "options": (opts if isinstance(opts, dict) else None)}
                  for k, (s, l, kd, opts) in FACTS.items()},
        "calcs": {k: {"section": s, "label": l} for k, (s, l) in CALCS.items()},
        "mix_keys": MIX_KEYS,
        "product_types": PRODUCT_TYPES,
        "statuses": STATUSES,
        "coverage": COVERAGE,
        "jurisdictions": JURISDICTIONS,
        "areas": {c: area_options(c) for c in COUNTIES},
        "party_roles": PARTY_ROLES,
        "financing_types": FINANCING_TYPES,
        "debt_types": sorted(DEBT_TYPES),
        "event_types": EVENT_TYPES,
    }
