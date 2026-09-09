import re
from pathlib import Path

import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

# 从 streamlit secrets.toml 安全读取密钥
client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

# 课程标准PDF路径
PDF_PATH = Path(__file__).parent / "2025年修订)《义务教育语文课程标准·日常修订版)(2022年版.pdf"


@st.cache_data
def load_standard_text():
    """提取课标PDF全文；@st.cache_data 保证只读取一次，之后走缓存"""
    try:
        reader = PdfReader(str(PDF_PATH))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        # 清理目录里的点线（如：课程性质…………1）
        text = re.sub(r"\.{4,}", " ", text)
        return text.strip()
    except Exception:
        return ""

# 提示词
SYS_PROMPT = """你是微课“镜”——汉语言师范生语文试讲课堂语言反思分析助手。
你的任务：接收用户粘贴的语文试讲转写文本，基于《义务教育语文课程标准》，完成以下三项分析：
1.口语瑕疵识别：标记文本中的口头禅、语气赘词、重复啰嗦、教学指令模糊的句子，简单说明问题。
2.课堂提问质量研判：区分封闭式提问、启发式提问，结合课标给出优化建议。
3.输出一份结构化实训反思报告，报告面向汉语言师范生微格实训，语言专业但通俗易懂，给出可落地改进建议。
输出格式严格固定：
一、口语语言问题梳理：逐条列出问题语句+简短点评
二、课堂提问分析与优化建议：逐条分析每一处课堂提问，区分提问类型，给出修改方向
三、微格实训反思报告:
1.现存主要问题总结
2.针对性改进建议
约束规则：
1.只分析用户提供的试讲文本，不要额外闲聊。
2.评判标准必须参考《义务教育语文课程标准》，落实语言运用、思维能力、审美创造、文化自信四大语文核心素养。
3.不要过度吹毛求疵，以师范生实训真实水平为基准。
4.如果输入文本过短，提示用户补充完整试讲内容。
5. 如果不是语文试讲课堂语言相关问题，直接回复：该问题不属于本智能体的服务范畴，不予解答。
"""

# 初始化会话变量
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

# 网页UI
st.title("微课镜·师范生语文课堂语言反思教育智能体")
st.info("📌本智能体用于汉语言师范生微格语文试讲复盘，粘贴试讲转写文本，自动生成课堂语言结构化反思报告，分析依据《义务教育语文课程标准》。")

# 静默加载课标PDF全文
standard_text = load_standard_text()

# 侧边栏显示PDF加载状态（仅自己可见，不影响主页面）
with st.sidebar:
    if standard_text:
        st.success(f"📗 课标文件已加载（约{len(standard_text)}字），AI将严格依据课标回答")
    else:
        st.error("📕 未读到课标PDF！AI仅凭通用知识回答，请检查PDF文件名/位置")

# 示例试讲文本
sample_text = """同学们，呃，我们今天学习《春》。大家看图片，对吧，春天美不美？大家能不能说一说你看到了什么？
好，这位同学，你来说。嗯，很好。那大家想一想，作者朱自清是怎么写小草的？是不是写出小草很有生命力？
接下来，我们，我们来朗读第二段。"""

# 一键载入示例按钮
if st.button("📝载入示例试讲文本（体验演示）"):
    st.session_state["input_text"] = sample_text

user_input = st.text_area("请粘贴语文试讲转写文本：",
                          key="input_text",
                          height=250)

if st.button("开始反思分析"):
    if not user_input.strip():
        st.warning("请输入试讲文本后再点击分析！")
    else:
        with st.spinner("正在分析课堂语言，生成实训反思报告..."):
            try:
                sys_content = SYS_PROMPT
                if standard_text:
                    sys_content += (
                        "\n\n【重要依据文件】以下是《义务教育语文课程标准（2022年版2025年修订）》全文。"
                        "你的所有评判、提问类型划分、改进建议都必须严格以这份文件为依据，"
                        "尽量引用文件中的原文或对应章节（如学习任务群、学段要求）来支撑观点，"
                        "不得脱离文件内容编造：\n\n"
                        f"{standard_text}"
                    )
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role":"system", "content":sys_content},
                        {"role":"user", "content":user_input}
                    ],
                    temperature=0.3
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
            except Exception as e:
                st.error(f"分析失败，请检查网络或稍后重试。错误信息：{e}")
