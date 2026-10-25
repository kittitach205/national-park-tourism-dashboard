"""
Dashboard จำนวนนักท่องเที่ยวในอุทยานแห่งชาติ (ปีงบประมาณ 2559–2568)
ข้อมูลจริงจาก data.go.th : https://data.go.th/dataset/gdpublish-stat-tourism
ชุดข้อมูล "ข้อมูลนักท่องเที่ยวในอุทยานแห่งชาติ" กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช

วิธีรันบนเครื่อง:
    pip install -r requirements.txt
    streamlit run app.py
"""

import re

import altair as alt
import pandas as pd
import streamlit as st

DATA_FILE = "park_tourism.csv"
SOURCE_URL = "https://data.go.th/dataset/gdpublish-stat-tourism"

# เดือนตามปีงบประมาณ (ต.ค. – ก.ย.)
MONTHS = ["ต.ค.", "พ.ย.", "ธ.ค.", "ม.ค.", "ก.พ.", "มี.ค.",
          "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย."]

GREEN = "#2d6a4f"
GREEN_LIGHT = "#95d5b2"
SAND = "#e9c46a"
CLAY = "#e76f51"


def short_office(name: str) -> str:
    """รวมชื่อสังกัดที่เขียนต่างกันในแต่ละปีให้เป็นชื่อเดียว เช่น สบอ.1, สบอ.6 สาขาปัตตานี"""
    m = re.search(r"ที่\s*(\d+)", str(name))
    if not m:
        return str(name)
    label = f"สบอ.{m.group(1)}"
    branch = re.search(r"สาขา\s*([^\s)]+)", str(name))
    return f"{label} สาขา{branch.group(1)}" if branch else label


@st.cache_data
def load_data():
    wide = pd.read_csv(DATA_FILE)
    wide["สำนัก"] = wide["สังกัด"].map(short_office)
    wide["อุทยาน"] = wide["อุทยานแห่งชาติ"].str.strip()
    wide["รวมทั้งปี"] = wide[MONTHS].sum(axis=1)
    long = wide.melt(
        id_vars=["ปี", "สำนัก", "อุทยาน"],
        value_vars=MONTHS,
        var_name="เดือน",
        value_name="นักท่องเที่ยว",
    )
    long["ลำดับเดือน"] = long["เดือน"].map({m: i for i, m in enumerate(MONTHS)})
    return wide, long


def fmt_int(x: float) -> str:
    return f"{x:,.0f}"


