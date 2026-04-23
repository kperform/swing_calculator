"""
SWING Calculator
====================

Risk Logic:
  ─ Risk per trade = Capital × Risk %
    Default: $100,000 × 0.2% = $200/trade
    e.g. AROC: 160 shares × $1.245 = $199.20, WFC: 40 × $5.00 = $200,
         VICI: 170 × $1.17 = $198.90, MS: 26 × $7.49 = $199.74

Max Entry Buffer Logic (from SWING system rules):
  ─ Long:  Max Entry = (Stop + ATR) × (1 − Buffer%)   → default 5% buffer
  ─ Short: Max Entry = (Stop − ATR) × (1 + Buffer%)   → default 5% buffer

Profit Targets (configurable, defaults: P1 = 1R, P2 = 1.8R):
  ─ Long:  TP1 = Entry + P1×1R  |  TP2 = Entry + P2×1R
  ─ Short: TP1 = Entry − P1×1R  |  TP2 = Entry − P2×1R
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
    st.caption("All fields are optional — defaults match the original SWING_Cal.xlsx settings.")

    # ── Capital & Risk ──────────────────────────────────────────────────────
    st.markdown("#### 💼 Capital & Risk")
    capital = st.number_input(
        "Account Capital ($)",
        min_value=1000.0, max_value=100_000_000.0,
        value=100_000.0, step=5000.0,
        format="%.0f",
        help="Total trading capital. Default: $100,000"
    )
    risk_pct = st.number_input(
        "Risk Per Trade (%)",
        min_value=0.01, max_value=10.0,
        value=0.20, step=0.05,
        format="%.2f",
        help="Percentage of capital risked per trade. Default: 0.20% → $200 on $100k"
    )
    risk_per_trade = capital * (risk_pct / 100)
    st.caption(f"💡 Risk per trade: **${risk_per_trade:,.2f}**  "
               f"({risk_pct:.2f}% of ${capital:,.0f})")

    st.markdown("---")

    # ── ATR Buffer ──────────────────────────────────────────────────────────
    st.markdown("#### 🛡️ ATR Entry Buffer")
    buffer_pct = st.number_input(
        "Max Entry Buffer (%)",
        min_value=0.0, max_value=50.0,
        value=5.0, step=0.5,
        format="%.1f",
        help=(
            "Buffer applied to the ATR boundary to define the max allowable entry.\n"
            "Default: 5%\n"
            "Long:  Max Entry = (Stop + ATR) × (1 − Buffer%)\n"
            "Short: Max Entry = (Stop − ATR) × (1 + Buffer%)"
        )
    )

    st.markdown("---")

    # ── Profit Targets ──────────────────────────────────────────────────────
    st.markdown("#### 🎯 Profit Target Ratios")
    p1_ratio = st.number_input(
        "P1 Target (×R)",
        min_value=0.1, max_value=20.0,
        value=1.0, step=0.1,
        format="%.1f",
        help="First profit target as a multiple of 1R. Default: 1.0 (1:1)"
    )
    p2_ratio = st.number_input(
        "P2 Target (×R)",
        min_value=0.1, max_value=20.0,
        value=1.8, step=0.1,
        format="%.1f",
        help="Second profit target as a multiple of 1R. Default: 1.8 (1:1.8)"
    )

    st.markdown("---")
    st.markdown("**Buffer formula (SWING system):**")
    st.code(
        f"Long:  Max Entry = (SL + ATR) × {1 - buffer_pct/100:.4f}\n"
        f"Short: Max Entry = (SL − ATR) × {1 + buffer_pct/100:.4f}"
    )

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

    if not valid:
        st.markdown(f"""
        <div class="alert error">
          ⚠️ Invalid setup: Stop Loss must be {'below' if is_long else 'above'} Entry Price.
          Adjust your inputs.
        </div>""", unsafe_allow_html=True)
    else:
        # ── Core calcs ──────────────────────────────────────────────────────
        shares_raw = risk_per_trade / per_share_risk
        shares = math.floor(shares_raw)
        actual_risk = shares * per_share_risk

        one_r       = per_share_risk                      # 1R per share
        p1_r        = one_r * p1_ratio                    # P1 per share (default 1R)
        p2_r        = one_r * p2_ratio                    # P2 per share (default 1.8R)

        if is_long:
            tp1 = entry + p1_r
            tp2 = entry + p2_r
        else:
            tp1 = entry - p1_r
            tp2 = entry - p2_r

        max_profit   = p2_r * shares                      # max profit at TP2
        capital_used = entry * shares                     # capital deployed
        atr_diff     = atr - one_r                        # ATR vs 1R spread

        # ── Max Entry Buffer ─────────────────────────────────────────────────
        # Long:  Max Entry = (Stop + ATR) × (1 − buffer_pct/100)
        # Short: Max Entry = (Stop − ATR) × (1 + buffer_pct/100)
        buf_multiplier_long  = 1 - (buffer_pct / 100)
        buf_multiplier_short = 1 + (buffer_pct / 100)

        if is_long:
            max_entry = (stop + atr) * buf_multiplier_long
        else:
            max_entry = (stop - atr) * buf_multiplier_short

        # ATR adequacy check (ATR should be > 1R for quality setups)
        atr_ok = atr_diff > 0

        # ── Shares highlight ─────────────────────────────────────────────────
        shares_display = f"{shares:,}" if is_long else f"−{shares:,}"
        shares_color   = "green" if is_long else "red"

        st.markdown(f"""
        <div class="big-num">
          <div class="label">Shares to {'Buy' if is_long else 'Sell Short'}</div>
          <div class="value {shares_color}">{shares_display}</div>
        </div>""", unsafe_allow_html=True)

        # ── Mini stats row ───────────────────────────────────────────────────
        rr_display = f"{p1_ratio:.1f}R / {p2_ratio:.1f}R"
        st.markdown(f"""
        <div class="grid2">
          <div class="mini-card">
            <div class="label">Actual Risk $</div>
            <div class="value red">${actual_risk:,.2f}</div>
          </div>
          <div class="mini-card">
            <div class="label">P1 / P2 Ratio</div>
            <div class="value green">{rr_display}</div>
          </div>
          <div class="mini-card">
            <div class="label">Capital Used</div>
            <div class="value blue">${capital_used:,.2f}</div>
          </div>
          <div class="mini-card">
            <div class="label">Max Profit (P2)</div>
            <div class="value green">${max_profit:,.2f}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Max entry buffer alert ───────────────────────────────────────────
        entry_within_buffer = (entry <= max_entry) if is_long else (entry >= max_entry)
        buffer_class = "ok"   if entry_within_buffer else "warn"
        buffer_icon  = "✅"   if entry_within_buffer else "⚠️"
        buffer_msg   = (
            f"Entry is within the {'Long' if is_long else 'Short'} buffer zone "
            f"({buffer_pct:.1f}% buffer applied)."
            if entry_within_buffer
            else f"⚠️ Entry {'exceeds' if is_long else 'is below'} the max buffer "
                 f"({buffer_pct:.1f}%) — "
                 f"{'chasing too far above ATR range' if is_long else 'chasing too far below ATR range'}!"
        )
        st.markdown(f"""
        <div class="alert {buffer_class}">
          {buffer_icon} {buffer_msg}
        </div>""", unsafe_allow_html=True)

        # ── ATR quality check ────────────────────────────────────────────────
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

        # ── Detailed breakdown ───────────────────────────────────────────────
        st.markdown('<div class="section-label">Full Breakdown</div>', unsafe_allow_html=True)

        rows_prices = [
            ("Entry Price",                              fmt(entry),     "blue"),
            ("Stop Loss",                                fmt(stop),      "red"),
            (f"Target P1 (1:{p1_ratio:.1f}R)",          fmt(tp1),       "green"),
            (f"Target P2 (1:{p2_ratio:.1f}R)",          fmt(tp2),       "green"),
            (f"Max Entry Boundary ({buffer_pct:.1f}%)", fmt(max_entry), "orange"),
        ]

        rows_risk = [
            ("Per-Share Risk (1R)",                      fmt(one_r),                          ""),
            (f"Per-Share P1 ({p1_ratio:.1f}R)",          fmt(p1_r),                           ""),
            (f"Per-Share P2 ({p2_ratio:.1f}R)",          fmt(p2_r),                           ""),
            ("Actual Dollar Risk",                        fmt(actual_risk),                    "red"),
            ("Max Profit @ P2",                          fmt(max_profit),                     "green"),
            ("Capital Deployed",                         fmt(capital_used),                   "blue"),
            (f"Risk % of Capital",                       f"{(actual_risk/capital)*100:.3f}%", ""),
            ("ATR",                                      fmt(atr, prefix="", decimals=3),     ""),
            ("ATR Diff (ATR − 1R)",                      f"{'+'if atr_diff>0 else ''}{atr_diff:.3f}",
                                                         "green" if atr_diff > 0 else "red"),
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

        # ── Formula reference ────────────────────────────────────────────────
        with st.expander("📋 Formulas & Logic Reference", expanded=False):
            st.markdown(f"""
**Shares** (from spreadsheet pattern)
```
{'Long' if is_long else 'Short'} Shares = floor({risk_per_trade:.2f} / |{entry:.2f} − {stop:.2f}|)
                = floor({risk_per_trade:.2f} / {per_share_risk:.4f})
                = {shares:,}
```

**Risk Per Trade** (from sidebar settings)
```
Risk = ${capital:,.0f} × {risk_pct:.2f}% = ${risk_per_trade:,.2f}
```

**Targets** (configurable P1 / P2 ratios)
```
TP1 = Entry {'+ ' if is_long else '− '}P1×1R = {entry:.2f} {'+ ' if is_long else '− '}{p1_ratio:.1f}×{one_r:.4f} = {tp1:.4f}
TP2 = Entry {'+ ' if is_long else '− '}P2×1R = {entry:.2f} {'+ ' if is_long else '− '}{p2_ratio:.1f}×{one_r:.4f} = {tp2:.4f}
```

**Max Entry Buffer** ({buffer_pct:.1f}% — configurable in sidebar)
```
{'Long:  Max Entry = (Stop + ATR) × (1 − buffer%)' if is_long else 'Short: Max Entry = (Stop − ATR) × (1 + buffer%)'}
             = ({stop:.2f} {'+ ' if is_long else '− '}{atr:.3f}) × {buf_multiplier_long if is_long else buf_multiplier_short:.4f}
             = {max_entry:.4f}
```

**Risk extracted from sample trades:
| Trade | Shares | ΔPrice | Risk |
|---|---|---|---|
| AROC | 160 | $1.245 | $199.20 |
| WFC  |  40 | $5.000 | $200.00 |
| VICI | 170 | $1.170 | $198.90 |
| MS   |  26 | $7.490 | $199.74 |
| AAL  | 217 | $0.918 | $199.21 |

→ **Consistent $200 risk per trade** (0.2% of $100,000 — current default)
""")

# ── footer ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:24px 0 8px;font-size:0.68rem;color:#3d444d;">
  SWING Trade Calculator · Logic extracted from SWING_Cal.xlsx<br>
  Adjust Capital, Risk %, Buffer & P1/P2 Targets in ⚙️ Settings (sidebar)
</div>""", unsafe_allow_html=True)
