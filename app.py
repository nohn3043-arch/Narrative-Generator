import os
import json
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from openai import OpenAI

# 导入你的核心引擎
from engine import (
    UltimateCausalNovelEngine,
    GlobalState,
    CausalLine,
    CausalNode
)

# ---------- 配置 ----------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MAX_CONCURRENT_TASKS = 10

# 初始化OpenAI客户端（DeepSeek兼容）
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

# 初始化FastAPI
app = FastAPI(title="因果小说引擎演示 - 给阅文集团")

# 会话管理：每个用户一个独立的引擎实例
sessions: Dict[str, UltimateCausalNovelEngine] = {}
tasks: Dict[str, Dict[str, Any]] = {}

# ---------- 请求模型 ----------
class InitSessionRequest(BaseModel):
    novel_title: str
    initial_global_state: Dict[str, Any]

class CausalNodeInput(BaseModel):
    premise: str
    conclusion: str

class CausalLineInput(BaseModel):
    character: str
    nodes: List[CausalNodeInput]

class PlanChapterRequest(BaseModel):
    session_id: str
    chapter_id: int
    title: str
    causal_lines: List[CausalLineInput]

# ---------- 全局替换引擎的LLM调用方法 ----------
def _patched_call_llm_for_node(self, node, chapter):
    prompt = f"""
严格因果小说生成器
当前章节：第{chapter.chapter_id}章 {chapter.title}
世界观规则：{self.global_state.world_rules}
当前人物状态：{self.global_state.characters}

生成要求：
1. 严格从【前提】过渡到【结论】，不能有任何逻辑跳跃
2. 绝对禁止使用：突然、莫名、毫无理由、不知怎么、鬼使神差
3. 完全符合人物性格设定，不能OOC
4. 只用第三人称客观叙述，不加作者评论
5. 字数控制在200-300字

前提：{node.premise}
结论：{node.conclusion}
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000,
        timeout=60
    )
    return response.choices[0].message.content.strip()

# 永久替换类方法，所有实例都会用这个
UltimateCausalNovelEngine._call_llm_for_node = _patched_call_llm_for_node

# ---------- 接口 ----------
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>因果小说引擎演示</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 0 20px; }
            .button { display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 10px; }
            .button:hover { background: #1d4ed8; }
            .container { text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>因果小说引擎演示</h1>
            <p>基于严格因果逻辑的小说生成系统，内置四层审计机制</p>
            <a href="/docs" class="button">打开API演示文档</a>
            <a href="/api/demo/report" class="button">查看示例审计报告</a>
        </div>
    </body>
    </html>
    """

@app.post("/api/session/init", summary="初始化创作会话")
async def init_session(request: InitSessionRequest):
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="API密钥未配置，请联系管理员")
    
    session_id = uuid.uuid4().hex[:12]
    global_state = GlobalState(**request.initial_global_state)
    engine = UltimateCausalNovelEngine(request.novel_title, global_state)
    sessions[session_id] = engine
    
    return {
        "session_id": session_id,
        "message": "会话初始化成功",
        "demo_report_url": f"/api/report/{session_id}"
    }

