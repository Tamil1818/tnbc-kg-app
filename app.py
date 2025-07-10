# app.py

import streamlit as st
import pandas as pd
from pyvis.network import Network
from streamlit.components.v1 import html
import os

# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="TNBC KG", layout="wide")
DATA_PATH = "data/tnbc_kg_triplets.csv"

# ----------------------------
# Load KG
# ----------------------------
@st.cache_data
def load_kg():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        st.error("❌ Data file not found.")
        return pd.DataFrame()

trip = load_kg()

# ----------------------------
# Page Title
# ----------------------------
st.markdown("<h1>🔬 TNBC Clinical Trial Knowledge Graph</h1><hr>", unsafe_allow_html=True)

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("🎯 Filters")
q = st.sidebar.text_input("🔍 Search")
rels = st.sidebar.multiselect("Relations", ["All"] + sorted(trip["relation"].unique()), default=["All"])

df = trip if "All" in rels else trip[trip["relation"].isin(rels)]

if q:
    df = df[df["head"].str.contains(q, case=False) | df["tail"].str.contains(q, case=False)]

# ----------------------------
# Show Table
# ----------------------------
st.subheader("📄 Triplets")
st.dataframe(df.head(200), use_container_width=True)

# ----------------------------
# Node Coloring Function
# ----------------------------
def infer_type(node):
    node = str(node).strip()
    if node.startswith("NCT"):
        return "TRIAL"
    elif node.upper() in ["PD-1", "PD-L1", "BRCA1", "BRCA2", "VEGF", "HER2", "EGFR", "TP53", "AKT1", "PIK3CA"]:
        return "GENE"
    elif "university" in node.lower() or "center" in node.lower() or "institute" in node.lower():
        return "SPONSOR"
    elif any(k in node.lower() for k in ["umab", "limab", "tinib", "drug", "ol", "inib", "umab"]):
        return "DRUG"
    elif len(node) < 12 and node.isupper():
        return "BIOMARKER"
    else:
        return "OTHER"

color_map = {
    "GENE": "#FF6B6B",
    "DRUG": "#89CFF0",
    "TRIAL": "#B0E57C",
    "SPONSOR": "#FFD700",
    "BIOMARKER": "#FFA07A",
    "OTHER": "#D3D3D3"
}

# ----------------------------
# Draw Network Function
# ----------------------------
def draw_network(df, limit=100):
    df = df.dropna(subset=["head", "tail", "relation"]).copy()
    df = df.head(limit)

    net = Network(height="600px", width="100%", directed=True)

    nodes = set(df["head"]).union(set(df["tail"]))

    for node in nodes:
        ntype = infer_type(node)
        color = color_map.get(ntype, "#D3D3D3")
        tooltip = f"{ntype} Node: {node}"
        net.add_node(str(node), label=str(node), color=color, title=tooltip)

    for _, r in df.iterrows():
        relation_label = str(r["relation"])
        net.add_edge(str(r["head"]), str(r["tail"]), label=relation_label, title=f"{r['head']} → {r['tail']}: {relation_label}")

    return net

# ----------------------------
# Show Graph
# ----------------------------
st.subheader("🧠 Graph View")

if df.empty:
    st.warning("No data to show.")
else:
    net = draw_network(df, limit=150)
    net.save_graph("kg.html")
    with open("kg.html", "r", encoding="utf-8") as f:
        html(f.read(), height=600, scrolling=True)

# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.caption("🚀 Built with ❤️ for TNBC Research • Streamlit • PyVis • ClinicalTrials.gov")
