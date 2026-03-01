import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import calendar

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="369 ELITE V42", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; text-shadow: 0 0 20px rgba(0,255,204,0.4); padding: 10px 0; }
    
    /* Metric Dynamic Colors */
    div[data-testid="stMetricDelta"] > div { font-weight: bold !important; }
    div[data-testid="stMetricDelta"] > div[data-direction="down"] { color: #ef4444 !important; }
    div[data-testid="stMetricDelta"] > div[data-direction="up"] { color: #34d399 !important; }
    
    /* Calendar Styling (المستطيلات) */
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-top: 20px; }
    .cal-header { text-align: center; color: #8b949e; font-weight: bold; padding-bottom: 5px; }
    .cal-card { border-radius: 8px; padding: 10px; text-align: center; min-height: 90px; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }
    .cal-win { background: linear-gradient(135deg, rgba(45, 101, 74, 0.4), rgba(20, 50, 40, 0.6)); border-top: 4px solid #34d399; }
    .cal-loss { background: linear-gradient(135deg, rgba(127, 45, 45, 0.4), rgba(60, 20, 20, 0.6)); border-top: 4px solid #ef4444; }
    .cal-be { background: linear-gradient(135deg, rgba(180, 130, 40, 0.4), rgba(80, 60, 20, 0.6)); border-top: 4px solid #fbbf24; }
    .cal-empty { background: #161b22; opacity: 0.3; }
    .cal-date { font-size: 0.9rem; font-weight: bold; margin-bottom: 5px; color: #8b949e; }
    .cal-pnl { font-size: 0.85rem; font-weight: 600; }
    .cal-trades { font-size: 0.7rem; opacity: 0.8; }
    
    div[data-testid="stMetric"] { background: rgba(22, 27, 34, 0.7) !important; border: 1px solid #30363d !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_v42.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, 
              outcome TEXT, pnl REAL, rr REAL, balance REAL, mindset TEXT, setup TEXT, timestamp DATETIME)''')
conn.commit()

# --- 3. DATA PREP ---
df = pd.read_sql_query("SELECT * FROM trades", conn)
current_balance = 0.0
daily_net_pnl = 0.0
initial_bal = 1000.0

if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    # إصلاح الشارت: ترتيب الصفقات حسب الـ ID والوقت باش ميبانوش عموديين
    df = df.sort_values(by=['date_dt', 'id'])
    initial_bal = df['balance'].iloc[0]
    df['cum_pnl'] = df['pnl'].cumsum()
    df['equity_curve'] = initial_bal + df['cum_pnl']
    current_balance = df['equity_curve'].iloc[-1]
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    daily_net_pnl = df[df['date'] == today_str]['pnl'].sum()

# --- 4. HEADER ---
st.markdown('<h1 class="main-title">369 TRACKER PRO</h1>', unsafe_allow_html=True)
col_eq1, col_eq2, col_eq3 = st.columns([1, 1.5, 1])
with col_eq2:
    st.metric(label="CURRENT EQUITY", value=f"${current_balance:,.2f}", 
              delta=f"{daily_net_pnl:+.2f} USD Today", delta_color="normal")

tabs = st.tabs(["🚀 TERMINAL", "📅 CALENDAR LOG", "📊 MONTHLY %", "🧬 ANALYZERS", "📜 JOURNAL"])

# --- TAB 1: TERMINAL (Improved Real-Chart) ---
with tabs[0]:
    c1, c2 = st.columns([1, 2.2])
    with c1:
        with st.form("entry_v42", clear_on_submit=True):
            bal_in = st.number_input("Initial Balance ($)", value=initial_bal)
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Pair", "XAUUSD").upper()
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            p_val = st.number_input("P&L ($)", value=0.0)
            r_val = st.number_input("RR Ratio", value=0.0)
            setup = st.text_input("Setup").upper()
            mind = st.selectbox("Mindset", ["Focused", "Impulsive", "Revenge", "Bored"])
            if st.form_submit_button("LOCK TRADE"):
                c.execute("INSERT INTO trades (date, pair, outcome, pnl, rr, balance, mindset, setup, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                          (str(d_in), asset, res, p_val, r_val, bal_in, mind, setup, datetime.now()))
                conn.commit()
                st.rerun()
    with c2:
        if not df.empty:
            fig_eq = go.Figure()
            fig_eq.add_hline(y=initial_bal, line_dash="dash", line_color="rgba(255,255,255,0.2)")
            # استعمال index كـ X-axis باش يفرق الصفقات اللي في نفس النهار
            fig_eq.add_trace(go.Scatter(
                x=list(range(len(df))), y=df['equity_curve'], mode='lines+markers',
                line=dict(color='#00ffcc', width=3, shape='spline'),
                fill='tonexty', fillcolor='rgba(0,255,204,0.1)',
                marker=dict(size=7, color='#00ffcc'),
                hovertemplate="Trade: %{x}<br>Equity: $%{y:.2f}<extra></extra>"
            ))
            fig_eq.update_layout(template="plotly_dark", height=450, xaxis_title="Trade Sequence", yaxis_title="Equity ($)")
            st.plotly_chart(fig_eq, use_container_width=True)

# --- TAB 2: CALENDAR LOG (إصلاح المستطيلات) ---
with tabs[1]:
    if not df.empty:
        today = datetime.now()
        cal = calendar.monthcalendar(today.year, today.month)
        st.markdown(f"### 📅 {today.strftime('%B %Y')}")
        
        # Header الأيام
        h_cols = st.columns(7)
        for i, d_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            h_cols[i].markdown(f'<p class="cal-header">{d_name}</p>', unsafe_allow_html=True)
            
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].markdown('<div class="cal-card cal-empty"></div>', unsafe_allow_html=True)
                else:
                    curr_date = datetime(today.year, today.month, day).strftime('%Y-%m-%d')
                    day_df = df[df['date'] == curr_date]
                    p_sum = day_df['pnl'].sum()
                    t_count = len(day_df)
                    
                    status = "cal-empty"
                    if t_count > 0:
                        status = "cal-win" if p_sum > 0 else "cal-loss" if p_sum < 0 else "cal-be"
                    
                    pnl_text = f"${p_sum:,.2f}" if t_count > 0 else ""
                    trades_text = f"{t_count} Trades" if t_count > 0 else ""
                    
                    cols[i].markdown(f"""
                        <div class="cal-card {status}">
                            <div class="cal-date">{day}</div>
                            <div class="cal-pnl">{pnl_text}</div>
                            <div class="cal-trades">{trades_text}</div>
                        </div>
                    """, unsafe_allow_html=True)

# --- TAB 3: MONTHLY % (Zero Center) ---
with tabs[2]:
    if not df.empty:
        df['month'] = df['date_dt'].dt.strftime('%b %Y')
        m_df = df.groupby('month')['pnl'].sum().reset_index()
        fig_m = go.Figure(go.Bar(x=m_df['month'], y=m_df['pnl'], 
                                marker_color=['#34d399' if x > 0 else '#ef4444' for x in m_df['pnl']]))
        fig_m.update_layout(template="plotly_dark", yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='white'))
        st.plotly_chart(fig_m, use_container_width=True)

# --- TAB 4: ANALYZERS ---
with tabs[3]:
    if not df.empty:
        st.subheader("🧬 Performance DNA")
        avg_w = df[df['pnl'] > 0]['pnl'].mean() if not df[df['pnl'] > 0].empty else 1
        avg_l = abs(df[df['pnl'] < 0]['pnl'].mean()) if not df[df['pnl'] < 0].empty else 1
        wr = len(df[df['outcome']=='WIN']) / len(df)
        score = min((avg_w / avg_l) * wr * 10, 10.0)
        st.metric("Consistency Score", f"{score:.1f} / 10")
        st.progress(score/10)
        
        c_a, c_b = st.columns(2)
        with c_a: st.plotly_chart(px.scatter(df, x='rr', y='pnl', color='outcome', title="Discipline: RR vs P&L", template="plotly_dark"), use_container_width=True)
        with c_b: st.plotly_chart(px.bar(df.groupby('mindset')['pnl'].sum().reset_index(), x='mindset', y='pnl', title="Mindset Tracker", template="plotly_dark"), use_container_width=True)

# --- TAB 5: JOURNAL ---
with tabs[4]:
    if not df.empty:
        st.dataframe(df.sort_values('id', ascending=False), use_container_width=True)
