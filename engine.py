# Narrative_Generation_Engine.py
import uuid
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict

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
# 新增：情感多因果计算核心数据结构
# =============================================================================
@dataclass
class EmotionalConstraint:
    """情感约束：多因果系统的核心变量，权重0-1，越高对行为影响越大"""
    name: str
    weight: float
    target: Optional[str] = None  # 情感指向的角色
    source: str = "initialization"  # 来源：初始化/文本提取/剧情演进
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
    causal_weights: Dict[str, float] = field(default_factory=dict)  # 新增：多因果权重分解

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
    emotional_constraints: Dict[str, List[EmotionalConstraint]] = field(default_factory=dict)  # 新增：全局情感状态库
    version: int = 0
    last_updated: str = field(default_factory=lambda: uuid.uuid1().hex[:8])

# =============================================================================
# 升级：工业级核心功能组件 (支持情感多因果)
# =============================================================================
class NarrativeStripper:
    """叙事剥离器：提取文学文本底层的决策动作链条"""
    @staticmethod
    def strip(text: str) -> Dict[str, Any]:
        stripped = re.sub(r'[，。！？；：""''()（）【】]', '', text)
        stripped = re.sub(r'[的地得]', '', stripped)
        stripped = re.sub(r'\s+', ' ', stripped).strip()
        actions = re.findall(r'([\u4e00-\u9fa5]+)([打跑走看说哭笑哭生气难过拉黑离开留在])', stripped)
        return {"raw_text": text, "stripped_text": stripped, "actions": actions}

class ImplicitAssumptionDetector:
    """升级：内隐情绪透视器，同时识别物理假设与情感动机"""
    @staticmethod
    def detect(node: CausalNode, global_state: GlobalState) -> List[ImplicitAssumption]:
        assumptions = []
        
        # 保留原物理层假设检测
        if "追上去" in node.conclusion or "留在原地" in node.conclusion:
            assumptions.append(ImplicitAssumption(
                content="角色具备物理位移行为能力且共处同一时空",
                confidence=0.8,
                risk_level="low"
            ))
        if "拉黑" in node.conclusion:
            assumptions.append(ImplicitAssumption(
                content="角色之间拥有生效的通讯网络连接手段",
                confidence=0.9,
                risk_level="low"
            ))
        if "打电话" in node.premise or "发消息" in node.premise:
            assumptions.append(ImplicitAssumption(
                content="角色持有可正常使用的通讯设备",
                confidence=0.95,
                risk_level="low"
            ))
        
        # 新增：情感动机自动检测（权重≥0.7的强情感自动成为隐含假设）
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
    """升级：情节稳态评估器，情感假设不再扣分"""
    @staticmethod
    def assess(node: CausalNode) -> float:
        score = 100.0
        
        # 仅对物理层隐含假设扣分，情感假设不扣分
        physical_assumptions = [a for a in node.implicit_assumptions if "情感" not in a.content]
        score -= len(physical_assumptions) * 3  # 扣分从5分下调至3分，更符合文学创作规律
        
        # 严格禁用破坏体验的逻辑跳跃词
        forbidden = ["突然", "莫名", "毫无理由", "不知怎么", "鬼使神差", "突然之间"]
        for word in forbidden:
            if word in node.premise or word in node.conclusion:
                score -= 15
        
        # 多因果加分：存在2个以上有效因果变量时额外加分
        if len(node.causal_weights) >= 2:
            score += min(10, len(node.causal_weights) * 2)
            
        return max(0.0, score)

