"""
Bhandari Trading Analysis Dashboard
Entry point — run with:  python -m streamlit run main.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of launch directory
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="Bhandari Trading Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Bhandari Trading Analysis Dashboard v1.0",
    },
)

# ── Inject custom CSS ────────────────────────────────────────────────────────
def _load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

_load_css()

# ── Session state defaults ───────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["RELIANCE.NS", "TCS.NS", "ADANIENT.NS", "HDFCBANK.NS"]

# ── Watchlist Sidebar ────────────────────────────────────────────────────────
def _render_watchlist_sidebar():
    from data.fetcher import get_ticker_prices
    from data.stocks_list import SYMBOL_NAMES, get_display_name
    from utils.helpers import clean_symbol

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">📋 Watchlist</div>',
            unsafe_allow_html=True,
        )

        # ── Search ──────────────────────────────────────────────────────────
        search_q = st.text_input(
            "search",
            placeholder="Search ticker or company…",
            key="wl_search_input",
            label_visibility="collapsed",
        )

        # ── Search results ───────────────────────────────────────────────────
        if search_q and len(search_q.strip()) >= 2:
            q = search_q.strip().lower()
            matches = [
                (sym, name)
                for sym, name in SYMBOL_NAMES.items()
                if q in sym.lower() or q in name.lower()
            ][:8]

            if matches:
                st.markdown(
                    '<div class="sidebar-section-label">Search Results</div>',
                    unsafe_allow_html=True,
                )
                for sym, name in matches:
                    c_sym = clean_symbol(sym)
                    sc1, sc2, sc3 = st.columns([3, 1, 1])
                    with sc1:
                        st.markdown(
                            f'<div class="wl-search-row">'
                            f'<b>{c_sym}</b><br>'
                            f'<span style="font-size:0.72rem;color:#8b949e;">{name[:24]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with sc2:
                        if st.button("➕", key=f"wl_add_{sym}", help="Add to watchlist"):
                            if sym not in st.session_state.watchlist:
                                st.session_state.watchlist.append(sym)
                            st.rerun()
                    with sc3:
                        if st.button("🔍", key=f"wl_view_{sym}", help="Analyse"):
                            if sym not in st.session_state.watchlist:
                                st.session_state.watchlist.append(sym)
                            st.session_state.selected_stock = sym
                            st.rerun()
            else:
                st.caption("No matching stocks found.")

            st.markdown("---")

        # ── Fetch live prices for watchlist ──────────────────────────────────
        wl = st.session_state.watchlist
        wl_prices: dict = {}
        if wl:
            try:
                price_list = get_ticker_prices(list(wl))
                wl_prices = {d["symbol"]: d for d in price_list}
            except Exception:
                pass

        # ── Watchlist items ──────────────────────────────────────────────────
        if wl:
            st.markdown(
                '<div class="sidebar-section-label">Your Watchlist</div>',
                unsafe_allow_html=True,
            )
            for sym in list(wl):
                name     = get_display_name(sym)
                c_sym    = clean_symbol(sym)
                pdata    = wl_prices.get(sym, {})
                price    = pdata.get("price", 0.0)
                pct      = pdata.get("pct_change", 0.0)
                clr      = "#00d4aa" if pct >= 0 else "#ff4444"
                arrow    = "▲" if pct >= 0 else "▼"
                is_sel   = st.session_state.selected_stock == sym
                sel_dot  = "● " if is_sel else ""

                price_str = f"₹{price:,.2f}" if price else "—"
                pct_str   = f"{arrow}{abs(pct):.2f}%"

                # Stock info HTML (non-interactive display)
                st.markdown(f"""
                <div class="wl-item {'wl-item-active' if is_sel else ''}">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                      <span class="wl-ticker">{sel_dot}{c_sym}</span>
                      <div class="wl-name">{name[:26]}</div>
                    </div>
                    <div style="text-align:right;">
                      <div class="wl-price">{price_str}</div>
                      <div class="wl-change" style="color:{clr};">{pct_str}</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons in a tight row
                b1, b2 = st.columns([4, 1])
                with b1:
                    if st.button(
                        f"Analyse {c_sym}",
                        key=f"wl_sel_{sym}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_stock = sym
                        st.rerun()
                with b2:
                    if st.button("✕", key=f"wl_rm_{sym}", help="Remove"):
                        st.session_state.watchlist.remove(sym)
                        if st.session_state.selected_stock == sym:
                            st.session_state.selected_stock = None
                        st.rerun()
        else:
            st.caption("Your watchlist is empty.\nUse the search above to add stocks.")

        # ── Footer ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.caption("NSE data · 15-min delayed · Powered by yfinance")


_render_watchlist_sidebar()

# ── App header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
        <div class="app-title">
            <span>Bhandari</span> Trading Analysis
        </div>
        <div class="app-sub">
            <span class="live-dot"></span>Professional Market Intelligence Dashboard
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Ticker bar (top of every page) ───────────────────────────────────────────
try:
    from components.ticker_bar import render_ticker_bar
    render_ticker_bar()
except Exception as _e:
    st.caption(f"Ticker unavailable: {_e}")

# ── Diplomatic / market news banner ─────────────────────────────────────────
try:
    from components.news_banner import render_news_banner
    render_news_banner()
except Exception as _e:
    pass

# ── Navigation (only show when not in stock detail view) ─────────────────────
PAGES = {
    "Home":     "🏠 Home",
    "Nifty100": "📊 Nifty 100",
    "Momentum": "🚀 Momentum Scanner",
}

nav_cols = st.columns(len(PAGES))
for col, (key, label) in zip(nav_cols, PAGES.items()):
    if col.button(label, key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key
        st.session_state.selected_stock = None   # exit stock detail on nav click
        st.rerun()

st.markdown("---")

# ── Page routing ─────────────────────────────────────────────────────────────
selected = st.session_state.selected_stock

try:
    if selected:
        # Stock drill-down view
        from pages.stock_detail import render_stock_detail
        render_stock_detail(selected)

    elif st.session_state.page == "Home":
        from pages.home import render_home
        render_home()

    elif st.session_state.page == "Nifty100":
        from pages.nifty100 import render_nifty100
        render_nifty100()

    elif st.session_state.page == "Momentum":
        from pages.momentum_scanner import render_momentum_scanner
        render_momentum_scanner()

except Exception as _page_err:
    import traceback
    st.error(f"Page error: {_page_err}")
    st.code(traceback.format_exc())
