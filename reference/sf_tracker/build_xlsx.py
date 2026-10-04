import os
OUT_DIR = os.environ.get("OUT_DIR", "./")  # set OUT_DIR to your output folder; must end with /
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
import data

wb = Workbook()
F = "Arial"
H = Font(name=F, bold=True, color="FFFFFF", size=10)
HF = PatternFill("solid", fgColor="1F3A5F")
B = Font(name=F, size=10)
BB = Font(name=F, size=10, bold=True)
T = Font(name=F, size=14, bold=True)
NOTE = Font(name=F, size=9, italic=True, color="555555")
LINK = Font(name=F, size=10, color="0563C1", underline="single")
FILL_IN = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BBBBBB")

def hdr(ws, row, cols, start=1):
    for i, c in enumerate(cols):
        cell = ws.cell(row=row, column=start+i, value=c); cell.font = H; cell.fill = HF
        cell.alignment = Alignment(wrap_text=True, vertical="center")
def widths(ws, w):
    for i, x in enumerate(w, 1): ws.column_dimensions[get_column_letter(i)].width = x
def put(ws, r, c, v, font=B, fmt=None):
    cell = ws.cell(row=r, column=c, value=v); cell.font = font
    if fmt: cell.number_format = fmt
    return cell

# ================= README =================
ws = wb.active; ws.title = "README"
lines = [
("San Francisco Housing Stock & Development Activity — Data Workbook", T),
("Compiled 2026-09-09 by Claude for Paul (RaaP). All figures trace to a source row in the Sources tab; every Projects row carries its own source URL.", B),
("", B),
("Tabs", BB),
("Summary — live COUNTIFS/SUMIFS over the Projects tab, plus the official citywide figures (Housing Inventory 2025, Pipeline Report 2026 Q2).", B),
("Stock — citywide housing stock by building type (2024, 2025), 41 Analysis Neighborhoods (2025), tenure / vacancy / age of stock (ACS).", B),
("Trend — units authorized, completed, demolished, altered, net change, 2006–2025 + 2026 H1; affordable production by income level and source, 2021–2025.", B),
("Pipeline_Q2_2026 — SF Planning Pipeline Report snapshot by stage and the 14 major multi-phase projects.", B),
("Projects — one row per project (265 rows): completions 2023–2026 YTD (10+ units), under construction, permitted, approved, filed/pre-development, and multi-phase remainders. Capital-stack columns populated where public sources exist; otherwise blank.", B),
("Sources — every dataset/report used, with URL and retrieval date.", B),
("How_to_update — refresh steps and cadence per source.", B),
("", B),
("Status (normalized) definitions", BB),
("Complete = TCO or CFC issued (Housing Inventory counts TCO as complete).", B),
("Under Construction = SF Planning definition: issued full building permit, OR issued site permit + approved first construction document (FCD). MOHCD construction status (5).", B),
("Permitted = issued site permit without FCD (MOHCD status 4) — Pipeline Report calls this 'Building Permit Issued'; NOT counted as under construction or toward RHNA.", B),
("Approved = Planning entitlement granted / MOHCD 'Design with Entitlements Approved' (3); building permits filed or not yet filed.", B),
("Under Review = application filed with Planning, or MOHCD pre-development / preliminary / multiphase-before-predevelopment (0–2).", B),
("Major Multi-Phase (remaining) = un-permitted remaining phases of the 14 entitled master-plan projects, as reported in the Pipeline Report.", B),
("", B),
("Size buckets (column M, formula): ≤4 | 5–10 | 11–20 | 21–50 | 51–250 | 251+ total units.", B),
("", B),
("Coverage caveat", BB),
("The Projects tab is NOT the full DataSF Development Pipeline (which has thousands of rows, most non-residential or <10 units). It covers every project ≥10 units listed in the 2023–2025 Housing Inventory appendices, the full MOHCD Affordable Housing Pipeline (≈170 projects captured), and named market-rate projects. For all small projects/ADUs, pull the DataSF CSV (Sources tab) and append.", B),
("Affordability mix is written as 'units @ AMI band' in one cell; AMI bands follow MOHCD's declared columns (20/30/40/50/55/60/80/90/100/110/120/130/150%). Housing Inventory rows use the four HI bands (Ext. Low ≤30%, Very Low ≤50%, Low ≤80%, Moderate ≤120%).", B),
("Unit counts for 100% affordable projects: 'Total Units' includes manager units; 'Affordable Units' excludes them (MOHCD convention).", B),
("Yellow cells = analyst estimate or placeholder to verify.", B),
]
for i,(t,f) in enumerate(lines,1):
    c = put(ws, i, 1, t, f); c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 150

# ================= PROJECTS =================
wp = wb.create_sheet("Projects")
cols = data.COLS
hdr(wp, 1, cols)
n = len(data.R)
for r, row in enumerate(data.R, 2):
    for c, v in enumerate(row, 1):
        cell = wp.cell(row=r, column=c, value=v); cell.font = B
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    # size bucket formula col M (13) based on J (Total Units)
    wp.cell(row=r, column=13, value=f'=IF(J{r}="","",IF(J{r}<=4,"≤4",IF(J{r}<=10,"5–10",IF(J{r}<=20,"11–20",IF(J{r}<=50,"21–50",IF(J{r}<=250,"51–250","251+"))))))').font = B
    for c in (18, 20, 22): wp.cell(row=r, column=c).number_format = '$#,##0'
    for c in (10, 11): wp.cell(row=r, column=c).number_format = '#,##0'
    src = wp.cell(row=r, column=26)
    if src.value: src.hyperlink = src.value; src.font = LINK
    if row[0] in ("U-01",): wp.cell(row=r, column=18).fill = FILL_IN  # estimated cost
widths(wp, [8,38,24,18,7,30,14,22,10,8,8,34,8,30,26,22,26,14,30,10,34,12,14,8,40,40])
wp.freeze_panes = "C2"
wp.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{n+1}"
wp.row_dimensions[1].height = 42

# ================= SUMMARY =================
s = wb.create_sheet("Summary", 1)
put(s,1,1,"San Francisco housing — summary dashboard",T)
put(s,2,1,"Formulas recalc from the Projects tab; 'official' blocks are hard-coded from SF Planning reports (see Sources).",NOTE)

put(s,4,1,"A. Official citywide figures",BB)
hdr(s,5,["Metric","Value","As of","Source"])
off = [
("Total housing units (SF Planning)",422958,"Dec 31, 2025","Housing Inventory 2025, Table 1"),
("Net units added 2025",2669,"2025","HI 2025, Table 2"),
("Units completed from new construction 2025",2406,"2025","HI 2025, Table 2"),
("Units completed 2026 H1 (ready for occupancy)",405,"Jan–Jun 2026","The Frisc (SF Planning Housing Dashboard), Jul 2026"),
("Net units authorized for construction 2025",1900,"2025","HI 2025, Table 2"),
("Units approved by Planning 2025",3723,"2025","HI 2025, Table 3"),
("Units filed at Planning 2025",9614,"2025","HI 2025, Table 3"),
("New affordable units completed 2025",1758,"2025","HI 2025, Table 23 (66% of new units)"),
("Pipeline — total new units",75853,"Q2 2026 (Apr 2026)","Pipeline Report 2026 Q2"),
("Pipeline — affordable units (24%)",18536,"Q2 2026","Pipeline Report 2026 Q2"),
("Pipeline — under construction",3301,"Q2 2026","Pipeline Report 2026 Q2"),
("Pipeline — building permits issued (site)",1219,"Q2 2026","Pipeline Report 2026 Q2"),
("Pipeline — building permits approved",2422,"Q2 2026","Pipeline Report 2026 Q2"),
("Pipeline — building permits filed",7856,"Q2 2026","Pipeline Report 2026 Q2"),
("Pipeline — approved, permits not yet filed",9477,"Q2 2026","Pipeline Report 2026 Q2"),
("Pipeline — applications filed (under review)",13036,"Q2 2026","Pipeline Report 2026 Q2"),
("Pipeline — major multi-phase (remaining)",37577,"Q2 2026","Pipeline Report 2026 Q2"),
("Affordable units under construction (MOHCD 'general estimation')",2000,"Jun 2026","MOHCD director to BOS, per The Frisc"),
("RHNA 2023–2031 progress (units credited)",9581,"Dec 2025","HI 2025 (12% of 82,069)"),
]
for i,(m,v,a,src) in enumerate(off,6):
    put(s,i,1,m); put(s,i,2,v,fmt='#,##0'); put(s,i,3,a); put(s,i,4,src)
r0 = 6+len(off)+1

put(s,r0,1,"B. Projects tracked in this workbook — by normalized status",BB)
hdr(s,r0+1,["Status (normalized)","Projects","Total units","Affordable units","Share of tracked units"])
statuses = ["Complete","Under Construction","Permitted","Approved","Under Review","Major Multi-Phase (remaining)"]
rs = r0+2
for i,st in enumerate(statuses):
    r = rs+i
    put(s,r,1,st)
    put(s,r,2,f'=COUNTIFS(Projects!$G:$G,A{r})',fmt='#,##0')
    put(s,r,3,f'=SUMIFS(Projects!$J:$J,Projects!$G:$G,A{r})',fmt='#,##0')
    put(s,r,4,f'=SUMIFS(Projects!$K:$K,Projects!$G:$G,A{r})',fmt='#,##0')
    put(s,r,5,f'=IF(C{rs+len(statuses)}=0,0,C{r}/C{rs+len(statuses)})',fmt='0.0%')
rt = rs+len(statuses)
put(s,rt,1,"Total",BB)
for c,L in ((2,"B"),(3,"C"),(4,"D")):
    put(s,rt,c,f'=SUM({L}{rs}:{L}{rt-1})',BB,'#,##0')
