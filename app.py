import streamlit as st
import random
import json
import time
import base64

# 1. 样式与配置
st.set_page_config(page_title="实验系统", layout="centered")
st.markdown("<style>html,body{font-size:22px;} .stButton button{height:3em; width:100%; font-size:22px; border-radius:12px;}</style>", unsafe_allow_html=True)

# 2. 核心跳转：强制销毁所有旧组件
def force_go(step_to):
    # 物理清空所有 session_state，除了核心数据
    core_data = {
        'step': step_to,
        'data': st.session_state.get('data', {}),
        'main_i': st.session_state.get('main_i', {}),
        'trans_i': st.session_state.get('trans_i', {})
    }
    st.session_state.clear()
    for k, v in core_data.items():
        st.session_state[k] = v
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

# 4. 主逻辑隔离容器
main_container = st.empty()

if 'step' not in st.session_state:
    st.session_state.step = 1

with main_container.container():
    # --- 阶段 1 ---
    if st.session_state.step == 1:
        st.header("📋 登记信息")
        sid = st.text_input("编号:", key="s1_sid")
        grp = st.selectbox("组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
        if st.button("🚀 开始实验", key="S1_REAL_BTN"):
            if sid:
                try:
                    with open("question_bank.json", "r", encoding="utf-8") as f:
                        bank = json.load(f)
                    sel = random.sample(bank["1"], 2) # 默认按学段1抽
                    st.session_state.main_i = sel[0]
                    st.session_state.trans_i = sel[1]
                    st.session_state.data = {'sid': sid, 'group': "指导" if "1" in grp else "支持"}
                    force_go(2)
                except: st.error("初始化失败")

    # --- 阶段 2：前测 ---
    elif st.session_state.step == 2:
        st.header("📝 阶段 1：前测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("输入回答:", height=300, key="s2_ans")
        if st.button("✅ 提交", key="S2_REAL_BTN") or run_timer(300, "p1"):
            st.session_state.data['pre_ans'] = ans
            force_go(3)

    # --- 阶段 3：互动 ---
    elif st.session_state.step == 3:
        st.header("🤖 阶段 2：AI 互动")
        st.markdown(f"### 题目：{st.session_state.main_i['content']}")
        p = f"针对题目《{st.session_state.main_i['content']}》启发我。"
        st.code(p)
        st.link_button("👉 打开豆包", "https://www.doubao.com")
        if st.button("✅ 结束互动", key="S3_REAL_BTN") or run_timer(180, "p2"):
            force_go(4)

    # --- 阶段 4：后测 ---
    elif st.session_state.step == 4:
        st.header("🏁 阶段 3：后测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("再次输入回答:", height=300, key="s4_ans")
        if st.button("✅ 提交", key="S4_REAL_BTN") or run_timer(300, "p3"):
            st.session_state.data['post_ans'] = ans
            force_go(5)

    # --- 阶段 5：迁移 ---
    elif st.session_state.step == 5:
        st.header("🚀 阶段 4：迁移测试")
        st.info(f"新题目：{st.session_state.trans_i['content']}")
        ans = st.text_area("独立回答:", height=300, key="s5_ans")
        if st.button("✅ 最终提交", key="S5_REAL_BTN") or run_timer(300, "p4"):
            st.session_state.data['trans_ans'] = ans
            force_go(6)

    # --- 阶段 6：回收 ---
    elif st.session_state.step == 6:
        st.success("🎉 实验结束")
        st.code(base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode())