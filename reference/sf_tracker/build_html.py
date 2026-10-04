import os
OUT_DIR = os.environ.get("OUT_DIR", "./")  # set OUT_DIR to your output folder; must end with /
import data, html
NAVY="#17304F"; GOLD="#D9A21B"; TEAL="#1B7F8C"; GRAY="#8A93A0"; LIGHT="#DDE3EA"; INK="#1C2430"

def esc(s): return html.escape(str(s))

def bars_vertical(series, years, w=860, h=300, colors=(NAVY,GOLD), labels=("Completed (new construction)","Net change"), highlight=None):
    # grouped bars: series = list of lists
    n=len(years); mx=max(max(s) for s in series); pad_l=48; pad_b=34; pad_t=14
    cw=(w-pad_l-10)/n; bw=cw/(len(series)+0.6)
    out=[f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Chart">']
    for g in range(0,6001,1000):
        y=pad_t+(h-pad_t-pad_b)*(1-g/mx) if g<=mx else None
        if y is None: continue
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-10}" y2="{y:.1f}" stroke="{LIGHT}" stroke-width="1"/>')
        out.append(f'<text x="{pad_l-6}" y="{y+4:.1f}" font-size="11" fill="{GRAY}" text-anchor="end">{g:,}</text>')
    for i,yr in enumerate(years):
        x0=pad_l+i*cw
        for k,s in enumerate(series):
            v=s[i]
            if v is None: continue
            bh=(h-pad_t-pad_b)*v/mx
            x=x0+bw*0.3+k*bw
            op="1" if (highlight is None or yr==highlight) else "0.9"
            out.append(f'<rect x="{x:.1f}" y="{h-pad_b-bh:.1f}" width="{bw*0.92:.1f}" height="{bh:.1f}" fill="{colors[k]}" opacity="{op}"><title>{yr}: {v:,}</title></rect>')
        lab = str(yr)[-2:] if isinstance(yr,int) else yr
        if not isinstance(yr,int) or yr%2==0:
            out.append(f'<text x="{x0+cw/2:.1f}" y="{h-pad_b+16}" font-size="11" fill="{INK}" text-anchor="middle">{"’"+lab if isinstance(yr,int) else lab}</text>')
    lx=pad_l
    for k,lb in enumerate(labels):
        out.append(f'<rect x="{lx}" y="{h-10}" width="12" height="10" fill="{colors[k]}"/><text x="{lx+16}" y="{h-1}" font-size="11" fill="{INK}">{esc(lb)}</text>')
        lx+=len(lb)*6.4+40
    out.append('</svg>'); return "".join(out)

