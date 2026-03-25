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
    .stTextArea textarea { font-size: 24px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 24px !important; border-radius: 12px; font-weight: bold; }
    .static-timer { color: white; background-color: #FF4B4B; padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JavaScript 唤回增强 (修改标题 & 发送系统通知) ---
def trigger_remote_alert(remaining, is_final=False):
    if is_final:
        js_code = """
        <script>
        // 修改标签页标题
        window.parent.document.title = "🚩 时间到！请回实验页面";
        // 发送浏览器系统通知 (需用户在第一页允许)
        if (Notification.permission === "granted") {
            new Notification("⏰ 实验提醒", {body: "互动时间已到，请返回填写后测！", icon: "https://cdn-icons-png.flaticon.com/512/179/179314.png"});
        }
        </script>
        """
    else:
        js_code = f"<script>window.parent.document.title = '⚠️ 剩 {remaining} 秒 | AI 实验';</script>"
    st.components.v1.html(js_code, height=0)

# --- 3. 核心跳转与计时 ---
def next_step(next_val):
    for key in list(st.session_state.keys()):
        if key.endswith("_end") or key.startswith("t_"):
            del st.session_state[key]
    st.session_state.step = next_val
    st.rerun()

def smart_timer(total_seconds, key):
    timer_key = f"{key}_end"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time() + total_seconds
    
    remaining = int(st.session_state[timer_key] - time.time())
    
    if remaining <= 0:
        trigger_remote_alert(0, is_final=True)
        return True
    
    # 每秒更新一次浏览器标签页标题
    if remaining <= 5:
        trigger_remote_alert(remaining)
        
    st.markdown(f'<div class="static-timer">⏱️ 剩余时间：{remaining} 秒</div>', unsafe_allow_html=True)
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 流程逻辑 ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

if st.session_state.step == 1:
    st.header("📋 登记信息")
    # 这一行很关键：请求系统通知权限
    st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)
    
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
                    st.session_state.main_i, st.session_state.trans_i = sel[0], sel[1]
                    st.session_state.data.update({'sid': sid, 'group': "指导型" if "1" in grp else "支持型"})
                    next_step(2)
                else: st.error("题库题目不足。")
            except: st.error("初始化失败，请检查 JSON。")
        else: st.warning("请输入编号。")

elif st.session_state.step == 2:
    st.header("📝 阶段 1：前测")
    st.info(f"题目：{st.session_state.main_i['content']}")
    ans = st.text_area("请在这里输入你的回答：", height=400, key="s2_ans")
    if st.button("✅ 提交下一步") or smart_timer(15, "t1"):
        st.session_state.data['pre_ans'] = ans
        next_step(3)

elif st.session_state.step == 3:
    st.header("🤖 阶段 2：AI 互动学习")
    st.warning("⚠️ 互动时请留意浏览器标签页标题的倒计时！")
    st.markdown(f"### 🔍 互动题目：\n{st.session_state.main_i['content']}")
    
    group_type = st.session_state.data['group']
    prompt = f"针对题目《{st.session_state.main_i['content']}》启发我思考。" if group_type == "支持型" else f"给出标准答案。"
    
    st.code(prompt)
    st.link_button("👉 点击打开【豆包 AI】", "https://www.doubao.com")
    
    if st.button("✅ 互动结束") or smart_timer(15, "t2"):
        next_step(4)

elif st.session_state.step == 4:
    st.header("🏁 阶段 3：后测")
    st.success("📝 请整理并输入你的最终答案：")
    st.info(f"题目：{st.session_state.main_i['content']}")
    ans = st.text_area("输入最终回答：", height=400, key="s4_ans")
    if st.button("✅ 提交下一步") or smart_timer(15, "t3"):
        st.session_state.data['post_ans'] = ans
        next_step(5)

elif st.session_state.step == 5:
    st.header("🚀 阶段 4：迁移测试")
    st.info(f"新题目：{st.session_state.trans_i['content']}")
    ans = st.text_area("独立解题：", height=400, key="s5_ans")
    if st.button("✅ 完成实验") or smart_timer(15, "t4"):
        st.session_state.data['trans_ans'] = ans
        next_step(6)

elif st.session_state.step == 6:
    st.success("🎉 全部实验已结束！")
    st.code(base64.b64encode(json.dumps(st.session_state.data, ensure_ascii=False).encode()).decode())