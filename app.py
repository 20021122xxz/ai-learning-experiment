import streamlit as st
import random
import json
import time
import base64

# 1. 样式与配置
st.set_page_config(page_title="实验系统", layout="centered")
st.markdown("<style>html,body{font-size:22px;} .stButton button{height:3em; width:100%; font-size:22px; border-radius:12px;}</style>", unsafe_allow_html=True)

# 2. 核心跳转：彻底清理所有旧组件和缓存
def force_go(step_to):
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
        st.error(f"⏱️ 剩余时间：{rem} 秒 (到时将自动跳转)")
    time.sleep(1)
    st.rerun()
    return False

# 4. 加载题库函数
def get_bank():
    try:
        with open("question_bank.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ 题库文件读取失败，请检查 question_bank.json。错误: {e}")
        return None

# --- 主逻辑隔离容器 ---
main_container = st.empty()

if 'step' not in st.session_state:
    st.session_state.step = 1

with main_container.container():
    # --- 阶段 1：信息登记 ---
    if st.session_state.step == 1:
        st.header("📋 登记信息")
        sid = st.text_input("1. 请输入被试编号:", key="s1_sid")
        age = st.selectbox("2. 请选择学段:", ["1 (小学)", "2 (中学)"], key="s1_age")
        grp = st.selectbox("3. 请选择分配组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
        
        if st.button("🚀 开始实验", key="S1_START_ACTUAL"):
            if sid:
                bank = get_bank()
                if bank:
                    age_key = age[0] # 取 "1" 或 "2"
                    if age_key in bank and len(bank[age_key]) >= 2:
                        sel = random.sample(bank[age_key], 2)
                        st.session_state.main_i = sel[0]
                        st.session_state.trans_i = sel[1]
                        st.session_state.data = {
                            'sid': sid, 
                            'group': "指导型" if "1" in grp else "支持型",
                            'age': "小学" if age_key=="1" else "中学"
                        }
                        force_go(2)
                    else:
                        st.error(f"❌ 题库中该学段题目不足（至少需要2道题）")
            else:
                st.warning("⚠️ 请输入编号后再开始。")

    # --- 阶段 2：前测 (5min) ---
    elif st.session_state.step == 2:
        st.header("📝 阶段 1：前测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("请在这里输入你的回答：", height=300, key="s2_ans")
        if st.button("✅ 提交并进入下一步", key="S2_SUBMIT") or run_timer(300, "p1"):
            st.session_state.data['pre_ans'] = ans
            force_go(3)

    # --- 阶段 3：互动 (3min) ---
    elif st.session_state.step == 3:
        st.header("🤖 阶段 2：AI 互动学习")
        st.warning("❗ 互动限时 3 分钟，时间到将自动跳转。")
        st.markdown(f"### 🔍 互动题目：\n{st.session_state.main_i['content']}")
        
        # 指导语生成
        if st.session_state.data['group'] == "指导型":
            prompt = f"针对题目《{st.session_state.main_i['content']}》直接给出标准答案。严禁提问。"
            sel_ins = "N/A"
        else:
            sel_ins = random.choice(st.session_state.main_i['instructions'])
            prompt = f"针对题目《{st.session_state.main_i['content']}》，请基于线索『{sel_ins}』启发我思考。"
        
        st.session_state.data['used_ins'] = sel_ins
        st.write("请复制下方指令前往豆包：")
        st.code(prompt)
        st.link_button("👉 点击打开【豆包 AI】", "https://www.doubao.com")
        
        if st.button("✅ 互动结束，进入下一阶段", key="S3_NEXT") or run_timer(180, "p2"):
            force_go(4)

    # --- 阶段 4：后测 (5min) ---
    elif st.session_state.step == 4:
        st.header("🏁 阶段 3：后测")
        st.info(f"题目：{st.session_state.main_i['content']}")
        ans = st.text_area("请再次输入你的回答：", height=300, key="s4_ans")
        if st.button("✅ 提交并进入下一步", key="S4_SUBMIT") or run_timer(300, "p3"):
            st.session_state.data['post_ans'] = ans
            force_go(5)

    # --- 阶段 5：迁移测试 (5min) ---
    elif st.session_state.step == 5:
        st.header("🚀 阶段 4：迁移测试")
        st.success("🌟 挑战：请利用刚才学到的方法，独立解决这道新题。")
        st.info(f"新题目：{st.session_state.trans_i['content']}")
        ans = st.text_area("请在此输入解题方案：", height=300, key="s5_ans")
        if st.button("✅ 完成实验", key="S5_FINISH") or run_timer(300, "p4"):
            st.session_state.data['trans_ans'] = ans
            force_go(6)

    # --- 阶段 6：回收数据 ---
    elif st.session_state.step == 6:
        st.balloons()
        st.success("🎉 全部实验已结束！")
        final_json = json.dumps(st.session_state.data, ensure_ascii=False)
        b64_code = base64.b64encode(final_json.encode()).decode()
        st.write("请复制下方代码发还给主试：")
        st.code(b64_code)