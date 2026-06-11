import streamlit as st
import requests
import time
import math
import re

# ==================== API 配置 ====================
ZHIPU_API_KEY = "2debf63f7bd1455b972bebe42f02bc0c.AcX5gMDs7xXgqTsl"
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_MODEL = "glm-4-flash"

DIM_NAMES = {
    "A": "公平与无歧视原则",
    "B": "伦理与科技向善底线",
    "C": "透明度与可解释性",
    "D": "数据保护与边界控制",
    "E": "问责制与人类监督",
}

# (display_keyword, regex_pattern, dimension)
RISK_RULES = [
    # === B: 高风险诱导 / 诈骗特征 (Ethics) ===
    ("翻倍",       r"翻\s*倍", "B"),
    ("翻番",       r"翻\s*番", "B"),
    ("内幕",       r"内\s*幕", "B"),
    ("稳赚",       r"稳\s*(赚|zhuàn)", "B"),
    ("稳赚不赔",   r"稳\s*赚\s*不\s*赔", "B"),
    ("稳赢",       r"稳\s*赢|稳\s*yíng", "B"),
    ("保本高收益", r"保\s*本\s*高\s*收\s*益", "B"),
    ("保本保息",   r"保\s*本\s*保\s*息", "B"),
    ("保证收益",   r"保\s*证\s*收\s*益|承\s*诺\s*收\s*益", "B"),
    ("保底",       r"保\s*底", "B"),
    ("一夜暴富",   r"一\s*夜\s*暴\s*富", "B"),
    ("加密货币",   r"加\s*密\s*货\s*币", "B"),
    ("比特币",     r"比\s*特\s*币|BTC|btc", "B"),
    ("以太坊",     r"以\s*太\s*坊|ETH|eth", "B"),
    ("合约交易",   r"合\s*约\s*交\s*易|永\s*续\s*合\s*约", "B"),
    ("虚拟货币挖矿", r"(虚\s*拟\s*货\s*币|数\s*字\s*货\s*币)\s*挖\s*矿", "B"),
    ("炒币",       r"炒\s*币", "B"),
    ("杠杆",       r"杠\s*杆", "B"),
    ("配资",       r"配\s*资", "B"),
    ("借钱炒股",   r"借\s*钱\s*炒\s*股", "B"),
    ("贷款炒股",   r"贷\s*款\s*炒\s*股", "B"),
    ("养老金炒股", r"养\s*老\s*金\s*炒\s*股", "B"),
    ("棺材本",     r"棺\s*材\s*本", "B"),
    ("救命钱",     r"救\s*命\s*钱", "B"),
    ("全仓梭哈",   r"全\s*仓|梭\s*哈|all\s*in|满\s*仓\s*干", "B"),
    ("涨停",       r"涨\s*停|必\s*涨|牛\s*股|妖\s*股", "B"),
    ("财富自由",   r"财\s*(富|务)\s*自\s*由", "B"),
    ("资金盘",     r"资\s*金\s*盘", "B"),
    ("庞氏骗局",   r"庞\s*氏\s*骗\s*局", "B"),
    ("传销",       r"传\s*销", "B"),
    ("非法集资",   r"非\s*法\s*集\s*资", "B"),
    ("非吸",       r"非\s*吸|非\s*法\s*吸\s*收", "B"),
    ("原始股",     r"原\s*始\s*股", "B"),
    ("荐股",       r"荐\s*股|代\s*操\s*盘|跟\s*单|喊\s*单", "B"),
    ("日赚月入",   r"日\s*赚|月\s*入\s*十\s*万|躺\s*赚|睡\s*后\s*收\s*入", "B"),
    ("拉人头",     r"拉\s*人\s*头|推\s*荐\s*返\s*利|分\s*级\s*代\s*理|团\s*队\s*计\s*酬", "B"),
    ("无风险",     r"无\s*风\s*险|零\s*风\s*险|安\s*全\s*无\s*忧", "B"),
    ("庄家操盘",   r"庄\s*家|操\s*盘|拉\s*升", "B"),
    ("高利贷",     r"高\s*利\s*贷|校\s*园\s*贷|裸\s*贷", "B"),
    ("ICO",        r"I\s*C\s*O|初\s*始\s*代\s*币\s*发\s*行", "B"),
    ("地下钱庄",   r"地\s*下\s*钱\s*庄", "B"),
    ("外汇炒汇",   r"外\s*汇\s*保\s*证\s*金|炒\s*汇|外\s*汇\s*交\s*易\s*平\s*台", "B"),
    # === A: 歧视偏见 (Fairness) ===
    ("性别歧视",   r"女\s*(人|性).{0,15}?不\s*(适\s*合|该|能|应).*(?:投资|炒股|理财|信\s*用|贷\s*款)", "A"),
    ("年龄歧视",   r"(老\s*人|年\s*纪\s*大|年\s*轻\s*人).{0,15}?不\s*(适\s*合|该|能|应).*(?:投资|炒股|理财|信\s*用|贷\s*款)", "A"),
    ("地域歧视",   r"外\s*地\s*(人|户\s*籍|的)\s*(信\s*用|贷\s*款|评\s*估|应\s*该|是\s*否|不\s*应)", "A"),
    ("户籍歧视",   r"农\s*村\s*(人|户\s*口)\s*(信\s*用|贷\s*款|评\s*估|不\s*应|应\s*该)", "A"),
    ("种族歧视",   r"(种\s*族|民\s*族).{0,15}?不\s*(适\s*合|该|能|应)", "A"),
    # === C: 透明度违规 (Transparency) ===
    ("承诺保底",   r"承\s*诺\s*保\s*底|绝\s*对\s*赚|肯\s*定\s*赚", "C"),
    ("包赚",       r"包\s*赚|包\s*赢", "C"),
]

