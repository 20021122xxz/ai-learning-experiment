import streamlit as st
import random
import json
import time
import base64

# --- 1. 全局配置与样式 ---
st.set_page_config(page_title="AI 学习实验控制台", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 24px !important; }
    .stTextArea textarea { font-size: 22px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 24px !important; border-radius: 10px; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .timer-warning { 
        color: white; background-color: red; padding: 20px; border-radius: 10px;
        font-weight: bold; animation: blink 0.8s infinite; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JavaScript 增强工具 (仅保留系统通知与标题) ---
def trigger_js_effects(remaining, is_final=False):
    if is_final:
        js_code = """
        <script>
        // 1. 系统级通知 (如果权限允许)
        if (Notification.permission === "granted") {
            new Notification("⏰ 时间到！", {body: "请返回实验页面进行下一步。"});
        }
        // 2. 静默修改标题，不弹窗
        window.parent.document.title = "🚩 时间到，请返回！";
        </script>
        """
    elif remaining <= 10:
        js_code = f"<script>window.parent.document.title = '⚠️仅剩 {remaining} 秒！';</script>"
    else:
        js_code = f"<script>window.parent.document.title = '剩余 {remaining} 秒...';</script>"
    
    st.components.v1.html(js_code, height=0)

# --- 3. 核心状态与计时逻辑 ---
def next_step_and_clean(next_val, data_key=None, data_val=None):
    if data_key: st.session_state.data[data_key] = data_val
    # 彻底清理计时器缓存
    for key in list(st.session_state.keys()):
        if key.endswith("_end") or key.startswith("t"): 
            del st.session_state[key]
    st.session_state.step = next_val
    st.rerun()

def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    
    remaining = int(st.session_state[timer_key] - time.time())
    
    if remaining <= 0:
        trigger_js_effects(0, is_final=True)
        return True # 强制跳转
    
    if remaining <= 30:
        trigger_js_effects(remaining)
        st.markdown(f'<p class="timer-warning">⚠️ 警告：本环节即将结束！剩余 {remaining} 秒</p>', unsafe_allow_html=True)
    
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 实验环节函数 ---
@st.cache_data
def load_bank():
    try:
        with open("question_bank.json", "r", encoding="utf-8") as f: return json.load(f)
    except: return {"1": [{"content": "示例题", "instructions": ["语料"]}], "2": []}

def stage_info():
    st.header("📋 实验信息登记")
    # 请求通知权限
    st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)
    sid = st.text_input("请输入被试编号:")
    age = st.selectbox("选择学段:", ["1 (小学)", "2 (中学)"])
    grp = st.selectbox("分配组别:", ["1 (指导型)", "2 (支持型)"])
    if st.button("🚀 开始实验"):
        bank = load_bank()
        if sid and len(bank[age[0]]) >= 2:
            sel = random.sample(bank[age[0]], 2)
            st.session_state.main_i, st.session_state.trans_i = sel[0], sel[1]
            st.session_state.data = {'sid': sid, 'group': "指导" if "1" in grp else "支持"}
            next_step_and_clean(2)

def stage_writing(title, item, data_key, next_val, timer_key, total_time, is_transfer=False):
    st.header(title)
    if is_transfer: st.success("🌟 迁移挑战：请独立解决这个新问题。")
    st.info(f"题目：{item['content']}")
    ans = st.text_area("请在此输入回答：", height=350, key=f"area_{timer_key}")
    if st.button("✅ 我已完成", key=f"btn_{timer_key}") or smart_timer(total_time, timer_key):
        next_step_and_clean(next_val, data_key, ans)

def stage_ai_interaction():
    st.header("🤖 阶段 2：AI 互动学习")
    st.error("❗ 本环节限时 3 分钟。请留意电脑通知提示或分屏观察倒计时。")
    st.markdown("### 🔍 互动题目：" + st.session_state.main_i['content'])
    
    ai_group = st.session_state.data['group']
    if ai_group == "指导":
        prompt, sel = f"针对题目《{st.session_state.main_i['content']}》直接给出答案。", "N/A"
    else:
        sel = random.choice(st.session_state.main_i['instructions'])
        prompt = f"针对题目《{st.session_state.main_i['content']}》，基于『{sel}』启发我。"
    
    st.session_state.data['used_ins'] = sel
    st.code(prompt)
    st.link_button("👉 点击打开豆包进行互动", "https://www.doubao.com")
    
    if st.button("✅ 互动结束") or smart_timer(180, "ai_timer"):
        next_step_and_clean(4)

# --- 5. 主逻辑入口 ---
if 'step' not in st.session_state: st.session_state.step = 1
if st.session_state.step == 1: stage_info()
elif st.session_state.step == 2: stage_writing("📝 阶段 1：前测", st.session_state.main_i, "pre_ans", 3, "t1", 300)
elif st.session_state.step == 3: stage_ai_interaction()
elif st.session_state.step == 4: stage_writing("🏁 阶段 3：后测", st.session_state.main_i, "post_ans", 5, "t3", 300)
elif st.session_state.step == 5: stage_writing("🚀 阶段 4：迁移测试", st.session_state.trans_i, "trans_ans", 6, "t4", 300, True)
elif st.session_state.step == 6:
    st.header("📊 阶段 5：问卷调查")
    q1 = st.slider("1. AI 对你有启发吗？", 1, 5, 3)
    if st.button("📤 提交结果"):
        st.session_state.data['survey'] = {"q1": q1}
        next_step_and_clean(7)
elif st.session_state.step == 7:
    st.success("🎉 全部实验已结束！")
    b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
    st.write("请复制下方代码发给主试：")
    st.code(b64)