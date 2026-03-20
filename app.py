import streamlit as st
from checker import run_quality_check
from utils import parse_checklist

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Code Quality Checker",
    page_icon="🔍",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}
code, pre, .stCodeBlock, textarea {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Header */
.hero {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d1b2a 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem 2rem 2rem;
    margin-bottom: 2rem;
    border: 1px solid #2a2a5a;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%);
    border-radius: 50%;
}
.hero h1 {
    color: #e2e8f0;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.5px;
}
.hero p {
    color: #94a3b8;
    margin: 0;
    font-size: 1rem;
}
.badge {
    display: inline-block;
    background: rgba(99,102,241,0.2);
    color: #818cf8;
    border: 1px solid rgba(99,102,241,0.4);
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Result cards */
.result-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.result-card:hover { border-color: #334155; }

.result-card .item-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: #e2e8f0;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.result-card .observation {
    color: #94a3b8;
    font-size: 0.88rem;
    line-height: 1.6;
    margin-bottom: 0.5rem;
}
.result-card .suggestion {
    color: #6ee7b7;
    font-size: 0.85rem;
    line-height: 1.5;
    background: rgba(110,231,183,0.07);
    border-left: 3px solid #6ee7b7;
    padding: 0.5rem 0.75rem;
    border-radius: 0 6px 6px 0;
    margin-top: 0.5rem;
}
.status-pass { color: #4ade80; }
.status-warn { color: #facc15; }
.status-fail { color: #f87171; }

/* Section headers */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.5rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0b0f1a;
    border-right: 1px solid #1e293b;
}
</style>
""", unsafe_allow_html=True)

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="badge">AI-Powered</div>
    <h1>🔍 Code Quality Checker</h1>
    <p>Paste your code and a checklist — get observations and improvement suggestions instantly.</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.info("Set your API credentials in the `.env` file. See `README.md` for details.", icon="🔑")
    st.markdown("---")
    st.markdown("### 📋 Checklist Format")
    st.markdown("""
Enter one item per line, e.g.:
```
1. Code follows PEP8
2. Functions have docstrings
3. No hardcoded credentials
4. Error handling present
5. No unused imports
```
    """)
    st.markdown("---")
    st.markdown("### 🗂 Language Hint *(optional)*")
    language = st.selectbox(
        "Code language",
        ["Auto-detect", "Python", "JavaScript", "TypeScript",
         "Java", "C++", "Go", "Rust", "SQL", "Other"],
        label_visibility="collapsed"
    )

# ── Main layout ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="section-label">Your Code</div>', unsafe_allow_html=True)
    code_input = st.text_area(
        label="code",
        placeholder="# Paste your code here...\ndef hello():\n    print('Hello, world!')",
        height=340,
        label_visibility="collapsed",
    )

with col2:
    st.markdown('<div class="section-label">Quality Checklist</div>', unsafe_allow_html=True)
    checklist_input = st.text_area(
        label="checklist",
        placeholder="1. Functions have docstrings\n2. No hardcoded secrets\n3. Proper error handling\n4. PEP8 compliance\n5. No unused imports",
        height=340,
        label_visibility="collapsed",
    )

# ── Run button ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
run_col, _, info_col = st.columns([2, 3, 2])
with run_col:
    run_btn = st.button("🚀 Run Quality Check", use_container_width=True, type="primary")
with info_col:
    if code_input:
        lines = code_input.strip().count('\n') + 1
        st.caption(f"📄 {lines} lines · {len(code_input)} chars")

# ── Results ───────────────────────────────────────────────────────────────────
if run_btn:
    if not code_input.strip():
        st.warning("⚠️ Please paste some code first.")
    elif not checklist_input.strip():
        st.warning("⚠️ Please enter at least one checklist item.")
    else:
        checklist_items = parse_checklist(checklist_input)
        lang = None if language == "Auto-detect" else language

        with st.spinner("🤖 Analysing your code..."):
            results = run_quality_check(code_input, checklist_items, lang)

        if "error" in results:
            st.error(f"❌ {results['error']}")
        else:
            st.markdown("---")
            st.markdown("## 📊 Quality Report")

            # Summary bar
            total = len(results["items"])
            passes = sum(1 for r in results["items"] if r["status"] == "pass")
            warns  = sum(1 for r in results["items"] if r["status"] == "warn")
            fails  = sum(1 for r in results["items"] if r["status"] == "fail")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Checks", total)
            m2.metric("✅ Passed",  passes)
            m3.metric("⚠️ Warnings", warns)
            m4.metric("❌ Issues",  fails)

            st.markdown("<br>", unsafe_allow_html=True)

            # Individual results
            status_icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
            status_class = {"pass": "status-pass", "warn": "status-warn", "fail": "status-fail"}

            for item in results["items"]:
                icon  = status_icon.get(item["status"], "🔹")
                cls   = status_class.get(item["status"], "")
                sugg  = f'<div class="suggestion">💡 <strong>Suggestion:</strong> {item["suggestion"]}</div>' \
                        if item.get("suggestion") else ""

                st.markdown(f"""
<div class="result-card">
    <div class="item-title">
        <span>{icon}</span>
        <span class="{cls}">{item['checklist_item']}</span>
    </div>
    <div class="observation">📝 {item['observation']}</div>
    {sugg}
</div>
""", unsafe_allow_html=True)

            # Overall summary
            if results.get("overall_summary"):
                st.markdown("---")
                st.markdown("### 🧠 Overall Summary")
                st.info(results["overall_summary"])

            # Download report
            report_md = "# Code Quality Report\n\n"
            for item in results["items"]:
                report_md += f"## {item['checklist_item']}\n"
                report_md += f"**Status:** {item['status'].upper()}\n\n"
                report_md += f"**Observation:** {item['observation']}\n\n"
                if item.get("suggestion"):
                    report_md += f"**Suggestion:** {item['suggestion']}\n\n"
                report_md += "---\n\n"

            st.download_button(
                "⬇️ Download Report (.md)",
                data=report_md,
                file_name="code_quality_report.md",
                mime="text/markdown",
            )