put(s,rt,5,1,BB,'0.0%')
put(s,rt+1,1,"Note: 'Complete' here = projects ≥10 units completed 2023–2026 YTD only (not all-time). Multi-phase remainders are unit counts from the Pipeline Report, not project rows with detail.",NOTE)

r1 = rt+3
put(s,r1,1,"C. Units by size bucket × status (SUMIFS on Projects)",BB)
buckets = ["≤4","5–10","11–20","21–50","51–250","251+"]
hdr(s,r1+1,["Size bucket (total units)"]+statuses+["All"])
for i,bk in enumerate(buckets):
    r = r1+2+i
    put(s,r,1,bk)
    for j,st in enumerate(statuses):
        put(s,r,2+j,f'=SUMIFS(Projects!$J:$J,Projects!$M:$M,$A{r},Projects!$G:$G,"{st}")',fmt='#,##0')
    put(s,r,2+len(statuses),f'=SUM(B{r}:{get_column_letter(1+len(statuses))}{r})',fmt='#,##0')
rb = r1+2+len(buckets)
put(s,rb,1,"All buckets",BB)
for j in range(len(statuses)+1):
    L = get_column_letter(2+j)
    put(s,rb,2+j,f'=SUM({L}{r1+2}:{L}{rb-1})',BB,'#,##0')

r2 = rb+2
put(s,r2,1,"D. Project count by size bucket × status (COUNTIFS on Projects)",BB)
hdr(s,r2+1,["Size bucket (total units)"]+statuses+["All"])
for i,bk in enumerate(buckets):
    r = r2+2+i
    put(s,r,1,bk)
    for j,st in enumerate(statuses):
        put(s,r,2+j,f'=COUNTIFS(Projects!$M:$M,$A{r},Projects!$G:$G,"{st}")',fmt='#,##0')
    put(s,r,2+len(statuses),f'=SUM(B{r}:{get_column_letter(1+len(statuses))}{r})',fmt='#,##0')
rc = r2+2+len(buckets)
put(s,rc,1,"All buckets",BB)
for j in range(len(statuses)+1):
    L = get_column_letter(2+j)
    put(s,rc,2+j,f'=SUM({L}{r2+2}:{L}{rc-1})',BB,'#,##0')

r3 = rc+2
put(s,r3,1,"E. Completions tracked by year (projects ≥10 units)",BB)
hdr(s,r3+1,["Year completed","Projects","Total units (tracked)","Affordable units (tracked)","Official new-construction units (HI)","Official affordable units (HI)"])
official = {2023:(2059,946),2024:(1457,1115),2025:(2406,1758),2026:(405,None)}
for i,y in enumerate([2023,2024,2025,2026]):
    r = r3+2+i
    put(s,r,1,y)
    put(s,r,2,f'=COUNTIFS(Projects!$X:$X,A{r})',fmt='#,##0')
    put(s,r,3,f'=SUMIFS(Projects!$J:$J,Projects!$X:$X,A{r})',fmt='#,##0')
    put(s,r,4,f'=SUMIFS(Projects!$K:$K,Projects!$X:$X,A{r})',fmt='#,##0')
    put(s,r,5,official[y][0],fmt='#,##0'); put(s,r,6,official[y][1],fmt='#,##0')
put(s,r3+6,1,"Tracked totals exceed official new-construction counts where multi-year projects TCO'd partially (e.g., 921 Howard, 600 7th) or completed units are counted by HI in a prior/later year. 2026 = H1 only; 2026 rows are MOHCD-estimated completions, verify on the Housing Dashboard.",NOTE)

r4 = r3+8
put(s,r4,1,"F. Affordable units tracked by Supervisor District (all statuses except Complete)",BB)
hdr(s,r4+1,["Supervisor District","Projects","Total units","Affordable units"])
for i,d in enumerate([str(x) for x in range(1,12)]):
    r = r4+2+i
    put(s,r,1,d)
    put(s,r,2,f'=COUNTIFS(Projects!$E:$E,A{r},Projects!$G:$G,"<>Complete")',fmt='#,##0')
    put(s,r,3,f'=SUMIFS(Projects!$J:$J,Projects!$E:$E,A{r},Projects!$G:$G,"<>Complete")',fmt='#,##0')
    put(s,r,4,f'=SUMIFS(Projects!$K:$K,Projects!$E:$E,A{r},Projects!$G:$G,"<>Complete")',fmt='#,##0')
widths(s,[52,18,18,18,18,18,20,14])

# ================= STOCK =================
st = wb.create_sheet("Stock", 2)
put(st,1,1,"Housing stock — citywide and by neighborhood",T)
put(st,3,1,"A. Citywide housing stock by building type (SF Planning)",BB)
hdr(st,4,["Year-end","Single family","2–4 units","5–9 units","10–19 units","20+ units","Total","Source"])
stock = [("2024 (restated in HI 2025)",94500,82988,39740,39649,163412,420289,"HI 2025 Table 1"),
         ("2025 net change",17,155,37,67,2393,2669,"HI 2025 Table 1"),
         ("2025",94517,83143,39777,39716,165805,422958,"HI 2025 Table 1"),
         ("2024 (as published in HI 2024)",95071,83015,39321,39064,161353,417824,"HI 2024 Table 1 — superseded"),
         ("2023 (as published in HI 2024)",95051,82856,39299,39040,159981,416227,"HI 2024 Table 1 — superseded")]
