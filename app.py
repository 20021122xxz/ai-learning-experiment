import streamlit as st
import time
import random
import json
import base64
from datetime import datetime

# ==========================================
# 1. 语料库与逻辑配置
# ==========================================

QUESTION_BANK = [
    {
        "id": "A",
        "title": "冰激凌融化挑战",
        "content": "暑假到了，天气非常炎热。小明和父母去买冰激凌准备带回家。但在回家途中，冰激凌开始融化。请问在没有冷藏设备的情况下，小明可以利用身边哪些物品或改变哪些行为来延缓融化？",
        "scaffolding_prompts": [
            "从“减少热量吸收”的角度，小明可以借助哪些身边物品延缓冰激凌融化？",
            "若向路人或商家求助，小明可以提出哪些合理的协助请求？",
            "若小明家距离购买地较远，他能通过调整行动方式来避免冰激凌融化吗？",
            "小明当下能利用的随身物品或周边环境资源有哪些可用于保冷？"
        ]
    },
    {
        "id": "B",
        "title": "课堂干扰应对方案",
        "content": "小红邻座的小紫经常在课堂上找她说话，导致小红无法集中注意力听课。请问小红应该采取哪些沟通策略或自我调节方法，既能保证听课，又不伤害友谊？",
        "scaffolding_prompts": [
            "小红可以直接和小紫沟通解决干扰问题吗？沟通时要注意什么？",
            "若不想直接沟通，小红能向老师或同学寻求哪些帮助？",
            "小红调整自己的听课状态能减少干扰影响吗？具体可以怎么做？",
            "长期解决课堂干扰问题，小红可以和老师提出哪些合理建议？"
        ]
    }
]

SURVEY_CORPUS = [
    {"dim": "学习投入度", "qs": ["我非常努力地思考了问题的答案", "我对解决这个题目充满了动力"]},
    {"dim": "AI辅助感知", "qs": ["AI给出的内容对我很有启发", "这种互动方式帮助我理清了思路", "我喜欢这种AI交流模式"]},
    {"dim": "自我效能感", "qs": ["我觉得我有能力解决类似的问题", "在AI辅助下，我变得更有信心了"]}
]
SURVEY_OPTIONS = ["非常不同意", "不同意", "一般", "同意", "非常同意"]

# ==========================================
# 2. 核心功能函数
# ==========================================

def get_ai_instruction(ai_type, question_obj):
    content = question_obj['content']
    if ai_type == "指导型AI":
        return f"【指令】：针对题目：{content}，直接给出正确答案，字数要求400-500字。"
    else:
        scaffold = random.choice(question_obj['scaffolding_prompts'])
        return (
            f"【指令】：针对题目：{content}，"
            f"请根据以下线索：“{scaffold}”，"
            f"启发我思考并引导我找出正确答案，字数要求400-500字。"
        )

def next_stage():
    stages = ["信息填写", "前测阶段", "AI互动", "后测阶段", "迁移阶段", "问卷阶段", "实验完成"]
    curr_idx = stages.index(st.session_state.stage)
    if curr_idx < len(stages) - 1:
        st.session_state.stage = stages[curr_idx + 1]
        st.session_state.start_time = None 
        st.rerun()

def countdown_timer(duration_min):
    total_sec = duration_min * 60
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, int(total_sec - elapsed))
    
    # 侧边栏字号也会受全局CSS影响
    st.sidebar.title("⏱️ 实验计时")
    st.sidebar.metric("剩余时间", f"{remaining // 60:02d}:{remaining % 60:02d}")
    
    if 0 < remaining <= 30:
        st.warning(f"⚠️ 注意：还剩 {remaining} 秒，系统即将自动保存并跳转！")
    
    if remaining <= 0:
        st.error("时间到，系统正在强制保存并跳转...")
        time.sleep(1)
        next_stage()
    
    time.sleep(1)
    st.rerun()

# ==========================================
# 3. 初始化与样式注入
# ==========================================

st.set_page_config(page_title="AI学习干预实验平台", layout="centered")

# --- 全局字号调大样式注入 ---
st.markdown("""
    <style>
    /* 调大所有正文字体 */
    html, body, [class*="css"] {
        font-size: 20px !important;
    }
    /* 调大输入框和答题框的字体 */
    textarea, input {
        font-size: 22px !important;
        line-height: 1.5 !important;
    }
    /* 调大按钮文字 */
    .stButton>button {
        font-size: 22px !important;
        height: 3em !important;
        width: 100% !important;
    }
    /* 调大侧边栏计时器文字 */
    [data-testid="stMetricValue"] {
        font-size: 40px !important;
    }
    /* 调大 Markdown 正文 */
    .stMarkdown p {
        font-size: 22px !important;
    }
    </style>
    """, unsafe_allow_stdio=True, unsafe_allow_html=True)

