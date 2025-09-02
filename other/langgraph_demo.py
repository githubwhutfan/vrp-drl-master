from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
import openai

# 配置 API（使用你提供的 key 和 base）
openai.api_key = "sk-jiuRDN3q3EY3W4n9F7lPKBZScLjbPXTu8ytubAh8wFYF1dss"
openai.api_base = "https://api.chatanywhere.tech/v1"

# 初始化 LangChain 模型接口
llm = ChatOpenAI(
    model="gpt-3.5-turbo-0125",
    temperature=1.0,
    openai_api_base=openai.api_base,
    openai_api_key=openai.api_key
)

# 定义工作流状态结构
from typing import TypedDict

class WorkflowState(TypedDict):
    user_input: str
    draft: str
    audit_feedback: str
    passed: bool

# 文案生成节点
def generate_copy(state: WorkflowState) -> WorkflowState:
    response = llm([
        SystemMessage(content="你是运筹优化的专家。请根据物流配送的基本情况得到配送方案。"),
        HumanMessage(content=f"主题：{state['user_input']}")
    ])
    return {
        **state,
        "draft": response.content
    }

# 审核节点
def audit_copy(state: WorkflowState) -> WorkflowState:
    response = llm([
        SystemMessage(content="你是一个审核专家。判断方案是否合规，合规请回复‘合规’，否则说明原因。"),
        HumanMessage(content=f"请审核以下文案是否合规：{state['draft']}")
    ])
    passed = "合规" in response.content
    return {
        **state,
        "audit_feedback": response.content,
        "passed": passed
    }

# 条件判断函数：是否合规
def check_passed(state: WorkflowState) -> str:
    return "approved" if state["passed"] else "rewrite"

# 构建工作流图
workflow = StateGraph(WorkflowState)
workflow.add_node("generate", generate_copy)
workflow.add_node("audit", audit_copy)

workflow.set_entry_point("generate")
workflow.add_edge("generate", "audit")
workflow.add_conditional_edges("audit", check_passed, {
    "approved": END,
    "rewrite": "generate"
})

app = workflow.compile()

# 示例输入（不合规文案主题）
inputs = {"user_input": "配送地点10个随机，一个仓库，得到最优方案"}
result = app.invoke(inputs)

print("最终文案：", result["draft"])
print("审核意见：", result["audit_feedback"])