def hbars(items, w=860, unit_fmt="{:,}", color=NAVY, label_w=250, h_row=30, total=None, shade=None):
    n=len(items); h=n*h_row+8; mx=max(v for _,v in items)
    out=[f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Chart">']
    for i,(lab,v) in enumerate(items):
        y=i*h_row+4; bw=(w-label_w-90)*v/mx
        c = color if not shade else shade[i]
        out.append(f'<text x="{label_w-8}" y="{y+h_row*0.62:.1f}" font-size="12" fill="{INK}" text-anchor="end">{esc(lab)}</text>')
        out.append(f'<rect x="{label_w}" y="{y+5}" width="{bw:.1f}" height="{h_row-11}" fill="{c}" rx="2"/>')
        txt=unit_fmt.format(v) + (f'  ({v/total:.0%})' if total else "")
        out.append(f'<text x="{label_w+bw+6:.1f}" y="{y+h_row*0.62:.1f}" font-size="12" fill="{INK}">{txt}</text>')
    out.append('</svg>'); return "".join(out)

def stacked(years, a, b, w=860, h=240, ca=GOLD, cb=NAVY, la="Affordable", lb="Market-rate"):
    n=len(years); mx=max(x+y for x,y in zip(a,b)); pad_l=48; pad_b=34; pad_t=14
    cw=(w-pad_l-10)/n; bw=cw*0.6
    out=[f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Chart">']
    for g in range(0,mx+1,1000):
        y=pad_t+(h-pad_t-pad_b)*(1-g/mx)
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-10}" y2="{y:.1f}" stroke="{LIGHT}"/><text x="{pad_l-6}" y="{y+4:.1f}" font-size="11" fill="{GRAY}" text-anchor="end">{g:,}</text>')
    for i,yr in enumerate(years):
        x=pad_l+i*cw+(cw-bw)/2; ha=(h-pad_t-pad_b)*a[i]/mx; hb=(h-pad_t-pad_b)*b[i]/mx
        out.append(f'<rect x="{x:.1f}" y="{h-pad_b-hb:.1f}" width="{bw:.1f}" height="{hb:.1f}" fill="{cb}"><title>{yr} market-rate {b[i]:,}</title></rect>')
        out.append(f'<rect x="{x:.1f}" y="{h-pad_b-hb-ha:.1f}" width="{bw:.1f}" height="{ha:.1f}" fill="{ca}"><title>{yr} affordable {a[i]:,}</title></rect>')
        out.append(f'<text x="{x+bw/2:.1f}" y="{h-pad_b-hb-ha-5:.1f}" font-size="11" fill="{INK}" text-anchor="middle">{a[i]/(a[i]+b[i]):.0%}</text>')
        out.append(f'<text x="{x+bw/2:.1f}" y="{h-pad_b+16}" font-size="11" fill="{INK}" text-anchor="middle">{yr}</text>')
    out.append(f'<rect x="{pad_l}" y="{h-10}" width="12" height="10" fill="{ca}"/><text x="{pad_l+16}" y="{h-1}" font-size="11" fill="{INK}">{la} (share labeled)</text>')
    out.append(f'<rect x="{pad_l+180}" y="{h-10}" width="12" height="10" fill="{cb}"/><text x="{pad_l+196}" y="{h-1}" font-size="11" fill="{INK}">{lb}</text>')
    out.append('</svg>'); return "".join(out)

years=list(range(2006,2026)); comp=[1358,2084,2142,2639,2737,809,289,1859,2533,2497,2169,4972,3678,4449,4996,4165,2244,2059,1457,2406]
net=[1598,2519,2270,3077,2963,769,493,1668,2538,2602,2960,5324,3968,4670,5083,4621,2781,2544,1603,2669]
chart1=bars_vertical([comp,net],years,highlight=2025)
chart_stock=hbars([("20+ units",165805),("Single family",94517),("2–4 units",83143),("5–9 units",39777),("10–19 units",39716)],total=422958)
chart_age=hbars([("Built 1939 or earlier",45.4),("1940–1969",24.7),("1970–1999",16.3),("2000 or later",13.6)],unit_fmt="{:.1f}%",color=TEAL)
pipe=[("Under construction",3301),("Site permit issued",1219),("Building permit approved",2422),("Building permit filed",7856),("Approved, permit not yet filed",9477),("Application under review",13036),("Major multi-phase (remaining)",37577)]
chart_pipe=hbars(pipe,total=75853,shade=[NAVY,NAVY,TEAL,TEAL,GRAY,GRAY,LIGHT])
chart_aff=stacked([2021,2022,2023,2024,2025],[1508,1195,946,1115,1758],[4638-1508,2881-1195,2581-946,1741-1115,2682-1758])
nb=[("South of Market",597),("Bayview Hunters Point",320),("Potrero Hill",265),("Treasure Island",178),("Visitacion Valley",172),("Haight Ashbury",165),("Fin. District/South Beach",158),("Bernal Heights",156),("Tenderloin",112),("Inner Richmond",107)]
chart_nb=hbars(nb,label_w=220)
mp=[(n,u) for n,u,s in data.MP]
chart_mp=hbars(mp,label_w=300,color=GRAY)
sizes=[("11–20 units",314),("21–50 units",1776),("51–250 units",15862),("251+ units",73552)]
chart_size=hbars(sizes,total=91527,color=TEAL,label_w=160)

def money(v): return "" if not v else ("$%.1fM" % (v/1e6))
rows_uc=[r for r in data.R if r[6]=="Under Construction" and r[9] and r[9]>=60]
rows_uc.sort(key=lambda r:-r[9])
def tr_uc(r):
    return f"<tr><td>{esc(r[1])}</td><td>{esc(r[3])}</td><td class='n'>{r[9]:,}</td><td class='n'>{'' if r[10] is None else format(r[10],',')}</td><td>{esc(r[13])}{('<br><span class=sub>'+esc(r[14])+'</span>') if r[14] else ''}</td><td>{esc(r[15])}</td><td>{esc(r[16])}</td><td class='n'>{money(r[17])}</td><td>{esc(r[18])}{('<br>'+esc(r[20])) if r[20] else ''}</td><td>{esc(r[22])}</td></tr>"
rows_ap=[r for r in data.R if r[6]=="Approved" and r[9] and r[9]>=300 and not r[7].startswith("Major")]
rows_ap.sort(key=lambda r:-r[9])
def tr_ap(r):
    return f"<tr><td>{esc(r[1])}</td><td>{esc(r[3])}</td><td class='n'>{r[9]:,}</td><td class='n'>{'' if r[10] is None else format(r[10],',')}</td><td>{esc(r[13])}</td><td>{esc(r[5])}</td></tr>"
rows_c=[r for r in data.R if r[6]=="Complete" and r[23]]
rows_c.sort(key=lambda r:(-r[23],-r[9]))
def tr_c(r):
    return f"<tr><td>{r[23]}</td><td>{esc(r[1])}</td><td>{esc(r[3])}</td><td class='n'>{r[9]:,}</td><td class='n'>{'' if r[10] is None else format(r[10],',')}</td><td>{esc(r[13])}</td><td>{esc(r[8])}</td></tr>"

page=f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>San Francisco Housing Stock &amp; Development Activity — September 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap" rel="stylesheet">
<style>
:root{{--ink:{INK};--navy:{NAVY};--gold:{GOLD};--teal:{TEAL};--gray:{GRAY};--rule:{LIGHT};--bg:#F6F7F4;--card:#FFFFFF}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "IBM Plex Sans",Segoe UI,Helvetica,Arial,sans-serif}}
main{{max-width:1080px;margin:0 auto;padding:40px 24px 80px}}
h1{{font:600 34px/1.15 "IBM Plex Serif",Georgia,serif;margin:0 0 6px;max-width:26ch}}h2{{font:600 22px/1.2 "IBM Plex Serif",Georgia,serif;margin:56px 0 6px;padding-top:18px;border-top:3px solid var(--navy)}}
h3{{font-size:15px;font-weight:600;margin:24px 0 6px}}p{{max-width:72ch}}.lede{{font-size:19px;color:#3A4756;max-width:66ch}}
.kicker{{color:var(--gray);font-size:14px;margin-bottom:22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}}.card{{background:var(--card);border:1px solid var(--rule);padding:18px 18px 8px}}
.card h3{{margin-top:0}}.note{{color:var(--gray);font-size:13px;max-width:none}}
svg{{width:100%;height:auto;display:block}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0 4px}}th{{text-align:left;background:var(--navy);color:#fff;font-weight:500;padding:7px 8px;vertical-align:bottom}}td{{padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:top}}td.n,th.n{{text-align:right;white-space:nowrap}}
.sub{{color:var(--gray);font-size:12px}}.wrap{{overflow-x:auto}}
.stat{{display:flex;gap:28px;flex-wrap:wrap;margin:18px 0 8px}}.stat div{{min-width:150px}}.stat b{{display:block;font:600 30px/1 "IBM Plex Serif",Georgia,serif;color:var(--navy)}}.stat span{{font-size:13px;color:#3A4756}}
a{{color:var(--teal)}}
@media(max-width:640px){{h1{{font-size:27px}}main{{padding:24px 14px 60px}}}}
</style></head><body><main>
<div class="kicker">San Francisco &middot; data through 2026 Q2 &middot; compiled September 9, 2026</div>
<h1>San Francisco has 423,000 homes, added 2,669 last year, and has 75,853 more in its pipeline. Only 3,301 of those are being built.</h1>
<p class="lede">The city delivered 2,406 new-construction units in 2025, a rebound from 2024’s 1,457 but still a quarter below its ten-year average. Two-thirds of what opened was deed-restricted affordable. The first half of 2026 produced 405 units, and the under-construction count has fallen to about 3,300 from 4,545 five years ago while entitled-but-unpermitted units have swelled to 9,477.</p>

<h2>Housing stock</h2>
<div class="stat"><div><b>422,958</b><span>housing units, year-end 2025 (SF Planning)</span></div><div><b>67%</b><span>renter-occupied (HUD CMAR, SF submarket)</span></div><div><b>1944</b><span>median year built (ACS)</span></div><div><b>9.6%</b><span>vacant, all ACS categories (≈40,450 units)</span></div><div><b>18,997</b><span>residential-hotel (SRO) rooms in 497 buildings</span></div></div>
<div class="grid">
<div class="card"><h3>Units by building type, 2025</h3>{chart_stock}<p class="note">Source: 2025 Housing Inventory, Table 1. Building-type split was re-based in the 2024 report; use the latest series.</p></div>
<div class="card"><h3>Age of stock (share of units)</h3>{chart_age}<p class="note">Source: ACS 5-year, San Francisco County. 45% of homes predate 1940; refresh from data.census.gov DP04.</p></div>
</div>
<p>The stock is 39% in buildings of 20 or more units and 22% single-family, with the balance in 2–19 unit structures that make up most of the pre-war neighborhoods. Growth is 0.6% a year in a good year. Condominium recordings jumped to 2,989 in 2025 (from 813 in 2024) as large rental buildings subdivided, and 223 ADUs were added or legalized.</p>

<h2>Production trend, 2006–2025</h2>
<div class="card">{chart1}<p class="note">Units completed from new construction vs. net change in stock (after alterations and demolitions). Source: 2025 Housing Inventory, Table 2. 2026 H1: 405 units ready for occupancy (Housing Dashboard via The Frisc).</p></div>
<div class="grid" style="margin-top:24px">
<div class="card"><h3>Delivered, three-year view</h3><table><tr><th>Year</th><th class="n">New construction</th><th class="n">Net change</th><th class="n">Affordable</th><th class="n">Authorized</th><th class="n">Approved</th></tr>
<tr><td>2023</td><td class="n">2,059</td><td class="n">2,544</td><td class="n">946 (37%)</td><td class="n">2,997</td><td class="n">3,045</td></tr>
<tr><td>2024</td><td class="n">1,457</td><td class="n">1,603</td><td class="n">1,115 (64%)</td><td class="n">1,031</td><td class="n">5,739</td></tr>
<tr><td>2025</td><td class="n">2,406</td><td class="n">2,669</td><td class="n">1,758 (66%)</td><td class="n">1,900</td><td class="n">3,723</td></tr>
<tr><td>2026 H1</td><td class="n">405</td><td class="n">—</td><td class="n">—</td><td class="n">—</td><td class="n">—</td></tr></table><p class="note">Authorized = net units with full building permit or site permit + first construction document. Approved = Planning entitlements. Filings spiked to 9,614 units in 2025 (88 Bluxome, Marina Safeway, 10 South Van Ness revision).</p></div>
<div class="card"><h3>Affordable vs. market-rate completions</h3>{chart_aff}<p class="note">All new units incl. ADUs. 2025 affordable = 1,440 in 100%-affordable buildings + 117 inclusionary + 201 ADUs; 86% at ≤80% AMI. Source: HI 2025 Tables 23–24.</p></div>
</div>
<h3>Where 2025’s new units landed (net gain by Analysis Neighborhood, top 10)</h3>
<div class="card">{chart_nb}<p class="note">Source: HI 2025 Table 27. 21 of 41 neighborhoods gained fewer than 10 units.</p></div>

<h2>Development pipeline, 2026 Q2</h2>
<p>SF Planning counts 75,853 new units in its pipeline as of April 2026, of which 18,536 (24%) are affordable. Half sit in the remaining phases of 14 entitled master plans; another 30% are approved or under review but have no building permit. The stages that signal near-term delivery, under construction plus issued and approved permits, total 6,942 units.</p>
<div class="card">{chart_pipe}<p class="note">Source: Pipeline Report 2026 Q2. Darker bars = permits in hand. "Under construction" means authorized to start, not necessarily active.</p></div>
<div class="grid" style="margin-top:24px">
<div class="card"><h3>Major multi-phase projects, remaining units</h3>{chart_mp}<p class="note">Un-permitted phases only; 37,577 total. Phases with permits are counted in the stage bars above.</p></div>
<div class="card"><h3>Tracked projects by size bucket (all statuses, units)</h3>{chart_size}<p class="note">From the workbook’s 265-row Projects tab (projects ≥10 units plus the MOHCD affordable pipeline). No tracked projects fall in the ≤4 bucket; 5–10 units: 23. Small projects and ADUs are in the DataSF pipeline export, not itemized here.</p></div>
</div>

<h3>Largest projects under construction (first construction document issued), with capital stack where public</h3>
<div class="wrap"><table><tr><th>Project</th><th>Neighborhood</th><th class="n">Units</th><th class="n">Affordable</th><th>Developer / partner</th><th>General contractor</th><th>Architect</th><th class="n">Total cost</th><th>Equity / lenders</th><th>Est. completion</th></tr>
{''.join(tr_uc(r) for r in rows_uc)}</table></div>
<p class="note">Sources per row in the workbook. Blank = not found in public sources. 300 De Haro cost is a developer-stated ceiling (&lt;$500k/unit); Transbay 2E is $189M TDC with a $115.8M city loan; 730 Stanyan (complete, 2025) was $153–155M with Bank of America construction debt.</p>

<h3>Largest entitled projects without permits (approved, ≥300 units)</h3>
<div class="wrap"><table><tr><th>Project</th><th>Neighborhood</th><th class="n">Units</th><th class="n">Affordable</th><th>Sponsor</th><th>Status</th></tr>
{''.join(tr_ap(r) for r in rows_ap)}</table></div>

<h2>Delivered, 2023–2026 YTD (projects of 10+ units)</h2>
<div class="wrap"><table><tr><th>Year</th><th>Project</th><th>Neighborhood</th><th class="n">Units</th><th class="n">Affordable</th><th>Developer</th><th>Tenure</th></tr>
{''.join(tr_c(r) for r in rows_c)}</table></div>
<p class="note">2026 rows are MOHCD-scheduled completions in H1 2026; confirm against the Housing Dashboard. Unit counts are project totals; the Housing Inventory may credit a project’s units across two years when TCOs are phased.</p>

<h2>What to watch</h2>
<p>Three things move the 2027–2028 delivery numbers. First, whether the 9,477 entitled-but-unpermitted units and the two approved SoMa towers (88 Bluxome, 1,500 units; 10 South Van Ness, 1,104) find construction financing; SF Planning’s own view is that this depends on interest rates more than approvals. Second, the November 2026 ballot measure to cap inclusionary at 5% in exchange for $125M a year in city affordable spending, which would change the economics of every mixed-income project in the approved column. Third, MOHCD’s roughly 2,000 affordable units under construction, of which only 1,139 have a 2026 completion date.</p>
<p class="note">Companion files: <b>SF_Housing_Stock_and_Pipeline_2026-09.xlsx</b> (data, formulas, sources, update guide) and <b>SF_Housing_RUNBOOK.md</b>. Primary sources: SF Planning Housing Inventory 2023–2025; SF Planning Pipeline Report 2026 Q2; DataSF Development Pipeline and MOHCD Affordable Housing Pipeline; CTCAC/CDLAC and MOHCD Loan Committee records; HUD CMAR; ACS.</p>
</main></body></html>"""
open(OUT_DIR + "SF_Housing_Brief_2026-09.html","w").write(page)
print(len(page), len(rows_uc), len(rows_ap), len(rows_c))