for i,row in enumerate(stock,5):
    for c,v in enumerate(row,1): put(st,i,c,v,fmt='#,##0' if isinstance(v,int) else None)
put(st,10,1,"Share of 2025 stock",BB)
for c in range(2,7):
    L=get_column_letter(c); put(st,10,c,f'={L}7/$G$7',fmt='0.0%')
put(st,11,1,"Building-type split reset in the 2024 report (2020 Census baseline + ACS ratios). The 2023 report showed 122,816 single-family; later reports show ~95k. Use the latest report's series.",NOTE)

put(st,13,1,"B. Tenure, vacancy, age of stock (Census ACS / HUD)",BB)
hdr(st,14,["Metric","Value","Note","Source"])
acs = [("Total housing inventory (HUD CMAR, SF submarket, current)",420800,"","HUD Comprehensive Housing Market Analysis, SF-Redwood City-SSF, 2024"),
("Occupied units",380400,"","HUD CMAR 2024"),("Owner-occupied share","32.6%","of occupied units","HUD CMAR 2024"),
("Renter-occupied share","67.4%","of occupied units","HUD CMAR 2024"),("Vacant units (all categories)",40450,"≈9.6% of inventory; ACS 'vacant' includes seasonal, sold/rented-not-occupied, under repair","HUD CMAR 2024"),
("Vacant — for rent share of vacant","26.5%","ACS 5-yr","Social Explorer / ACS 5-year (SF County)"),
("Vacant — for sale share of vacant","2.5%","ACS 5-yr","Social Explorer / ACS 5-year"),
("Median year structure built",1944,"","ACS 5-year (SF County)"),
("Built 1939 or earlier","45.4%","of housing units","ACS 5-year via NeighborhoodScout"),
("Built 1940–1969","24.7%","","ACS 5-year via NeighborhoodScout"),
("Built 1970–1999","16.3%","","ACS 5-year via NeighborhoodScout"),
("Built 2000 or later","13.6%","","ACS 5-year via NeighborhoodScout"),
("Single-unit structures share","30.9%","ACS 5-yr; SF Planning building-type table above is the operative series","ACS 5-year"),
("Multi-unit structures share","68.9%","","ACS 5-year"),
("Residential hotel (SRO) rooms",18997,"497 buildings (375 for-profit / 122 nonprofit)","HI 2025 Table 20 (DBI)"),
("New condominiums recorded 2025",2989,"vs 813 in 2024","HI 2025 Table 16 (DPW)"),
("ADUs added or legalized 2025",223,"folded into totals above","HI 2025 Table 9")]
for i,row in enumerate(acs,15):
    for c,v in enumerate(row,1): put(st,i,c,v,fmt='#,##0' if isinstance(v,int) and c==2 and v>3000 else None)
put(st,15+len(acs),1,"Refresh age/tenure from data.census.gov table DP04 (ACS 1-year, San Francisco County) — cadence: annually each September.",NOTE)

rn = 15+len(acs)+2
put(st,rn,1,"C. Housing stock by Analysis Neighborhood, year-end 2025 (HI 2025 Table 28) + 2025 net gain (Table 27)",BB)
hdr(st,rn+1,["Analysis Neighborhood","Single family","2–4 units","5–9 units","10–19 units","20+ units","Total 2025","Net gain 2025","New-construction units 2025"])
NB = [("Bayview Hunters Point",5846,1458,281,296,5735,13616,320,304),("Bernal Heights",4674,3234,582,253,682,9425,156,147),
("Castro/Upper Market",1583,5684,2092,1284,1887,12530,10,1),("Chinatown",27,816,1099,889,3230,6061,0,0),("Excelsior",7688,1163,341,282,770,10244,7,0),
("Financial District/South Beach",7,105,110,196,19649,20067,158,151),("Glen Park",1991,973,119,116,1040,4239,0,0),("Golden Gate Park",0,0,0,0,42,42,0,0),
("Haight Ashbury",749,3872,2430,1456,937,9444,165,162),("Hayes Valley",196,2439,1824,2044,5726,12229,68,64),("Inner Richmond",1350,4822,1917,1374,565,10028,107,98),
("Inner Sunset",4237,4311,1479,1223,1385,12635,11,3),("Japantown",23,190,78,155,2428,2874,-1,0),("Lakeshore",118,2,0,32,4505,4657,0,0),("Lincoln Park",18,46,6,0,0,70,0,0),
("Lone Mountain/USF",664,3167,1212,984,1149,7176,2,0),("Marina",1139,4594,2287,4718,3052,15790,18,3),("McLaren Park",104,0,0,0,91,195,0,0),
("Mission",1368,8845,5620,3448,10809,30090,70,51),("Mission Bay",0,4,0,45,10880,10929,1,0),("Nob Hill",133,1347,1847,3626,12755,19708,38,0),
("Noe Valley",3164,5133,1482,737,1194,11710,12,4),("North Beach",116,1839,1837,989,2950,7731,5,0),("Oceanview/Merced/Ingleside",5654,731,193,116,442,7136,5,0),
("Outer Mission",4516,824,241,143,784,6508,62,55),("Outer Richmond",5129,8516,2550,2131,1085,19411,17,0),("Pacific Heights",1139,2630,2222,3380,6035,15406,8,0),
("Portola",3343,678,147,199,74,4441,8,1),("Potrero Hill",1288,2350,446,350,5253,9687,265,264),("Presidio",10,17,0,0,0,27,0,0),("Presidio Heights",971,1911,908,887,2139,6816,5,0),
("Russian Hill",282,2691,2692,2721,3725,12111,38,35),("Seacliff",711,160,86,33,0,990,1,1),("South of Market",57,910,682,1092,17491,20232,597,596),
("Sunset/Parkside",19522,4616,1431,984,724,27277,46,6),("Tenderloin",17,120,225,887,23411,24660,112,112),("Treasure Island",0,0,0,0,1264,1264,178,178),
("Twin Peaks",1360,426,308,1000,727,3821,0,0),("Visitacion Valley",3106,483,78,85,1173,4925,172,170),("West of Twin Peaks",12101,1006,194,325,603,14229,6,0),
("Western Addition",116,1030,731,1236,9414,12527,2,0)]
for i,row in enumerate(NB,rn+2):
    for c,v in enumerate(row,1): put(st,i,c,v,fmt='#,##0' if c>1 else None)
