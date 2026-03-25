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
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.2; } 100% { opacity: 1; } }
    .timer-warning { 
        color: white; background-color: red; padding: 15px; border-radius: 10px;
        font-weight: bold; animation: blink 0.8s infinite; text-align: center; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心函数 ---
@st.cache_data
def load_bank():
    try:
        with open("question_bank.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"1": [{"content": "示例题", "instructions": ["语料"]}], "2": []}

def generate_prompt(ai_group, item_content, instructions):
    if ai_group == "指导":
        return f"你好！针对题目《{item_content}》直接给出标准答案。严禁提问。", "N/A"
    else:
        sel = random.choice(instructions)
        return f"你好！任务《{item_content}》。请作为支持型导师，基于线索『{sel}』启发我。", sel

# --- 3. 稳健型计时器：自动清理旧缓存 ---
def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    
    # 核心修复：如果切换了环节，确保只运行当前 key 的计时器
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    
    remaining = int(st.session_state[timer_key] - time.time())
    
    if remaining <= 0:
        return True 
    
    if remaining <= 30:
        # 修改标签页标题唤回被试
        st.components.v1.html(f"<script>window.parent.document.title = '⚠️ 剩余{remaining}秒！';</script>", height=0)
        st.markdown(f'<p class="timer-warning">⚠️ 警告：时间即将耗尽！剩余 {remaining} 秒</p>', unsafe_allow_html=True)
    else:
        st.components.v1.html("<script>window.parent.document.title = '实验进行中...';</script>", height=0)
    
    time.sleep(1)
    st.rerun()
    return False

# 强制跳转并清理所有计时器
def force_next_step(next_step_val):
    # 清理所有以 "_end" 结尾的计时器缓存
    keys_to_del = [k for k in st.session_state.keys() if k.endswith("_end")]
    for k in keys_to_del:
        del st.session_state[k]
    st.session_state.step = next_step_val
    st.rerun()

# --- 4. 流程控制 ---
bank = load_bank()
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# 【步骤 1】信息采集
if st.session_state.step == 1:
    st.header("📋 实验信息登记")
    sid = st.text_input("请输入被试编号:")
    age = st.selectbox("选择学段:", ["1 (小学)", "2 (中学)"])
    grp = st.selectbox("分配组别:", ["1 (指导型)", "2 (支持型)"])
    if st.button("🚀 开始实验"):
        if sid and len(bank[age[0]]) >= 2:
            sel = random.sample(bank[age[0]], 2)
            st.session_state.main_i, st.session_state.trans_i = sel[0], sel[1]
            st.session_state.data.update({'sid': sid, 'group': "指导" if "1" in grp else "支持"})
            force_next_step(2)

# 【通用环节模板】
def task_stage(title, content, data_key, next_step, timer_key, total_time, is_transfer=False):
    st.header(title)
    if is_transfer: st.success("🌟 迁移挑战：请独立解决这个新问题。")
    st.info(f"题目：{content}")
    ans = st.text_area("请在这里输入回答：", key=f"in_{timer_key}", height=350)
    
    if st.button("✅ 我已完成，进入下一环节", key=f"btn_{timer_key}"):
        st.session_state.data[data_key] = ans
        force_next_step(next_step)
    
    if smart_timer(total_time, timer_key):
        st.session_state.data[data_key] = ans
        force_next_step(next_step)

# --- 分阶段执行 ---
if st.session_state.step == 2:
    task_stage("📝 阶段 1：前测", st.session_state.main_i['content'], "pre_ans", 3, "t1", 300)

elif st.session_state.step == 3:
    st.header("🤖 阶段 2：AI 互动学习")
    st.error("❗ 请将此窗口与豆包并排显示，观察倒计时！")
    st.markdown("### 🔍 互动题目：" + st.session_state.main_i['content'])
    p, ins = generate_prompt(st.session_state.data['group'], st.session_state.main_i['content'], st.session_state.main_i['instructions'])
    st.session_state.data['used_ins'] = ins
    st.code(p)
    st.link_button("👉 点击打开豆包互动", "https://www.doubao.com")
    
    if st.button("✅ 互动结束，进入下一阶段") or smart_timer(180, "t2"):
        force_next_step(4)

elif st.session_state.step == 4:
    task_stage("🏁 阶段 3：后测", st.session_state.main_i['content'], "post_ans", 5, "t3", 300)

elif st.session_state.step == 5:
    task_stage("🚀 阶段 4：迁移测试", st.session_state.trans_i['content'], "trans_ans", 6, "t4", 300, is_transfer=True)

elif st.session_state.step == 6:
    st.header("📊 阶段 5：问卷调查")
    q1 = st.slider("1. AI 的回复是否有启发？(1-5)", 1, 5, 3)
    q2 = st.radio("2. 偏好的引导方式：", ["直接答案", "启发思路"])
    q3 = st.text_input("3. 评价：")
    if st.button("📤 提交结果"):
        st.session_state.data['survey'] = {"q1": q1, "q2": q2, "q3": q3}
        force_next_step(7)

elif st.session_state.step == 7:
    st.balloons()
    st.success("🎉 全部实验已结束！")
    b64 = base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode()
    st.write("请复制下方代码发给主试：")
    st.code(b64)