import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="The Liar's Dashboard", page_icon="🔍", layout="wide")

st.markdown("""
<h1 style='text-align:center; color:#e74c3c;'>🔍 The Liar's Dashboard</h1>
<h3 style='text-align:center; color:#7f8c8d;'>Automated Data Quality Audit — Because real-world data lies.</h3>
<hr/>
""", unsafe_allow_html=True)

st.sidebar.header("📂 Upload Your Dataset")
uploaded_file = st.sidebar.file_uploader("Upload any CSV file", type=['csv'])
st.sidebar.markdown("---")
st.sidebar.markdown("**👤 Built by:** Sogana Pawankalyan")
st.sidebar.markdown("**🎓 MS Business Analytics, UConn**")
st.sidebar.markdown("**🔧 Tools:** Python · pandas · Streamlit · Plotly")

def compute_scores(df):
    total_cells = df.shape[0] * df.shape[1]
    missing_pct = df.isnull().sum().sum() / total_cells * 100
    dupe_pct = df.duplicated().sum() / len(df) * 100
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    impossible = sum(int((df[c] < 0).sum()) for c in numeric_cols)
    outliers = 0
    for c in numeric_cols:
        Q1, Q3 = df[c].quantile(0.25), df[c].quantile(0.75)
        IQR = Q3 - Q1
        outliers += int(((df[c] < Q1 - 3*IQR) | (df[c] > Q3 + 3*IQR)).sum())
    score = 100
    score -= min(missing_pct * 2, 30)
    score -= min(dupe_pct * 3, 20)
    score -= min(impossible * 0.5, 25)
    score -= min(outliers * 0.1, 25)
    return max(round(score, 1), 0), missing_pct, dupe_pct, impossible, outliers