re_ = rn+2+len(NB)
put(st,re_,1,"Citywide (check)",BB)
for c in range(2,10):
    L=get_column_letter(c); put(st,re_,c,f'=SUM({L}{rn+2}:{L}{re_-1})',BB,'#,##0')
widths(st,[44,14,12,12,12,12,12,12,16])

# ================= TREND =================
tr = wb.create_sheet("Trend", 3)
put(tr,1,1,"Housing production trend, 2006–2026 H1 (SF Planning Housing Inventory 2025, Table 2)",T)
hdr(tr,3,["Year","Net units authorized for construction","Units completed from new construction","Units demolished","Units gained/lost from alterations","Net change in units","Source"])
T2 = [(2006,4275,1358,45,285,1598),(2007,3133,2084,37,472,2519),(2008,2355,2142,60,188,2270),(2009,288,2639,31,469,3077),(2010,314,2737,56,282,2963),
(2011,2412,809,33,-7,769),(2012,2500,289,141,345,493),(2013,3221,1859,431,240,1668),(2014,5176,2533,95,100,2538),(2015,3605,2497,26,131,2602),
(2016,2606,2169,23,814,2960),(2017,4560,4972,24,376,5324),(2018,4343,3678,50,340,3968),(2019,3975,4449,142,363,4670),(2020,3102,4996,352,439,5083),
(2021,1835,4165,12,468,4621),(2022,2898,2244,98,635,2781),(2023,2997,2059,13,498,2544),(2024,1031,1457,132,278,1603),(2025,1900,2406,6,269,2669)]
for i,row in enumerate(T2,4):
    for c,v in enumerate(row,1): put(tr,i,c,v,fmt='#,##0' if c>1 else None)
    put(tr,i,7,"HI 2025 Table 2")
r26 = 4+len(T2)
put(tr,r26,1,"2026 H1"); put(tr,r26,3,405,fmt='#,##0'); put(tr,r26,7,"SF Planning Housing Dashboard via The Frisc (Jul 2026); 'ready for occupancy'")
put(tr,r26+1,1,"10-yr avg 2016–2025",BB)
for c in range(2,7):
    L=get_column_letter(c); put(tr,r26+1,c,f'=AVERAGE({L}14:{L}23)',BB,'#,##0')

ra = r26+3
put(tr,ra,1,"New units added by building type, 2021–2025 (HI 2025 Table 13; includes ADUs and alterations)",BB)
hdr(tr,ra+1,["Year","Single family","2–4","5–9","10–19","20+","Total"])
T13=[(2021,26,229,114,109,4160,4638),(2022,16,211,100,59,2495,2881),(2023,32,192,81,69,2207,2581),(2024,33,166,70,97,1375,1741),(2025,26,157,37,67,2395,2682)]
for i,row in enumerate(T13,ra+2):
    for c,v in enumerate(row,1): put(tr,i,c,v,fmt='#,##0' if c>1 else None)

