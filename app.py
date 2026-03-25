import streamlit as st
import random
import json
import time
import base64

# --- 1. 全局配置 ---
st.set_page_config(page_title="AI 学习实验控制台", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 24px !important; }
    .stTextArea textarea { font-size: 22px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 24px !important; border-radius: 10px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .timer-warning { 
        color: white; background-color: red; padding: 20px; border-radius: 10px;
        font-weight: bold; animation: blink 0.8s infinite; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 状态清理与跳转 ---
def next_step_and_clean(next_val, data_key=None, data_val=None):
    if data_key:
        st.session_state.data[data_key] = data_val
    
    # 【核心修复】清理所有计时器相关的旧缓存，彻底防止 UI 叠加
    for key in list(st.session_state.keys()):
        if key.endswith("_end") or key.startswith("t"):
            del st.session_state[key]
            
    st.session_state.step = next_val
    st.rerun()

# --- 3. 稳健型计时器 ---
def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    
    remaining = int(st.session_state[timer_key] - time.time())
    
    if remaining <= 0:
        return True # 时间到
    
    if remaining <= 30:
        # 修改浏览器标签页标题唤回
        st.components.v1.html(f"<script>window.parent.document.title = '⚠️仅剩{remaining}秒！';</script>", height=0)
        st.markdown(f'<p class="timer-warning">⚠️ 警告：本环节即将结束！剩余 {remaining} 秒</p>', unsafe_allow_html=True)
    else:
        st.components.v1.html("<script>window.parent.document.title = '实验进行中...';</script>", height=0)
    
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 实验环节函数化 (物理隔离) ---
@st.cache_data
def load_bank():
    try:
        with open("question_bank.json", "r", encoding="utf-8") as f: return json.load(f)
    except: return {"1": [{"content": "示例题", "instructions": ["语料"]}], "2": []}

# 阶段 1：信息登记
def show_stage_1():
    st.header("📋 实验信息登记")
    # 请求通知权限
    st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)
    sid = st.text_input("请输入被试编号:", key="input_sid")
    age = st.selectbox("选择学段:", ["1 (小学)", "2 (中学)"], key="select_age")
    grp = st.selectbox("分配组别:", ["1 (指导型)", "2 (支持型)"], key="select_grp")
    
    if st.button("🚀 开始实验", key="main_start_btn"):
        bank = load_bank()
        if sid and len(bank[age[0]]) >= 2:
            sel = random.sample(bank[age[0]], 2)
            st.session_state.main_i = sel[0]
            st.session_state.trans_i = sel[1]
            st.session_state.data = {
                'sid': sid, 
                'group': "指导" if "1" in grp else "支持"
            }
            next_step_and_clean(2)
        else:
            st.error("请完整填写编号并确保题库充足。")

# 通用作答环节
def show_stage_writing(title, item, data_key, next_val, timer_key, total_time, is_transfer=False):
    st.header(title)
    if is_transfer: 
        st.success("🌟 迁移挑战：请利用刚才学到的思考方式，独立解决这个新问题。")
    st.info(f"题目：{item['content']}")
    ans = st.text_area("请在这里输入你的回答：", height=350, key=f"area_{timer_key}")
    
    if st.button("✅ 我已完成", key=f"btn_{timer_key}") or smart_timer(total_time, timer_key):
        next_step_and_clean(next_val, data_key, ans)

# 阶段 2：AI 互动
def show_stage_ai():
    st.header("🤖 阶段 2：AI 互动学习")
    st.error("❗ 本环节限时 3 分钟。时间到将自动进入下一环节。")
    st.markdown("### 🔍 互动题目：" + st.session_state.main_i['content'])
    
    # Prompt 生成逻辑
    ai_group = st.session_state.data['group']
    content = st.session_state.main_i['content']
    if ai_group == "指导":
        prompt = f"针对题目《{content}》直接给出标准答案。严禁提问。"
        sel = "N/A"
    else:
        sel = random.choice(st.session_state.main_i['instructions'])
        prompt = f"针对题目《{content}》，请基于线索『{sel}』启发我思考。严禁直接给答案。"
    
    st.session_state.data['used_ins'] = sel
    st.code(prompt)
    st.link_button("👉 点击打开豆包进行互动", "https://www.doubao.com")
    
    if st.button("✅ 互动结束", key="ai_finish_btn") or smart_timer(180, "t_ai"):
        next_step_and_clean(4)

# 阶段 5：问卷
def show_stage_survey():
    st.header("📊 阶段 5：问卷调查")
    q1 = st.slider("1. AI 的回复对你是否有启发？(1-5)", 1, 5, 3)
    q2 = st.radio("2. 偏好的引导方式：", ["直接告诉我答案", "给我思路让我想"])
    if st.button("📤 提交并结算结果"):
        st.session_state.data['survey'] = {"q1": q1, "q2": q2}
        next_step_and_clean(7)

# --- 5. 主逻辑入口 (分级渲染) ---
if 'step' not in st.session_state:
    st.session_state.step = 1

# 【重点】使用完全隔离的 if-elif 结构，确保同一时间只运行一个函数
if st.session_state.step == 1:
    show_stage_1()
elif st.session_state.step == 2:
    show_stage_writing("📝 阶段 1：前测", st.session_state.main_i, "pre_ans", 3, "t1", 300)
elif st.session_state.step == 3:
    show_stage_ai()
elif st.session_state.step == 4:
    show_stage_writing("🏁 阶段 3：后测", st.session_state.main_i, "post_ans", 5, "t3", 300)
elif st.session_state.step == 5:
    show_stage_writing("🚀 阶段 4：迁移测试", st.session_state.trans_i, "trans_ans", 6, "t4", 300, True)
elif st.session_state.step == 6:
    show_stage_survey()
elif st.session_state.step == 7:
    st.balloons()
    st.success("🎉 全部实验已结束！")
    b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
    st.write("请复制下方代码发给主试：")
    st.code(b64)