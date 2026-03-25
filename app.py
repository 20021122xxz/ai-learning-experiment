import streamlit as st
import random
import json
import time
import base64

# --- 1. 字号与样式 (确保大字号不丢失) ---
st.set_page_config(page_title="AI 实验控制台", layout="centered")

def apply_custom_style():
    st.markdown("""
        <style>
        /* 全局字号调大 */
        html, body, [class*="css"], .stMarkdown, p { font-size: 24px !important; }
        .stTextArea textarea { font-size: 24px !important; line-height: 1.5 !important; }
        .stButton button { height: 3.5em; width: 100%; font-size: 26px !important; border-radius: 12px; font-weight: bold; }
        .stSelectbox label, .stTextInput label { font-size: 24px !important; }
        /* 强制隐藏 Step 1 的按钮，防止残留 */
        button:contains("开始实验") { display: none !important; }
        #root > div:nth-child(1) > div > div > div > div > section > div { gap: 2rem; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. 状态跳转 ---
def force_go(step_to):
    st.session_state.step = step_to
    # 清理所有非核心缓存
    for key in list(st.session_state.keys()):
        if key.startswith("t_") or key.startswith("s1_") or key.startswith("btn_"):
            del st.session_state[key]
    st.rerun()

# --- 3. 稳健计时器 ---
def run_timer(seconds, key):
    t_key = f"t_{key}"
    if t_key not in st.session_state:
        st.session_state[t_key] = time.time() + seconds
    rem = int(st.session_state[t_key] - time.time())
    if rem <= 0: return True
    if rem <= 30:
        st.error(f"⏱️ 剩余时间：{rem} 秒 (到时将自动跳转)")
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 核心逻辑 ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# --- 阶段 1：登记信息 (此时不应用隐藏按钮的样式) ---
if st.session_state.step == 1:
    # 局部样式：此时显示开始按钮
    st.markdown("<style>button:contains('开始实验') { display: block !important; } html,body{font-size:24px;}</style>", unsafe_allow_html=True)
    st.header("📋 登记信息")
    sid = st.text_input("1. 编号:", key="s1_sid")
    age_opt = st.selectbox("2. 学段:", ["1 (小学)", "2 (中学)"], key="s1_age")
    grp_opt = st.selectbox("3. 组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
    
    if st.button("🚀 开始实验"):
        if sid:
            try:
                with open("question_bank.json", "r", encoding="utf-8") as f:
                    bank = json.load(f)
                # 兼容性抽题逻辑
                age_key = age_opt[0] 
                if age_key in bank and len(bank[age_key]) >= 2:
                    sel = random.sample(bank[age_key], 2)
                    st.session_state.main_i = sel[0]
                    st.session_state.trans_i = sel[1]
                    st.session_state.data = {
                        'sid': sid, 
                        'group': "指导型" if "1" in grp_opt else "支持型"
                    }
                    force_go(2)
                else:
                    st.error(f"题库数据异常：{age_key} 组下题目不足 2 道。")
            except Exception as e:
                st.error(f"初始化失败：请确认 question_bank.json 是否在 GitHub 根目录。")
        else:
            st.warning("请输入编号。")

# --- 阶段 2 及以后：启用全局隐藏样式 ---
else:
    apply_custom_style()

    if st.session_state.step == 2:
        st.header("📝 阶段 1：前测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("输入回答:", height=400, key="s2_ans")
        if st.button("✅ 提交并进入下一步") or run_timer(300, "p1"):
            st.session_state.data['pre_ans'] = ans
            force_go(3)

    elif st.session_state.step == 3:
        st.header("🤖 阶段 2：AI 互动")
        st.markdown(f"### 互动题目：\n{st.session_state.main_i['content']}")
        
        # 实时生成 Prompt
        grp = st.session_state.data['group']
        if grp == "指导型":
            p = f"针对题目《{st.session_state.main_i['content']}》直接给出答案。"
            ins = "N/A"
        else:
            ins = random.choice(st.session_state.main_i['instructions'])
            p = f"针对题目《{st.session_state.main_i['content']}》，基于线索『{ins}』启发我。"
        st.session_state.data['used_ins'] = ins
        
        st.write("请复制指令前往豆包：")
        st.code(p)
        st.link_button("👉 点击打开豆包", "https://www.doubao.com")
        if st.button("✅ 互动结束") or run_timer(180, "p2"):
            force_go(4)

    elif st.session_state.step == 4:
        st.header("🏁 阶段 3：后测")
        st.info(f"题目(同前测)：{st.session_state.main_i['content']}")
        ans = st.text_area("再次输入回答:", height=400, key="s4_ans")
        if st.button("✅ 提交并进入下一步") or run_timer(300, "p3"):
            st.session_state.data['post_ans'] = ans
            force_go(5)

    elif st.session_state.step == 5:
        st.header("🚀 阶段 4：迁移测试")
        st.success("🌟 迁移挑战：独立解决新题目。")
        st.info(f"题目：{st.session_state.trans_i['content']}")
        ans = st.text_area("独立解题:", height=400, key="s5_ans")
        if st.button("✅ 完成实验") or run_timer(300, "p4"):
            st.session_state.data['trans_ans'] = ans
            force_go(6)

    elif st.session_state.step == 6:
        st.balloons()
        st.success("🎉 全部实验已结束！")
        b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
        st.write("请复制下方代码发还主试：")
        st.code(b64)