# ---------------- หน้าเว็บ ----------------
st.set_page_config(page_title="นักท่องเที่ยวอุทยานแห่งชาติ", page_icon="🏞️", layout="wide")

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;500;600&family=Sarabun:wght@400;600&display=swap');
    html, body, [class*="css"], p, label, li, input, button {{ font-family: 'Sarabun', sans-serif !important; }}
    h1, h2, h3, h4 {{ font-family: 'Kanit', sans-serif !important; }}
    .block-container {{ padding-top: 1.6rem; }}
    .hero {{
        background: linear-gradient(120deg, #1b4332 0%, {GREEN} 55%, #52b788 100%);
        color: #fff; border-radius: 18px; padding: 22px 28px; margin-bottom: 1rem;
    }}
    .hero h1 {{ color: #fff; margin: 0; font-size: 2rem; font-weight: 600; }}
    .hero p {{ color: #d8f3dc; margin: 4px 0 0 0; }}
    .hero a {{ color: #fefae0; }}
    div[data-testid="stMetric"] {{
        background: #f1f8f4; border: 1px solid #cfe8da; border-radius: 14px; padding: 12px 16px;
    }}
    div[data-testid="stMetricValue"] {{ color: #1b4332; font-size: 1.6rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

wide, long = load_data()
years = sorted(wide["ปี"].unique())

st.markdown(
    f"""
    <div class="hero">
      <h1>🏞️ นักท่องเที่ยวในอุทยานแห่งชาติ ปีงบประมาณ {years[0]}–{years[-1]}</h1>
      <p>กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช · {wide['อุทยาน'].nunique()} อุทยาน ·
      ข้อมูลจริงจาก <a href="{SOURCE_URL}" target="_blank">data.go.th</a></p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- Interactive Widgets (Sidebar) ----------------
with st.sidebar:
    st.header("🔎 ตัวเลือก")

    year = st.selectbox("ปีงบประมาณที่วิเคราะห์", years[::-1], index=0)

    y_from, y_to = st.slider(
        "ช่วงปีสำหรับกราฟแนวโน้ม", min_value=int(years[0]), max_value=int(years[-1]),
        value=(int(years[0]), int(years[-1])),
    )

    offices = sorted(wide["สำนัก"].unique(), key=lambda s: (int(re.search(r"\d+", s).group()), s))
    office_sel = st.multiselect("สำนักบริหารพื้นที่อนุรักษ์ (เว้นว่าง = ทั้งหมด)", offices)

    top_n = st.slider("จำนวนอุทยานในกราฟอันดับ", 5, 25, 10)

    st.caption("ปีงบประมาณเริ่ม ต.ค. ของปีก่อนหน้า ถึง ก.ย. ของปีนั้น")

# ---------------- กรองข้อมูล ----------------
w = wide if not office_sel else wide[wide["สำนัก"].isin(office_sel)]
l = long if not office_sel else long[long["สำนัก"].isin(office_sel)]

w_year = w[w["ปี"] == year]
w_prev = w[w["ปี"] == year - 1]

if w_year.empty:
    st.warning("ไม่มีข้อมูลตามตัวเลือกนี้ ลองเลือกสำนักเพิ่ม")
    st.stop()

# ---------------- KPI ----------------
total = w_year["รวมทั้งปี"].sum()
prev_total = w_prev["รวมทั้งปี"].sum()
delta = (total - prev_total) / prev_total * 100 if prev_total else None
month_sum = w_year[MONTHS].sum()
peak_month = month_sum.idxmax()
top_park = w_year.sort_values("รวมทั้งปี", ascending=False).iloc[0]
pre_covid = w[w["ปี"] == 2562]["รวมทั้งปี"].sum()

st.subheader(f"ภาพรวมปีงบประมาณ {year}" + (f" · {', '.join(office_sel)}" if office_sel else ""))
k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "นักท่องเที่ยวทั้งปี (คน)",
    fmt_int(total),
    f"{delta:+.1f}% จากปี {year - 1}" if delta is not None else None,
)
k2.metric("เดือนที่คนมากที่สุด", peak_month, f"{fmt_int(month_sum.max())} คน", delta_color="off", delta_arrow="off")
k3.metric("อุทยานยอดนิยมอันดับ 1", top_park["อุทยาน"], f"{fmt_int(top_park['รวมทั้งปี'])} คน", delta_color="off", delta_arrow="off")
k4.metric(
    "เทียบก่อนโควิด (ปี 2562)",
    f"{total / pre_covid * 100:.0f}%" if pre_covid else "-",
    "ของจำนวนปี 2562",
    delta_color="off", delta_arrow="off",
)

st.divider()

# ---------------- กราฟที่ 1: แนวโน้มรายปี ----------------
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown("#### 📈 จำนวนนักท่องเที่ยวรายปี")
    yearly = (
        w[w["ปี"].between(y_from, y_to)]
        .groupby("ปี", as_index=False)["รวมทั้งปี"].sum()
        .rename(columns={"รวมทั้งปี": "นักท่องเที่ยว"})
    )
    yearly["ปีงบ"] = yearly["ปี"].astype(str)
    yearly["ไฮไลต์"] = yearly["ปี"].eq(year).map({True: "ปีที่เลือก", False: "ปีอื่น"})
    base = alt.Chart(yearly).encode(x=alt.X("ปีงบ:O", title="ปีงบประมาณ", axis=alt.Axis(labelAngle=0)))
    area = base.mark_area(color=GREEN_LIGHT, opacity=0.45).encode(y=alt.Y("นักท่องเที่ยว:Q", title="คน"))
    line = base.mark_line(color=GREEN, strokeWidth=3).encode(y="นักท่องเที่ยว:Q")
    pts = base.mark_circle(size=90).encode(
        y="นักท่องเที่ยว:Q",
        color=alt.Color("ไฮไลต์:N", scale=alt.Scale(domain=["ปีที่เลือก", "ปีอื่น"], range=[CLAY, GREEN]), legend=None),
        tooltip=["ปีงบ", alt.Tooltip("นักท่องเที่ยว:Q", format=",")],
    )
    st.altair_chart((area + line + pts).properties(height=330), use_container_width=True)
    st.caption("ปี 2563–2564 ลดลงมากจากสถานการณ์โควิด-19 และฟื้นตัวตั้งแต่ปี 2565")

# ---------------- กราฟที่ 2: รายเดือนของปีที่เลือก เทียบปีก่อน ----------------
with c2:
    st.markdown(f"#### 📅 รายเดือน ปี {year} เทียบปี {year - 1}")
    mon = (
        l[l["ปี"].isin([year, year - 1])]
        .groupby(["ปี", "เดือน", "ลำดับเดือน"], as_index=False)["นักท่องเที่ยว"].sum()
    )
    mon["ปีงบ"] = mon["ปี"].astype(str)
    bars = (
        alt.Chart(mon)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("เดือน:N", sort=MONTHS, title="เดือน", axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("ปีงบ:N", sort=[str(year - 1), str(year)]),
            y=alt.Y("นักท่องเที่ยว:Q", title="คน"),
            color=alt.Color(
                "ปีงบ:N",
                scale=alt.Scale(domain=[str(year - 1), str(year)], range=["#b7e4c7", GREEN]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["ปีงบ", "เดือน", alt.Tooltip("นักท่องเที่ยว:Q", format=",")],
        )
        .properties(height=330)
    )
    st.altair_chart(bars, use_container_width=True)

# ---------------- กราฟที่ 3: อันดับอุทยาน ----------------
st.markdown(f"#### 🏆 {top_n} อุทยานแห่งชาติที่มีนักท่องเที่ยวมากที่สุด ปี {year}")
rank = (
    w_year.sort_values("รวมทั้งปี", ascending=False).head(top_n)[["อุทยาน", "สำนัก", "รวมทั้งปี"]]
    .rename(columns={"รวมทั้งปี": "นักท่องเที่ยว"})
)
rank_chart = (
    alt.Chart(rank)
    .mark_bar(color=GREEN, cornerRadiusEnd=4)
    .encode(
        x=alt.X("นักท่องเที่ยว:Q", title="คน"),
        y=alt.Y("อุทยาน:N", sort="-x", title=None, axis=alt.Axis(labelLimit=300, labelOverlap=False)),
        tooltip=["อุทยาน", "สำนัก", alt.Tooltip("นักท่องเที่ยว:Q", format=",")],
    )
    .properties(height=alt.Step(28))
)
labels = rank_chart.mark_text(align="left", dx=4, color="#1b4332").encode(text=alt.Text("นักท่องเที่ยว:Q", format=","))
st.altair_chart(rank_chart + labels, use_container_width=True)

# ---------------- กราฟที่ 4: Heatmap ฤดูกาลท่องเที่ยว ----------------
st.markdown("#### 🌡️ ฤดูกาลท่องเที่ยว: จำนวนนักท่องเที่ยวรายเดือนในแต่ละปี")
heat = (
    l[l["ปี"].between(y_from, y_to)]
    .groupby(["ปี", "เดือน", "ลำดับเดือน"], as_index=False)["นักท่องเที่ยว"].sum()
)
heat["ปีงบ"] = heat["ปี"].astype(str)
heatmap = (
    alt.Chart(heat)
    .mark_rect(cornerRadius=3)
    .encode(
        x=alt.X("เดือน:N", sort=MONTHS, title="เดือน", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("ปีงบ:O", title="ปีงบประมาณ"),
        color=alt.Color("นักท่องเที่ยว:Q", scale=alt.Scale(scheme="greens"), legend=alt.Legend(title="คน", format="~s")),
        tooltip=["ปีงบ", "เดือน", alt.Tooltip("นักท่องเที่ยว:Q", format=",")],
    )
    .properties(height=alt.Step(30))
)
st.altair_chart(heatmap, use_container_width=True)
st.caption("สีเข้ม = นักท่องเที่ยวมาก · ช่วง ธ.ค.–ม.ค. เป็นช่วงที่คนเที่ยวอุทยานมากที่สุดเกือบทุกปี")

# ---------------- เปรียบเทียบอุทยานที่สนใจ ----------------
st.markdown("#### 🔍 เปรียบเทียบอุทยานที่สนใจ")
park_opts = sorted(w["อุทยาน"].unique())
default_parks = [p for p in rank["อุทยาน"].head(3)]
park_sel = st.multiselect("เลือกอุทยาน (ได้หลายแห่ง)", park_opts, default=default_parks)
if park_sel:
    cmp = (
        w[w["อุทยาน"].isin(park_sel) & w["ปี"].between(y_from, y_to)]
        .groupby(["ปี", "อุทยาน"], as_index=False)["รวมทั้งปี"].sum()
        .rename(columns={"รวมทั้งปี": "นักท่องเที่ยว"})
    )
    cmp["ปีงบ"] = cmp["ปี"].astype(str)
    cmp_chart = (
        alt.Chart(cmp)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("ปีงบ:O", title="ปีงบประมาณ", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("นักท่องเที่ยว:Q", title="คน"),
            color=alt.Color("อุทยาน:N", legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["อุทยาน", "ปีงบ", alt.Tooltip("นักท่องเที่ยว:Q", format=",")],
        )
        .properties(height=320)
    )
    st.altair_chart(cmp_chart, use_container_width=True)
else:
    st.info("เลือกอุทยานอย่างน้อย 1 แห่งเพื่อดูกราฟเปรียบเทียบ")

# ---------------- ตารางข้อมูล ----------------
with st.expander(f"📋 ตารางข้อมูลปี {year}"):
    table = w_year[["อุทยาน", "สำนัก", *MONTHS, "รวมทั้งปี"]].sort_values("รวมทั้งปี", ascending=False)
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button(
        "⬇️ ดาวน์โหลด CSV",
        table.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"park_tourism_{year}.csv",
        mime="text/csv",
    )

st.caption(f"ที่มา: ชุดข้อมูล “ข้อมูลนักท่องเที่ยวในอุทยานแห่งชาติ” กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช — {SOURCE_URL}")
