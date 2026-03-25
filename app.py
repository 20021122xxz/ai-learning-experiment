import streamlit as st
import time
import random
import json
import base64
from datetime import datetime

# --- 配置与数据准备 ---
st.set_page_config(page_title="AI学习干预实验平台", layout="centered")

# 题库
QUESTION_BANK = [
    {"id": "Q1", "content": "题目A：关于冰激凌融化的科学原理及应对方案..."},
    {"id": "Q2", "content": "题目B：关于课堂社交干扰的沟通策略分析..."}
]

# 初始化 Session State
if 'stage' not in st.session_state:
    st.session_state.stage = "信息采集"
    st.session_state.user_data = {}
    # 随机决定题目顺序 (ABBA: 前、互、后用Q_main, 迁移用Q_transfer)
    indices = [0, 1]
    random.shuffle(indices)
    st.session_state.q_main = QUESTION_BANK[indices[0]]
    st.session_state.q_transfer = QUESTION_BANK[indices[1]]
    st.session_state.responses = {}
    st.session_state.start_time = None

# --- 工具函数 ---
def next_stage():
    stages = ["信息采集", "前测阶段", "AI互动", "后测阶段", "迁移阶段", "问卷阶段", "实验完成"]
    current_idx = stages.index(st.session_state.stage)
    if current_idx < len(stages) - 1:
        st.session_state.stage = stages[current_idx + 1]
        st.session_state.start_time = time.time()
        st.rerun()

def countdown_timer(duration_min):
    """简易倒计时逻辑"""
    total_seconds = duration_min * 5
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, int(total_seconds - elapsed))
    
    # 倒计时显示
    mins, secs = divmod(remaining, 5)
    st.sidebar.metric("剩余时间", f"{mins:02d}:{secs:02d}")
    
    # 5秒预警
    if 0 < remaining <= 5:
        st.warning(f"注意：还剩 {remaining} 秒，系统即将自动跳转！")
    
    # 结束跳转
    if remaining <= 0:
        st.error("时间到！正在保存并跳转...")
        time.sleep(1)
        next_stage()
    
    # 自动刷新页面（Streamlit需要刷新才能更新显示）
    time.sleep(1)
    st.rerun()

# --- 页面逻辑 ---

# 1. 信息采集
if st.session_state.stage == "信息采集":
    st.title("🧪 AI学习干预实验平台")
    with st.form("info_form"):
        subject_id = st.text_input("被试编号")
        grade = st.selectbox("年级", ["小学四年级", "小学五年级", "小学六年级", "初中一年级", "初中二年级"])
        ai_type = st.selectbox("AI类型", ["指导型AI", "支持型AI"])
        submit = st.form_submit_button("进入实验")
        
        if submit:
            if subject_id:
                st.session_state.user_data = {"id": subject_id, "grade": grade, "ai_type": ai_type}
                next_stage()
            else:
                st.error("请输入编号")

# 2. 前测阶段 (15s)
elif st.session_state.stage == "前测阶段":
    st.header("第一阶段：前测")
    st.write(f"**请阅读以下题目并给出你的初始回答：**")
    st.info(st.session_state.q_main['content'])
    ans = st.text_area("你的答案：", key="pre_test_ans", height=200)
    st.session_state.responses['pre_test'] = ans
    countdown_timer(5)

# 3. AI互动阶段 (15s)
elif st.session_state.stage == "AI互动":
    st.header("第二阶段：AI 互动辅助")
    st.write("针对刚才的题目，请通过 AI 获取启发或答案：")
    st.info(st.session_state.q_main['content'])
    
    # 根据AI类型生成指导语
    if st.session_state.user_data['ai_type'] == "指导型AI":
        prompt_text = f"针对题目：{st.session_state.q_main['content']}，请直接给出正确答案。"
    else:
        prompt_text = f"针对题目：{st.session_state.q_main['content']}，请根据已知线索，启发我思考并引导我找出正确答案。"
    
    st.code(prompt_text, language=None)
    st.write("⬆️ 请点击右上角复制以上指令")
    
    st.link_button("前往 豆包AI 进行提问", "https://www.doubao.com/")
    
    countdown_timer(3)

# 4. 后测阶段 (15s)
elif st.session_state.stage == "后测阶段":
    st.header("第三阶段：后测整理")
    st.write("请结合刚才的互动过程，完善并提交你的最终答案：")
    st.info(st.session_state.q_main['content'])
    ans = st.text_area("最终答案：", key="post_test_ans", height=250)
    st.session_state.responses['post_test'] = ans
    countdown_timer(5)

# 5. 迁移阶段 (15s)
elif st.session_state.stage == "迁移阶段":
    st.header("第四阶段：迁移测试")
    st.write("请独立完成以下新题目：")
    st.success(st.session_state.q_transfer['content'])
    ans = st.text_area("回答：", key="transfer_ans", height=250)
    st.session_state.responses['transfer_test'] = ans
    countdown_timer(5)

# 6. 问卷阶段
elif st.session_state.stage == "问卷阶段":
    st.header("第五阶段：问卷调查")
    # 问卷语料库模拟
    survey_questions = ["你觉得AI对你有帮助吗？", "你对刚才的互动形式满意吗？", "你会推荐同学使用吗？"]
    survey_results = {}
    
    with st.form("survey_form"):
        for q in survey_questions:
            survey_results[q] = st.radio(q, ["非常不同意", "不同意", "一般", "同意", "非常同意"])
        
        if st.form_submit_button("提交实验"):
            st.session_state.responses['survey'] = survey_results
            next_stage()

# 7. 实验完成与乱码生成
elif st.session_state.stage == "实验完成":
    st.balloons()
    st.success("实验已结束，感谢您的参与！")
    
    # 汇总所有数据
    final_data = {
        "user_info": st.session_state.user_data,
        "responses": st.session_state.responses,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 生成“乱码” (Base64编码处理)
    json_str = json.dumps(final_data, ensure_ascii=False)
    secret_code = base64.b64encode(json_str.encode()).decode()
    
    st.warning("⚠️ 重要步骤：")
    st.write("请复制下方生成的【实验凭证】，并将其发送给主试：")
    st.code(secret_code, wrap_lines=True)
    st.info("主试将通过此代码恢复你的实验数据。")