import streamlit as st
import random
import json
import time
import base64

# --- 1. 全局样式配置 (大字号) ---
st.set_page_config(page_title="AI 学习实验控制台", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 24px !important; }
    .stTextArea textarea { font-size: 22px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 24px !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心逻辑函数 ---
@st.cache_data
def load_bank():
    try:
        with open("question_bank.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"1": [{"content": "示例题", "instructions": ["语料"]}], "2": []}

def generate_prompt(ai_group, item_content, instructions):
    if ai_group == "指导":
        return f"你好！针对题目《{item_content}》直接给出标准答案。严禁提问。", "N/A"
    else:
        sel = random.choice(instructions)
        return f"你好！任务《{item_content}》。请作为支持型导师，基于线索『{sel}』启发我。", sel

# --- 3. 智能倒计时组件 (最后30秒才显示) ---
def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    
    remaining = int(st.session_state[timer_key] - time.time())
    
    if remaining <= 0:
        return True # 时间耗尽，强制跳转
    
    # 关键逻辑：仅在最后 30 秒显示提示
    if remaining <= 30:
        st.error(f"⚠️ 注意：本环节即将结束！剩余 {remaining} 秒")
    
    # 为了保证计时精准且不影响输入体验，设置较短的刷新间隔
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 实验流程控制 ---
bank = load_bank()
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# 步骤 1：信息采集
if st.session_state.step == 1:
    st.header("📋 实验信息登记")
    sid = st.text_input("请输入被试编号:")
    age = st.selectbox("选择学段:", ["1 (小学)", "2 (中学)"])
    grp = st.selectbox("分配组别:", ["1 (指导型)", "2 (支持型)"])
    if st.button("🚀 开始实验"):
        if sid and len(bank[age[0]]) >= 2:
            sel = random.sample(bank[age[0]], 2)
            st.session_state.main_i, st.session_state.trans_i = sel[0], sel[1]
            st.session_state.data.update({'sid': sid, 'group': "指导" if "1" in grp else "支持"})
            st.session_state.step = 2
            st.rerun()

# 通用作答模板函数
def task_stage(title, content, data_key, next_step, timer_key, total_time):
    st.header(title)
    st.info(f"题目：{content}")
    ans = st.text_area("请在这里输入你的回答：", key=f"in_{timer_key}", height=300)
    
    # 手动提交按钮
    if st.button("✅ 我已完成，进入下一环节", key=f"btn_{timer_key}"):
        st.session_state.data[data_key] = ans
        st.session_state.step = next_step
        st.rerun()
    
    # 隐形计时器（最后30s显形）
    if smart_timer(total_time, timer_key):
        st.session_state.data[data_key] = ans
        st.session_state.step = next_step
        st.rerun()

# --- 实验各阶段 ---
if st.session_state.step == 2:
    # 阶段1：前测 5min (300s)
    task_stage("📝 阶段 1：前测", st.session_state.main_i['content'], "pre_ans", 3, "t1", 300)

elif st.session_state.step == 3:
    # 阶段2：互动 3min (180s)
    st.header("🤖 阶段 2：AI 互动学习")
    st.warning("⚠️ 作答期间请勿离开此页面！")
    st.markdown("### 🔍 互动题目：" + st.session_state.main_i['content'])
    
    p, ins = generate_prompt(st.session_state.data['group'], st.session_state.main_i['content'], st.session_state.main_i['instructions'])
    st.session_state.data['used_ins'] = ins
    st.code(p)
    st.link_button("👉 点击打开豆包 (完成后请立即返回)", "https://www.doubao.com")
    
    if st.button("✅ 互动结束，进入下一阶段") or smart_timer(180, "t2"):
        st.session_state.step = 4
        st.rerun()

elif st.session_state.step == 4:
    # 阶段3：后测 5min (300s)
    task_stage("🏁 阶段 3：后测", st.session_state.main_i['content'], "post_ans", 5, "t3", 300)

elif st.session_state.step == 5:
    # 阶段4：能力迁移测试 5min (300s)
    task_stage("🚀 阶段 4：迁移测试", st.session_state.trans_i['content'], "trans_ans", 6, "t4", 300)

elif st.session_state.step == 6:
    # 阶段5：问卷
    st.header("📊 阶段 5：问卷调查")
    q1 = st.slider("1. AI 的回复对你是否有启发？(1-5)", 1, 5, 3)
    q2 = st.radio("2. 如果有困难，你更希望 AI 怎么做？", ["直接告诉我答案", "给我思路让我思考"])
    q3 = st.text_input("3. 你对本次互动的评价：")
    if st.button("📤 提交实验结果"):
        st.session_state.data['survey'] = {"q1": q1, "q2": q2, "q3": q3}
        st.session_state.step = 7
        st.rerun()

elif st.session_state.step == 7:
    st.balloons()
    st.success("🎉 全部实验已结束！")
    b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
    st.write("请复制下方代码发还给主试：")
    st.code(b64)