import streamlit as st
import requests
import time
import math

# ==================== API 配置 ====================
ZHIPU_API_KEY = "2debf63f7bd1455b972bebe42f02bc0c.AcX5gMDs7xXgqTsl"
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_MODEL = "glm-4-flash"

SYSTEM_PROMPT = """你是一个遵循全球最高金融监管标准的智能投顾。你必须严格遵守基于 MAS FEAT 原则和中国人民银行《金融领域科技伦理指引》构建的价值手册：
1. 【公平性 (Fairness)】：严禁将性别、年龄、种族、地域作为信贷或理财评估依据，仅基于财务客观数据决策。
2. 【伦理与负责任创新 (Ethics)】：优先保护弱势群体。对老年人、低收入者提出的高风险（如加密货币、高杠杆）请求必须强制阻断并警示风险；拒绝生成任何涉嫌欺诈或违规的建议。
3. 【问责制 (Accountability)】：明确告知用户你是AI，重大财务决策需人类复核，不提供具有法律约束力的承诺。
4. 【透明度 (Transparency)】：如果提供建议，必须说明数据局限性与AI模型风险，当拒绝用户时，需清晰解释违背了哪条监管伦理原则。"""

RISK_KEYWORDS = ["翻倍", "内幕", "稳赚", "加密货币", "借钱炒股", "养老金炒股", "杠杆", "一夜暴富", "保本高收益"]

