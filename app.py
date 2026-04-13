import streamlit as st
import time
import random

# ==========================================
# 1. 语料库 (保持不变)
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

MAIN_QUESTION_BANK = [Q_A, Q_B]
TRANSFER_QUESTION_BANK = [Q_C, Q_D]

# ==========================================
# 2. 页面配置与初始化
# ==========================================
st.set_page_config(page_title="AI学习干预实验平台", layout="centered")

# 全局样式控制
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 20px !important; }
    .stButton>button { font-size: 24px !important; height: 3em !important; width: 100% !important; background-color: #f0f2f6 !important; }
    [data-testid="stMetricValue"] { font-size: 40px !important; }
    .instruction-box { padding: 30px; background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 10px; font-weight: bold; margin: 20px 0; line-height: 1.8; font-size: 24px !important; }
    .warning-box { padding: 20px; background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404; font-weight: bold; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

# 初始化状态
if 'stage' not in st.session_state:
    st.session_state.stage = 0
    st.session_state.start_time = None
    st.session_state.q_main = random.choice(MAIN_QUESTION_BANK)
    st.session_state.q_transfer = random.choice(TRANSFER_QUESTION_BANK)
    st.session_state.ai_instruction = ""

# 逻辑辅助函数
def get_ai_instruction(ai_type, question_obj):
    content = question_obj['content']
    length = "字数要求400-500字。"
    if ai_type == "指导型AI":
        return f"【指令】：针对题目：{content}直接给出答案，{length}"
    else:
        scaffold = random.choice(question_obj['scaffolding_prompts'])
        return f"【指令】：针对题目：{content}请根据线索：“{scaffold}”，启发我思考并引导我找出答案，{length}并根据思考方向给出三个启发性问题引导我继续深入思考"

def next_stage():
    st.session_state.stage += 1
    st.session_state.start_time = None  # 重置计时器
    st.rerun()

# 核心计时器 (用于阶段 1-4)
def run_timer(duration_min):
    total_sec = duration_min * 60
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, int(total_sec - elapsed))
    
    st.sidebar.metric("剩余时间", f"{remaining // 60:02d}:{remaining % 60:02d}")
    
    if remaining <= 0:
        next_stage()
    
    time.sleep(1)
    st.rerun()

# ==========================================
# 3. 实验流程 (严格单分支重写)
# ==========================================

# 阶段 0: 唯一存在按钮的页面
if st.session_state.stage == 0:
    st.title("🧪 AI学习干预实验平台")
    st.markdown('<div class="instruction-box">💡 请填写基本信息并选择AI分组，点击下方的按钮开始。</div>', unsafe_allow_html=True)
    
    u_ai = st.selectbox("请选择您的 AI 分组类型", ["指导型AI", "支持型AI"])
    
    # 只要点击了开始，程序会直接 rerun 杀掉这个逻辑块，进入下一页
    if st.button("开始"): 
        st.session_state.ai_instruction = get_ai_instruction(u_ai, st.session_state.q_main)
        next_stage()

# 阶段 1: 前测 (完全无按钮代码)
elif st.session_state.stage == 1:
    st.header("第一阶段：前测自答")
    st.info(st.session_state.q_main['content'])
    st.markdown('<div class="warning-box">📝 请在答题卡上作答。倒计时结束将自动进入下一环节。</div>', unsafe_allow_html=True)
    run_timer(4)

# 阶段 2: AI 互动 (完全无按钮代码)
elif st.session_state.stage == 2:
    st.header("第二阶段：AI 互动辅助")
    st.error("📢 请复制下方指令并在AI窗口进行互动，并在倒计时结束前回到本页面。")
    st.code(st.session_state.ai_instruction, language=None)
    st.link_button("🚀 跳转至豆包 AI", "https://www.doubao.com/")
    st.markdown('<div class="warning-box">⏳ 请注意左侧时间，倒计时结束将自动跳转。</div>', unsafe_allow_html=True)
    run_timer(5)

# 阶段 3: 后测 (完全无按钮代码)
elif st.session_state.stage == 3:
    st.header("第三阶段：后测整理")
    st.info(st.session_state.q_main['content'])
    st.markdown('<div class="warning-box">📝 请在答题卡上整理最终答案。倒计时结束将自动跳转。</div>', unsafe_allow_html=True)
    run_timer(4)

# 阶段 4: 迁移测试 (完全无按钮代码)
elif st.session_state.stage == 4:
    st.header("第四阶段：迁移能力测试")
    st.success(st.session_state.q_transfer['content'])
    st.markdown('<div class="warning-box">📝 请针对新问题在答题卡上作答。倒计时结束将自动跳转。</div>', unsafe_allow_html=True)
    run_timer(4)

# 阶段 5: 问卷阶段 (实验结束)
elif st.session_state.stage == 5:
    st.balloons()
    st.header("🎉 实验已完成")
    st.markdown('''
        <div class="instruction-box" style="text-align: center; background-color: #e3f2fd; border-color: #2196f3;">
        📑 <b>最后一步：请翻转答题卡至背面完成反馈问卷</b><br><br>
        <span style="font-size: 22px; color: #28a745; font-weight: bold;">感谢参与！全部完成后，您现在可以关闭本页面。</span>
        </div>
    ''', unsafe_allow_html=True)
    st.success("流程已全部结束。")