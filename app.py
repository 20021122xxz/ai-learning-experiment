import streamlit as st
import random
import json
import time
import base64

# --- 页面配置 ---
st.set_page_config(page_title="AI 学习干预实验", layout="centered")

# --- 1. 加载题库 ---
@st.cache_data
def load_bank():
    try:
        with open("question_bank.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # 如果文件不存在，提供默认结构供测试
        return {"1": [{"content": "示例题目", "instructions": ["示例语料"]}], "2": []}

bank = load_bank()

# --- 2. 核心逻辑函数 ---
def generate_prompt(ai_group, task_item):
    content = task_item['content']
    if ai_group == "指导型":
        return f"你好！请针对题目《{content}》直接给出详尽标准答案。字数400-600字。", "N/A"
    else:
        sel = random.choice(task_item['instructions'])
        p = (f"你好！目前的任务是《{content}》。请作为【支持型导师】引导我思考。\n"
             f"你的回复必须包含：1. 基于线索『{sel}』的启发式提问；"
             f"2. 2-3 个可行的思考方案或实验建议。字 shorthand200-300 字。")
        return p, sel

# --- 3. 实验界面 ---
st.title("🎓 AI 学习干预实验平台")
st.write("欢迎参加本次学术实验，请按照页面提示顺序操作。")

# 初始化 Session State (用于跨页面存数据)
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.data = {}

# --- 流程控制 ---

# 步骤 1：信息采集
if st.session_state.step == 1:
    st.header("📋 第一步：基本信息")
    sid = st.text_input("请输入您的编号 (如 S01):")
    age_idx = st.selectbox("请选择您的学段:", ["1 (小学)", "2 (中学)"])
    group_idx = st.selectbox("实验组别 (由主试指定):", ["1 (指导型)", "2 (支持型)"])
    
    if st.button("进入实验"):
        if sid:
            age_key = age_idx[0]
            if len(bank[age_key]) < 2:
                st.error("题库题目不足，请联系主试。")
            else:
                # 随机抽题
                sel_items = random.sample(bank[age_key], 2)
                st.session_state.test_i = sel_items[0]
                st.session_state.task_i = sel_items[1]
                st.session_state.data['sid'] = sid
                st.session_state.data['group'] = "指导型" if "1" in group_idx else "支持型"
                st.session_state.step = 2
                st.rerun()
        else:
            st.warning("请输入编号！")

# 步骤 2：前测
elif st.session_state.step == 2:
    st.header("📝 第二步：前测练习")
    st.info(f"题目：{st.session_state.test_i['content']}")
    pre_ans = st.text_area("请写下你的解题思路或答案：", height=150)
    if st.button("提交并进入互动环节"):
        st.session_state.data['pre_ans'] = pre_ans
        st.session_state.step = 3
        st.rerun()

# 步骤 3：AI 互动
elif st.session_state.step == 3:
    st.header("🤖 第三步：AI 辅助学习")
    st.warning(f"当前学习任务：{st.session_state.task_i['content']}")
    
    # 生成 Prompt
    final_p, used_ins = generate_prompt(st.session_state.data['group'], st.session_state.task_i)
    st.session_state.data['used_instr'] = used_ins
    
    st.write("请点击下方按钮复制【导师指令】，然后前往豆包进行探讨：")
    st.code(final_p, language=None)
    
    st.link_button("👉 点击打开【豆包 AI】网页版", "https://www.doubao.com")
    
    st.write("---")
    if st.button("探讨结束，进入最后阶段"):
        st.session_state.step = 4
        st.rerun()

# 步骤 4：总结与后测
elif st.session_state.step == 4:
    st.header("🏁 第四步：总结与后测")
    summary = st.text_area("针对刚才探讨的任务题，你的最终方案是？", height=100)
    st.write("---")
    st.info(f"后测题目 (同前测)：{st.session_state.test_i['content']}")
    post_ans = st.text_area("请再次尝试回答这道题：", height=150)
    
    if st.button("完成实验"):
        st.session_state.data['summary'] = summary
        st.session_state.data['post_ans'] = post_ans
        st.session_state.step = 5
        st.rerun()

# 步骤 5：数据回收
elif st.session_state.step == 5:
    st.balloons()
    st.success("🎉 实验已完成！感谢您的参与。")
    
    # 将结果转为 JSON 字符串并编码，方便被试复制
    final_json = json.dumps(st.session_state.data, ensure_ascii=False)
    b64_data = base64.b64encode(final_json.encode()).decode()
    
    st.write("⚠️ **最后一步：** 请复制下方的数据代码发还给主试，以完成数据统计：")
    st.code(b64_data)
    if st.button("重新开始 (仅限主试调试)"):
        st.session_state.clear()
        st.rerun()