if 'stage' not in st.session_state:
    st.session_state.stage = "信息填写"
    st.session_state.start_time = None
    st.session_state.responses = {}
    indices = [0, 1]
    random.shuffle(indices)
    st.session_state.q_main = QUESTION_BANK[indices[0]]
    st.session_state.q_transfer = QUESTION_BANK[indices[1]]
    st.session_state.ai_instruction = None

# ==========================================
# 4. 实验流程页面
# ==========================================

# --- 1. 信息填写 ---
if st.session_state.stage == "信息填写":
    st.title("🧪 AI学习干预实验平台")
    st.write("请填写以下信息开始实验：")
    with st.form("info_form"):
        u_id = st.text_input("被试编号")
        u_grade = st.selectbox("所在年级", ["小学四年级", "小学五年级", "小学六年级", "初中一年级", "初中二年级"])
        u_ai = st.selectbox("AI 分组类型", ["指导型AI", "支持型AI"])
        if st.form_submit_button("确认并开始实验"):
            if u_id:
                st.session_state.user_info = {"id": u_id, "grade": u_grade, "ai_type": u_ai}
                st.session_state.ai_instruction = get_ai_instruction(u_ai, st.session_state.q_main)
                next_stage()
            else:
                st.error("请输入被试编号")

# --- 2. 前测阶段 (5min) ---
elif st.session_state.stage == "前测阶段":
    st.header("第一阶段：前测自答")
    st.info(f"**题目内容：**\n\n{st.session_state.q_main['content']}")
    ans = st.text_area("请在这里写下你的初始思考：", key="ans_pre", height=250)
    st.session_state.responses['pre_test'] = ans
    if st.button("✅ 保存并进入 AI 互动阶段"):
        next_stage()
    countdown_timer(5)

# --- 3. AI互动阶段 (3min) ---
elif st.session_state.stage == "AI互动":
    st.header("第二阶段：AI 互动辅助")
    st.write("请利用 AI 辅助你深入思考。此阶段无需填写答案。")
    st.info(f"**针对题目：**\n\n{st.session_state.q_main['content']}")
    st.subheader("请点击复制下方指令并发送给 AI：")
    st.code(st.session_state.ai_instruction, language=None)
    st.link_button("🚀 前往 豆包 AI (Doubao)", "https://www.doubao.com/")
    st.divider()
    if st.button("✅ 互动已完成，进入后测阶段"):
        next_stage()
    countdown_timer(3)

# --- 4. 后测阶段 (5min) ---
elif st.session_state.stage == "后测阶段":
    st.header("第三阶段：后测整理")
    st.write("请结合刚才的互动交流，给出你的最终答案：")
    st.info(f"**题目内容：**\n\n{st.session_state.q_main['content']}")
    ans = st.text_area("请在这里写下你的最终答案：", key="ans_post", height=350)
    st.session_state.responses['post_test'] = ans
    if st.button("✅ 提交最终答案，进入迁移测试"):
        next_stage()
    countdown_timer(5)

# --- 5. 迁移阶段 (5min) ---
elif st.session_state.stage == "迁移阶段":
    st.header("第四阶段：迁移能力测试")
    st.success(f"**这是一道全新的题目：**\n\n{st.session_state.q_transfer['content']}")
    ans = st.text_area("请独立作答（不可使用 AI）：", key="ans_transfer", height=300)
    st.session_state.responses['transfer_test'] = ans
    if st.button("✅ 完成答题，进入最后问卷"):
        next_stage()
    countdown_timer(5)

# --- 6. 问卷阶段 ---
elif st.session_state.stage == "问卷阶段":
    st.header("第五阶段：实验反馈问卷")
    survey_results = {}
    # 问卷表单字号也会受 CSS 影响
    with st.form("survey_form"):
        for section in SURVEY_CORPUS:
            st.markdown(f"### 【{section['dim']}】")
            for q in section['qs']:
                survey_results[q] = st.select_slider(q, options=SURVEY_OPTIONS, value="一般")
            st.divider()
        if st.form_submit_button("提交问卷"):
            st.session_state.responses['survey'] = survey_results
            next_stage()

# --- 7. 实验完成 ---
elif st.session_state.stage == "实验完成":
    st.balloons()
    st.header("🎉 实验已结束！")
    st.write("感谢参与。你的数据已安全记录。")
    final_payload = {
        "info": st.session_state.user_info,
        "data": st.session_state.responses,
        "main_q_id": st.session_state.q_main['id'],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    secret_code = base64.b64encode(json.dumps(final_payload, ensure_ascii=False).encode()).decode()
    st.warning("请将下方【实验凭证】复制发给老师：")
    st.code(secret_code, wrap_lines=True)