def col_scores(df):
    rows = []
    for col in df.columns:
        score = 100
        issues = []
        miss = df[col].isnull().mean() * 100
        if miss > 0:
            score -= min(miss * 2, 40)
            issues.append(f"{miss:.1f}% missing")
        if col in df.select_dtypes(include=[np.number]).columns:
            neg = int((df[col] < 0).sum())
            if neg:
                score -= min(neg * 2, 30)
                issues.append(f"{neg} impossible values")
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            out = int(((df[col] < Q1-3*(Q3-Q1)) | (df[col] > Q3+3*(Q3-Q1))).sum())
            if out:
                score -= min(out, 20)
                issues.append(f"{out} outliers")
        score = max(round(score, 1), 0)
        emoji = "🟢" if score>=90 else "🟡" if score>=75 else "🟠" if score>=50 else "🔴"
        rows.append({"Column": col, "Trust Score": score, "Status": emoji,
                     "Issues": ", ".join(issues) or "Clean ✓"})
    return pd.DataFrame(rows).sort_values("Trust Score")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    trust, miss_pct, dupe_pct, impossible, outliers = compute_scores(df)
    color = "#27ae60" if trust>=90 else "#f39c12" if trust>=75 else "#e67e22" if trust>=50 else "#e74c3c"
    label = "EXCELLENT 🟢" if trust>=90 else "ACCEPTABLE 🟡" if trust>=75 else "POOR 🟠" if trust>=50 else "CRITICAL 🔴"

    st.markdown("## 📊 Dataset Overview")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Rows", f"{df.shape[0]:,}")
    c2.metric("Total Columns", f"{df.shape[1]}")
    c3.metric("Missing Values", f"{df.isnull().sum().sum():,}", f"{miss_pct:.1f}%")
    c4.metric("Duplicates", f"{df.duplicated().sum():,}", f"{dupe_pct:.1f}%")
    c5.metric("Outliers", f"{outliers:,}")
    st.markdown("---")

    st.markdown("## 🏆 Overall Trust Score")
    col1, col2 = st.columns([1,1])
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=trust,
            title={'text': "Data Trust Score"},
            gauge={
                'axis': {'range': [0,100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0,50],  'color': '#fadbd8'},
                    {'range': [50,75], 'color': '#fdebd0'},
                    {'range': [75,90], 'color': '#fef9e7'},
                    {'range': [90,100],'color': '#eafaf1'}
                ],
                'threshold': {'line': {'color':'black','width':4}, 'thickness':0.75, 'value':75}
            }
        ))
        fig.update_layout(height=300, margin=dict(t=40,b=0))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(f"""
        <div style='background:{color}20; border-left:5px solid {color};
                    padding:25px; border-radius:8px; margin-top:30px;'>
            <h2 style='color:{color}; margin:0;'>{label}</h2>
            <p style='font-size:16px; margin-top:10px;'>
            Score: <strong>{trust}/100</strong><br><br>
            {'✅ Safe to use for analysis.' if trust>=75
             else '⚠️ Needs cleaning before use.' if trust>=50
             else '🚨 Critical issues — do not use raw data for decisions.'}
            </p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 📋 Column Trust Scores")
    cdf = col_scores(df)
    fig2 = px.bar(cdf, x="Trust Score", y="Column", orientation='h',
                  color="Trust Score",
                  color_continuous_scale=["#e74c3c","#f39c12","#27ae60"],
                  range_color=[0,100], text="Trust Score", hover_data=["Issues"])
    fig2.add_vline(x=75, line_dash="dash", line_color="orange",
                   annotation_text="75 = Acceptable")
    fig2.update_layout(height=max(300, len(df.columns)*40), showlegend=False,
                       coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(cdf, use_container_width=True)

    st.markdown("---")
    st.markdown("## 🗺️ Missing Values Map")
    sample = df.isnull().astype(int).head(200)
    fig3 = px.imshow(sample.T, color_continuous_scale=["#27ae60","#e74c3c"],
                     aspect="auto", labels={"color":"Missing"})
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("## 📄 Executive Health Report")
    st.markdown(f"""
| Issue | Count | Severity |
|---|---|---|
| Missing Values | {df.isnull().sum().sum():,} ({miss_pct:.1f}%) | {'🔴 High' if miss_pct>10 else '🟡 Medium' if miss_pct>2 else '🟢 Low'} |
| Duplicate Rows | {df.duplicated().sum():,} ({dupe_pct:.1f}%) | {'🔴 High' if dupe_pct>5 else '🟡 Medium' if dupe_pct>1 else '🟢 Low'} |
| Impossible Values | {impossible:,} | {'🔴 High' if impossible>10 else '🟡 Medium' if impossible>0 else '🟢 None'} |
| Outliers | {outliers:,} | {'🟡 Review' if outliers>0 else '🟢 None'} |
| **Trust Score** | **{trust}/100** | **{label}** |
    """)
    report = f"""DATA QUALITY REPORT - The Liar's Dashboard
Built by: Sogana Pawankalyan | MS Business Analytics, UConn
{'='*50}
File: {uploaded_file.name}
Rows: {df.shape[0]:,} | Columns: {df.shape[1]}
{'='*50}
Missing Values:    {df.isnull().sum().sum():,} ({miss_pct:.1f}%)
Duplicate Rows:    {df.duplicated().sum():,} ({dupe_pct:.1f}%)
Impossible Values: {impossible:,}
Outliers:          {outliers:,}
{'='*50}
TRUST SCORE: {trust}/100 — {label}
"""
    st.download_button("📥 Download Report", report,
                       file_name="data_health_report.txt", mime="text/plain")

else:
    st.info("👈 Upload any CSV file from the sidebar to start your audit!")
    st.markdown("""
    ### 💡 What This Does:
    - ✅ Scans for **missing values, duplicates, outliers, impossible values**
    - ✅ Gives your dataset a **Trust Score out of 100**
    - ✅ Scores **every column individually**
    - ✅ Shows a **visual missing data heatmap**
    - ✅ Generates a **downloadable Executive Report**

    ### 🎯 Try it with the test dataset:
    Upload the file at: **`liars-dashboard/data/unemployment_raw.csv`**
    """)
