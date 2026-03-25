import streamlit as st
import random
import json
import time
import base64

# --- 1. 全局样式配置 (调大字号) ---
st.set_page_config(page_title="AI 学习实验控制台", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 24px !important;  /* 整体字号调大 */
    }
    .stTextArea textarea {
        font-size: 20px !important;
    }
    .stButton button {
        height: 3em;
        width: 100%;
        font-size: 22px !important;
    }
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
    if ai_group == "指导型":
        return f"你好！针对题目《{item_content}》直接给出标准答案。严禁提问。", "N/A"
    else:
        sel = random.choice(instructions)
        return f"你好！任务《{item_content}》。请作为支持型导师，基于线索『{sel}』启发我。", sel

# --- 3. 强制倒计时组件 ---
def mandatory_timer(seconds, key):
    if f"{key}_end" not in st.session_state:
        st.session_state[f"{key}_end"] = time.time() + seconds
    
    remaining = int(st.session_state[f"{key}_end"] - time.time())
    if remaining > 0:
        st.error(f"⏱️ 强制倒计时：{remaining} 秒")
        time.sleep(1)
        st.rerun()
        return False
    else:
        return True # 时间到，触发强制跳转

# --- 4. 实验流程控制 ---
bank = load_bank()
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# 步骤 1：信息采集
if st.session_state.step == 1:
    st.header("📋 基本信息登记")
    sid = st.text_input("请输入被试编号:")
    age = st.selectbox("学段:", ["1 (小学)", "2 (中学)"])
    grp = st.selectbox("组别:", ["1 (指导型)", "2 (支持型)"])
    if st.button("进入实验"):
        if sid and len(bank[age[0]]) >= 2:
            sel = random.sample(bank[age[0]], 2)
            st.session_state.main_i, st.session_state.trans_i = sel[0], sel[1]
            st.session_state.data.update({'sid': sid, 'group': "指导" if "1" in grp else "支持"})
            st.session_state.step = 2
            st.rerun()

# 步骤 2/4/5 的通用作答模板 (含 30s 强制跳转)
def task_stage(title, content, data_key, next_step, timer_key):
    st.header(title)
    st.info(f"题目：{content}")
    ans = st.text_area("请作答：", key=f"input_{timer_key}", height=250)
    if mandatory_timer(30, timer_key):
        st.session_state.data[data_key] = ans
        st.session_state.step = next_step
        st.rerun()
    if st.button("提前提交"):
        st.session_state.data[data_key] = ans
        st.session_state.step = next_step
        st.rerun()

if st.session_state.step == 2:
    task_stage("📝 阶段 1：前测", st.session_state.main_i['content'], "pre_ans", 3, "t1")

elif st.session_state.step == 3:
    st.header("🤖 阶段 2：AI 互动学习")
    st.warning("⚠️ 注意：互动期间请勿关闭或离开本页面！")
    st.markdown("### 🔍 互动题目：" + st.session_state.main_i['content'])
    
    p, ins = generate_prompt(st.session_state.data['group'], st.session_state.main_i['content'], st.session_state.main_i['instructions'])
    st.session_state.data['used_ins'] = ins
    st.code(p)
    st.link_button("👉 点击打开豆包 (完成后请立即返回)", "https://www.doubao.com")
    
    if mandatory_timer(30, "t2"):
        st.session_state.step = 4
        st.rerun()

elif st.session_state.step == 4:
    task_stage("🏁 阶段 3：后测", st.session_state.main_i['content'], "post_ans", 5, "t3")

elif st.session_state.step == 5:
    task_stage("🚀 阶段 4：迁移测试", st.session_state.trans_i['content'], "trans_ans", 6, "t4")

# 步骤 6：问卷环节 (内置小脚本)
elif st.session_state.step == 6:
    st.header("📊 阶段 5：主观感受问卷")
    q1 = st.slider("1. 你觉得 AI 对你的帮助大吗？(1-5)", 1, 5, 3)
    q2 = st.radio("2. 你更喜欢哪种引导方式？", ["直接给答案", "启发我思考"])
    q3 = st.text_input("3. 你对本次实验有什么建议？")
    
    if st.button("提交问卷"):
        st.session_state.data['survey'] = {"q1": q1, "q2": q2, "q3": q3}
        st.session_state.step = 7
        st.rerun()

# 步骤 7：最终回收
elif st.session_state.step == 7:
    st.balloons()
    st.success("全部实验已结束！")
    b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
    st.write("请复制下方代码发给主试：")
    st.code(b64)