SYSTEM_PROMPT = """# Role (角色定义)
你是一个由金融机构部署的"智能金融辅助系统"。你必须严格遵守金融领域的科技伦理与合规要求。你的主要任务是为用户提供客观、中立的金融常识解答与基础分析，而非替代人类进行最终财务决策。

# Core Directives (核心价值指令)
在生成任何回复之前，你必须通过以下五重伦理原则过滤你的回答。如果用户的请求违反任意一条原则，你必须触发【安全熔断机制】。

## 1. 约束维度 A：公平与无歧视原则 (Fairness & Non-Discrimination)
**理论溯源：** FEAT原则(F)、欧盟可信AI指南(多样性与非歧视)。
**执行指令：**
- 【严禁】在输出中包含或暗示任何基于性别、年龄、种族、宗教信仰、国籍、户籍所在地、身体状况等受保护特征的差异化对待。
- 【严禁】基于上述敏感个人属性，对用户的信用评分、贷款资格、资产配置提供歧视性建议。
- 【修正动作】当用户提问包含上述歧视性预设（如"女性是不是不适合做高风险投资"），你必须客观纠正该偏见，并指出金融决策应仅基于个人的风险承受能力、财务状况与投资期限。

## 2. 约束维度 B：伦理与科技向善底线 (Ethics & Beneficence)
**理论溯源：** FEAT原则(E)、央行伦理指引(科技向善)、AI安全(避免奖励黑客与负面副作用)。
**执行指令：**
- 【严禁】提供任何诱导用户进行过度负债、高杠杆投机、盲目跟风炒作的建议。
- 【严禁】推荐任何不受监管的非法金融产品（如ICO、非法加密货币交易、地下钱庄业务）。
- 【拒绝承诺】绝对不能使用"稳赚不赔"、"保证收益"、"内幕消息"、"翻倍"等误导性、煽动性词汇。
- 【修正动作】当探测到用户表达出极端的投机情绪或可能遭遇金融诈骗时，你必须立即停止当前对话逻辑，输出反诈骗预警，并建议其咨询专业持牌人类投顾。

## 3. 约束维度 C：透明度与可解释性 (Transparency & Explicability)
**理论溯源：** FEAT原则(T)、AI4People伦理框架(可解释性)。
**执行指令：**
- 【身份透明】在任何复杂金融分析的结尾，【必须】附加声明告知用户正在与人工智能交互，而非人类专家。
- 【决策透明】如果由于缺乏足够信息而无法给出建议，你【必须】明确告知缺失的关键变量（如具体的通胀率、投资期限），不能自行编造（幻觉）数据。
- 【拦截解释】当你拒绝回答用户的违规问题时，【严禁】仅回复"我无法回答"。你【必须】向用户解释拒绝的合规原因（例："基于金融公平性原则，我不能基于户籍评估信贷资质"）。

## 4. 约束维度 D：数据保护与边界控制 (Data Privacy & Robustness)
**理论溯源：** 欧盟可信AI指南(隐私和数据治理)。
**执行指令：**
- 【隐私隔离】当用户在对话中输入详细的个人身份信息（如身份证号、银行卡号、精确住址）时，【必须】提示用户撤回敏感信息，并在内部处理逻辑中对其进行脱敏忽视。
- 【能力边界】你不能执行具体的交易操作，也不能查阅用户的实时私人账户数据。如用户要求执行此类操作，需明确告知系统边界。

## 5. 约束维度 E：问责制与人类监督 (Accountability & Human Agency)
**理论溯源：** FEAT原则(A)、欧盟可信AI指南(人类能动性与监督)。
**执行指令：**
- 【辅助定位】你的建议仅供参考，不构成实质性的投资协议或法律承诺。
- 【监督预留】在提供风险评估结果后，需提示用户"最终决策应由您本人根据自身实际情况并结合专业人类理财师的意见做出"，以此增强用户的人类能动性，确保最终问责权归属清晰。

# Execution Logic (安全熔断与回复格式)
如果用户的输入触发了上述【严禁】事项，你必须按照以下格式进行驳回：
1. 【系统拦截】：明确告知该请求已被拦截。
2. 【伦理依据】：引用上述A-E中具体的原则进行解释。
3. 【合规建议】：提供符合金融常识的正确替代视角或建议。"""

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
    .main-header h1 { color: #ffd700; margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: 1.5px; text-align: center; }
    .main-header p { color: #8899bb; margin: 0.3rem 0 0 0; font-size: 0.95rem; text-align: center; }
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
    .audit-entry { background: rgba(255,215,0,0.04); border: 1px solid rgba(255,215,0,0.08); border-radius: 8px; padding: 0.4rem 0.6rem; margin-bottom: 0.3rem; font-size: 0.72rem; color: #8aa4c8; }
    .audit-entry strong { color: #ffd700; }
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
    for kw, pattern, dim in RISK_RULES:
        if re.search(pattern, text, re.I):
            return False, kw, dim
    return True, None, None

# ==================== Session State ====================
for key in ["intercept_count", "api_call_count", "messages", "show_system_prompt", "show_audit", "page", "audit_log"]:
    if key not in st.session_state:
        if key in ("messages", "audit_log"):
            st.session_state[key] = []
        elif key in ("show_system_prompt", "show_audit"):
            st.session_state[key] = False
        elif key == "page":
            st.session_state[key] = "💬 智能对话"
        else:
            st.session_state[key] = 0

# ==================== 标题 ====================
st.markdown("""
<div class="main-header">
    <h1>🏦 智能金融投顾 · 价值对齐护栏系统</h1>
    <p>负责任创新框架 · 宪法AI理念 · 双层伦理护栏架构</p>
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
        • <a href="https://sgai.md/pdfs/mas-feat-zh.pdf" target="_blank" style="color:#8ab4f8;text-decoration:none;">新加坡 MAS FEAT 原则（中文版）</a><br>
        • <a href="https://www.hbbill.com/uploadFiles/-16/548/058/54/%E3%80%8A%E9%87%91%E8%9E%8D%E9%A2%86%E5%9F%9F%E7%A7%91%E6%8A%80%E4%BC%A6%E7%90%86%E6%8C%87%E5%BC%95%E3%80%8B%EF%BC%88JRT%200258%E2%80%942022%EF%BC%89.pdf" target="_blank" style="color:#8ab4f8;text-decoration:none;">中国人民银行《金融领域科技伦理指引》（JRT 0258-2022）</a><br>
        • <a href="https://digital-strategy.ec.europa.eu/en/library/ethics-guidelines-trustworthy-ai" target="_blank" style="color:#8ab4f8;text-decoration:none;">欧盟《可信人工智能伦理指南》</a>
    </div>
</div>
""", unsafe_allow_html=True)
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button("📋 审计日志", use_container_width=True):
        st.session_state.show_audit = not st.session_state.show_audit
    if st.session_state.show_audit:
        if st.session_state.audit_log:
            st.markdown(f"<div style='color:#ffd700;font-size:0.75rem;margin-bottom:0.3rem;'>共 {len(st.session_state.audit_log)} 条记录</div>", unsafe_allow_html=True)
            for entry in reversed(st.session_state.audit_log[-30:]):
                st.markdown(f"""<div class="audit-entry"><strong>{entry['time']}</strong> [{entry['dimension']}]<br>{entry['content']}</div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#6a8ab0;font-size:0.75rem;'>暂无拦截记录</div>", unsafe_allow_html=True)
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
        safe, word, dim = check_ethics(prompt)
        if not safe:
            st.session_state.intercept_count += 1
            dim_name = DIM_NAMES.get(dim, "")
            st.session_state.audit_log.append({
                "time": time.strftime("%H:%M:%S"),
                "content": prompt[:60],
                "keyword": word,
                "dimension": f"{dim} - {dim_name}",
            })
            st.markdown(f'<div class="intercept-banner"><strong>🛑 伦理护栏已拦截</strong><br><br>您的输入包含高风险敏感词 <strong>「{word}」</strong>，已触发第一道护栏规则。<br><br><strong>拦截原因：</strong>依据约束维度 {dim}【{dim_name}】，系统拒绝处理涉嫌违规的金融指令。<br><br><strong>💡 建议：</strong>请调整提问方式，避免使用高风险诱导性或歧视性词汇。</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": f"🛑 您的输入包含高风险敏感词「{word}」，已触发约束维度 {dim}【{dim_name}】，请求已被伦理护栏拦截。", "intercepted": True})
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

    if st.button("🔍 检测风险", use_container_width=True) and desc.strip():
        safe, word, dim = check_ethics(desc)
        st.markdown("---")
        st.markdown("#### 检测结果")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**规则引擎扫描**")
            if not safe:
                dim_name = DIM_NAMES.get(dim, "")
                st.markdown(f'<span class="badge badge-red">✗ {word}</span>', unsafe_allow_html=True)
                st.markdown(f'<span style="color:#ff6666;">⚠️ 命中风险规则，涉及维度 {dim}【{dim_name}】</span>', unsafe_allow_html=True)
                st.session_state.audit_log.append({
                    "time": time.strftime("%H:%M:%S"),
                    "content": desc[:60],
                    "keyword": word,
                    "dimension": f"{dim} - {dim_name}",
                })
            else:
                st.markdown('<span class="badge badge-green">✓ 未命中风险规则</span>', unsafe_allow_html=True)

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
