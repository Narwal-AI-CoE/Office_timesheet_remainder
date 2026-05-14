"""
app.py  —  Timesheet Reminder Dashboard
Run from project root: streamlit run app.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

import streamlit as st
import pandas as pd
import time

from data_processing import load_employee_data, load_timesheet_data, build_reminder_df
from email_sender import send_reminder_email
from teams_sender import send_reminder_teams

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Timesheet Reminder",
    page_icon="⏱️",
    layout="wide",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.header-bar {
    background: linear-gradient(135deg, #0f1923 0%, #1a2d42 100%);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid rgba(255,255,255,0.06);
}
.header-icon  { font-size: 36px; }
.header-title { color: #ffffff; font-size: 22px; font-weight: 700; margin: 0; letter-spacing: -0.3px; }
.header-sub   { color: #7a9bb5; font-size: 13px; margin: 2px 0 0 0; }

.stat-row  { display: flex; gap: 16px; margin-bottom: 28px; }
.stat-card {
    flex: 1; background: #ffffff; border: 1px solid #e8ecf0;
    border-radius: 10px; padding: 18px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.stat-label { font-size: 12px; color: #8a9bb0; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-value { font-size: 30px; font-weight: 700; color: #0f1923; line-height: 1.1; margin-top: 4px; }
.stat-value.amber { color: #d97706; }
.stat-value.red   { color: #dc2626; }

.badge        { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-amber  { background: #fef3c7; color: #92400e; }
.badge-red    { background: #fee2e2; color: #991b1b; }

div[data-testid="stButton"] button { border-radius: 8px; font-family: 'DM Sans', sans-serif; font-weight: 600; }
div[data-testid="stCheckbox"]      { margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
    <div class="header-icon">⏱️</div>
    <div>
        <p class="header-title">Timesheet Reminder Dashboard</p>
        <p class="header-sub">Narwal · People Operations · Auto Reminder System</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "reminder_df" not in st.session_state:
    st.session_state.reminder_df = None
if "results" not in st.session_state:
    st.session_state.results = []

DATA_FOLDER    = "data"
TIMESHEET_PATH = os.path.join(DATA_FOLDER, "Timesheet_Report.xlsx")
EMPLOYEE_PATH  = os.path.join(DATA_FOLDER, "employee_data_Export.csv")

# ─────────────────────────────────────────────
# PHASE 1 — UPLOAD (two files side by side)
# ─────────────────────────────────────────────
st.markdown("### 📂 Upload Files")

up_col1, up_col2 = st.columns(2)

with up_col1:
    st.markdown("**Employee Data** (CSV)")
    uploaded_emp = st.file_uploader(
        "employee_data_Export.csv",
        type=["csv"],
        key="emp_upload",
        label_visibility="collapsed",
    )
    if uploaded_emp:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        with open(EMPLOYEE_PATH, "wb") as f:
            f.write(uploaded_emp.read())
        st.success("✅ Employee data saved")

with up_col2:
    st.markdown("**Timesheet Report** (XLSX)")
    uploaded_ts = st.file_uploader(
        "Detail Timesheet Report",
        type=["xlsx"],
        key="ts_upload",
        label_visibility="collapsed",
    )
    if uploaded_ts:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        with open(TIMESHEET_PATH, "wb") as f:
            f.write(uploaded_ts.read())
        st.success("✅ Timesheet saved")

# Process button — only show when both files exist on disk
both_exist = os.path.exists(EMPLOYEE_PATH) and os.path.exists(TIMESHEET_PATH)

if both_exist:
    proc_col, _ = st.columns([1, 3])
    if proc_col.button("⚙️ Process & Build Reminder List", type="primary", use_container_width=True):
        with st.spinner("Processing data…"):
            try:
                employee_df  = load_employee_data()
                timesheet_df = load_timesheet_data()
                reminder_df  = build_reminder_df(employee_df, timesheet_df)

                reminder_df["channel"] = reminder_df["not_submitted_count"].apply(
                    lambda n: "Email" if n >= 4 else "Teams"
                )
                reminder_df["severity"] = reminder_df["not_submitted_count"].apply(
                    lambda n: "Critical" if n >= 4 else "Mild"
                )
                reminder_df["selected"] = True

                st.session_state.reminder_df = reminder_df
                st.session_state.results     = []
                st.success(f"✅ Done — {len(reminder_df)} employees need reminders")
            except Exception as e:
                st.error(f"❌ Processing failed: {e}")
                st.stop()
else:
    missing = []
    if not os.path.exists(EMPLOYEE_PATH):  missing.append("Employee CSV")
    if not os.path.exists(TIMESHEET_PATH): missing.append("Timesheet XLSX")
    st.info(f"⬆️ Please upload: {' and '.join(missing)}")

# ─────────────────────────────────────────────
# PHASE 2 — REVIEW TABLE
# ─────────────────────────────────────────────
if st.session_state.reminder_df is not None:
    df = st.session_state.reminder_df.copy()

    total    = len(df)
    critical = (df["severity"] == "Critical").sum()
    mild     = (df["severity"] == "Mild").sum()

    # ── Stat cards ──
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-label">Total Pending</div>
            <div class="stat-value">{total}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Critical (4+ days)</div>
            <div class="stat-value red">{critical}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Mild (1–3 days)</div>
            <div class="stat-value amber">{mild}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Via Teams</div>
            <div class="stat-value">{(df['channel']=='Teams').sum()}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Via Email</div>
            <div class="stat-value">{(df['channel']=='Email').sum()}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters + Select/Deselect buttons ──
    st.markdown("### 👥 Reminder List")
    col_f1, col_f2, col_f3, col_f4 = st.columns([1.2, 1.2, 1.2, 0.8])

    sev_options = ["All", "Critical (4+ days)", "Mild (1–3 days)"]
    ch_options  = ["All", "Teams", "Email"]
    managers    = ["All"] + sorted(df["manager_name"].dropna().unique().tolist())

    # Clear button FIRST — before any selectbox renders
    with col_f4:
        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        if st.button("✕ Clear Filters", use_container_width=True, key="btn_clear"):
            st.session_state["sb_sev"] = "All"
            st.session_state["sb_mgr"] = "All"
            st.session_state["sb_ch"]  = "All"
            st.rerun()

    # Selectboxes — key IS the state, no separate filter_ variables needed
    with col_f1:
        st.selectbox("Severity", sev_options, key="sb_sev")
    with col_f2:
        st.selectbox("Manager", managers, key="sb_mgr")
    with col_f3:
        st.selectbox("Channel", ch_options, key="sb_ch")

    # Read directly from widget state
    filter_sev = st.session_state["sb_sev"]
    filter_mgr = st.session_state["sb_mgr"]
    filter_ch  = st.session_state["sb_ch"]

    # Apply filters
    view = df.copy()
    if filter_sev == "Critical (4+ days)":
        view = view[view["severity"] == "Critical"]
    elif filter_sev == "Mild (1–3 days)":
        view = view[view["severity"] == "Mild"]
    if filter_mgr != "All":
        view = view[view["manager_name"] == filter_mgr]
    if filter_ch != "All":
        view = view[view["channel"] == filter_ch]

    # ── Table header with Select All checkbox ──
    hcols = st.columns([0.4, 2, 1.5, 1, 1, 1.5, 2])

    # Compute from actual row checkboxes in session state
    all_currently = all(
        st.session_state.get(f"sel_{i}", st.session_state.reminder_df.at[i, "selected"])
        for i in view.index
    )
    # Native checkbox — ticked = all selected, unticked = all deselected
    select_all_val = hcols[0].checkbox(
        "Select All",
        value=all_currently,
        key=f"cb_all_{all_currently}",  # key changes with state so it always re-renders correctly
        label_visibility="collapsed"
    )
    if select_all_val != all_currently:
        for i in view.index:
            st.session_state.reminder_df.at[i, "selected"] = select_all_val
            st.session_state[f"sel_{i}"] = select_all_val

    for col, h in zip(hcols[1:], ["Employee", "Manager", "Days", "Severity", "Channel", "Missing Dates"]):
        col.markdown(
            f"<span style='font-size:11px;font-weight:700;color:#8a9bb0;"
            f"text-transform:uppercase;letter-spacing:0.5px'>{h}</span>",
            unsafe_allow_html=True
        )
    st.divider()

    # ── Table rows ──
    for idx, row in view.iterrows():
        cols = st.columns([0.4, 2, 1.5, 1, 1, 1.5, 2])

        # Only set initial value — never overwrite after user clicks
        if f"sel_{idx}" not in st.session_state:
            st.session_state[f"sel_{idx}"] = st.session_state.reminder_df.at[idx, "selected"]
        cols[0].checkbox("Select", key=f"sel_{idx}", label_visibility="collapsed")
        # Always read back what user has set
        st.session_state.reminder_df.at[idx, "selected"] = st.session_state[f"sel_{idx}"]

        cols[1].markdown(
            f"**{row['full_name']}**<br>"
            f"<span style='font-size:12px;color:#8a9bb0'>{row['email']}</span>",
            unsafe_allow_html=True
        )

        cols[2].markdown(
            f"<span style='font-size:13px'>{row.get('manager_name', '—')}</span>",
            unsafe_allow_html=True
        )

        day_color = "#dc2626" if row["severity"] == "Critical" else "#d97706"
        cols[3].markdown(
            f"<span style='font-size:18px;font-weight:700;color:{day_color}'>"
            f"{row['not_submitted_count']}</span>",
            unsafe_allow_html=True
        )

        badge_cls = "badge-red" if row["severity"] == "Critical" else "badge-amber"
        cols[4].markdown(
            f"<span class='badge {badge_cls}'>{row['severity']}</span>",
            unsafe_allow_html=True
        )

        channel_choice = cols[5].selectbox(
            "Channel", ["Teams", "Email", "Both"],
            index=["Teams", "Email", "Both"].index(row["channel"]),
            key=f"ch_{idx}",
            label_visibility="collapsed"
        )
        st.session_state.reminder_df.at[idx, "channel"] = channel_choice

        dates_short = row["not_submitted_dates"]
        if len(dates_short) > 40:
            dates_short = dates_short[:40] + "…"
        cols[6].markdown(
            f"<span style='font-size:12px;font-family:DM Mono,monospace;color:#4a6375'>"
            f"{dates_short}</span>",
            unsafe_allow_html=True
        )

    st.divider()

    # ─────────────────────────────────────────────
    # PHASE 3 — SEND PANEL
    # ─────────────────────────────────────────────
    selected_df = st.session_state.reminder_df[
        st.session_state.reminder_df["selected"] == True
    ]
    n_selected = len(selected_df)
    n_teams    = (selected_df["channel"].isin(["Teams", "Both"])).sum()
    n_email    = (selected_df["channel"].isin(["Email", "Both"])).sum()

    st.markdown(f"""
    <div style='background:#0f1923;border-radius:10px;padding:16px 24px;
                border:1px solid rgba(255,255,255,0.08)'>
        <div style='color:#cdd9e5;font-size:14px'>
            <strong style='color:#fff;font-size:16px'>{n_selected}</strong> selected &nbsp;·&nbsp;
            <strong style='color:#60a5fa'>{n_teams}</strong> via Teams &nbsp;·&nbsp;
            <strong style='color:#4ade80'>{n_email}</strong> via Email
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    send_col, _ = st.columns([1, 3])
    send_clicked = send_col.button(
        f"🚀 Send {n_selected} Reminder{'s' if n_selected != 1 else ''}",
        type="primary",
        use_container_width=True,
        disabled=n_selected == 0,
    )

    if send_clicked:
        results  = []
        progress = st.progress(0, text="Sending reminders…")
        status   = st.empty()

        rows_to_send = selected_df.to_dict("records")
        total_sends  = sum(2 if r["channel"] == "Both" else 1 for r in rows_to_send)
        done = 0

        for row in rows_to_send:
            name = row["full_name"]

            if row["channel"] in ("Teams", "Both"):
                status.info(f"📨 Sending Teams message to {name}…")
                result = send_reminder_teams(row)
                results.append({**result, "name": name})
                done += 1
                progress.progress(done / total_sends, text=f"Sending… ({done}/{total_sends})")
                time.sleep(0.3)

            if row["channel"] in ("Email", "Both"):
                status.info(f"📧 Sending email to {name}…")
                result = send_reminder_email(row)
                results.append({**result, "name": name})
                done += 1
                progress.progress(done / total_sends, text=f"Sending… ({done}/{total_sends})")
                time.sleep(0.3)

        progress.empty()
        status.empty()
        st.session_state.results = results

    # ─────────────────────────────────────────────
    # RESULTS LOG
    # ─────────────────────────────────────────────
    if st.session_state.results:
        st.markdown("### 📋 Send Results")
        successes = [r for r in st.session_state.results if r["status"] == "success"]
        errors    = [r for r in st.session_state.results if r["status"] == "error"]

        if successes:
            st.success(f"✅ {len(successes)} reminder(s) sent successfully")
        if errors:
            st.error(f"❌ {len(errors)} reminder(s) failed")
            with st.expander("View errors"):
                for e in errors:
                    st.markdown(f"**{e['name']}** ({e['channel']}) → `{e.get('error', 'unknown error')}`")

        with st.expander("View full send log"):
            log_df = pd.DataFrame(st.session_state.results)
            log_df["icon"] = log_df["status"].map({"success": "✅", "error": "❌"})
            st.dataframe(
                log_df[["icon", "name", "channel", "email", "status"]].rename(
                    columns={"icon": "", "name": "Employee", "channel": "Channel",
                             "email": "Email", "status": "Status"}
                ),
                use_container_width=True,
                hide_index=True,
            )

else:
    st.markdown("""
    <div style='text-align:center;padding:60px 20px;color:#8a9bb0'>
        <div style='font-size:48px;margin-bottom:16px'>📤</div>
        <div style='font-size:18px;font-weight:600;color:#4a6375;margin-bottom:8px'>
            Upload both files and click Process to get started
        </div>
        <div style='font-size:14px'>Employee CSV + Timesheet XLSX → then hit Process</div>
    </div>
    """, unsafe_allow_html=True)