rb_ = ra+2+len(T13)+1
put(tr,rb_,1,"New affordable units by income level, 2021–2025 (HI 2025 Table 23)",BB)
hdr(tr,rb_+1,["Year","Extremely Low (≤30% AMI)","Very Low (≤50%)","Low (≤80%)","Moderate (≤120%)","Moderate non-deed-restricted (ADUs)","Total affordable","Total all new units","Affordable share"])
T23=[(2021,34,529,551,98,296,1508,4638),(2022,188,461,206,70,270,1195,2881),(2023,0,209,288,212,237,946,2581),(2024,100,182,327,294,212,1115,1741),(2025,216,801,495,45,201,1758,2682)]
for i,row in enumerate(T23,rb_+2):
    for c,v in enumerate(row,1): put(tr,i,c,v,fmt='#,##0' if c>1 else None)
    put(tr,i,9,f'=G{i}/H{i}',fmt='0%')

rc_ = rb_+2+len(T23)+1
put(tr,rc_,1,"Affordable production by source, 2021–2025 (HI 2025 Table 24)",BB)
hdr(tr,rc_+1,["Year","Inclusionary units","100% affordable units","ADU / legalizations","Total"])
T24=[(2021,226,986,297,1509),(2022,197,728,270,1195),(2023,144,585,239,968),(2024,83,820,212,1115),(2025,117,1440,201,1758)]
for i,row in enumerate(T24,rc_+2):
    for c,v in enumerate(row,1): put(tr,i,c,v,fmt='#,##0' if c>1 else None)

rd_ = rc_+2+len(T24)+1
put(tr,rd_,1,"Units authorized for construction by building type, 2021–2025 (HI 2025 Table 4)",BB)
hdr(tr,rd_+1,["Year","Single family","2–4","5–9","10–19","20+","Total new units","Projects"])
T4=[(2021,44,275,81,118,1435,1953,394),(2022,39,241,115,145,2390,2930,368),(2023,41,190,63,79,2763,3136,288),(2024,32,180,38,45,786,1081,244),(2025,29,183,18,16,1707,1953,216)]
for i,row in enumerate(T4,rd_+2):
    for c,v in enumerate(row,1): put(tr,i,c,v,fmt='#,##0' if c>1 else None)

re2 = rd_+2+len(T4)+1
put(tr,re2,1,"Planning filings and approvals, 2021–2025 (HI 2025 Table 3)",BB)
hdr(tr,re2+1,["Year","Projects filed","Units filed","Projects approved","Units approved"])
T3=[(2021,423,8041,415,3796),(2022,333,2602,235,2893),(2023,247,2674,294,3045),(2024,241,2517,245,5739),(2025,289,9614,274,3723)]
for i,row in enumerate(T3,re2+2):
    for c,v in enumerate(row,1): put(tr,i,c,v,fmt='#,##0' if c>1 else None)
widths(tr,[22,20,20,16,20,18,18,18,14])

# ================= PIPELINE =================
pp = wb.create_sheet("Pipeline_Q2_2026", 4)
put(pp,1,1,"SF Planning Housing Development Pipeline — 2026 Q2 snapshot (projects and permits as of April 2026)",T)
hdr(pp,3,["Stage","New pipeline units","Share","Definition"])
PS=[("Under Construction",3301,"Issued full building permit, or site permit + approved first construction document"),
("Building Permits Issued (site permit)",1219,"Site permit issued, no FCD yet; not counted toward RHNA"),
("Building Permits Approved",2422,"Permit approved by DBI, not yet issued"),
("Building Permits Filed",7856,"Includes estimated inclusionary units for projects that haven't declared method"),
("Building Permits Not Yet Filed (entitled)",9477,"Planning approval granted; no building permit application"),
("Applications Filed (Under Review)",13036,"Planning application filed; includes ministerial projects with BP filed"),
("Major Multi-Phased Projects (remaining)",37577,"Entitled master plans; un-permitted phases only")]
for i,(a,b,c) in enumerate(PS,4):
    put(pp,i,1,a); put(pp,i,2,b,fmt='#,##0'); put(pp,i,3,f'=B{i}/$B$11',fmt='0%'); put(pp,i,4,c)
put(pp,11,1,"Total new pipeline units",BB); put(pp,11,2,'=SUM(B4:B10)',BB,'#,##0'); put(pp,11,3,1,BB,'0%')
put(pp,12,1,"New affordable units in pipeline"); put(pp,12,2,18536,fmt='#,##0'); put(pp,12,3,'=B12/B11',fmt='0%'); put(pp,12,4,"Includes estimated inclusionary units; boosted by MOHCD Affordable Housing Pipeline data fill-in")
put(pp,13,1,"Source: https://sfplanning.org/project/pipeline-report (PDF: Housing_Production_Development_Pipeline-2026Q2.pdf). Under-construction units were 4,545 five years earlier; 'permits not yet filed' was 448 (The Frisc).",NOTE)

put(pp,15,1,"Major multi-phase projects — remaining units (Pipeline Report 2026 Q2)",BB)
hdr(pp,16,["Project","Remaining units","Master developer (per public sources)"])
for i,(n,u,sp) in enumerate(data.MP,17):
    put(pp,i,1,n); put(pp,i,2,u,fmt='#,##0'); put(pp,i,3,sp)
