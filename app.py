import streamlit as st
import random
import json
import time
import base64

# 1. 样式与“幽灵按钮”强制物理屏蔽
st.set_page_config(page_title="实验系统", layout="centered")

# 定义一个函数，在进入实验后强制隐藏含有“开始实验”文字的按钮
def hide_ghost_button():
    st.markdown("""
        <style>
        /* 强制隐藏包含“开始实验”字样的所有按钮 */
        button:contains("开始实验") {
            display: none !important;
        }
        /* 全局字号与样式 */
        html, body, [class*="css"] { font-size: 22px !important; }
        .stButton button { height: 3em; width: 100%; font-size: 22px !important; border-radius: 12px; }
        </style>
    """, unsafe_allow_html=True)

# 2. 核心跳转函数
def force_go(step_to):
    st.session_state.step = step_to
    # 跳转时清理所有临时 key，但不清理核心数据
    for key in list(st.session_state.keys()):
        if key.startswith("t_") or key.startswith("s1_"):
            del st.session_state[key]
    st.rerun()

# 3. 稳健计时器
def run_timer(seconds, key):
    t_key = f"t_{key}"
    if t_key not in st.session_state:
        st.session_state[t_key] = time.time() + seconds
    rem = int(st.session_state[t_key] - time.time())
    if rem <= 0: return True
    if rem <= 30:
        st.error(f"⏱️ 剩余时间：{rem} 秒")
    time.sleep(1)
    st.rerun()
    return False

# 4. 主流程逻辑
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# --- 阶段 1：信息登记 (仅在 step 1 运行) ---
if st.session_state.step == 1:
    st.header("📋 登记信息")
    sid = st.text_input("编号:", key="s1_sid")
    age = st.selectbox("学段:", ["1 (小学)", "2 (中学)"], key="s1_age")
    grp = st.selectbox("组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
    
    if st.button("🚀 开始实验"):
        if sid:
            try:
                with open("question_bank.json", "r", encoding="utf-8") as f:
                    bank = json.load(f)
                age_key = age[0]
                sel = random.sample(bank[age_key], 2)
                st.session_state.main_i = sel[0]
                st.session_state.trans_i = sel[1]
                st.session_state.data = {'sid': sid, 'group': "指导型" if "1" in grp else "支持型"}
                force_go(2)
            except: st.error("初始化失败，请检查 JSON")
        else: st.warning("请输入编号")

# --- 阶段 2 及以后：激活【隐身屏蔽】 ---
else:
    hide_ghost_button() # 只要不是第一步，就强行从底层抹除“开始实验”按钮

    if st.session_state.step == 2:
        st.header("📝 阶段 1：前测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("回答:", height=300, key="s2_ans")
        if st.button("✅ 提交并下一步") or run_timer(300, "p1"):
            st.session_state.data['pre_ans'] = ans
            force_go(3)

    elif st.session_state.step == 3:
        st.header("🤖 阶段 2：AI 互动")
        st.code(f"题目：{st.session_state.main_i['content']}\n指令：去豆包讨论吧！")
        st.link_button("👉 点击打开豆包", "https://www.doubao.com")
        if st.button("✅ 互动结束") or run_timer(180, "p2"):
            force_go(4)

    elif st.session_state.step == 4:
        st.header("🏁 阶段 3：后测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("再次回答:", height=300, key="s4_ans")
        if st.button("✅ 提交并下一步") or run_timer(300, "p3"):
            st.session_state.data['post_ans'] = ans
            force_go(5)

    elif st.session_state.step == 5:
        st.header("🚀 阶段 4：迁移测试")
        st.info(f"新题目：{st.session_state.trans_i['content']}")
        ans = st.text_area("独立解题:", height=300, key="s5_ans")
        if st.button("✅ 完成实验") or run_timer(300, "p4"):
            st.session_state.data['trans_ans'] = ans
            force_go(6)

    elif st.session_state.step == 6:
        st.balloons()
        st.success("🎉 实验结束")
        st.code(base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode())