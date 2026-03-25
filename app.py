import streamlit as st
import random
import json
import time
import base64

# --- 1. 全局样式 ---
st.set_page_config(page_title="AI 实验控制台", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 22px !important; }
    .stTextArea textarea { font-size: 20px !important; }
    .stButton button { height: 3em; width: 100%; font-size: 22px !important; border-radius: 12px; font-weight: bold; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .timer-warning { color: white; background-color: #FF4B4B; padding: 15px; border-radius: 10px; animation: blink 0.8s infinite; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心跳转函数 (物理清理) ---
def go_to(next_step):
    # 清理所有计时器和临时组件缓存
    keys_to_keep = {'step', 'data', 'main_i', 'trans_i'}
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.session_state.step = next_step
    st.rerun()

# --- 3. 稳健计时器 ---
def run_timer(seconds, key):
    t_key = f"timer_{key}"
    if t_key not in st.session_state:
        st.session_state[t_key] = time.time() + seconds
    
    rem = int(st.session_state[t_key] - time.time())
    if rem <= 0: return True
    
    if rem <= 30:
        st.markdown(f'<div class="timer-warning">⚠️ 倒计时：{rem} 秒 (到时将自动跳转)</div>', unsafe_allow_html=True)
        st.components.v1.html(f"<script>window.parent.document.title='剩{rem}秒';</script>", height=0)
    
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 环节内容 ---

# A. 信息采集
def show_start():
    st.header("📋 实验信息登记")
    st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)
    sid = st.text_input("被试编号:", key="init_sid")
    age = st.selectbox("学段:", ["1 (小学)", "2 (中学)"], key="init_age")
    grp = st.selectbox("组别:", ["1 (指导型)", "2 (支持型)"], key="init_grp")
    
    if st.button("🚀 开始实验", key="btn_start_global"):
        if sid:
            try:
                with open("question_bank.json", "r", encoding="utf-8") as f:
                    bank = json.load(f)
                sel = random.sample(bank[age[0]], 2)
                st.session_state.main_i = sel[0]
                st.session_state.trans_i = sel[1]
                st.session_state.data = {'sid': sid, 'group': "指导" if "1" in grp else "支持"}
                go_to(2)
            except Exception as e:
                st.error(f"题库加载失败: {e}")

# B. 作答环节模板
def show_write(title, item, d_key, n_step, t_key, seconds, is_trans=False):
    st.header(title)
    if is_trans: st.success("🌟 迁移挑战：请独立解决这个新题目。")
    st.info(f"题目：{item['content']}")
    ans = st.text_area("在此输入回答:", height=300, key=f"input_{t_key}")
    
    if st.button("✅ 提交并进入下一步", key=f"btn_{t_key}") or run_timer(seconds, t_key):
        st.session_state.data[d_key] = ans
        go_to(n_step)

# C. AI 互动
def show_ai():
    st.header("🤖 阶段 2：AI 互动学习")
    st.warning("⚠️ 限时 3 分钟。时间到将自动翻页。")
    st.markdown(f"### 🔍 互动题目：\n{st.session_state.main_i['content']}")
    
    grp = st.session_state.data['group']
    if grp == "指导":
        prompt = f"针对题目《{st.session_state.main_i['content']}》直接给出答案。"
        sel = "N/A"
    else:
        sel = random.choice(st.session_state.main_i['instructions'])
        prompt = f"针对题目《{st.session_state.main_i['content']}》，基于线索『{sel}』启发我。"
    
    st.session_state.data['used_ins'] = sel
    st.code(prompt)
    st.link_button("👉 打开豆包", "https://www.doubao.com")
    
    if st.button("✅ 互动结束", key="btn_ai_done") or run_timer(180, "ai"):
        go_to(4)

# --- 5. 主逻辑入口 (核心隔离) ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# 重点：通过这种结构，Step 1 的代码在 Step 2 之后绝对不会被运行到
curr_step = st.session_state.step

if curr_step == 1:
    show_start()
elif curr_step == 2:
    show_write("📝 阶段 1：前测", st.session_state.main_i, "pre_ans", 3, "t1", 300)
elif curr_step == 3:
    show_ai()
elif curr_step == 4:
    show_write("🏁 阶段 3：后测", st.session_state.main_i, "post_ans", 5, "t3", 300)
elif curr_step == 5:
    show_write("🚀 阶段 4：迁移测试", st.session_state.trans_i, "trans_ans", 6, "t4", 300, True)
elif curr_step == 6:
    st.header("📊 阶段 5：问卷调查")
    q1 = st.slider("AI 是否有启发？", 1, 5, 3)
    if st.button("📤 提交结果"):
        st.session_state.data['survey'] = {"q1": q1}
        go_to(7)
elif curr_step == 7:
    st.balloons()
    st.success("🎉 实验结束！请复制下方代码：")
    st.code(base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode())