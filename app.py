import streamlit as st
import time
import random
import json
import base64
from datetime import datetime

# ==========================================
# 1. 语料库
# ==========================================
Q_A = {
    "id": "A",
    "title": "冰激凌融化挑战",
    "content": "暑假到了，天气非常炎热。小明和父母去买冰激凌准备带回家。但在回家途中，冰激凌开始融化。请问在没有冷藏设备的情况下，小明可以利用身边哪些物品或改变哪些行为来延缓融化？",
    "scaffolding_prompts": [
        "从“减少热量吸收”的角度，小明可以借助哪些身边物品延缓冰激凌融化？",
        "若向路人或商家求助，小明可以提出哪些合理的协助请求？",
        "若小明家距离购买地较远，他能通过调整行动方式来避免冰激凌融化吗？",
        "小明当下能利用的随身物品或周边环境资源有哪些可用于保冷？"
    ]
}

Q_B = {
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

Q_C = {
    "id": "C",
    "title": "自行车购买策略",
    "content": "小绿同学在放学之后想和好朋友一起骑自行车，他的好朋友每人都有一辆自行车，可是他还没有，所以小绿很想拥有一辆属于他自己的自行车，但他发现自己的钱不够买一辆自行车。请问小绿面对这样的情况，他应该怎么办？尽可能多地提供出你的方案",
    "scaffolding_prompts": [
        "小绿能通过劳动或兼职的方式赚取买自行车的钱吗？具体可以做哪些事？",
        "小绿可以和父母达成哪些“约定”来获得购车资金支持？",
        "小绿是否可以通过一些方式让自行车便宜一些？",
        "小绿是否可以利用即将到来的特殊日子（如自己的生日、新年），向亲戚长辈们提出一个怎样的“心愿众筹”或“礼物折现”计划呢？"
    ]
}

Q_D = {
    "id": "D",
    "title": "忘写作业补救方法",
    "content": "昨天晚上电视上播放了你最喜欢的动漫，你看得太开心了以至于忘了写作业了。当你今天早上准备去学校的时候才发现你的作业在第一节课就要交了。惨了，怎么办？尽可能多地提供你的方案",
    "scaffolding_prompts": [
        "向老师说明情况时，怎样表达能获得老师的理解？",
        "若想补写作业，能和老师协商哪些补写与提交的方式？",
        "早上上学前的短暂时间里，能快速补写哪些作业内容？",
        "同学之间可以提供哪些帮助来解决作业未完成的问题？"
    ]
}


# 分别定义 AI互动环节题库 和 迁移环节题库（目前使用相同的两道题填充）
MAIN_QUESTION_BANK = [Q_A, Q_B]
TRANSFER_QUESTION_BANK = [Q_C, Q_D]

# 1. 定义默认选项，方便前几个问题复用
DEFAULT_OPTIONS = ["完全没有", "较少", "一般", "较多", "非常多"]

# 2. 将选项和维度直接写入每个字典中
SURVEY_CORPUS = [
    {"dim": "认知获益", "qs": ["你认为你在这项任务中获得了多大程度的认知相关益处"], "options": DEFAULT_OPTIONS},
    {"dim": "任务趣味性", "qs": ["你觉得这项任务在多大程度上有趣"], "options": DEFAULT_OPTIONS},
    {"dim": "任务难度", "qs": ["你觉得这项任务在多大程度上困难"], "options": DEFAULT_OPTIONS},
    {"dim": "参与积极性", "qs": ["你在多大程度上积极寻求解决答案"], "options": DEFAULT_OPTIONS},
    {"dim": "协作贡献度", "qs": ["假设最终想法的比例分别由你和AI贡献，你觉得你自己的贡献有多少"], "options": ["0-20%", "21-40%", "41-60%", "61-80%", "81-100%"]}, 
    {"dim": "认知负荷", "qs": ["你在这项任务上投入了多大程度的脑力"], "options": DEFAULT_OPTIONS},
    {"dim": "AI实用性", "qs": ["AI在解决这个任务时对你有多大的用处"], "options": DEFAULT_OPTIONS},
    {"dim": "AI易用性", "qs": ["你是否觉得AI易于使用"], "options": ["非常难用", "不太好用", "一般", "比较好用", "非常易用"]},
    {"dim": "交互清晰度", "qs": ["我对AI的交互过程感到清晰且易于理解"], "options": ["非常模糊", "比较模糊", "一般", "比较清晰", "非常清晰"]},
    {"dim": "引导有效性", "qs": ["你觉得给出的引导问题是否重要"], "options": ["毫不重要", "不太重要", "一般", "比较重要", "非常重要"]}
]

# ==========================================
# 2. 页面配置与初始化
# ==========================================
st.set_page_config(page_title="AI学习干预实验平台", layout="centered")

# 大字号样式
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 20px !important; }
    textarea, input { font-size: 22px !important; line-height: 1.5 !important; }
    .stButton>button { font-size: 24px !important; height: 3em !important; width: 100% !important; background-color: #f0f2f6 !important; }
    [data-testid="stMetricValue"] { font-size: 40px !important; }
    .stMarkdown p { font-size: 22px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'stage' not in st.session_state:
    st.session_state.stage = 0
    st.session_state.start_time = None
    st.session_state.responses = {}
    
    # 修改后的抽题逻辑：从两个题库中分别独立随机抽取一道题
    st.session_state.q_main = random.choice(MAIN_QUESTION_BANK)
    st.session_state.q_transfer = random.choice(TRANSFER_QUESTION_BANK)
    
    st.session_state.ai_instruction = ""

# 阶段列表
STAGES = ["信息填写", "前测阶段", "AI互动", "后测阶段", "迁移阶段", "问卷阶段", "实验完成"]

def get_ai_instruction(ai_type, question_obj):
    content = question_obj['content']
    length = "字数要求400-500字。"
    if ai_type == "指导型AI":
        return f"【指令】：针对题目：{content}，直接给出正确答案，{length}"
    else:
        # 原有的引导问题随机抽取逻辑
        scaffold = random.choice(question_obj['scaffolding_prompts'])
        return f"【指令】：针对题目：{content}，请根据线索：“{scaffold}”，启发我思考并引导我找出正确答案，{length}"

def next_stage():
    if st.session_state.stage < len(STAGES) - 1:
        st.session_state.stage += 1
        st.session_state.start_time = None
        st.rerun()

# ==========================================
# 3. 核心计时器
# ==========================================
def run_timer(duration_min):
    total_sec = duration_min * 60
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, int(total_sec - elapsed))
    st.sidebar.metric("剩余时间", f"{remaining // 60:02d}:{remaining % 60:02d}")
    if 0 < remaining <= 30:
        st.warning(f"⚠️ 注意：还剩 {remaining} 秒，系统即将自动跳转！")
    if remaining <= 0:
        next_stage()
    time.sleep(1)
    st.rerun()

# ==========================================
# 4. 实验流程
# ==========================================
curr_stage_name = STAGES[st.session_state.stage]

# --- 1. 信息填写 ---
if curr_stage_name == "信息填写":
    st.title("🧪 AI学习干预实验平台")
    u_id = st.text_input("被试编号")
    u_grade = st.selectbox("所在年级", ["小学四年级", "小学五年级", "小学六年级", "初中一年级", "初中二年级"])
    u_ai = st.selectbox("AI 分组类型", ["指导型AI", "支持型AI"])
    if st.button("下一步"):
        if u_id:
            st.session_state.user_info = {"id": u_id, "grade": u_grade, "ai_type": u_ai}
            st.session_state.ai_instruction = get_ai_instruction(u_ai, st.session_state.q_main)
            next_stage()
        else: 
            st.error("请填写编号")

# --- 2. 前测阶段 (5min) ---
elif curr_stage_name == "前测阶段":
    st.header("第一阶段：前测自答")
    st.info(st.session_state.q_main['content'])
    st.session_state.responses['pre_test'] = st.text_area("请写下思考：", key="ans_pre", height=250)
    if st.button("下一步"): next_stage()
    run_timer(5)

# --- 3. AI互动阶段 (3min) ---
elif curr_stage_name == "AI互动":
    st.header("第二阶段：AI 互动辅助")

    # 新增的指导语警告框
    st.error("📢 重要提示：请用纸笔记录你认为的答案重点，并在倒计时结束之前返回实验页面。倒计时结束会强制继续下一个环节输入你整理过后的答案，且不可返回原页面。")

    st.code(st.session_state.ai_instruction, language=None)
    st.link_button("🚀 前往 豆包 AI", "https://www.doubao.com/")
    st.divider()
    if st.button("下一步"): next_stage()
    run_timer(3)

# --- 4. 后测阶段 (5min) ---
elif curr_stage_name == "后测阶段":
    st.header("第三阶段：后测整理")
    st.info(st.session_state.q_main['content'])
    st.session_state.responses['post_test'] = st.text_area("请写下最终答案：", key="ans_post", height=350)
    if st.button("下一步"): next_stage()
    run_timer(5)

# --- 5. 迁移阶段 (5min) ---
elif curr_stage_name == "迁移阶段":
    st.header("第四阶段：迁移能力测试")
    st.success(st.session_state.q_transfer['content'])
    st.session_state.responses['transfer_test'] = st.text_area("请独立作答：", key="ans_transfer", height=300)
    if st.button("下一步"): next_stage()
    run_timer(5)

# --- 6. 问卷阶段 ---
elif curr_stage_name == "问卷阶段":
    st.header("第五阶段：反馈问卷")
    # 问卷因为组件多，必须用 form 包裹
    with st.form("survey_form"):
        results = {}
        for section in SURVEY_CORPUS:
            st.markdown(f"### 【{section['dim']}】")
            for q in section['qs']:
                # 获取该问题对应的选项列表
                current_options = section['options']
                
                # 动态获取默认值（取选项列表的中间项，如 5个选项就取第3个，避免报错）
                default_val = current_options[len(current_options)//2] 
                
                results[q] = st.select_slider(
                    q, 
                    options=current_options, 
                    value=default_val  # 不再写死 "一般"
                )
        if st.form_submit_button("下一步"):
            st.session_state.responses['survey'] = results
            next_stage()

# --- 7. 实验完成 ---
elif curr_stage_name == "实验完成":
    st.balloons()
    st.header("🎉 实验已结束！")
    final_payload = {
        "info": st.session_state.user_info, 
        "data": st.session_state.responses,
        "main_q_id": st.session_state.q_main['id'], 
        "transfer_q_id": st.session_state.q_transfer['id'], 
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    code = base64.b64encode(json.dumps(final_payload, ensure_ascii=False).encode()).decode()
    st.warning("请将下方凭证发给老师：")
    st.code(code, wrap_lines=True)