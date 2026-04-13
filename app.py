import streamlit as st
import time
import random

# ==========================================
# 1. 实验语料库
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

# ================= 配置与初始化 =================
st.set_page_config(page_title="AI学习干预实验平台", layout="wide")

# 隐藏网页默认的菜单栏和页脚，防止被试误触
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 实验时间设置 (单位：秒，方便调试时修改)
PRE_TEST_TIME = 240     # 4分钟
INTERACT_TIME = 300     # 5分钟
POST_TEST_TIME = 240    # 4分钟
TRANSFER_TIME = 240     # 4分钟

# 初始化 session_state
if 'stage' not in st.session_state:
    st.session_state.stage = 1
    st.session_state.ai_type = ""

# ================= 通用倒计时函数 =================
def run_timer(stage_key, duration):
    """
    在左侧边栏运行倒计时，最后30秒显示静态红色警告框。
    到点后返回 True 触发跳转。
    """
    if f"{stage_key}_end" not in st.session_state:
        st.session_state[f"{stage_key}_end"] = time.time() + duration
    
    end_time = st.session_state[f"{stage_key}_end"]
    
    # 在左侧栏创建提示语和计时器占位符
    st.sidebar.markdown("### ⚠️ 注意事项")
    st.sidebar.info("请将自己的答案写在答题纸上，记得注意左侧剩余时间，倒计时结束将自动跳转。")
    timer_ph = st.sidebar.empty()
    
    while True:
        now = time.time()
        remaining = int(end_time - now)
        
        if remaining <= 0:
            timer_ph.empty()
            return True # 时间到，允许跳转
            
        mins, secs = divmod(remaining, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        # 倒计时最后 30s 呈现静态红色框（无闪烁）
        if remaining <= 30:
            timer_ph.markdown(
                f"""<div style='border: 2px solid #D32F2F; background-color: #FFEBEE; color: #D32F2F; 
                padding: 15px; border-radius: 8px; text-align: center; font-size: 32px; font-weight: bold;'>
                ⏳ {time_str}
                </div>""", unsafe_allow_html=True)
        else:
            timer_ph.markdown(
                f"""<div style='border: 2px solid #E0E0E0; background-color: #F5F5F5; color: #333; 
                padding: 15px; border-radius: 8px; text-align: center; font-size: 32px; font-weight: bold;'>
                ⏳ {time_str}
                </div>""", unsafe_allow_html=True)
        
        time.sleep(1) # 暂停一秒

# ================= 实验流程控制 =================

# 页面一：信息填写页面
if st.session_state.stage == 1:
    st.title("AI学习干预实验平台")
    st.markdown("### 请在答题卡上填写自己的姓名、性别、学号、班级，并根据答题卡上已选的AI类型选择下方的AI类型，完成后点击“开始”进入实验。")
    
    ai_choice = st.radio("选择AI类型：", ("指导型AI", "支持型AI"), index=None)
    
    st.write("---")
    # 全局唯一的主动跳转按钮
    if st.button("开始"):
        if ai_choice:
            st.session_state.ai_type = ai_choice
            st.session_state.stage = 2
            st.rerun()
        else:
            st.error("请先选择AI类型！")

# 页面二：前测阶段 (4分钟)
elif st.session_state.stage == 2:
    st.title("第一阶段：前测")
    st.write("---")
    st.markdown(f"**{st.session_state.q_A}**")
    
    # 渲染内容后，启动阻塞式倒计时
    if run_timer("stage2", PRE_TEST_TIME):
        st.session_state.stage = 3
        st.rerun()

# 页面三：AI互动环节 (5分钟)
elif st.session_state.stage == 3:
    st.title("第二阶段：AI 互动环节")
    st.write("---")
    st.markdown(f"**当前题目：**\n{st.session_state.q_A}")
    st.write("---")
    
    st.markdown("### 请复制以下指导语，并点击下方按钮前往豆包 AI 提问：")
    
    # 根据 AI 类型生成不同的复制文本
    if st.session_state.ai_type == "指导型AI":
        prompt_text = f"针对题目：{st.session_state.q_A}，直接给出答案。"
    else:
        prompt_text = f"针对题目：{st.session_state.q_A}，请根据以下线索 [请在此替换你的线索] ，启发我思考并引导我找出答案，并给出新的三个引导性问题启发我继续思考。"
    
    # 提供一键复制框
    st.code(prompt_text, language="text")
    
    # 跳转链接（在新标签页打开，不影响当前计时器）
    st.markdown(
        """
        <a href="https://www.doubao.com" target="_blank" style="display: inline-block; padding: 10px 20px; 
        background-color: #4CAF50; color: white; text-align: center; text-decoration: none; 
        font-size: 16px; border-radius: 5px; font-weight: bold;">
        👉 点击此处跳转至豆包AI网页
        </a>
        <br><br>
        """, 
        unsafe_allow_html=True
    )
    
    # 启动倒计时
    if run_timer("stage3", INTERACT_TIME):
        st.session_state.stage = 4
        st.rerun()

# 页面四：后测阶段 (4分钟)
elif st.session_state.stage == 4:
    st.title("第三阶段：后测")
    st.write("---")
    st.markdown("### 请整理并作答以下题目：")
    st.markdown(f"**{st.session_state.q_A}**")
    
    if run_timer("stage4", POST_TEST_TIME):
        st.session_state.stage = 5
        st.rerun()

# 页面五：迁移阶段 (4分钟)
elif st.session_state.stage == 5:
    st.title("第四阶段：迁移测试")
    st.write("---")
    st.markdown("### 请自由作答以下题目：")
    # 这里使用的是 ABBA 中的 B 题
    st.markdown(f"**{st.session_state.q_B}**")
    
    if run_timer("stage5", TRANSFER_TIME):
        st.session_state.stage = 6
        st.rerun()

# 页面六：问卷阶段
elif st.session_state.stage == 6:
    st.title("实验结束")
    st.write("---")
    st.success("请翻转答题纸至背面完成反馈问卷，谢谢你的认真参与，恭喜你已完成本次实验！")
    
    # 防止被试意外回退，侧边栏清空
    st.sidebar.empty()