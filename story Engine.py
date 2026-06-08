import uuid
import json
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable, Optional, Protocol
from collections import defaultdict

# =============================================================================
# 🎯 插件标准接口定义（支持任意大模型接入）
# =============================================================================
class LLMProvider(Protocol):
    """大模型提供者标准接口，所有外部大模型必须实现这个接口"""
    def generate(self, prompt: str, **kwargs) -> str:
        """
        标准生成接口
        Args:
            prompt: 提示词
            **kwargs: 扩展参数（temperature、max_tokens等）
        Returns:
            生成的文本内容
        """
        ...

# =============================================================================
# 核心数据结构
# =============================================================================
@dataclass
class ResponsibilityAccount:
    organization: str
    role: str
    stage: str
    nonce: str = None

    def __post_init__(self) -> None:
        if not self.nonce:
            self.nonce = uuid.uuid4().hex[:8]

@dataclass
class ImplicitAssumption:
    content: str
    confidence: float  # 0-1
    risk_level: str  # low/medium/high

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
    version: int = 0
    last_updated: str = field(default_factory=lambda: uuid.uuid1().hex[:8])

# =============================================================================
# 审计引擎核心
# =============================================================================
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
            "disclaimer": self.config.get("disclaimer", "本报告基于因果逻辑分析"),
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
# 核心组件
# =============================================================================
class NarrativeStripper:
    @staticmethod
    def strip(text: str) -> Dict[str, Any]:
        stripped = re.sub(r'[，。！？；：""''()（）【】]', '', text)
        stripped = re.sub(r'[的地得]', '', stripped)
        stripped = re.sub(r'\s+', ' ', stripped).strip()
        actions = re.findall(r'([\u4e00-\u9fa5]+)([打跑走看说哭笑哭生气难过])', stripped)
        return {"raw_text": text, "stripped_text": stripped, "actions": actions}

class ImplicitAssumptionDetector:
    @staticmethod
    def detect(node: CausalNode) -> List[ImplicitAssumption]:
        assumptions = []
        if "追上去" in node.conclusion:
            assumptions.append(ImplicitAssumption("人物有能力追上对方", 0.8, "low"))
        if "拉黑" in node.conclusion:
            assumptions.append(ImplicitAssumption("人物知道对方的联系方式", 0.9, "low"))
        return assumptions

class VulnerabilityAssessor:
    @staticmethod
    def assess(node: CausalNode) -> float:
        score = 100.0
        score -= len(node.implicit_assumptions) * 5
        forbidden = ["突然", "莫名", "毫无理由", "不知怎么", "鬼使神差"]
        for word in forbidden:
            if word in node.premise or word in node.conclusion:
                score -= 20
        return max(0.0, score)

class AutomaticStateExtractor:
    @staticmethod
    def extract(text: str, current_state: GlobalState) -> Dict[str, Any]:
        # 实际部署时可接入小型信息抽取模型
        return {}

# 🚀 革命性升级：基于 LLM 的因果反思修复引擎
class AutomaticRepairEngine:
    @staticmethod
    def repair(provider: LLMProvider, text: str, audit_report: Dict[str, Any]) -> str:
        """
        利用大模型进行上下文感知的智能因果修复
        """
        # 提取所有的不合规审计问题
        issues_summary = []
        for plugin_name, result in audit_report["analysis"].items():
            if not result["passed"] and "issues" in result:
                issues_summary.extend(result["issues"])
        
        if not issues_summary:
            return text  # 无需修复，原样返回
            
        repair_prompt = f"""
【角色说明】你是一个严谨的小说逻辑修复专家。当前有一段文本未能通过因果逻辑审计。

【原始故障文本】
{text}

【审计未通过原因（红线痛点）】
{json.dumps(issues_summary, ensure_ascii=False)}

【重写铁律】
1. 必须修正上述所有逻辑错误（如：绝对不能包含禁用词、必须平滑过渡逻辑跳跃）。
2. 严禁机械粗暴地替换词语，必须结合上下文重新润色，使表达通顺自然。
3. 保持原有的剧情走向、人物性格和文学张力。
4. 仅输出最终重写修复后的故事文本，严禁包含任何多余的解释、前言或客套话。
"""
        return provider.generate(repair_prompt).strip()

