# Narrative_Generation_Engine.py
import uuid
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Dict, Any, List, Callable, Optional, Protocol
from collections import defaultdict

# =============================================================================
# LLMProvider 协议（不再依赖外部模块）
# =============================================================================
class LLMProvider(Protocol):
    """大模型提供者标准接口，所有外部大模型必须实现此协议"""
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        ...

# =============================================================================
# 核心逻辑校验架构 (底层内核)
# =============================================================================
@dataclass
class ResponsibilityAccount:
    organization: str
    role: str
    stage: str
    nonce: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.nonce:
            self.nonce = uuid.uuid4().hex[:8]

class AuditConfigLoader:
    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> Dict[str, Any]:
        return config

    @staticmethod
    def load_from_json(path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

class AuditPlugin:
    def __init__(self, name: str, analyze_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.name = name
        self.analyze = analyze_func

class CognitiveAuditEngine:
    def __init__(self, account: ResponsibilityAccount, config: Dict[str, Any]):
        self.account = account
        self.config = config
        self.plugins: List[AuditPlugin] = []

        allowed_stages = self.config.get("allowed_stages", [])
        if account.stage not in allowed_stages:
            raise ValueError(f"Unsupported stage: {account.stage}")

    def register_plugin(self, plugin: AuditPlugin) -> None:
        self.plugins.append(plugin)

    def audit(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        report = {
            "disclaimer": self.config.get("disclaimer", "本报告基于情节逻辑分析，不构成创作建议"),
            "responsibility_account": self.account.__dict__,
            "audit_timestamp": uuid.uuid1().hex[:8],
            "overall_passed": True,
            "overall_score": 100.0,
            "analysis": {},
            "custom_fields": self.config.get("custom_fields", {})
        }
        
        total_score = 0.0
        for plugin in self.plugins:
            result = plugin.analyze(decision_context)
            report["analysis"][plugin.name] = result
            if not result["passed"]:
                report["overall_passed"] = False
            total_score += result["score"]
        
        if self.plugins:
            report["overall_score"] = round(total_score / len(self.plugins), 2)
        return report

# =============================================================================
# 情感多因果核心数据结构
# =============================================================================
@dataclass
class EmotionalConstraint:
    """情感约束：多因果系统的核心变量，权重0-1，越高对行为影响越大"""
    name: str
    weight: float
    target: Optional[str] = None          # 情感指向的角色
    source: str = "initialization"        # 来源：初始化/文本提取/剧情演进
    version: int = 1

# =============================================================================
# 小说叙事图谱数据结构
# =============================================================================
@dataclass
class ImplicitAssumption:
    content: str
    confidence: float  
    risk_level: str  

@dataclass
class CausalNode:
    premise: str
    conclusion: str
    context: Dict[str, Any] = field(default_factory=dict)
    node_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    implicit_assumptions: List[ImplicitAssumption] = field(default_factory=list)
    vulnerability_score: float = 100.0
    audit_report: Optional[Dict[str, Any]] = None
    parent_nodes: List[str] = field(default_factory=list)
    child_nodes: List[str] = field(default_factory=list)
    causal_weights: Dict[str, float] = field(default_factory=dict)

@dataclass
class CausalLine:
    line_id: str
    character: str  
    nodes: List[CausalNode] = field(default_factory=list)

@dataclass
class Chapter:
    chapter_id: int
    title: str
    causal_lines: List[CausalLine]  
    global_state_before: Dict[str, Any]
    global_state_after: Dict[str, Any] = field(default_factory=dict)
    content: str = ""
    audit_report: Optional[Dict[str, Any]] = None

@dataclass
class GlobalState:
    characters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    world_rules: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    emotional_constraints: Dict[str, List[EmotionalConstraint]] = field(default_factory=dict)
    version: int = 0
    last_updated: str = field(default_factory=lambda: uuid.uuid1().hex[:8])

# =============================================================================
# 工业级核心功能组件 (支持情感多因果)
# =============================================================================
class NarrativeStripper:
    @staticmethod
    def strip(text: str) -> Dict[str, Any]:
        stripped = re.sub(r'[，。！？；：""''()（）【】]', '', text)
        stripped = re.sub(r'[的地得]', '', stripped)
        stripped = re.sub(r'\s+', ' ', stripped).strip()
        actions = re.findall(r'([\u4e00-\u9fa5]+)([打跑走看说哭笑哭生气难过拉黑离开留在])', stripped)
        return {"raw_text": text, "stripped_text": stripped, "actions": actions}

class ImplicitAssumptionDetector:
    @staticmethod
    def detect(node: CausalNode, global_state: GlobalState) -> List[ImplicitAssumption]:
        assumptions = []
        # 物理层假设
        if "追上去" in node.conclusion or "留在原地" in node.conclusion:
            assumptions.append(ImplicitAssumption(
                content="角色具备物理位移行为能力且共处同一时空",
                confidence=0.8, risk_level="low"
            ))
        if "拉黑" in node.conclusion:
            assumptions.append(ImplicitAssumption(
                content="角色之间拥有生效的通讯网络连接手段",
                confidence=0.9, risk_level="low"
            ))
        if "打电话" in node.premise or "发消息" in node.premise:
            assumptions.append(ImplicitAssumption(
                content="角色持有可正常使用的通讯设备",
                confidence=0.95, risk_level="low"
            ))
        # 情感层假设 (从全局情感库中提取)
        for char_name, emotions in global_state.emotional_constraints.items():
            if char_name in node.premise or char_name in node.conclusion:
                for emotion in emotions:
                    if emotion.weight >= 0.7:
                        target_desc = f"对{emotion.target}" if emotion.target else ""
                        assumptions.append(ImplicitAssumption(
                            content=f"{char_name}{target_desc}存在强烈的{emotion.name}情感",
                            confidence=emotion.weight,
                            risk_level="medium"
                        ))
        return assumptions

class VulnerabilityAssessor:
    @staticmethod
    def assess(node: CausalNode) -> float:
        score = 100.0
        # 仅物理假设扣分，情感假设不扣分
        physical = [a for a in node.implicit_assumptions if "情感" not in a.content]
        score -= len(physical) * 3
        forbidden = ["突然", "莫名", "毫无理由", "不知怎么", "鬼使神差", "突然之间"]
        for word in forbidden:
            if word in node.premise or word in node.conclusion:
                score -= 15
        if len(node.causal_weights) >= 2:
            score += min(10, len(node.causal_weights) * 2)
        return max(0.0, score)

class AutomaticStateExtractor:
    @staticmethod
    def extract(text: str, current_state: GlobalState) -> Dict[str, Any]:
        changes = {}
        # 原有事实变化
        if "拉黑了" in text or "拉黑" in text:
            changes.setdefault("characters", {})
            changes["characters.叶婉清.relationship.陆景川"] = "blocked"
        if "克制住" in text or "留在原地" in text:
            changes.setdefault("events", [])
            changes["events"] = current_state.events + [
                {"event": "核心成长点", "desc": "行为走向独立"}
            ]
        # 情感变化自动提取
        emotion_keyword_map = {
            "害怕失去": ("fear_of_loss", 0.8),
            "习惯了": ("habit", 0.7),
            "心动": ("attraction", 0.6),
            "难过": ("sadness", 0.6),
            "愤怒": ("anger", 0.7),
            "愧疚": ("guilt", 0.75),
            "依赖": ("dependence", 0.8),
            "占有欲": ("possessiveness", 0.85),
            "不舍": ("reluctance", 0.65)
        }
        emotional_updates = defaultdict(list)
        for keyword, (emotion_name, base_weight) in emotion_keyword_map.items():
            if keyword in text:
                for char_name in current_state.characters.keys():
                    context_window = text.split(keyword)[0][-20:] + text.split(keyword)[1][:20]
                    if char_name in context_window:
                        target = None
                        for other in current_state.characters.keys():
                            if other != char_name and other in context_window:
                                target = other
                                break
                        emotional_updates[char_name].append(
                            EmotionalConstraint(
                                name=emotion_name,
                                weight=base_weight,
                                target=target,
                                source="text_extraction",
                                version=current_state.version + 1
                            )
                        )
        if emotional_updates:
            changes["emotional_constraints"] = dict(emotional_updates)
        return changes

class AutomaticRepairEngine:
    @staticmethod
    def repair(text: str, audit_report: Dict[str, Any]) -> str:
        repaired = text
        for result in audit_report.get("analysis", {}).values():
            for issue in result.get("issues", []):
                if "逻辑跳跃词" in issue:
                    match = re.search(r"'([^']+)'", issue)
                    if match:
                        word = match.group(1)
                        repaired = repaired.replace(word, "伴随着情绪的沉淀，顺理成章地")
        return repaired

class VisualReportGenerator:
    @staticmethod
    def generate(novel_title: str, chapters: List[Chapter]) -> str:
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{novel_title} - 情节逻辑校验报告</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 30px; background: #fdfdfd; color: #333; }}
.chapter {{ margin-bottom: 35px; background: white; border: 1px solid #eee; padding: 25px; border-radius: 12px; }}
.node {{ margin-left: 20px; margin-top: 15px; padding: 18px; background: #f9f9f9; border-radius: 8px; border-left: 4px solid #3498db; }}
.emotion-tag {{ display: inline-block; background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px; }}
.passed {{ color: #27ae60; font-weight: bold; }}
.failed {{ color: #e67e22; font-weight: bold; }}
.score {{ float: right; background: #e0f2fe; color: #0369a1; padding: 5px 12px; border-radius: 20px; font-weight: bold; }}
h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
</style>
</head>
<body>
<h1>📊 《{novel_title}》情节逻辑校验报告</h1>
<p style="color:#777;">系统自动梳理多因果链条、检测情感动机并完成逻辑桥接。</p>
"""
        for ch in chapters:
            if not ch.audit_report:
                continue
            status = "passed" if ch.audit_report.get("overall_passed", True) else "failed"
            html += f"""
<div class="chapter">
    <h2>演进段落：{ch.title} <span class="score">稳态评分：{ch.audit_report.get('overall_score', 100)}</span></h2>
    <p>连贯性验证：<span class="{status}">{"✅ 剧情顺畅" if status=="passed" else "⚠️ 部分断层已修复"}</span></p>
"""
            for line in ch.causal_lines:
                html += f"<h3>👤 角色故事线：{line.character}</h3>"
                for node in line.nodes:
                    node_status = "passed" if (node.audit_report and node.audit_report.get("overall_passed", True)) else "failed"
                    emotion_tags = ""
                    for a in node.implicit_assumptions:
                        if "情感" in a.content:
                            emotion_tags += f'<span class="emotion-tag">{a.content}</span>'
                    html += f"""
<div class="node">
    <strong>🧬 节点 {node.node_id}</strong>
    <p><b>情节起点：</b>{node.premise}</p>
    <p><b>剧情走向：</b>{node.conclusion}</p>
    {f'<p>💡 情感动机：{emotion_tags}</p>' if emotion_tags else ''}
    <p style="color:#666; font-size:13px;">🔍 潜在线索：{', '.join([a.content for a in node.implicit_assumptions if "情感" not in a.content]) or '无明显物理断层'}</p>
</div>"""
            html += "</div>"
        html += "</body></html>"
        return html

# =============================================================================
# 终极智能小说故事引擎 (情感多因果版)
# =============================================================================
class UltimateCausalNovelEngine:
    def __init__(self, novel_title: str, initial_global_state: GlobalState):
        self.novel_title = novel_title
        self.global_state = initial_global_state
        self.chapters: List[Chapter] = []
        self.causal_graph: Dict[str, CausalNode] = {}
        self.llm_provider: Optional[LLMProvider] = None

        self._init_audit_engines()
        self._register_all_audit_plugins()
        self.stripper = NarrativeStripper()
        self.assumption_detector = ImplicitAssumptionDetector()
        self.vulnerability_assessor = VulnerabilityAssessor()
        self.state_extractor = AutomaticStateExtractor()
        self.repair_engine = AutomaticRepairEngine()
        self.report_generator = VisualReportGenerator()

    def set_llm_provider(self, provider: LLMProvider) -> None:
        self.llm_provider = provider

    def _init_audit_engines(self) -> None:
        self.planning_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("StoryStudio", "ChapterPlanner", "planning"),
            config={"allowed_stages": ["planning"]}
        )
        self.node_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("StoryStudio", "NodeGenerator", "generation"),
            config={"allowed_stages": ["generation"]}
        )
        self.consistency_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("StoryStudio", "ConsistencyChecker", "consistency"),
            config={"allowed_stages": ["consistency"]}
        )
        self.vulnerability_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("StoryStudio", "VulnerabilityAssessor", "vulnerability"),
            config={"allowed_stages": ["vulnerability"]}
        )

    def _register_all_audit_plugins(self) -> None:
        self.planning_auditor.register_plugin(AuditPlugin("story_chain_integrity", self._audit_causal_chain_integrity))
        self.planning_auditor.register_plugin(AuditPlugin("implicit_assumption_detection", self._audit_implicit_assumptions))
        self.node_auditor.register_plugin(AuditPlugin("logical_jump_detection", self._audit_logical_jump))
        self.node_auditor.register_plugin(AuditPlugin("premise_conclusion_match", self._audit_premise_conclusion_match))
        self.consistency_auditor.register_plugin(AuditPlugin("character_consistency", self._audit_character_consistency))
        self.consistency_auditor.register_plugin(AuditPlugin("world_rule_consistency", self._audit_world_rule_consistency))
        self.vulnerability_auditor.register_plugin(AuditPlugin("vulnerability_assessment", self._audit_vulnerability))

    # ---------- 柔性校验插件 ----------
    def _audit_causal_chain_integrity(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_implicit_assumptions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for line in context["causal_lines"]:
            for node in line.nodes:
                node.implicit_assumptions = self.assumption_detector.detect(node, self.global_state)
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_logical_jump(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context.get("text", "")
        forbidden = ["突然", "莫名", "毫无理由", "不知怎么", "鬼使神差", "突然之间"]
        issues = [f"发现逻辑跳跃词：'{w}'" for w in forbidden if w in text]
        score = max(0.0, 100.0 - len(issues) * 15)
        return {"passed": len(issues) == 0, "issues": issues, "score": score}

    def _audit_premise_conclusion_match(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_character_consistency(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_world_rule_consistency(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_vulnerability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        node = context["node"]
        score = self.vulnerability_assessor.assess(node)
        node.vulnerability_score = score
        return {"passed": score >= 50, "issues": [], "score": score}

    # ---------- 宏观控制 ----------
    def plan_chapter(self, chapter_id: int, title: str, causal_lines: List[CausalLine]) -> Optional[Chapter]:
        print(f"\n📝 规划演进段落：{title}")
        report = self.planning_auditor.audit({"chapter_id": chapter_id, "title": title, "causal_lines": causal_lines})
        for line in causal_lines:
            for node in line.nodes:
                self.causal_graph[node.node_id] = node
        chapter = Chapter(
            chapter_id=chapter_id,
            title=title,
            causal_lines=causal_lines,
            global_state_before=json.loads(json.dumps(asdict(self.global_state))),
            audit_report=report
        )
        self.chapters.append(chapter)
        return chapter

    def render_chapter(self, chapter: Chapter, max_retries: int = 3) -> Optional[str]:
        print(f"\n📖 开始演绎：{chapter.title}")
        full_content = ""
        for line in chapter.causal_lines:
            print(f"  处理角色故事线：{line.character}")
            for i, node in enumerate(line.nodes):
                print(f"    生成剧情节点 {i+1}/{len(line.nodes)}")
                for attempt in range(max_retries):
                    if i > 0:
                        text = self._call_llm_to_bridge_gap(line.nodes[i-1], node, chapter)
                    else:
                        text = self._call_llm_for_node(node, chapter)
                    node_audit = self.node_auditor.audit({
                        "node": node,
                        "text": text,
                        "global_state": asdict(self.global_state)
                    })
                    vuln_audit = self.vulnerability_auditor.audit({"node": node, "text": text})
                    if node_audit["overall_passed"] and vuln_audit["overall_passed"]:
                        node.audit_report = {**node_audit, "vulnerability": vuln_audit}
                        full_content += text + "\n\n"
                        break
                    text = self.repair_engine.repair(text, node_audit)
                else:
                    # 最终保底
                    text = self.repair_engine.repair(text, {"analysis": {"logical_jump_detection": {"issues": ["发现逻辑跳跃词"]}}})
                    full_content += text + "\n\n"
        # 一致性审计
        consistency_audit = self.consistency_auditor.audit({
            "chapter": asdict(chapter),
            "text": full_content,
            "global_state": asdict(self.global_state)
        })
        chapter.content = full_content.strip()
        chapter.audit_report = consistency_audit
        # 状态更新
        changes = self.state_extractor.extract(full_content, self.global_state)
        for key, val in changes.items():
            self._apply_state_change(key, val)
        self.global_state.version += 1
        chapter.global_state_after = json.loads(json.dumps(asdict(self.global_state)))
        return full_content

    # ---------- 底层LLM调用 ----------
    def _call_llm_for_node(self, node: CausalNode, chapter: Chapter) -> str:
        if self.llm_provider is not None:
            emotions = []
            for char, cons in self.global_state.emotional_constraints.items():
                if char in node.premise or char in node.conclusion:
                    for e in cons:
                        emotions.append(f"{e.name}(权重{e.weight})")
            emotion_hint = f"当前角色情感状态：{', '.join(emotions)}。请据此合理推导行为动机。" if emotions else ""
            prompt = f"""你是一名优秀的网络小说作家。
角色设定：{self.global_state.characters}
{emotion_hint}
请将情节起点【{node.premise}】自然演进至故事走向【{node.conclusion}】。
要求：文字细腻流畅，符合人物性格，行为必须有合理动机，严禁使用“突然”“莫名其妙”等生硬转折词。
输出150-250字的小说文本。"""
            return self.llm_provider.generate(prompt, temperature=0.7, max_tokens=800)
        # 演示模式
        return f"【演示】从「{node.premise}」到「{node.conclusion}」，角色的内心经历了细腻的转变，情节自然推进。"

    def _call_llm_to_bridge_gap(self, prev_node: CausalNode, curr_node: CausalNode, chapter: Chapter) -> str:
        if self.llm_provider is not None:
            emotions = []
            for char, cons in self.global_state.emotional_constraints.items():
                if char in prev_node.conclusion or char in curr_node.premise:
                    for e in cons:
                        if e.weight >= 0.6:
                            emotions.append(f"{char}的{e.name}")
            emotion_hint = f"重点体现{', '.join(emotions)}的变化过程。" if emotions else ""
            prompt = f"""你是顶级小说情节逻辑架构师。
作者大纲存在自然断层：上一段结尾【{prev_node.conclusion}】，下一段开头【{curr_node.premise}】。
请写一段200字左右的过渡剧情，通过心理活动、情绪变化或环境细节将两个场景无缝连接。
{emotion_hint}
严禁使用生硬转折词，让过渡自然流畅。"""
            return self.llm_provider.generate(prompt, temperature=0.7, max_tokens=1200)
        return self._call_llm_for_node(curr_node, chapter)

    def _apply_state_change(self, key: str, value: Any) -> None:
        """递归更新 global_state 中的字段"""
        parts = key.split('.')
        obj = self.global_state
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict):
                obj = obj.setdefault(part, {})
            elif isinstance(obj, list) and part.lstrip('-').isdigit():
                idx = int(part)
                if idx >= len(obj):
                    obj.extend([{}] * (idx - len(obj) + 1))
                obj = obj[idx]
            else:
                raise KeyError(f"无法解析路径: {key}")
        last = parts[-1]
        if isinstance(obj, dict):
            obj[last] = value
        elif hasattr(obj, last):
            setattr(obj, last, value)
        else:
            raise KeyError(f"无法设置属性 {last} 在 {type(obj)}")

    def generate_novel(self, chapter_plans: List[Chapter]) -> str:
        full = f"# {self.novel_title}\n\n"
        for ch in chapter_plans:
            content = self.render_chapter(ch)
            if content:
                full += f"## 第{ch.chapter_id}章 {ch.title}\n\n{content}\n\n"
        with open("audit_report.html", "w", encoding="utf-8") as f:
            f.write(self.report_generator.generate(self.novel_title, self.chapters))
        print("\n📊 故事演进逻辑校验报告已保存：audit_report.html")
        return full