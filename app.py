import streamlit as st
import random
import json
import time
import base64

# --- 1. 样式与标题 ---
st.set_page_config(page_title="AI 学习干预实验平台", layout="centered")

st.markdown("""
    <div style='text-align: center; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; margin-bottom: 25px;'>
        <h1 style='font-size: 42px; white-space: nowrap; color: #31333F; margin: 0;'>🎓 AI 学习干预实验平台</h1>
    </div>
    <style>
    html, body, [class*="css"] { font-size: 24px !important; }
    .stTextArea textarea { font-size: 22px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 24px !important; border-radius: 12px; font-weight: bold; }
    
    /* 优化后的温和红框计时器 */
    .timer-box {
        color: #721c24; 
        background-color: #f8d7da; 
        border: 1px solid #f5c6cb;
        padding: 15px; 
        border-radius: 10px; 
        font-weight: bold; 
        text-align: center;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 状态跳转函数 ---
def next_step(next_val):
    for key in list(st.session_state.keys()):
        if key.endswith("_end") or key.startswith("t_"):
            del st.session_state[key]
    st.session_state.step = next_val
    st.rerun()

# --- 3. 温和计时器 (解决堆叠与视觉过重问题) ---
def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    
    remaining = int(st.session_state[timer_key] - time.time())
    
    # 使用占位符防止堆叠
    timer_placeholder = st.empty()
    
    if remaining <= 0:
        return True
    
    with timer_placeholder:
        # 使用更柔和的提示框样式
        msg = f"⏱️ 剩余时间：{remaining} 秒"
        if remaining <= 5:
            msg = f"⚠️ 倒计时：{remaining} 秒 (时间到将自动跳转)"
        
        st.markdown(f'<div class="timer-box">{msg}</div>', unsafe_allow_html=True)
    
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 流程逻辑 ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

step = st.session_state.step

# 阶段隔离逻辑，防止组件残留
if step == 1:
    st.header("📋 登记信息")
    sid = st.text_input("请输入被试编号:", key="s1_sid")
    age = st.selectbox("请选择学段:", ["1 (小学)", "2 (中学)"], key="s1_age")
    grp = st.selectbox("请选择分配组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
    if st.button("🚀 开始实验"):
        if sid:
            try:
                with open("question_bank.json", "r", encoding="utf-8") as f:
                    bank = json.load(f)
                age_key = age[0]
                if age_key in bank and len(bank[age_key]) >= 2:
                    sel = random.sample(bank[age_key], 2)
                    st.session_state.main_i, st.session_state.trans_i = sel[0], sel[1]
                    st.session_state.data.update({'sid': sid, 'group': "指导型" if "1" in grp else "支持型"})
                    next_step(2)
                else: st.error("题目不足。")
            except: st.error("初始化失败，请确保 question_bank.json 已上传。")
        else: st.warning("请输入编号。")

elif step == 2:
    st.header("📝 阶段 1：前测")
    st.info(f"题目：{st.session_state.main_i['content']}")
    ans = st.text_area("请输入你的回答：", height=400, key="s2_ans")
    if st.button("✅ 提交下一步") or smart_timer(15, "t1"):
        st.session_state.data['pre_ans'] = ans
        next_step(3)

elif step == 3:
    st.header("🤖 阶段 2：AI 互动学习")
    st.markdown(f"### 🔍 互动题目：\n{st.session_state.main_i['content']}")
    group_type = st.session_state.data['group']
    prompt = f"针对题目《{st.session_state.main_i['content']}》启发我思考。" if group_type == "支持型" else f"针对题目《{st.session_state.main_i['content']}》直接给答案。"
    st.code(prompt)
    st.link_button("👉 点击打开豆包", "https://www.doubao.com")
    if st.button("✅ 互动结束") or smart_timer(15, "t2"):
        next_step(4)

elif step == 4:
    st.header("🏁 阶段 3：后测")
    st.info(f"题目：{st.session_state.main_i['content']}")
    ans = st.text_area("整理并输入你的最终回答：", height=400, key="s4_ans")
    if st.button("✅ 提交下一步") or smart_timer(15, "t3"):
        st.session_state.data['post_ans'] = ans
        next_step(5)

elif step == 5:
    st.header("🚀 阶段 4：迁移测试")
    st.info(f"新题目：{st.session_state.trans_i['content']}")
    ans = st.text_area("独立完成新题目：", height=400, key="s5_ans")
    if st.button("✅ 完成实验") or smart_timer(15, "t4"):
        st.session_state.data['trans_ans'] = ans
        next_step(6)

elif step == 6:
    st.balloons()
    st.success("🎉 全部实验已结束！")
    b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
    st.write("请复制下方代码发给主试：")
    st.code(b64)