class VisualReportGenerator:
    @staticmethod
    def generate(novel_title: str, chapters: List[Chapter]) -> str:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{novel_title} - 因果审计报告</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; margin: 30px; line-height: 1.6; }}
                .header {{ text-align: center; margin-bottom: 40px; padding: 20px; background: #f8fafc; border-radius: 8px; }}
                .chapter {{ margin-bottom: 40px; border: 1px solid #e2e8f0; padding: 25px; border-radius: 8px; background: white; }}
                .node {{ margin-left: 30px; margin-bottom: 15px; padding: 15px; background: #f8fafc; border-radius: 6px; border-left: 4px solid #3b82f6; }}
                .passed {{ color: #059669; font-weight: 600; }}
                .failed {{ color: #dc2626; font-weight: 600; }}
                .score {{ float: right; padding: 4px 12px; border-radius: 4px; }}
                .score.passed {{ background: #dcfce7; }}
                .score.failed {{ background: #fee2e2; }}
                h1 {{ color: #1e293b; margin: 0; }}
                h2 {{ color: #334155; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
                h3 {{ color: #475569; margin-top: 25px; }}
                h4 {{ color: #64748b; margin: 0 0 10px 0; }}
                p {{ margin: 5px 0; color: #475569; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{novel_title}</h1>
                <p style="color: #64748b; margin: 10px 0 0 0;">双对抗因果逻辑审计报告</p>
            </div>
        """
        
        for chapter in chapters:
            status = "passed" if chapter.audit_report and chapter.audit_report.get("overall_passed", True) else "failed"
            score = chapter.audit_report.get("overall_score", 100) if chapter.audit_report else 100
            html += f"""
            <div class="chapter">
                <h2>第{chapter.chapter_id}章：{chapter.title} <span class="score {status}">得分：{score}</span></h2>
            """
            
            for line in chapter.causal_lines:
                html += f"<h3>📌 人物因果线：{line.character}</h3>"
                
                for node in line.nodes:
                    node_status = "passed" if node.vulnerability_score >= 60 else "failed"
                    assumptions_text = ', '.join([a.content for a in node.implicit_assumptions]) if node.implicit_assumptions else "无"
                    html += f"""
                    <div class="node">
                        <h4>节点 {node.node_id} <span class="score {node_status}">得分：{node.vulnerability_score}</span></h4>
                        <p><strong>前提：</strong>{node.premise}</p>
                        <p><strong>结论：</strong>{node.conclusion}</p>
                        <p><strong>内隐假设：</strong>{assumptions_text}</p>
                    </div>
                    """
            
            html += "</div>"
        
        html += "</body></html>"
        return html

# =============================================================================
# 🔌 终极因果小说引擎（完全解耦插件版）
# =============================================================================
class UltimateCausalNovelEngine:
    """
    双对抗因果逻辑小说生成引擎
    """
    
    def __init__(self, novel_title: str, initial_global_state: GlobalState):
        self.novel_title = novel_title
        self.global_state = initial_global_state
        self.chapters: List[Chapter] = []
        self.causal_graph: Dict[str, CausalNode] = {}
        self._llm_provider: Optional[LLMProvider] = None
        
        self._init_audit_engines()
        self._register_all_audit_plugins()
        
        self.stripper = NarrativeStripper()
        self.assumption_detector = ImplicitAssumptionDetector()
        self.vulnerability_assessor = VulnerabilityAssessor()
        self.state_extractor = AutomaticStateExtractor()
        self.repair_engine = AutomaticRepairEngine()
        self.report_generator = VisualReportGenerator()

    def set_llm_provider(self, provider: LLMProvider) -> None:
        """设置大模型提供者"""
        self._llm_provider = provider

    def _call_llm_for_node(self, node: CausalNode, chapter: Chapter) -> str:
        """内部LLM调用，生成初版内容"""
        if not self._llm_provider:
            raise RuntimeError("请先调用 set_llm_provider() 设置大模型提供者")
        
        prompt = f"""
【小说名称】{self.novel_title}
【当前章节】第{chapter.chapter_id}章 {chapter.title}
【世界观设定】{json.dumps(self.global_state.world_rules, ensure_ascii=False)}
【人物设定】{json.dumps(self.global_state.characters, ensure_ascii=False)}

【生成要求】
1. 严格基于给定的背景和设定展开，逻辑连贯。
2. 绝对禁止使用：突然、莫名、毫无理由、不知怎么、鬼使神差。
3. 完全符合人物性格设定，禁止OOC。
4. 只用第三人称客观叙述，不加作者评论。
5. 字数控制在适当范围，叙事紧凑。

【因果前提】{node.premise}
【因果结论】{node.conclusion}

请基于以上设定生成连贯的故事段落：
"""
        return self._llm_provider.generate(prompt).strip()

    def _init_audit_engines(self) -> None:
        self.planning_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelEngine", "ChapterPlanner", "planning"),
            config={"allowed_stages": ["planning"], "disclaimer": "章节规划因果审计"}
        )
        self.node_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelEngine", "NodeGenerator", "generation"),
            config={"allowed_stages": ["generation"], "disclaimer": "节点生成因果审计"}
        )
        self.consistency_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelEngine", "ConsistencyChecker", "consistency"),
            config={"allowed_stages": ["consistency"], "disclaimer": "跨章节一致性审计"}
        )
        self.vulnerability_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelEngine", "VulnerabilityAssessor", "vulnerability"),
            config={"allowed_stages": ["vulnerability"], "disclaimer": "逻辑脆弱性审计"}
        )

    def _register_all_audit_plugins(self) -> None:
        self.planning_auditor.register_plugin(AuditPlugin("causal_chain_integrity", self._audit_causal_chain_integrity))
        self.planning_auditor.register_plugin(AuditPlugin("implicit_assumption_detection", self._audit_implicit_assumptions))
        self.node_auditor.register_plugin(AuditPlugin("logical_jump_detection", self._audit_logical_jump))
        self.node_auditor.register_plugin(AuditPlugin("premise_conclusion_match", self._audit_premise_conclusion_match))
        self.consistency_auditor.register_plugin(AuditPlugin("character_consistency", self._audit_character_consistency))
        self.consistency_auditor.register_plugin(AuditPlugin("world_rule_consistency", self._audit_world_rule_consistency))
        self.vulnerability_auditor.register_plugin(AuditPlugin("vulnerability_assessment", self._audit_vulnerability))

    # --- 审计规则实现 ---
    def _audit_causal_chain_integrity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        causal_lines = context["causal_lines"]
        issues = []
        score = 100.0
        for line in causal_lines:
            for i in range(1, len(line.nodes)):
                prev = line.nodes[i-1]
                curr = line.nodes[i]
                if prev.conclusion[:15] not in curr.premise and curr.premise[:15] not in prev.conclusion:
                    issues.append(f"因果线[{line.character}]节点{i}与{i+1}断裂")
                    score -= 20
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_implicit_assumptions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        causal_lines = context["causal_lines"]
        issues = []
        score = 100.0
        for line in causal_lines:
            for node in line.nodes:
                assumptions = self.assumption_detector.detect(node)
                node.implicit_assumptions = assumptions
                high_risk = [a for a in assumptions if a.risk_level == "high"]
                if high_risk:
                    issues.append(f"节点[{node.node_id}]存在高风险内隐假设")
                    score -= 30 * len(high_risk)
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_logical_jump(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["text"]
        issues = []
        score = 100.0
        forbidden = ["突然", "莫名", "毫无理由", "不知怎么", "鬼使神差"]
        for word in forbidden:
            if word in text:
                issues.append(f"发现逻辑跳跃词：'{word}'")
                score -= 15
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_premise_conclusion_match(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["text"]
        node = context["node"]
        issues = []
        score = 100.0
        stripped = self.stripper.strip(text)["stripped_text"]
        if node.premise[:10] not in stripped:
            issues.append("前提未在文本中体现")
            score -= 25
        if node.conclusion[:10] not in stripped:
            issues.append("结论未在文本中体现")
            score -= 25
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_character_consistency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["text"]
        global_state = context["global_state"]
        issues = []
        score = 100.0
        for char_name, char_state in global_state.characters.items():
            if char_name in text and "contradiction" in char_state:
                if char_state["contradiction"] in text:
                    issues.append(f"人物[{char_name}]行为违背设定")
                    score -= 30
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_world_rule_consistency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["text"]
        global_state = context["global_state"]
        issues = []
        score = 100.0
        for rule_name, rule_content in global_state.world_rules.items():
            if "超过2.5会导致自我意识消失" in rule_content and "2.7" in text:
                if "自我意识消失" not in text and "失去自我" not in text:
                    issues.append(f"违背世界观规则[{rule_name}]")
                    score -= 30
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_vulnerability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        node = context["node"]
        score = self.vulnerability_assessor.assess(node)
        node.vulnerability_score = score
        issues = []
        if score < 60:
            issues.append(f"节点[{node.node_id}]逻辑脆弱性过高")
        return {"passed": score >= 60, "issues": issues, "score": score}

    # --- 核心调度 API ---
    def plan_chapter(self, chapter_id: int, title: str, causal_lines: List[CausalLine]) -> Optional[Chapter]:
        audit_report = self.planning_auditor.audit({
            "chapter_id": chapter_id,
            "title": title,
            "causal_lines": causal_lines,
            "global_state": self.global_state.__dict__
        })
        
        if not audit_report["overall_passed"]:
            return None
        
        for line in causal_lines:
            for node in line.nodes:
                self.causal_graph[node.node_id] = node
        
        chapter = Chapter(
            chapter_id=chapter_id,
            title=title,
            causal_lines=causal_lines,
            global_state_before=json.loads(json.dumps(self.global_state.__dict__)),
            audit_report=audit_report
        )
        self.chapters.append(chapter)
        return chapter

    def render_chapter(self, chapter: Chapter, max_retries: int = 3) -> Optional[str]:
        full_content = ""
        
        for line in chapter.causal_lines:
            for i, node in enumerate(line.nodes):
                for attempt in range(max_retries):
                    node_text = self._call_llm_for_node(node, chapter)
                    
                    node_audit = self.node_auditor.audit({
                        "node": node,
                        "text": node_text,
                        "global_state": self.global_state.__dict__
                    })
                    vuln_audit = self.vulnerability_auditor.audit({"node": node, "text": node_text})
                    
                    if node_audit["overall_passed"] and vuln_audit["overall_passed"]:
                        node.audit_report = {**node_audit, "vulnerability": vuln_audit}
                        full_content += node_text + "\n\n"
                        break
                    
                    # 🚀 调用基于大模型的因果修复引擎，传入 self._llm_provider
                    node_text = self.repair_engine.repair(self._llm_provider, node_text, node_audit)
                else:
                    return None
        
        consistency_audit = self.consistency_auditor.audit({
            "chapter": chapter.__dict__,
            "text": full_content,
            "global_state": self.global_state.__dict__
        })
        
        if not consistency_audit["overall_passed"]:
            return None
        
        chapter.content = full_content.strip()
        chapter.audit_report = consistency_audit
        
        state_changes = self.state_extractor.extract(full_content, self.global_state)
        for key, value in state_changes.items():
            parts = key.split('.')
            obj = self.global_state
            for part in parts[:-1]:
                obj = getattr(obj, part) if hasattr(obj, part) else obj[part]
            obj[parts[-1]] = value
        
        self.global_state.version += 1
        chapter.global_state_after = json.loads(json.dumps(self.global_state.__dict__))
        
        return full_content.strip()

    def generate_audit_report(self) -> str:
        return self.report_generator.generate(self.novel_title, self.chapters)