rmp=17+len(data.MP)
put(pp,rmp,1,"Total",BB); put(pp,rmp,2,f'=SUM(B17:B{rmp-1})',BB,'#,##0')
put(pp,rmp+2,1,"Density bonus pipeline (HI 2025 Tables 11–12, Dec 2025): 93 State Density Bonus projects = 17,554 units (4,175 affordable); 11 HOME-SF projects = 422 units (112 affordable).",NOTE)
widths(pp,[48,18,10,90])

# ================= SOURCES =================
so = wb.create_sheet("Sources")
put(so,1,1,"Sources",T)
hdr(so,2,["ID","Source","Publisher","URL","Retrieved","Covers","Refresh cadence"])
SRC=[("S1","2025 San Francisco Housing Inventory (56th ed.)","SF Planning",data.HI25,"2026-09-09","Stock, trends, 2025 completions/approvals/authorizations, affordability","Annual, ~April 1"),
("S2","2024 San Francisco Housing Inventory","SF Planning",data.HI24,"2026-09-09","2024 completions & approvals","Superseded annually"),
("S3","2023 San Francisco Housing Inventory","SF Planning",data.HI23,"2026-09-09","2023 completions, approvals, authorizations","Superseded annually"),
("S4","Housing Inventory landing page","SF Planning","https://sfplanning.org/project/housing-inventory","2026-09-09","Latest report link","Annual"),
("S5","Pipeline Report 2026 Q2 (page + PDF)","SF Planning",data.PIPE,"2026-09-09","Stage totals, affordable units, multi-phase list","Quarterly (~2 months after quarter end)"),
("S6","San Francisco Development Pipeline (dataset 6jgi-cpb4, 2026 Q2)","DataSF","https://data.sf.gov/d/6jgi-cpb4","2026-09-09","Row-level pipeline incl. sponsor, contact, BMR by AMI, neighborhood, SD; CSV export: https://data.sf.gov/api/v3/views/6jgi-cpb4/export.csv?accessType=DOWNLOAD","Quarterly"),
("S7","MOHCD/OCII Affordable Housing Pipeline (dataset aaxw-2cb8)","DataSF / MOHCD",data.MOHCD,"2026-09-09","Affordable + inclusionary projects: sponsor, status, AMI mix, schedule; CSV: https://data.sfgov.org/api/views/aaxw-2cb8/rows.csv?accessType=DOWNLOAD","Periodic (last modified 2026-02-05)"),
("S8","San Francisco Housing Dashboard","SF Planning","https://sfplanning.org/san-francisco-housing-dashboard","2026-09-09","Completed units since 2005; active pipeline by geography/affordability","Continuous"),
("S9","Dwelling Unit Completion Counts by Building Permit (j67f-aayr)","DataSF","https://data.sfgov.org/Housing-and-Buildings/Dwelling-Unit-Completion-Counts-by-Building-Permit/j67f-aayr","2026-09-09","Monthly completions (use for 2026 YTD)","Monthly"),
("S10","'SF Has Built Only 400 Homes This Year...'","The Frisc (A. Brinklow)","https://thefrisc.com/sf-has-built-only-400-homes-this-year-tens-of-thousands-more-are-waiting/","2026-09-09","2026 H1 completions (405), UC trend, MOHCD 2,000 affordable UC","n/a"),
("S11","'More homes are entering S.F.'s pipeline...'","SF Chronicle","https://www.sfchronicle.com/realestate/article/sf-homes-built-22208676.php","2026-09-09","2025 filings context (88 Bluxome, Marina Safeway, 10 SVN)","n/a"),
("S12","Comprehensive Housing Market Analysis, SF-Redwood City-SSF (2024)","HUD PD&R","https://www.huduser.gov/portal/publications/pdf/CMARtables_SanFranciscoRedwoodCitySouthSanFranciscoCA_24.pdf","2026-09-09","Inventory, tenure, vacancy (SF submarket)","Irregular"),
("S13","ACS 5-year profile, San Francisco County","Census via Social Explorer / NeighborhoodScout / Census Reporter","https://censusreporter.org/profiles/16000US0667000-san-francisco-ca","2026-09-09","Tenure, vacancy, year built (refresh from data.census.gov DP04)","Annual (Sept/Dec)"),
("S14","CTCAC/CDLAC staff reports (Transbay 2W/2E, 1515 SVN, Balboa E)","CA State Treasurer","https://www.treasurer.ca.gov/ctcac/","2026-09-09","LIHTC allocations, bond cap, investors, lenders","Per meeting"),
("S15","Citywide Affordable Housing Loan Committee agendas/evaluations","SF MOHCD","https://www.sf.gov/departments--mayors-office-housing-and-community-development","2026-09-09","City gap loans, LOSP, TDC (e.g., 1633 Valencia, Balboa A, 850 Turk)","Monthly"),
("S16","CalHFA Mixed-Income Program staff report — Sutter Street","CalHFA","https://www.calhfa.ca.gov/multifamily/mixedincome/approved/20250623-Sutter-Street.pdf","2026-09-09","1101 Sutter financing","n/a"),
("S17","SF YIMBY project coverage (300 De Haro, 88 Bluxome, TB2, Balboa, 1633 Valencia, 1101 Sutter)","SF YIMBY","https://sfyimby.com","2026-09-09","Architect, GC, cost estimates","Continuous"),
("S18","SF.gov press releases (730 Stanyan, 1515 SVN, 1633 Valencia, TB2)","City & County of SF","https://www.sf.gov/news","2026-09-09","TDC, lenders, partners","Continuous"),
("S19","CoStar — Quincy (555 Bryant) Impact Award","CoStar","https://www.costar.com/article/147377327","2026-09-09","Quincy developer/lease-up","n/a"),
("S20","SF Chronicle — DM Development 300 De Haro","SF Chronicle","https://www.sfchronicle.com/realestate/article/sf-housing-affordable-apartments-20816373.php","2026-09-09","300 De Haro cost/financing","n/a"),
("S21","Chinatown CDC — In Development (730 Stanyan)","CCDC","https://www.chinatowncdc.org/our-housing/in-development","2026-09-09","GC, architect, TDC","Continuous")]
for i,row in enumerate(SRC,3):
    for c,v in enumerate(row,1):
        cell=put(so,i,c,v)
        if c==4: cell.hyperlink=v; cell.font=LINK
