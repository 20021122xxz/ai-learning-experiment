import streamlit as st
import random
import json
import time
import base64

# --- 1. 样式与标题 (视觉平衡版) ---
st.set_page_config(page_title="AI 学习干预实验平台", layout="centered")

# 顶部大标题
st.markdown("""
    <div style='text-align: center; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; margin-bottom: 25px;'>
        <h1 style='font-size: 42px; white-space: nowrap; color: #31333F; margin: 0;'>🎓 AI 学习干预实验平台</h1>
    </div>
    <style>
    html, body, [class*="css"] { font-size: 24px !important; }
    .stTextArea textarea { font-size: 22px !important; }
    .stButton button { height: 3.5em; width: 100%; font-size: 24px !important; border-radius: 12px; font-weight: bold; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .timer-warning { color: white; background-color: red; padding: 15px; border-radius: 10px; font-weight: bold; animation: blink 1s infinite; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 状态跳转函数 ---
def next_step(next_val):
    # 跳转时清理所有计时器相关的旧缓存
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
    
    if remaining <= 5:
        st.markdown(f'<p class="timer-warning">⚠️ 警告：本环节即将结束！剩余 {remaining} 秒</p>', unsafe_allow_html=True)
    
    time.sleep(1)
    st.rerun()
    return False

# --- 4. 流程控制逻辑 ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# 【阶段 1：信息登记】
if st.session_state.step == 1:
    st.header("📋 登记信息")
    sid = st.text_input("请输入被试编号:", key="s1_sid")
    age = st.selectbox("请选择学段:", ["1 (小学)", "2 (中学)"], key="s1_age")
    grp = st.selectbox("请选择分配组别:", ["1 (指导型)", "2 (支持型)"], key="s1_grp")
    
    if st.button("🚀 开始实验", key="s1_start_btn"):
        if sid:
            try:
                # 读取题库
                with open("question_bank.json", "r", encoding="utf-8") as f:
                    bank = json.load(f)
                    next_step(1)
                
                # 根据选中的学段（取第一个字符 "1" 或 "2"）去抽题
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
                    # 针对你提供的 JSON 中 "2": [] 做的容错提示
                    st.error(f"❌ 题库错误：学段 '{age}' 题目不足2道，请完善 question_bank.json。")
            except FileNotFoundError:
                st.error("❌ 找不到文件：请确认 question_bank.json 已上传到 GitHub。")
            except Exception as e:
                st.error(f"❌ 初始化失败: {e}")
        else:
            st.warning("⚠️ 请先输入被试编号。")

# 【阶段 2：前测】
elif st.session_state.step == 2:
    st.header("📝 阶段 1：前测")
    st.info(f"题目：{st.session_state.main_i['content']}")
    ans = st.text_area("请在这里输入你的回答：", height=400, key="s2_ans")
    
    if st.button("✅ 提交并进入下一步", key="s2_btn") or smart_timer(10, "t1"):
        st.session_state.data['pre_ans'] = ans
        next_step(3)

# 【阶段 3：AI 互动】
elif st.session_state.step == 3:
    st.header("🤖 阶段 2：AI 互动学习")
    st.error("❗ 时间到将自动跳转下一步。")
    st.markdown(f"### 🔍 互动题目：\n{st.session_state.main_i['content']}")
    
    # 动态生成指令
    group_type = st.session_state.data['group']
    if group_type == "指导型":
        prompt = f"针对题目《{st.session_state.main_i['content']}》直接给出标准答案。"
        sel_ins = "N/A"
    else:
        sel_ins = random.choice(st.session_state.main_i['instructions'])
        prompt = f"针对题目《{st.session_state.main_i['content']}》，请基于线索『{sel_ins}』启发我思考。"
    
    st.session_state.data['used_ins'] = sel_ins
    st.write("请复制下方指令前往豆包：")
    st.code(prompt)
    st.link_button("👉 点击打开【豆包 AI】", "https://www.doubao.com")
    
    if st.button("✅ 互动结束，进入下一阶段", key="s3_btn") or smart_timer(10, "t2"):
        next_step(4)

# 【阶段 4：后测】
elif st.session_state.step == 4:
    st.header("🏁 阶段 3：后测")
    st.info(f"题目：{st.session_state.main_i['content']}")
    ans = st.text_area("请再次回答：", height=400, key="s4_ans")
    
    if st.button("✅ 提交并进入下一步", key="s4_btn") or smart_timer(10, "t3"):
        st.session_state.data['post_ans'] = ans
        next_step(5)

# 【阶段 5：迁移测试】
elif st.session_state.step == 5:
    st.header("🚀 阶段 4：迁移测试")
    st.success("🌟 挑战：利用刚才学到的思考方式，独立解决新题。")
    st.info(f"题目：{st.session_state.trans_i['content']}")
    ans = st.text_area("请在此输入回答：", height=400, key="s5_ans")
    
    if st.button("✅ 完成实验", key="s5_btn") or smart_timer(10, "t4"):
        st.session_state.data['trans_ans'] = ans
        next_step(6)

# 【阶段 6：回收代码】
elif st.session_state.step == 6:
    st.balloons()
    st.success("🎉 全部实验已结束！")
    final_data = json.dumps(st.session_state.data, ensure_ascii=False)
    b64 = base64.b64encode(final_data.encode()).decode()
    st.write("请复制下方代码发还给主试：")
    st.code(b64)