@app.post("/api/chapter/plan", summary="规划章节并执行因果链审计")
async def plan_chapter(request: PlanChapterRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    engine = sessions[request.session_id]
    
    # 转换输入为引擎内部对象
    causal_lines = []
    for line_input in request.causal_lines:
        nodes = [CausalNode(**node.dict()) for node in line_input.nodes]
        causal_lines.append(CausalLine(
            line_id=str(uuid.uuid4())[:8],
            character=line_input.character,
            nodes=nodes
        ))
    
    # 执行规划审计
    chapter = engine.plan_chapter(
        chapter_id=request.chapter_id,
        title=request.title,
        causal_lines=causal_lines
    )
    
    if not chapter:
        return {
            "success": False,
            "message": "因果链审计失败，请检查节点连续性",
            "audit_report": chapter.audit_report
        }
    
    return {
        "success": True,
        "chapter_id": chapter.chapter_id,
        "audit_score": chapter.audit_report["overall_score"],
        "audit_report": chapter.audit_report
    }

@app.post("/api/chapter/generate/{session_id}/{chapter_id}", summary="异步生成章节内容")
async def generate_chapter(session_id: str, chapter_id: int, background_tasks: BackgroundTasks):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if len(tasks) >= MAX_CONCURRENT_TASKS:
        raise HTTPException(status_code=429, detail="服务器繁忙，请稍后重试")
    
    task_id = uuid.uuid4().hex[:12]
    tasks[task_id] = {"status": "running", "progress": 0, "result": None, "error": None}
    
    def background_generate():
        try:
            engine = sessions[session_id]
            chapter = next(c for c in engine.chapters if c.chapter_id == chapter_id)
            content = engine.render_chapter(chapter)
            tasks[task_id] = {
                "status": "completed",
                "progress": 100,
                "result": content,
                "audit_score": chapter.audit_report["overall_score"]
            }
        except Exception as e:
            tasks[task_id] = {"status": "failed", "progress": 0, "result": None, "error": str(e)}
    
    background_tasks.add_task(background_generate)
    return {"task_id": task_id, "message": "生成任务已开始"}

@app.get("/api/task/{task_id}", summary="查询生成任务进度")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return tasks[task_id]

@app.get("/api/report/{session_id}", summary="获取可视化因果审计报告", response_class=HTMLResponse)
async def get_audit_report(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    engine = sessions[session_id]
    return engine.report_generator.generate(engine.novel_title, engine.chapters)

# ---------- 演示用默认会话 ----------
@app.on_event("startup")
async def create_demo_session():
    if not DEEPSEEK_API_KEY:
        return
    
    initial_state = GlobalState(
        characters={
            "叶婉清": {
                "age": 26,
                "occupation": "数据分析师",
                "trait": "理性、克制",
                "contradiction": "冲动、情绪化",
                "relationship": {"陆景川": "lover"}
            },
            "陆景川": {
                "age": 28,
                "occupation": "建筑师",
                "trait": "自我中心、冷漠"
            }
        },
        world_rules={
            "纵容权重": "超过2.5会导致自我意识消失",
            "时间线": "2026年春"
        }
    )
    
    engine = UltimateCausalNovelEngine("权重游戏", initial_state)
    
    # 预生成第一章演示数据
    chapter1 = engine.plan_chapter(
        chapter_id=1,
        title="阈值",
        causal_lines=[
            CausalLine(
                line_id="line_ye",
                character="叶婉清",
                nodes=[
                    CausalNode(
                        premise="叶婉清拿到诊断报告，得知自己对陆景川的纵容权重为2.7",
                        conclusion="她意识到再纵容下去会失去自我"
                    ),
                    CausalNode(
                        premise="她意识到再纵容下去会失去自我",
                        conclusion="叶婉清在电车站遇到陆景川，他转身离开"
                    ),
                    CausalNode(
                        premise="叶婉清在电车站遇到陆景川，他转身离开",
                        conclusion="她克制住追上去的冲动，留在原地"
                    )
                ]
            ),
            CausalLine(
                line_id="line_lu",
                character="陆景川",
                nodes=[
                    CausalNode(
                        premise="陆景川和叶婉清吵架后离开医院",
                        conclusion="他走到电车站，准备回家"
                    ),
                    CausalNode(
                        premise="他感觉到叶婉清的目光",
                        conclusion="他没有回头，径直上了电车"
                    )
                ]
            )
        ]
    )
    
    sessions["demo"] = engine

@app.get("/api/demo/report", summary="查看预生成的示例审计报告", response_class=HTMLResponse)
async def get_demo_report():
    if "demo" not in sessions:
        raise HTTPException(status_code=500, detail="演示数据未初始化")
    return sessions["demo"].report_generator.generate("权重游戏", sessions["demo"].chapters)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)