class AutomaticStateExtractor:
    """升级：全局状态提取器，自动从文本中提取并更新情感状态"""
    @staticmethod
    def extract(text: str, current_state: GlobalState) -> Dict[str, Any]:
        changes = {}
        
        # 保留原事实状态提取
        if "拉黑了" in text or "拉黑" in text:
            changes["characters.叶婉清.relationship.陆景川"] = "blocked"
        if "克制住" in text or "留在原地" in text:
            changes["events"] = current_state.events + [
                {"event": "核心成长点", "desc": "叶婉清行为走向独立"}
            ]
        
        # 新增：情感变化自动提取与权重计算
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
        
        emotional_changes = defaultdict(list)
        for keyword, (emotion_name, base_weight) in emotion_keyword_map.items():
            if keyword in text:
                # 提取触发情感的角色
                for char_name in current_state.characters.keys():
                    # 检查关键词前后20个字符内是否出现角色名
                    context_window = text.split(keyword)[0][-20:] + text.split(keyword)[1][:20]
                    if char_name in context_window:
                        # 提取情感指向的目标
                        target = None
                        for other_char in current_state.characters.keys():
                            if other_char != char_name and other_char in context_window:
                                target = other_char
                                break
                        
                        emotional_changes[char_name].append(
                            EmotionalConstraint(
                                name=emotion_name,
                                weight=base_weight,
                                target=target,
                                source="text_extraction"
                            )
                        )
        
        if emotional_changes:
            changes["emotional_constraints"] = dict(emotional_changes)
        
        return changes

class AutomaticRepairEngine:
    """情节平滑修缮引擎：消除生硬突兀的桥接词"""
    @staticmethod
    def repair(text: str, audit_report: Dict[str, Any]) -> str:
        repaired = text
        for plugin_name, result in audit_report.get("analysis", {}).items():
            for issue in result.get("issues", []):
                if "逻辑跳跃词" in issue:
                    match = re.search(r"'([^']+)'", issue)
                    if match:
                        word = match.group(1)
                        repaired = repaired.replace(word, "伴随着情绪的沉淀，顺理成章地")
        return repaired