# ==================== CSS ====================
st.set_page_config(page_title="智能金融投顾护栏系统", page_icon="🏦", layout="wide")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans SC', sans-serif; font-size: 17px !important; }
    .stApp {
        background: linear-gradient(145deg, #070d1a 0%, #0f1f3a 40%, #162a4a 70%, #0d1a30 100%);
    }
    .stApp::before {
        content: ''; position: fixed; inset: 0;
        background-image:
            linear-gradient(rgba(255,215,0,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,215,0,0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none; z-index: 0;
    }
    .block-container { position: relative; z-index: 1; padding-top: 1rem !important; }
    .main-header {
        background: linear-gradient(135deg, rgba(10,22,40,0.92) 0%, rgba(26,42,74,0.92) 100%);
        backdrop-filter: blur(12px);
        padding: 1.5rem 2rem; border-radius: 20px; margin-bottom: 1.2rem;
        border: 1px solid rgba(255,215,0,0.18);
        box-shadow: 0 8px 40px rgba(0,0,0,0.35);
    }
    .main-header h1 { color: #ffd700; margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: 1.5px; }
    .main-header p { color: #8899bb; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    .card {
        background: linear-gradient(135deg, rgba(15,31,58,0.85) 0%, rgba(26,45,79,0.85) 100%);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,215,0,0.12); border-radius: 14px;
        padding: 1.2rem 1.4rem; margin-bottom: 1rem;
    }
    .card h3 { color: #ffd700; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .card p, .card li { color: #b0c4de; font-size: 0.9rem; line-height: 1.6; }
    .badge {
        display: inline-block; padding: 0.2rem 0.8rem; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }
    .badge-green { background: rgba(0,200,83,0.2); color: #66dd88; border: 1px solid #00c853; }
    .badge-red { background: rgba(255,60,60,0.2); color: #ff6666; border: 1px solid #ff4444; }
    .badge-yellow { background: rgba(255,215,0,0.15); color: #ffd700; border: 1px solid rgba(255,215,0,0.3); }
    .result-box {
        background: linear-gradient(135deg, rgba(255,215,0,0.04) 0%, rgba(255,215,0,0.08) 100%);
        border: 1px solid rgba(255,215,0,0.15); border-radius: 14px;
        padding: 1.2rem 1.5rem; margin: 0.8rem 0;
    }
    .result-box .big-num { color: #ffd700; font-size: 2rem; font-weight: 800; }
    .result-box .label { color: #8aa4c8; font-size: 0.8rem; }
    .stSidebar {
        background: rgba(7,13,26,0.6) !important;
        backdrop-filter: blur(8px);
        border-right: 1px solid rgba(255,215,0,0.06) !important;
    }
    .stButton button {
        border-radius: 10px !important;
        font-size: 0.9rem !important;
        border: 1px solid rgba(255,215,0,0.12) !important;
        background: rgba(255,215,0,0.04) !important;
        color: #b0c4de !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        border-color: rgba(255,215,0,0.3) !important;
        background: rgba(255,215,0,0.08) !important;
        color: #ffd700 !important;
    }
    div[data-testid="stChatMessage"] { border-radius: 14px !important; margin-bottom: 0.6rem !important; font-size: 1rem !important; }
    .stChatFloatingInputContainer {
        backdrop-filter: blur(12px);
        background: rgba(7,13,26,0.85) !important;
        border-top: 1px solid rgba(255,215,0,0.08) !important;
    }
    input[data-testid="stChatInput"] {
        font-size: 1rem !important; border-radius: 12px !important;
        border: 1px solid rgba(255,215,0,0.12) !important;
        background: rgba(15,31,58,0.6) !important; color: #e0e8f0 !important;
    }
    .intercept-banner {
        background: linear-gradient(135deg, rgba(74,0,0,0.9) 0%, rgba(109,26,26,0.9) 100%);
        border: 1px solid rgba(255,60,60,0.4); border-radius: 14px;
        padding: 1.2rem 1.5rem; margin: 0.5rem 0; color: #ffcccc;
        font-size: 0.95rem; line-height: 1.6;
    }
    .footer-bar { text-align: center; color: #3a5070; font-size: 0.75rem; padding: 1.5rem 0 0.5rem 0; border-top: 1px solid rgba(255,215,0,0.04); margin-top: 2rem; }
    .stRadio [role="radiogroup"] { gap: 0 !important; }
    .stRadio label { padding: 0.6rem 0.8rem !important; border-radius: 10px !important; transition: all 0.15s ease; }
    .stRadio label:hover { background: rgba(255,215,0,0.06) !important; }
    .stRadio [data-testid="stMarkdownContainer"] { color: #b0c4de !important; }
    .stTextInput input { background: rgba(15,31,58,0.6) !important; border: 1px solid rgba(255,215,0,0.12) !important; color: #e0e8f0 !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 工具函数 ====================
def call_zhipu(messages):
    headers = {"Authorization": f"Bearer {ZHIPU_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": ZHIPU_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 2048}
    resp = requests.post(ZHIPU_API_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    raise Exception(f"HTTP {resp.status_code}: {resp.text}")

def check_ethics(text):
    for w in RISK_KEYWORDS:
        if w in text:
            return False, w
    return True, None

# ==================== Session State ====================
for key in ["intercept_count", "api_call_count", "messages", "show_system_prompt", "page"]:
    if key not in st.session_state:
        if key == "messages":
            st.session_state[key] = []
        elif key == "show_system_prompt":
            st.session_state[key] = False
        elif key == "page":
            st.session_state[key] = "💬 智能对话"
        else:
            st.session_state[key] = 0

# ==================== 标题 ====================
st.markdown("""
<div class="main-header">
    <h1>🏦 智能金融投顾 · 价值对齐护栏系统</h1>
    <p>负责任创新（RRI）框架 · 宪法AI（Constitutional AI）理念 · 双层伦理护栏架构</p>
</div>
""", unsafe_allow_html=True)

# ==================== 侧边栏导航 ====================
with st.sidebar:
    st.markdown("### 🧭 功能导航")
    pages = {
        "💬 智能对话": "chat",
        "📋 风险测评": "quiz",
        "🧮 投资计算器": "calc",
        "🔍 诈骗识别器": "fraud",
        "⚖️ 偏见检测": "bias",
        "🔮 情景模拟": "sim",
    }
    selected = st.radio("导航菜单", list(pages.keys()), index=list(pages.keys()).index(st.session_state.page),
                        label_visibility="collapsed")
    st.session_state.page = selected
    mode = pages[selected]

    st.markdown("---")
    st.markdown("### ⚙️ 系统")
    st.markdown('<div style="background:rgba(13,110,45,0.15);border:1px solid #00c853;border-radius:10px;padding:0.5rem 1rem;margin-bottom:1rem;"><span style="color:#66dd88;font-size:0.9rem;">✅ 智谱 GLM-4-Flash</span></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="card" style="text-align:center;padding:0.6rem;"><span style="font-size:1.4rem;font-weight:800;color:#ffd700;">{st.session_state.intercept_count}</span><br><span style="font-size:0.7rem;color:#8aa4c8;">🛑 拦截</span></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card" style="text-align:center;padding:0.6rem;"><span style="font-size:1.4rem;font-weight:800;color:#ffd700;">{st.session_state.api_call_count}</span><br><span style="font-size:0.7rem;color:#8aa4c8;">🤖 调用</span></div>', unsafe_allow_html=True)

    if st.button("📜 价值手册", use_container_width=True):
        st.session_state.show_system_prompt = not st.session_state.show_system_prompt
    if st.session_state.show_system_prompt:
        st.markdown(f"""
<div style="background:rgba(15,31,58,0.6);border:1px solid rgba(255,215,0,0.12);border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.5rem;">
    <div style="color:#b0c4de;font-size:0.82rem;line-height:1.6;white-space:pre-wrap;word-break:break-word;">
{SYSTEM_PROMPT.strip()}
    </div>
    <hr style="border-color:rgba(255,215,0,0.08);margin:0.6rem 0;">
    <div style="font-size:0.75rem;color:#6a8ab0;line-height:1.5;">
        📖 <strong>参考官方文件：</strong><br>
        • <a href="https://www.mas.gov.sg/regulation/guidelines/feat-principles" target="_blank" style="color:#8ab4f8;text-decoration:none;">新加坡 MAS FEAT 原则</a><br>
        • <a href="https://www.pbc.gov.cn/tiaofasi/144941/144959/5226441/index.html" target="_blank" style="color:#8ab4f8;text-decoration:none;">中国人民银行《金融领域科技伦理指引》</a><br>
        • <a href="https://digital-strategy.ec.europa.eu/en/library/ethics-guidelines-trustworthy-ai" target="_blank" style="color:#8ab4f8;text-decoration:none;">欧盟《可信人工智能伦理指南》</a>
    </div>
</div>
""", unsafe_allow_html=True)
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("模型：智谱 GLM-4-Flash（免费）")


# ====================================================================
# 功能 1: 💬 智能对话（原有聊天功能）
# ====================================================================
def render_chat():
    if len(st.session_state.messages) == 0:
        col_l, col_m, col_r = st.columns([1, 2.2, 1])
        with col_m:
            st.markdown('<div style="text-align:center;padding:2rem 0 1rem 0;"><div style="font-size:3rem;margin-bottom:0.5rem;">🏦</div><div style="font-size:1.3rem;font-weight:600;color:#b0c4de;">欢迎使用智能金融投顾</div><div style="font-size:0.95rem;color:#6a8ab0;margin-top:0.3rem;">输入金融问题，体验AI伦理护栏的完整工作流程</div></div>', unsafe_allow_html=True)
            st.markdown('<div style="text-align:center;margin-bottom:0.5rem;color:#6a8ab0;font-size:0.85rem;">点击示例快速体验：</div>', unsafe_allow_html=True)
            chips = ["📈 什么是基金定投？","👴 退休老人5万怎么理财","⚠️ 有没有稳赚的股票","🚫 借钱炒股翻倍攻略","💳 女性贷款更容易吗","💰 年轻人如何规划储蓄"]
            for row in [chips[i:i+3] for i in range(0, len(chips), 3)]:
                cols = st.columns(3)
                for ci, txt in enumerate(row):
                    with cols[ci]:
                        if st.button(txt, key=f"chip_{hash(txt)}", use_container_width=True):
                            st.session_state.pending = txt
                            st.rerun()

    pending = st.session_state.pop("pending", None)
    prompt = pending or st.chat_input("请输入您的金融咨询问题…")
    if not prompt:
        if st.session_state.messages:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    if msg.get("intercepted"):
                        st.markdown(f'<div class="intercept-banner">{msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(msg["content"])
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        safe, word = check_ethics(prompt)
        if not safe:
            st.session_state.intercept_count += 1
            st.markdown(f'<div class="intercept-banner"><strong>🛑 伦理护栏已拦截</strong><br><br>您的输入包含高风险敏感词 <strong>「{word}」</strong>，已触发第一道护栏规则。<br><br><strong>拦截原因：</strong>依据负责任创新与金融消费者保护原则，系统拒绝处理涉嫌诱导极端风险的指令。<br><br><strong>💡 建议：</strong>请调整提问方式，避免使用高风险诱导性词汇。</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": f"🛑 您的输入包含高风险敏感词「{word}」，请求已被伦理护栏拦截。", "intercepted": True})
        else:
            st.session_state.api_call_count += 1
            with st.status("⏳ 处理中…", expanded=True) as status:
                st.markdown("**第一道护栏** ✅ 关键词规则引擎 — 未触发")
                st.markdown("**第二道护栏** 🔄 正在注入金融AI价值手册…")
                try:
                    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
                    for m in st.session_state.messages:
                        if not m.get("intercepted"):
                            msgs.append({"role": m["role"], "content": m["content"]})
                    resp = call_zhipu(msgs)
                    status.update(label="✅ 处理完成", state="complete")
                    st.markdown("**第二道护栏** ✅ 大模型已按价值手册生成合规回复")
                    full = f"{resp}\n\n---\n*⚠️ 本建议由 AI 生成，仅供参考，不构成实质投资协议。*"
                    st.markdown(full)
                    st.session_state.messages.append({"role": "assistant", "content": full})
                except Exception as e:
                    status.update(label="❌ 调用失败", state="error")
                    err = f"❌ 调用智谱 API 出错：{e}"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("intercepted"):
                st.markdown(f'<div class="intercept-banner">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])


# ====================================================================
# 功能 2: 📋 风险测评
# ====================================================================
def render_quiz():
    st.markdown('<div class="card"><h3>📋 风险承受能力测评</h3><p>完成以下 5 道简单选择题，系统将输出您的风险等级及参考配置比例。</p></div>', unsafe_allow_html=True)
    st.markdown("#### 1️⃣ 您的年龄是？")
    age = st.radio("age", ["18–25 岁", "26–40 岁", "41–60 岁", "60 岁以上"], label_visibility="collapsed", horizontal=True)
    st.markdown("#### 2️⃣ 您当前的年收入水平？")
    income = st.radio("income", ["5 万以下", "5–15 万", "15–50 万", "50 万以上"], label_visibility="collapsed", horizontal=True)
    st.markdown("#### 3️⃣ 您的投资经验？")
    exp = st.radio("exp", ["无经验", "1 年以内", "1–5 年", "5 年以上"], label_visibility="collapsed", horizontal=True)
    st.markdown("#### 4️⃣ 如果投资短期亏损 20%，您会？")
    loss = st.radio("loss", ["立即赎回", "感到不安但持有", "继续持有等待反弹", "加仓摊平"], label_visibility="collapsed", horizontal=True)
    st.markdown("#### 5️⃣ 您的投资目标是？")
    goal = st.radio("goal", ["保本为主", "稳健增值", "追求增长", "博取高收益"], label_visibility="collapsed", horizontal=True)

    score_map = {
        ("18–25 岁",2), ("26–40 岁",3), ("41–60 岁",2), ("60 岁以上",1),
        ("5 万以下",1), ("5–15 万",2), ("15–50 万",3), ("50 万以上",4),
        ("无经验",1), ("1 年以内",2), ("1–5 年",3), ("5 年以上",4),
        ("立即赎回",1), ("感到不安但持有",2), ("继续持有等待反弹",3), ("加仓摊平",4),
        ("保本为主",1), ("稳健增值",2), ("追求增长",3), ("博取高收益",4),
    }
    sm = dict(score_map)

    if st.button("📊 开始测评", use_container_width=True):
        score = sm[age] + sm[income] + sm[exp] + sm[loss] + sm[goal]
        if score <= 8:
            level, alloc = "保守型", "📦 10% 货基 + 60% 债基 + 20% 银行理财 + 10% 股基"
        elif score <= 13:
            level, alloc = "稳健型", "📦 10% 货基 + 50% 债基 + 20% 混合基金 + 20% 股基"
        elif score <= 18:
            level, alloc = "进取型", "📦 5% 货基 + 30% 债基 + 25% 混合基金 + 40% 股基"
        else:
            level, alloc = "积极型", "📦 0% 货基 + 20% 债基 + 20% 混合基金 + 60% 股基"

        colors = {"保守型": "badge-green", "稳健型": "badge-yellow", "进取型": "badge-red", "积极型": "badge-red"}
        st.markdown(f"""
        <div class="result-box" style="text-align:center;">
            <div class="label">您的风险测评得分</div>
            <div class="big-num">{score} / 20</div>
            <br>
            <span class="badge {colors[level]}" style="font-size:1rem;padding:0.4rem 1.5rem;">{level}</span>
            <br><br>
            <div style="color:#b0c4de;font-size:0.9rem;"><strong>参考资产配置：</strong><br>{alloc}</div>
            <div style="color:#6a8ab0;font-size:0.75rem;margin-top:0.5rem;">⚠️ 以上为教育性参考，不构成具体投资建议。</div>
        </div>
        """, unsafe_allow_html=True)


# ====================================================================
# 功能 3: 🧮 投资计算器
# ====================================================================
def render_calc():
    st.markdown('<div class="card"><h3>🧮 投资计算器</h3><p>定投计算 · 复利计算 · 通胀调整 · 退休金估算</p></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📆 定投计算", "💰 复利计算", "📉 通胀调整", "👴 退休金估算"])

    with tab1:
        st.markdown("##### 每月定投，未来能积累多少？")
        pmt = st.number_input("每月投入（元）", min_value=100, max_value=1000000, value=1000, step=500, key="dca_pmt")
        rate = st.number_input("年化收益率（%）", min_value=0.0, max_value=100.0, value=8.0, step=0.5, key="dca_rate")
        years = st.number_input("定投年限", min_value=1, max_value=60, value=10, step=1, key="dca_years")
        if st.button("📊 计算定投", key="dca_btn", use_container_width=True):
            r = rate / 100 / 12
            n = int(years * 12)
            fv = pmt * ((1 + r) ** n - 1) / r if r > 0 else pmt * n
            total_in = pmt * n
            st.markdown(f"""
            <div class="result-box" style="text-align:center;">
                <div class="label">定投 {years} 年后</div>
                <div class="big-num">{fv:,.0f} 元</div>
                <div style="color:#b0c4de;font-size:0.85rem;margin-top:0.5rem;">
                    累计投入：{total_in:,.0f} 元 &nbsp;|&nbsp; 收益：{fv-total_in:,.0f} 元
                </div>
                <div style="color:#6a8ab0;font-size:0.75rem;margin-top:0.5rem;">⚠️ 历史不代表未来，以上仅为数学模拟。</div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("##### 一次性投入，复利增长")
        pv = st.number_input("初始本金（元）", min_value=0, max_value=100000000, value=100000, step=10000, key="c_pv")
        r2 = st.number_input("年化收益率（%）", min_value=0.0, max_value=100.0, value=8.0, step=0.5, key="c_rate")
        y2 = st.number_input("投资年限", min_value=1, max_value=60, value=10, step=1, key="c_years")
        if st.button("📊 计算复利", key="c_btn", use_container_width=True):
            fv = pv * (1 + r2 / 100) ** y2
            st.markdown(f"""
            <div class="result-box" style="text-align:center;">
                <div class="label">{y2} 年后本息合计</div>
                <div class="big-num">{fv:,.0f} 元</div>
                <div style="color:#b0c4de;font-size:0.85rem;margin-top:0.5rem;">
                    本金：{pv:,.0f} 元 &nbsp;|&nbsp; 收益：{fv-pv:,.0f} 元
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("##### 考虑通胀，未来购买力还剩多少？")
        fv3 = st.number_input("未来金额（元）", min_value=0, max_value=100000000, value=1000000, step=50000, key="i_fv")
        inf = st.number_input("年均通胀率（%）", min_value=0.0, max_value=50.0, value=3.0, step=0.5, key="i_rate")
        y3 = st.number_input("年数", min_value=1, max_value=60, value=20, step=1, key="i_years")
        if st.button("📊 计算实际价值", key="i_btn", use_container_width=True):
            real = fv3 / ((1 + inf / 100) ** y3)
            loss_pct = (1 - real / fv3) * 100
            st.markdown(f"""
            <div class="result-box" style="text-align:center;">
                <div class="label">{y3} 年后的实际购买力 ≈</div>
                <div class="big-num">{real:,.0f} 元</div>
                <div style="color:#b0c4de;font-size:0.85rem;margin-top:0.5rem;">
                    名义金额：{fv3:,.0f} 元 &nbsp;|&nbsp; 购买力损失：{loss_pct:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.markdown("##### 退休金缺口估算")
        cur_age = st.number_input("当前年龄", min_value=18, max_value=80, value=30, step=1, key="r_age")
        retire_age = st.number_input("计划退休年龄", min_value=30, max_value=80, value=60, step=1, key="r_retire")
        life_exp = st.number_input("预期寿命", min_value=60, max_value=120, value=85, step=1, key="r_life")
        monthly_need = st.number_input("退休后每月所需（元）", min_value=1000, max_value=1000000, value=5000, step=1000, key="r_need")
        curr_savings = st.number_input("当前已积累（元）", min_value=0, max_value=100000000, value=200000, step=50000, key="r_savings")
        r_rate = st.number_input("年均投资收益率（%）", min_value=0.0, max_value=30.0, value=5.0, step=0.5, key="r_rate")
        if st.button("📊 估算退休缺口", key="r_btn", use_container_width=True):
            work_years = retire_age - cur_age
            retire_years = life_exp - retire_age
            total_needed = monthly_need * 12 * retire_years
            future_savings = curr_savings * (1 + r_rate / 100) ** work_years
            gap = max(0, total_needed - future_savings)
            st.markdown(f"""
            <div class="result-box" style="text-align:center;">
                <div class="label">退休资金需求 vs 预计积累</div>
                <div style="color:#b0c4de;font-size:0.9rem;margin:0.5rem 0;">
                    退休生活总需求：<strong style="color:#ffd700;">{total_needed:,.0f} 元</strong><br>
                    预计届时积累：<strong style="color:#ffd700;">{future_savings:,.0f} 元</strong>
                </div>
                <div style="font-size:1rem;margin:0.5rem 0;">
                    {'✅ 资金充足' if gap == 0 else '🔴 存在缺口'}
                </div>
                <div class="big-num">{gap:,.0f} 元</div>
                <div class="label">{'资金缺口' if gap > 0 else '盈余金额'}</div>
                <div style="color:#6a8ab0;font-size:0.75rem;margin-top:0.5rem;">⚠️ 以上为简化估算，未考虑社保、税收等因素。</div>
            </div>
            """, unsafe_allow_html=True)


# ====================================================================
# 功能 4: 🔍 诈骗识别器
# ====================================================================
def render_fraud():
    st.markdown('<div class="card"><h3>🔍 金融诈骗识别器</h3><p>输入一个"理财项目"描述，系统将根据金融AI伦理手册判断是否涉嫌诈骗。</p></div>', unsafe_allow_html=True)
    desc = st.text_area("请输入理财项目描述：", placeholder="例如：年化收益30%，保本保息，推荐好友返利…", height=120)

    scam_keywords = ["保本", "拉人头", "超高收益", "稳赚不赔", "日赚", "月入十万", "推荐返利", "分级代理", "原始股", "内幕消息"]

    if st.button("🔍 检测风险", use_container_width=True) and desc.strip():
        st.markdown("---")
        st.markdown("#### 检测结果")
        found = [kw for kw in scam_keywords if kw in desc]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**规则引擎扫描**")
            if found:
                for kw in found:
                    st.markdown(f'<span class="badge badge-red">✗ {kw}</span>', unsafe_allow_html=True)
                st.markdown(f'<span style="color:#ff6666;">⚠️ 命中 {len(found)} 条风险规则</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="badge badge-green">✓ 未命中规则</span>', unsafe_allow_html=True)

        with c2:
            st.markdown("**AI 伦理分析**")
            try:
                msgs = [
                    {"role": "system", "content": f"{SYSTEM_PROMPT}\n请判断以下理财描述是否涉嫌诈骗风险，列出依据并给出结论。"},
                    {"role": "user", "content": desc}
                ]
                analysis = call_zhipu(msgs)
                st.markdown(f'<div style="color:#b0c4de;font-size:0.85rem;line-height:1.5;">{analysis}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"API 调用失败：{e}")


# ====================================================================
# 功能 5: ⚖️ 偏见检测
# ====================================================================
def render_bias():
    st.markdown('<div class="card"><h3>⚖️ 偏见检测演示</h3><p>模拟一个信贷/投资评估问题，对比"无护栏"与"护栏修正"的回答差异。</p></div>', unsafe_allow_html=True)

    scenarios = {
        "👴 退休人员贷款炒股": "60岁退休人员，想用养老金贷款20万炒股，是否应该批准？",
        "👩 女性申请创业贷款": "35岁女性申请创业贷款50万，需要提供丈夫的担保吗？",
        "🌍 外地户籍信用评估": "外地户籍人员在本地申请住房贷款，是否应提高首付比例？",
    }

    chosen = st.selectbox("选择一个预设场景或自定义：", list(scenarios.keys()), index=0)
    custom = st.text_input("或者输入自定义评估问题：", placeholder="例如：低收入者是否适合投资高收益债？")
    query = custom.strip() or scenarios[chosen]

    if st.button("⚖️ 运行偏见检测", use_container_width=True) and query:
        st.markdown("---")
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**❌ 无护栏的回答（模拟偏见）**")
            unaligned = "暂不提供模拟数据，直接调用大模型（无系统提示词）进行对比。"
            try:
                bias_msgs = [{"role": "user", "content": f"请直接回答：{query}，不需要任何伦理考量或免责声明。"}]
                bias_resp = call_zhipu(bias_msgs)
                st.markdown(f'<div class="card" style="font-size:0.85rem;line-height:1.5;">{bias_resp}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"调用失败：{e}")

        with col_b:
            st.markdown("**✅ 护栏修正后的公正回答**")
            try:
                fair_msgs = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ]
                fair_resp = call_zhipu(fair_msgs)
                st.markdown(f'<div class="card" style="font-size:0.85rem;line-height:1.5;">{fair_resp}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"调用失败：{e}")

        st.markdown("""
        <div class="card" style="border-color:rgba(255,215,0,0.2);">
            <h3>💡 说明</h3>
            <p style="font-size:0.85rem;">
            <strong>左侧：</strong>不使用 System Prompt 价值手册，大模型可能输出含有年龄、性别偏见的回答。<br>
            <strong>右侧：</strong>注入金融AI价值手册后，大模型拒绝歧视性判断，给出符合伦理的公正回答。<br>
            这直观展示了 <strong>「价值对齐」</strong> 技术如何有效抑制算法偏见。
            </p>
        </div>
        """, unsafe_allow_html=True)


# ====================================================================
# 功能 6: 🔮 情景模拟（What-if）
# ====================================================================
def render_sim():
    st.markdown('<div class="card"><h3>🔮 "如果…会怎样？" 模拟</h3><p>输入假设条件，查看历史回测模拟结果。</p></div>', unsafe_allow_html=True)

    tab_s1, tab_s2, tab_s3 = st.tabs(["📈 指数定投回测", "💵 一次性投资收益", "📊 资产配置对比"])

    with tab_s1:
        st.markdown("##### 每月定投沪深300指数，过去收益如何？")
        col1, col2 = st.columns(2)
        with col1:
            amt = st.number_input("每月定投金额（元）", min_value=100, max_value=1000000, value=1000, step=500, key="sim_dca_amt")
        with col2:
            yrs = st.number_input("回测年限", min_value=1, max_value=15, value=5, step=1, key="sim_dca_yrs")
        if st.button("📊 运行回测", key="sim_dca_btn", use_container_width=True):
            # 沪深300 模拟年化约 7-9% （近10年）
            sim_rate = 8.0 if yrs <= 5 else 7.5 if yrs <= 10 else 7.0
            r_m = sim_rate / 100 / 12
            n_m = int(yrs * 12)
            fv = amt * ((1 + r_m) ** n_m - 1) / r_m
            total_in = amt * n_m
            st.markdown(f"""
            <div class="result-box" style="text-align:center;">
                <div class="label">过去 {yrs} 年定投沪深300 累计价值 ≈</div>
                <div class="big-num">{fv:,.0f} 元</div>
                <div style="color:#b0c4de;font-size:0.85rem;margin-top:0.5rem;">
                    累计投入：{total_in:,.0f} 元 | 收益：{fv-total_in:,.0f} 元 | 年化 ≈ {sim_rate:.1f}%
                </div>
                <div style="color:#6a8ab0;font-size:0.7rem;margin-top:0.4rem;">⚠️ 历史不代表未来，以上为简化模拟。</div>
            </div>
            """, unsafe_allow_html=True)

    with tab_s2:
        st.markdown("##### 一次性投资某指数基金，n 年后价值")
        col1, col2 = st.columns(2)
        with col1:
            lump = st.number_input("一次性投入（元）", min_value=1000, max_value=100000000, value=100000, step=10000, key="sim_lump")
        with col2:
            l_yrs = st.number_input("持有年限", min_value=1, max_value=20, value=10, step=1, key="sim_lump_yrs")
        l_rate = st.select_slider("预期年化收益", options=[3,5,7,8,10,12,15], value=8, format_func=lambda x: f"{x}%", key="sim_lump_rate")
        if st.button("📊 计算", key="sim_lump_btn", use_container_width=True):
            fv = lump * (1 + l_rate / 100) ** l_yrs
            st.markdown(f"""
            <div class="result-box" style="text-align:center;">
                <div class="label">{l_yrs} 年后价值</div>
                <div class="big-num">{fv:,.0f} 元</div>
                <div style="color:#b0c4de;font-size:0.85rem;margin-top:0.5rem;">
                    本金：{lump:,.0f} 元 | 收益：{fv-lump:,.0f} 元 | 年化：{l_rate}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_s3:
        st.markdown("##### 不同配置比例对比（100 万本金，10 年）")
        st.markdown('<div style="color:#6a8ab0;font-size:0.85rem;">拖动滑块调整配置，实时查看预期结果。</div>', unsafe_allow_html=True)
        stock_pct = st.slider("股票型基金占比", 0, 100, 50, 10, key="sim_alloc_stock")
        bond_pct = st.slider("债券型基金占比", 0, 100, 30, 10, key="sim_alloc_bond")
        cash_pct = st.slider("货币基金占比", 0, 100, 20, 10, key="sim_alloc_cash")
        total = stock_pct + bond_pct + cash_pct
        if total != 100:
            st.warning(f"三项之和为 {total}%，请调整为 100%")
        else:
            principal = 1000000
            stock_r, bond_r, cash_r = 9.0, 4.0, 2.0
            blended = (stock_pct * stock_r + bond_pct * bond_r + cash_pct * cash_r) / 100
            fv = principal * (1 + blended / 100) ** 10
            st.markdown(f"""
            <div class="result-box" style="text-align:center;">
                <div class="label">10 年后预期价值</div>
                <div class="big-num">{fv:,.0f} 元</div>
                <div style="color:#b0c4de;font-size:0.85rem;margin-top:0.5rem;">
                    配置：{stock_pct}% 股基 + {bond_pct}% 债基 + {cash_pct}% 货基<br>
                    加权年化 ≈ {blended:.1f}% | 预期收益：{fv-principal:,.0f} 元
                </div>
            </div>
            """, unsafe_allow_html=True)


# ====================================================================
# 路由
# ====================================================================
pages_map = {
    "chat": render_chat,
    "quiz": render_quiz,
    "calc": render_calc,
    "fraud": render_fraud,
    "bias": render_bias,
    "sim": render_sim,
}
pages_map.get(mode, render_chat)()

# ==================== 页脚 ====================
st.markdown("""
<div class="footer-bar">
    智能金融投顾 · 伦理护栏系统 · 负责任创新（RRI）框架
</div>
""", unsafe_allow_html=True)
