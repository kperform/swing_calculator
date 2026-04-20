"""
SWING Trade Calculator
====================
Extracted from SWING_Cal.xlsx (SWING2026 sheet)

Risk Logic Reverse-Engineered from Spreadsheet:
  ─ Risk per trade = $200 (consistent across all April 2026 active trades)
    e.g. AROC: 160 shares × $1.245 = $199.20, WFC: 40 × $5.00 = $200,
         VICI: 170 × $1.17 = $198.90, MS: 26 × $7.49 = $199.74

Max Entry Buffer Logic (from SWING system rules):
  ─ Long:  Max Entry = (Entry + ATR) × 0.95   → 5% buffer below (Entry+ATR)
  ─ Short: Max Entry = (Entry − ATR) × 1.05   → 5% buffer above (Entry−ATR)
"""

import math
import streamlit as st

# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SWING Trade Calculator",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── mobile-first CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ─ global ─ */
  html, body, [data-testid="stAppViewContainer"] {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  [data-testid="stAppViewContainer"] { padding: 0 !important; }

  /* ─ header ─ */
  .swing-header {
    background: linear-gradient(135deg, #1a2744 0%, #0d1117 100%);
    border-bottom: 1px solid #21262d;
    padding: 20px 20px 16px;
    text-align: center;
    margin-bottom: 8px;
  }
  .swing-header h1 { font-size: 1.45rem; font-weight: 700;
    background: linear-gradient(90deg, #58a6ff, #79c0ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 2px;
  }
  .swing-header p { font-size: 0.75rem; color: #8b949e; margin: 0; }

  /* ─ cards ─ */
  .card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
  }
  .card-title {
    font-size: 0.70rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #8b949e;
    margin-bottom: 12px; display: flex; align-items: center; gap: 6px;
  }

  /* ─ result rows ─ */
  .res-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 9px 0; border-bottom: 1px solid #21262d;
  }
  .res-row:last-child { border-bottom: none; }
  .res-label { font-size: 0.82rem; color: #8b949e; }
  .res-value { font-size: 0.92rem; font-weight: 600; color: #e6edf3; }
  .res-value.green  { color: #3fb950; }
  .res-value.red    { color: #f85149; }
  .res-value.blue   { color: #79c0ff; }
  .res-value.orange { color: #e3b341; }
  .res-value.purple { color: #bc8cff; }

  /* ─ big number highlight ─ */
  .big-num {
    text-align: center; padding: 14px 0 8px;
  }
  .big-num .label { font-size: 0.70rem; color: #8b949e; letter-spacing:.06em; text-transform:uppercase; margin-bottom:4px; }
  .big-num .value { font-size: 2.1rem; font-weight: 700; line-height: 1; }

  /* ─ two-col grid ─ */
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
  .mini-card {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 10px; padding: 12px; text-align: center;
  }
  .mini-card .label { font-size: 0.65rem; color: #8b949e; text-transform: uppercase; letter-spacing:.06em; margin-bottom:4px; }
  .mini-card .value { font-size: 1.15rem; font-weight: 700; }

  /* ─ alert banner ─ */
  .alert { border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; margin-bottom: 12px; }
  .alert.warn  { background: #2d1f0a; border: 1px solid #e3b341; color: #e3b341; }
  .alert.ok    { background: #0a2d10; border: 1px solid #3fb950; color: #3fb950; }
  .alert.info  { background: #0a1f2d; border: 1px solid #58a6ff; color: #79c0ff; }
  .alert.error { background: #2d0a0a; border: 1px solid #f85149; color: #f85149; }

  /* ─ section divider ─ */
  .section-label {
    font-size: 0.68rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; color: #58a6ff;
    margin: 18px 0 8px; padding-left: 2px;
  }

  /* ─ Streamlit widget overrides ─ */
  [data-testid="stNumberInput"] input,
  [data-testid="stSelectbox"] select,
  div[data-baseweb="select"] { font-size: 1rem !important; }
  [data-testid="stNumberInput"] label,
  [data-testid="stSelectbox"] label { font-size: 0.78rem !important; color: #8b949e !important; }
  div[data-testid="stNumberInput"] { margin-bottom: 4px; }
  [data-testid="stButton"] button {
    width: 100%; border-radius: 10px; font-size: 1rem;
    font-weight: 600; padding: 12px; background: #1f6feb;
    border: none; color: #fff; margin-top: 8px;
  }
  [data-testid="stButton"] button:hover { background: #388bfd; }
  .stAlert { display: none; }
  footer { display: none; }
  #MainMenu { display: none; }
  header { display: none; }
  [data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── helpers ─────────────────────────────────────────────────────────────────
def fmt(v, prefix="$", decimals=2):
    return f"{prefix}{v:,.{decimals}f}" if prefix == "$" else f"{v:,.{decimals}f}"

def color_class(v, positive_is_good=True):
    if v > 0:
        return "green" if positive_is_good else "red"
    elif v < 0:
        return "red" if positive_is_good else "green"
    return ""


# ── header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="swing-header">
  <h1>📊 SWING Trade Calculator</h1>
  <p>Position sizing · Buffer logic · Risk-to-reward</p>
</div>
""", unsafe_allow_html=True)

# ── settings sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Portfolio Settings")
    st.caption("Risk per trade extracted from SWING_Cal.xlsx — "
               "Jan-Mar 2026 trades averaged **~$100**, "
               "April 2026 active trades average **~$200**, "
               "suggesting capital was doubled ~Feb 2026.")
    risk_per_trade = st.number_input(
        "Risk Per Trade ($)",
        min_value=1.0, max_value=100000.0,
        value=200.0, step=50.0,
        help="Extracted: Jan-Mar ≈$100/trade, Apr 2026 ≈$200/trade (current)"
    )
    st.caption(f"💡 Implied capital @ 1% risk: **${risk_per_trade*100:,.0f}**")
    st.markdown("---")
    st.markdown("**Buffer logic (from SWING system):**")
    st.code("Long:  Max Entry = SL + ATR − $0.05\nShort: Max Entry = SL − ATR + $0.05")

# ── input form ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Trade Setup</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    direction = st.selectbox("Direction", ["Long", "Short"])
with col2:
    atr = st.number_input("ATR", min_value=0.001, value=2.50, step=0.01, format="%.3f")

col3, col4 = st.columns(2)
with col3:
    entry = st.number_input("Entry Price", min_value=0.01, value=50.00, step=0.01, format="%.4f")
with col4:
    stop = st.number_input("Stop Loss", min_value=0.01, value=47.50, step=0.01, format="%.4f")

calculate = st.button("Calculate")

# ── calculation ─────────────────────────────────────────────────────────────
if calculate or True:  # live recalc always

    # Validate
    is_long = direction == "Long"
    per_share_risk = entry - stop if is_long else stop - entry
    valid = per_share_risk > 0
    entry_valid_atr = (entry < entry + atr) if is_long else (entry > entry - atr)

    if not valid:
        st.markdown(f"""
        <div class="alert error">
          ⚠️ Invalid setup: Stop Loss must be {'below' if is_long else 'above'} Entry Price.
          Adjust your inputs.
        </div>""", unsafe_allow_html=True)
    else:
        # Core calcs — matching spreadsheet exactly
        shares_raw = risk_per_trade / per_share_risk
        shares = math.floor(shares_raw)
        actual_risk = shares * per_share_risk

        one_r      = per_share_risk                     # col J: per-share
        one_eight_r = one_r * 1.8                       # col K
        tp1        = entry + one_r                      # col L: =J+G  (Long)
        tp2        = entry + one_eight_r                # col M: =K+G  (Long)
        if not is_long:
            tp1 = entry - one_r
            tp2 = entry - one_eight_r

        max_profit  = one_eight_r * shares              # col N (for Long; positive)
        capital_used = entry * shares                   # col X
        atr_diff    = atr - one_r                       # col W: =V-U

        # Max Entry Buffer
        # Long:  entry must not exceed SL + ATR − $0.05
        # Short: entry must not go below SL − ATR + $0.05
        BUFFER = 0.05
        if is_long:
            max_entry = stop + atr - BUFFER
        else:
            max_entry = stop - atr + BUFFER

        # ATR adequacy check (ATR should be > 1R for quality setups)
        atr_ok = atr_diff > 0

        # ── shares highlight ───────────────────────────────────────────────
        shares_display = f"{shares:,}" if is_long else f"−{shares:,}"
        shares_color = "green" if is_long else "red"

        st.markdown(f"""
        <div class="big-num">
          <div class="label">Shares to {'Buy' if is_long else 'Sell Short'}</div>
          <div class="value {shares_color}">{shares_display}</div>
        </div>""", unsafe_allow_html=True)

        # ── mini stats row ─────────────────────────────────────────────────
        rr_ratio = one_eight_r / one_r  # always 1.8
        st.markdown(f"""
        <div class="grid2">
          <div class="mini-card">
            <div class="label">Actual Risk $</div>
            <div class="value red">${actual_risk:,.2f}</div>
          </div>
          <div class="mini-card">
            <div class="label">R:R Ratio</div>
            <div class="value green">{rr_ratio:.1f}R</div>
          </div>
          <div class="mini-card">
            <div class="label">Capital Used</div>
            <div class="value blue">${capital_used:,.2f}</div>
          </div>
          <div class="mini-card">
            <div class="label">Max Profit</div>
            <div class="value green">${max_profit:,.2f}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── max entry buffer alert ─────────────────────────────────────────
        entry_within_buffer = (entry <= max_entry) if is_long else (entry >= max_entry)
        buffer_class = "ok" if entry_within_buffer else "warn"
        buffer_icon  = "✅" if entry_within_buffer else "⚠️"
        buffer_msg   = (
            f"Entry is within the {'Long' if is_long else 'Short'} buffer zone."
            if entry_within_buffer
            else f"⚠️ Entry {'exceeds' if is_long else 'is below'} the max buffer — "
                 f"{'chasing too far above ATR range' if is_long else 'chasing too far below ATR range'}!"
        )
        st.markdown(f"""
        <div class="alert {buffer_class}">
          {buffer_icon} {buffer_msg}
        </div>""", unsafe_allow_html=True)

        # ── ATR quality check ───────────────────────────────────────────────
        atr_class = "ok" if atr_ok else "warn"
        atr_msg   = (
            f"ATR ({atr:.3f}) > 1R ({one_r:.3f}) — ATR Diff: +{atr_diff:.3f}. Quality setup."
            if atr_ok
            else f"ATR ({atr:.3f}) < 1R ({one_r:.3f}) — ATR Diff: {atr_diff:.3f}. "
                 "Tight ATR: your stop is wider than the stock's average range. "
                 "Consider a tighter entry or wider timeframe."
        )
        st.markdown(f"""
        <div class="alert {atr_class}">
          {'📐' if atr_ok else '⚡'} {atr_msg}
        </div>""", unsafe_allow_html=True)

        # ── detailed breakdown ──────────────────────────────────────────────
        st.markdown('<div class="section-label">Full Breakdown</div>', unsafe_allow_html=True)

        rows_prices = [
            ("Entry Price",             fmt(entry),          "blue"),
            ("Stop Loss",               fmt(stop),           "red"),
            ("Target P1 (1R)",          fmt(tp1),            "green"),
            ("Target P2 (1.8R)",        fmt(tp2),            "green"),
            ("Max Entry Boundary",      fmt(max_entry),      "orange"),
        ]

        rows_risk = [
            ("Per-Share Risk (1R)",     fmt(one_r),          ""),
            ("Per-Share 1.8R",          fmt(one_eight_r),    ""),
            ("Actual Dollar Risk",      fmt(actual_risk),    "red"),
            ("Max Profit @ TP2",        fmt(max_profit),     "green"),
            ("Capital Deployed",        fmt(capital_used),   "blue"),
            ("ATR",                     fmt(atr, prefix="", decimals=3), ""),
            ("ATR Diff (ATR − 1R)",     f"{'+'if atr_diff>0 else ''}{atr_diff:.3f}", "green" if atr_diff>0 else "red"),
        ]

        def render_card(title_icon, title_text, rows):
            inner = "".join(
                f'<div class="res-row">'
                f'  <span class="res-label">{lbl}</span>'
                f'  <span class="res-value {cls}">{val}</span>'
                f'</div>'
                for lbl, val, cls in rows
            )
            st.markdown(f"""
            <div class="card">
              <div class="card-title">{title_icon} {title_text}</div>
              {inner}
            </div>""", unsafe_allow_html=True)

        render_card("💰", "Price Levels", rows_prices)
        render_card("📐", "Risk & Sizing", rows_risk)

        # ── formula reference ───────────────────────────────────────────────
        with st.expander("📋 Formulas & Logic Reference", expanded=False):
            st.markdown(f"""
**Shares** (from spreadsheet pattern)
```
{'Long' if is_long else 'Short'} Shares = floor({risk_per_trade:.0f} / |{entry:.2f} − {stop:.2f}|)
                = floor({risk_per_trade:.0f} / {per_share_risk:.4f})
                = {shares:,}
```

**Targets** (col L, M in SWING_Cal.xlsx)
```
TP1 = Entry {'+ 1R' if is_long else '− 1R'} = {entry:.2f} {'+ ' if is_long else '− '}{one_r:.4f} = {tp1:.4f}
TP2 = Entry {'+ 1.8R' if is_long else '− 1.8R'} = {entry:.2f} {'+ ' if is_long else '− '}{one_eight_r:.4f} = {tp2:.4f}
```

**Max Entry Buffer** (SWING system rule)
```
{'Long:  Max Entry = SL + ATR − $0.05' if is_long else 'Short: Max Entry = SL − ATR + $0.05'}
             = {stop:.2f} {'+ ' if is_long else '− '}{atr:.3f} {'− ' if is_long else '+ '}0.05
             = {max_entry:.4f}
```

**Risk extracted from SWING_Cal.xlsx** — Apr 2026 active trades:
| Trade | Shares | ΔPrice | Risk |
|---|---|---|---|
| AROC | 160 | $1.245 | $199.20 |
| WFC  |  40 | $5.000 | $200.00 |
| VICI | 170 | $1.170 | $198.90 |
| MS   |  26 | $7.490 | $199.74 |
| AAL  | 217 | $0.918 | $199.21 |

→ **Consistent $200 risk per trade** (current setting)
""")

# ── footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:24px 0 8px;font-size:0.68rem;color:#3d444d;">
  SWING Trade Calculator · Logic extracted from SWING_Cal.xlsx<br>
  Change Risk Per Trade in ⚙️ Settings (sidebar)
</div>""", unsafe_allow_html=True)