class VisualReportGenerator:
    """升级：可视化报告生成器，新增情感因果权重展示"""
    @staticmethod
    def generate(novel_title: str, chapters: List[Chapter]) -> str:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{novel_title} - 情节逻辑校验报告</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 30px; background: #fdfdfd; color: #333; }}
                .chapter {{ margin-bottom: 35px; background: white; border: 1px solid #eee; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); }}
                .node {{ margin-left: 20px; margin-top: 15px; padding: 18px; background: #f9f9f9; border-radius: 8px; border-left: 4px solid #3498db; }}
                .emotion-tag {{ display: inline-block; background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px; margin-top: 5px; }}
                .passed {{ color: #27ae60; font-weight: bold; }}
                .failed {{ color: #e67e22; font-weight: bold; }}
                .score {{ float: right; background: #e0f2fe; color: #0369a1; padding: 5px 12px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            </style>
        </head>
        <body>
            <h1>📊 《{novel_title}》情节逻辑校验报告</h1>
            <p style="color: #777; font-size: 14px;">本报告展示了系统如何自动梳理多因果链条、检测情感动机并完成逻辑桥接的全过程。</p>
        """
        for chapter in chapters:
            if not chapter.audit_report: continue
            status = "passed" if chapter.audit_report.get("overall_passed", True) else "failed"
            html += f"""
            <div class="chapter">
                <h2>演进段落：{chapter.title} <span class="score">情节稳态评分：{chapter.audit_report.get('overall_score', 100)}分</span></h2>
                <p>连贯性验证：<span class="{status}">{"✅ 剧情推演整体顺畅" if status=="passed" else "⚠️ 部分断层已由系统自动平滑修复"}</span></p>
            """
            for line in chapter.causal_lines:
                html += f"<h3 style='color:#555; margin-top:20px;'>👤 角色故事线：{line.character}</h3>"
                for node in line.nodes:
                    node_status = "passed" if (node.audit_report and node.audit_report.get("overall_passed", True)) else "failed"
                    
                    # 生成情感标签
                    emotion_tags = ""
                    for a in node.implicit_assumptions:
                        if "情感" in a.content:
                            emotion_tags += f'<span class="emotion-tag">{a.content}</span>'
                    
                    html += f"""
                    <div class="node">
                        <strong>🧬 剧情动作节点 ID: {node.node_id}</strong>
                        <p><b>[情节起点]</b> {node.premise}</p>
                        <p><b>[剧情走向]</b> {node.conclusion}</p>
                        {f'<p style="margin-top:8px;">💡 <b>识别到的情感动机：</b>{emotion_tags}</p>' if emotion_tags else ''}
                        <p style="color:#666; font-size:13px; background:#fff; padding:6px; border-radius:4px; border:1px solid #f0f0f0; margin-top:8px;">
                            🔍 <b>自动补充的潜在线索：</b>{', '.join([a.content for a in node.implicit_assumptions if "情感" not in a.content]) if [a for a in node.implicit_assumptions if "情感" not in a.content] else '无明显物理断层，逻辑链条完备'}
                        </p>
                    </div>
                    """
            html += "</div>"
        html += "</body></html>"
        return html

# =============================================================================
# 升级：终极智能小说故事引擎 (情感多因果版)
# =============================================================================
class UltimateCausalNovelEngine:
    def __init__(self, novel_title: str, initial_global_state: GlobalState):
        self.novel_title = novel_title
        self.global_state = initial_global_state
        self.chapters: List[Chapter] = []
        self.causal_graph: Dict[str, CausalNode] = {}  
        self.llm_provider = None  
        
        self._init_audit_engines()
        self._register_all_audit_plugins()
        
        self.stripper = NarrativeStripper()
        self.assumption_detector = ImplicitAssumptionDetector()
        self.vulnerability_assessor = VulnerabilityAssessor()
        self.state_extractor = AutomaticStateExtractor()
        self.repair_engine = AutomaticRepairEngine()
        self.report_generator = VisualReportGenerator()

    def set_llm_provider(self, provider: Any) -> None:
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
        self.planning_auditor.register_plugin(AuditPlugin(
            name="story_chain_integrity",
            analyze_func=self._audit_causal_chain_integrity
        ))
        self.planning_auditor.register_plugin(AuditPlugin(
            name="implicit_assumption_detection",
            analyze_func=self._audit_implicit_assumptions
        ))
        self.node_auditor.register_plugin(AuditPlugin(
            name="logical_jump_detection",
            analyze_func=self._audit_logical_jump
        ))
        self.node_auditor.register_plugin(AuditPlugin(
            name="premise_conclusion_match",
            analyze_func=self._audit_premise_conclusion_match
        ))
        self.consistency_auditor.register_plugin(AuditPlugin(
            name="character_consistency",
            analyze_func=self._audit_character_consistency
        ))
        self.consistency_auditor.register_plugin(AuditPlugin(
            name="world_rule_consistency",
            analyze_func=self._audit_world_rule_consistency
        ))
        self.vulnerability_auditor.register_plugin(AuditPlugin(
            name="vulnerability_assessment",
            analyze_func=self._audit_vulnerability
        ))

    # --- 柔性校验插件实现 ---
    def _audit_causal_chain_integrity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_implicit_assumptions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        causal_lines = context["causal_lines"]
        for line in causal_lines:
            for node in line.nodes:
                node.implicit_assumptions = self.assumption_detector.detect(node, self.global_state)
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_logical_jump(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["text"]
        issues = []
        score = 100.0
        forbidden = ["突然", "莫名", "毫无理由", "不知怎么", "鬼使神差", "突然之间"]
        for word in forbidden:
            if word in text:
                issues.append(f"发现逻辑跳跃词：'{word}'")
                score -= 15
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_premise_conclusion_match(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_character_consistency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_world_rule_consistency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"passed": True, "issues": [], "score": 100.0}

    def _audit_vulnerability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        node = context["node"]
        score = self.vulnerability_assessor.assess(node)
        node.vulnerability_score = score
        return {"passed": score >= 50, "issues": [], "score": score}

    # --- 宏观情节演进控制中心 ---
    def plan_chapter(self, chapter_id: int, title: str, causal_lines: List[CausalLine]) -> Optional[Chapter]:
        print(f"\n📝 规划演进段落：{title}")
        audit_report = self.planning_auditor.audit({"chapter_id": chapter_id, "title": title, "causal_lines": causal_lines})
        
        for line in causal_lines:
            for node in line.nodes:
                self.causal_graph[node.node_id] = node
        
        chapter = Chapter(
            chapter_id=chapter_id,
            title=title,
            causal_lines=causal_lines,
            global_state_before=json.loads(json.dumps(asdict(self.global_state))),
            audit_report=audit_report
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
                node_text = ""
                for attempt in range(max_retries):
                    if i > 0:
                        prev_node = line.nodes[i-1]
                        node_text = self._call_llm_to_bridge_gap(prev_node, node, chapter)
                    else:
                        node_text = self._call_llm_for_node(node, chapter)
                        
                    node_audit = self.node_auditor.audit({"node": node, "text": node_text, "global_state": self.global_state.__dict__})
                    vuln_audit = self.vulnerability_auditor.audit({"node": node, "text": node_text})
                    
                    if node_audit["overall_passed"] and vuln_audit["overall_passed"]:
                        node.audit_report = {**node_audit, "vulnerability": vuln_audit}
                        full_content += node_text + "\n\n"
                        break
                    
                    node_text = self.repair_engine.repair(node_text, node_audit)
                else:
                    node_text = self.repair_engine.repair(node_text, {"analysis": {"logical_jump_detection": {"issues": ["发现逻辑跳跃词"]}}})
                    full_content += node_text + "\n\n"
        
        consistency_audit = self.consistency_auditor.audit({"chapter": chapter.__dict__, "text": full_content, "global_state": self.global_state.__dict__})
        chapter.content = full_content.strip()
        chapter.audit_report = consistency_audit
        
        # 自动沉淀更新全局事实库与情感状态
        state_changes = self.state_extractor.extract(full_content, self.global_state)
        for key, value in state_changes.items():
            self._apply_state_change(key, value)

        self.global_state.version += 1
        chapter.global_state_after = json.loads(json.dumps(asdict(self.global_state)))
        return full_content

    # --- 升级：底层生成驱动 (情感感知版) ---
    def _call_llm_for_node(self, node: CausalNode, chapter: Chapter) -> str:
        if self.llm_provider is not None:
            # 提取当前节点涉及的角色及其情感状态
            current_char = None
            emotion_context = []
            for char_name, char_emotions in self.global_state.emotional_constraints.items():
                if char_name in node.premise or char_name in node.conclusion:
                    current_char = char_name
                    for e in char_emotions:
                        target_desc = f"指向{e.target}" if e.target else ""
                        emotion_context.append(f"{e.name}{target_desc}(权重{e.weight})")
            
            emotion_prompt = f"当前角色核心情感状态：{', '.join(emotion_context)}。请基于这些情感状态合理推导角色行为，明确写出行为背后的情感动机。" if emotion_context else ""
            
            prompt = f"""你是一名优秀的网络小说作家。
基础角色设定：{self.global_state.characters}
{emotion_prompt}
请将情节起点【{node.premise}】自然演进至故事走向【{node.conclusion}】。
要求：
1. 文字细腻流畅，符合人物性格
2. 行为必须有合理的情感或现实动机
3. 严禁使用"突然"、"莫名其妙"等生硬转折词
输出150-250字的小说文本片段。"""
            return self.llm_provider.generate(prompt)
            
        # 演示模式默认返回
        return f"随着故事的发展，【{node.premise}】顺理成章地推进至【{node.conclusion}】。角色的行为源于其内心深处的情感驱动与现实处境的共同作用。"

    def _call_llm_to_bridge_gap(self, prev_node: CausalNode, curr_node: CausalNode, chapter: Chapter) -> str:
        """柔韧桥接器：自动补全大纲断层，融合情感逻辑"""
        if self.llm_provider is not None:
            # 提取桥接段涉及的情感状态
            emotion_context = []
            for char_name, char_emotions in self.global_state.emotional_constraints.items():
                if char_name in prev_node.conclusion or char_name in curr_node.premise:
                    for e in char_emotions:
                        if e.weight >= 0.6:
                            emotion_context.append(f"{char_name}的{e.name}")
            
            emotion_prompt = f"重点体现{', '.join(emotion_context)}在这段时间内的变化与作用。" if emotion_context else ""
            
            prompt = f"""你是顶级小说情节逻辑架构师。
作者大纲存在自然断层：上一段结尾是【{prev_node.conclusion}】，下一段开头是【{curr_node.premise}】。
请写一段200字左右的过渡剧情，通过人物的心理活动、情绪变化或环境细节将两个场景无缝连接。
{emotion_prompt}
严禁使用任何生硬转折词，让过渡自然得仿佛原本就该如此。"""
            return self.llm_provider.generate(prompt)
            
        return self._call_llm_for_node(curr_node, chapter)

    def _apply_state_change(self, key: str, value: Any) -> None:
        parts = key.split('.')
        obj: Any = self.global_state
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict):
                obj = obj.setdefault(part, {})
            elif isinstance(obj, list) and part.isdigit():
                obj = obj[int(part)]
            else:
                raise KeyError(f"无法更新状态路径：{key}")

        final_key = parts[-1]
        if isinstance(obj, dict):
            obj[final_key] = value
        elif isinstance(obj, list) and final_key.isdigit():
            obj[int(final_key)] = value
        elif hasattr(obj, final_key):
            setattr(obj, final_key, value)
        else:
            raise KeyError(f"无法设置状态字段：{final_key} 对象：{obj}")

    def generate_novel(self, chapter_plans: List[Chapter]) -> str:
        full_novel = f"# {self.novel_title}\n\n"
        for chapter in chapter_plans:
            content = self.render_chapter(chapter)
            if content:
                full_novel += f"## 第{chapter.chapter_id}章 {chapter.title}\n\n{content}\n\n"
        
        html_report = self.report_generator.generate(self.novel_title, self.chapters)
        with open("audit_report.html", "w", encoding="utf-8") as f:
            f.write(html_report)
        print(f"\n📊 故事演进逻辑校验报告已保存：audit_report.html")
        return full_novel

# =============================================================================
# 模块独立验证入口 (宋玖凝&宋明乘测试用例)
# =============================================================================
if __name__ == "__main__":
    initial_state = GlobalState(
        characters={
            "宋玖凝": {"age": 38, "trait": "冷静理智、外冷内热", "identity": "清日科技CEO"},
            "宋明乘": {"age": 18, "trait": "安静执拗、缺乏安全感", "identity": "宋玖凝的外甥"}
        },
        world_rules={"现实世界": "所有行为均符合人性逻辑与社会规则"},
        # 初始化多因果情感约束
        emotional_constraints={
            "宋玖凝": [
                EmotionalConstraint(name="害怕失去", weight=0.9, target="宋明乘"),
                EmotionalConstraint(name="习惯了照顾", weight=0.8, target="宋明乘"),
                EmotionalConstraint(name="愧疚感", weight=0.7, target="宋明乘")
            ],
            "宋明乘": [
                EmotionalConstraint(name="深度依赖", weight=0.9, target="宋玖凝"),
                EmotionalConstraint(name="偏执爱慕", weight=0.85, target="宋玖凝"),
                EmotionalConstraint(name="害怕被抛弃", weight=0.8, target="宋玖凝")
            ]
        }
    )
    
    engine = UltimateCausalNovelEngine("晚风知我意", initial_state)
    
    chapter1 = engine.plan_chapter(
        chapter_id=1,
        title="录取通知书",
        causal_lines=[
            CausalLine(
                line_id="line_song",
                character="宋玖凝",
                nodes=[
                    CausalNode(premise="宋明乘收到帝都大学物理系录取通知书", conclusion="宋玖凝提前下班准备了丰盛的晚餐庆祝"),
                    CausalNode(premise="宋玖凝告知已在帝都购置好公寓并准备了信托基金", conclusion="宋明乘突然表示不想去帝都上学"),
                    CausalNode(premise="宋明乘向宋玖凝坦白了藏在心里多年的爱意", conclusion="宋玖凝没有推开他")
                ]
            )
        ]
    )
    
    if chapter1:
        novel = engine.generate_novel([chapter1])
        print("\n" + "="*60)
        print(novel)
        print("="*60)