widths(so,[6,54,26,60,12,60,26])

# ================= HOW TO UPDATE =================
hu = wb.create_sheet("How_to_update")
put(hu,1,1,"How to update this workbook",T)
hdr(hu,3,["Step","What","Where","How","Cadence"])
UP=[("1","Refresh citywide stock, trend, affordable tables (Stock A, Trend)","Housing Inventory (S1/S4)","Download the new PDF each April. Copy Tables 1, 2, 3, 4, 13, 23, 24, 27, 28 into the Stock/Trend tabs. Note: prior years get restated; overwrite the whole series from the newest report.","Annual (April)"),
("2","Add completed projects for the new year","Housing Inventory Appendix A-1 (market-rate ≥10 units) and A-2 (affordable ≥20 units)","Add one Projects row per project with Status = Complete, Year Completed = report year, Source URL = the PDF. Merge with existing rows if the project was already tracked (change status, add milestone to Notes).","Annual (April)"),
("3","Refresh pipeline stage totals and multi-phase list (Pipeline_Q2_2026 tab; rename tab)","Pipeline Report page (S5)","Copy the summary breakdown and the 14-project list from the quarterly page/PDF. Update Summary section A rows 14–23.","Quarterly"),
("4","Pull row-level pipeline for status changes and small projects","DataSF 6jgi-cpb4 CSV (S6)","Download CSV; filter 'net pipeline units' > 0; columns: NAMEADDR, current status, net pipeline units, pipeline affordable units, bmr units by AMI, SPONSOR, NHOOD41, SD22. Map 'current status' → normalized: Construction→Under Construction; BP BP Issued→Permitted; BP Approved/BP Filed/PL Approved→Approved; PL Filed→Under Review. Append rows not already in Projects (match on address).","Quarterly"),
("5","Refresh affordable project detail (sponsor, AMI mix, schedule)","MOHCD Affordable Housing Pipeline CSV (S7)","Download CSV; key on Project ID. Update Status (raw), construction status (0–5), est. completion, AMI columns → rewrite 'Affordability mix' cell as 'n @ x% AMI; ...'.","When modified (check 'Last Updated' on dataset page)"),
("6","2026 YTD completions","Housing Dashboard (S8) or DataSF j67f-aayr (S9)","Sum completed units for the current year; list projects ≥10 units; set Year Completed = 2026.","Monthly"),
("7","Capital stack for large projects","CTCAC/CDLAC staff reports (S14), MOHCD Loan Committee (S15), CalHFA (S16), SF YIMBY / Chronicle / Business Times (S17)","Search '<address> CTCAC staff report' for LIHTC/bond/investor; '<address> loan committee' for city loans and TDC; '<address> sfyimby' for GC/architect. Fill Total Project Cost, Equity Partners, Equity $, Lenders, Loan $. Leave blank if not found.","Per project, as milestones occur"),
("8","Tenure, vacancy, age of stock (Stock B)","data.census.gov table DP04, ACS 1-year, San Francisco County","Replace values; keep the HUD CMAR row until a newer CMAR is issued.","Annual (Sept)"),
("9","Check Summary formulas","Summary tab","Formulas are whole-column COUNTIFS/SUMIFS on Projects — no range edits needed when adding rows. Keep normalized status spellings exactly as listed in README.","After every edit")]
for i,row in enumerate(UP,4):
    for c,v in enumerate(row,1):
        cell=put(hu,i,c,v); cell.alignment=Alignment(wrap_text=True,vertical="top")
widths(hu,[6,44,40,90,22])

wb.move_sheet("Sources", offset=0)
wb.save(OUT_DIR + "SF_Housing_Stock_and_Pipeline_2026-09.xlsx")
print("saved")
