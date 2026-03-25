import streamlit as st
import random
import json
import time
import base64

# --- 1. 样式配置 (调大字号) ---
st.set_page_config(page_title="AI 实验控制台", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 24px !important; }
    .stTextArea textarea { font-size: 24px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 26px !important; border-radius: 12px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .timer-warning { color: white; background-color: red; padding: 15px; border-radius: 10px; font-weight: bold; animation: blink 0.8s infinite; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 状态跳转函数 ---
def next_step(next_val):
    # 彻底清理所有计时器相关的旧缓存
    for key in list(st.session_state.keys()):
        if key.endswith("_end") or key.startswith("t_"):
            del st.session_state[key]
    st.session_state.step = next_val
    st.rerun()

# --- 3. 稳健计时器 ---
def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    
    remaining = int(st.session_state[timer_key] - time.time())
    if remaining <= 0: return True
    
    if remaining <= 30:
        st.markdown(f'<p class="timer-warning">⚠️ 警告：时间即将耗尽！剩余 {remaining} 秒</p>', unsafe_allow_html=True)
    
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 核心渲染逻辑 ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# 【关键】创建一个空的占位符作为唯一的渲染容器
placeholder = st.empty()

# 使用 with 语句确保每次渲染都是从空白开始
with placeholder.container():
    # 阶段 1：信息登记
    if st.session_state.step == 1:
        st.header("📋 登记信息")
        sid = st.text_input("请输入被试编号:", key="s1_sid")
        age = st.selectbox("请选择学段:", ["1 (小学)", "2 (中学)"], key="s1_age")
        grp = st.selectbox("请选择分配组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
        
        if st.button("🚀 开始实验", key="s1_start_btn"):
            if sid:
                try:
                    with open("question_bank.json", "r", encoding="utf-8") as f:
                        bank = json.load(f)
                    age_key = age[0]
                    if age_key in bank and len(bank[age_key]) >= 2:
                        sel = random.sample(bank[age_key], 2)
                        st.session_state.main_i = sel[0]
                        st.session_state.trans_i = sel[1]
                        st.session_state.data.update({
                            'sid': sid, 
                            'group': "指导型" if "1" in grp else "支持型"
                        })
                        next_step(2)
                    else:
                        st.error("题库中该组别题目不足。")
                except:
                    st.error("初始化失败，请检查 question_bank.json 是否存在。")
            else:
                st.warning("请输入编号。")

    # 阶段 2：前测
    elif st.session_state.step == 2:
        st.header("📝 阶段 1：前测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("请在这里输入你的回答：", height=400, key="s2_ans")
        if st.button("✅ 提交并进入下一步", key="s2_btn") or smart_timer(300, "t1"):
            st.session_state.data['pre_ans'] = ans
            next_step(3)

    # 阶段 3：互动
    elif st.session_state.step == 3:
        st.header("🤖 阶段 2：AI 互动学习")
        st.error("❗ 时间到将自动跳转。")
        st.markdown(f"### 🔍 题目：{st.session_state.main_i['content']}")
        
        group = st.session_state.data['group']
        if group == "指导型":
            prompt = f"针对题目《{st.session_state.main_i['content']}》直接给出答案。"
        else:
            ins = random.choice(st.session_state.main_i['instructions'])
            prompt = f"针对题目《{st.session_state.main_i['content']}》，基于线索『{ins}』启发我。"
        
        st.code(prompt)
        st.link_button("👉 点击打开豆包", "https://www.doubao.com")
        if st.button("✅ 互动结束", key="s3_btn") or smart_timer(180, "t2"):
            next_step(4)

    # 阶段 4：后测
    elif st.session_state.step == 4:
        st.header("🏁 阶段 3：后测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("请再次回答：", height=400, key="s4_ans")
        if st.button("✅ 提交并进入下一步", key="s4_btn") or smart_timer(300, "t3"):
            st.session_state.data['post_ans'] = ans
            next_step(5)

    # 阶段 5：迁移
    elif st.session_state.step == 5:
        st.header("🚀 阶段 4：迁移测试")
        st.success("🌟 独立解决新题：")
        st.info(f"题目：{st.session_state.trans_i['content']}")
        ans = st.text_area("请输入回答：", height=400, key="s5_ans")
        if st.button("✅ 完成实验", key="s5_btn") or smart_timer(300, "t4"):
            st.session_state.data['trans_ans'] = ans
            next_step(6)

    # 阶段 6：回收
    elif st.session_state.step == 6:
        st.success("🎉 全部实验已结束！")
        b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
        st.write("请复制下方代码：")
        st.code(b64)