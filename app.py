import streamlit as st
import random
import json
import time
import base64

# --- 1. 样式配置 ---
st.set_page_config(page_title="AI 学习实验控制台", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 24px !important; }
    .stTextArea textarea { font-size: 22px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 24px !important; border-radius: 10px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .timer-warning { color: white; background-color: red; padding: 15px; border-radius: 10px; font-weight: bold; animation: blink 0.8s infinite; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 状态跳转与物理清理 ---
def next_step_and_clean(next_val, data_key=None, data_val=None):
    if data_key:
        st.session_state.data[data_key] = data_val
    # 清理所有旧环节残留的计时器和临时状态
    for key in list(st.session_state.keys()):
        if key.endswith("_end") or key.startswith("t") or key.startswith("btn_"):
            del st.session_state[key]
    st.session_state.step = next_val
    st.rerun()

# --- 3. 稳健型计时器 ---
def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    remaining = int(st.session_state[timer_key] - time.time())
    if remaining <= 0: return True
    if remaining <= 30:
        st.components.v1.html(f"<script>window.parent.document.title = '⚠️剩{remaining}秒！';</script>", height=0)
        st.markdown(f'<p class="timer-warning">⚠️ 警告：时间即将耗尽！剩余 {remaining} 秒</p>', unsafe_allow_html=True)
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 环节内容渲染器 ---
@st.cache_data
def load_bank():
    try:
        with open("question_bank.json", "r", encoding="utf-8") as f: return json.load(f)
    except: return {"1": [{"content": "示例", "instructions": ["语料"]}], "2": []}

# 使用 placeholder 确保物理隔离
placeholder = st.empty()

with placeholder.container():
    if 'step' not in st.session_state:
        st.session_state.step = 1
        st.session_state.data = {}

    # 阶段 1：信息登记
    if st.session_state.step == 1:
        st.header("📋 实验信息登记")
        st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)
        sid = st.text_input("请输入被试编号:", key="s1_sid")
        age = st.selectbox("选择学段:", ["1 (小学)", "2 (中学)"], key="s1_age")
        grp = st.selectbox("分配组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
        if st.button("🚀 开始实验", key="s1_start_btn"):
            bank = load_bank()
            if sid and len(bank[age[0]]) >= 2:
                sel = random.sample(bank[age[0]], 2)
                st.session_state.main_i, st.session_state.trans_i = sel[0], sel[1]
                st.session_state.data.update({'sid': sid, 'group': "指导" if "1" in grp else "支持"})
                next_step_and_clean(2)

    # 阶段 2：前测
    elif st.session_state.step == 2:
        st.header("📝 阶段 1：前测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("请在这里输入你的回答：", height=350, key="s2_area")
        if st.button("✅ 我已完成", key="s2_btn") or smart_timer(300, "t1"):
            next_step_and_clean(3, "pre_ans", ans)

    # 阶段 3：互动
    elif st.session_state.step == 3:
        st.header("🤖 阶段 2：AI 互动学习")
        st.error("❗ 时间到将自动翻页，请分屏观察倒计时。")
        st.markdown(f"### 🔍 题目：{st.session_state.main_i['content']}")
        ai_group = st.session_state.data['group']
        if ai_group == "指导":
            prompt = f"针对题目《{st.session_state.main_i['content']}》直接给出答案。"
            sel = "N/A"
        else:
            sel = random.choice(st.session_state.main_i['instructions'])
            prompt = f"针对题目《{st.session_state.main_i['content']}》，基于『{sel}』启发我。"
        st.session_state.data['used_ins'] = sel
        st.code(prompt)
        st.link_button("👉 点击打开豆包", "https://www.doubao.com")
        if st.button("✅ 互动结束", key="s3_btn") or smart_timer(180, "t2"):
            next_step_and_clean(4)

    # 阶段 4：后测
    elif st.session_state.step == 4:
        st.header("🏁 阶段 3：后测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("请再次输入你的回答：", height=350, key="s4_area")
        if st.button("✅ 我已完成", key="s4_btn") or smart_timer(300, "t3"):
            next_step_and_clean(5, "post_ans", ans)

    # 阶段 5：迁移
    elif st.session_state.step == 5:
        st.header("🚀 阶段 4：迁移测试")
        st.success("🌟 独立解决这个新问题：")
        st.info(f"题目：{st.session_state.trans_i['content']}")
        ans = st.text_area("请在此输入回答：", height=350, key="s5_area")
        if st.button("✅ 完成所有题目", key="s5_btn") or smart_timer(300, "t4"):
            next_step_and_clean(6, "trans_ans", ans)

    # 阶段 6：问卷
    elif st.session_state.step == 6:
        st.header("📊 阶段 5：问卷调查")
        q1 = st.slider("AI 对你有启发吗？", 1, 5, 3)
        if st.button("📤 提交结果", key="s6_btn"):
            st.session_state.data['survey'] = {"q1": q1}
            next_step_and_clean(7)

    # 阶段 7：结算
    elif st.session_state.step == 7:
        st.balloons()
        st.success("🎉 全部实验已结束！请复制下方代码：")
        st.code(base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode())