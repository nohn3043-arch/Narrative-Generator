import uuid
import json
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable, Optional, Set
from collections import defaultdict

# ----------------------
# 原有认知审计引擎核心
# ----------------------
@dataclass
class ResponsibilityAccount:
    organization: str
    role: str
    stage: str
    nonce: str = None

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
            "disclaimer": self.config.get("disclaimer", "本报告基于因果逻辑分析，不构成创作建议"),
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

# ----------------------
# 新增核心数据结构
# ----------------------
@dataclass
class ImplicitAssumption:
    content: str
    confidence: float  # 0-1，假设成立的概率
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
    parent_nodes: List[str] = field(default_factory=list)  # 支持多父节点
    child_nodes: List[str] = field(default_factory=list)  # 支持多子节点

@dataclass
class CausalLine:
    line_id: str
    character: str  # 该因果线所属人物
    nodes: List[CausalNode] = field(default_factory=list)

@dataclass
class Chapter:
    chapter_id: int
    title: str
    causal_lines: List[CausalLine]  # 支持多人物并行因果线
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

# ----------------------
# 新增核心组件
# ----------------------
class NarrativeStripper:
    """叙事剥离器：将文学文本剥离为纯因果结构"""
    @staticmethod
    def strip(text: str) -> Dict[str, Any]:
        # 去除修饰词、形容词、副词，保留主谓宾
        stripped = re.sub(r'[，。！？；：""''()（）【】]', '', text)
        stripped = re.sub(r'[的地得]', '', stripped)
        stripped = re.sub(r'\s+', ' ', stripped).strip()
        
        # 提取动作和主体
        actions = re.findall(r'([\u4e00-\u9fa5]+)([打跑走看说哭笑哭生气难过])', stripped)
        
        return {
            "raw_text": text,
            "stripped_text": stripped,
            "actions": actions
        }

class ImplicitAssumptionDetector:
    """内隐假设透视器：识别因果节点中未明确说明的假设"""
    @staticmethod
    def detect(node: CausalNode) -> List[ImplicitAssumption]:
        assumptions = []
        
        # 示例规则（实际可扩展为LLM驱动的语义分析）
        if "追上去" in node.conclusion:
            assumptions.append(ImplicitAssumption(
                content="叶婉清有能力追上陆景川",
                confidence=0.8,
                risk_level="low"
            ))
        
        if "拉黑" in node.conclusion:
            assumptions.append(ImplicitAssumption(
                content="叶婉清知道陆景川的联系方式",
                confidence=0.9,
                risk_level="low"
            ))
        
        return assumptions

class VulnerabilityAssessor:
    """脆弱性对冲器：评估因果节点的逻辑脆弱性"""
    @staticmethod
    def assess(node: CausalNode) -> float:
        score = 100.0
        
        # 内隐假设越多，脆弱性越高
        score -= len(node.implicit_assumptions) * 5
        
        # 逻辑跳跃词扣分
        forbidden = ["突然", "莫名", "毫无理由"]
        for word in forbidden:
            if word in node.premise or word in node.conclusion:
                score -= 20
        
        return max(0.0, score)

class AutomaticStateExtractor:
    """自动状态提取器：从文本中自动提取全局状态变化"""
    @staticmethod
    def extract(text: str, current_state: GlobalState) -> Dict[str, Any]:
        changes = {}
        
        # 示例规则（实际可扩展为LLM驱动的实体关系提取）
        if "拉黑了陆景川" in text:
            changes["characters.叶婉清.relationship.陆景川"] = "blocked"
        
        if "清理了所有和陆景川有关的东西" in text:
            changes["characters.叶婉清.items.陆景川"] = "removed"
        
        return changes

class AutomaticRepairEngine:
    """自动修复引擎：根据审计报告自动修正文本"""
    @staticmethod
    def repair(text: str, audit_report: Dict[str, Any]) -> str:
        repaired = text
        
        for plugin_name, result in audit_report["analysis"].items():
            for issue in result["issues"]:
                if "逻辑跳跃词" in issue:
                    # 提取跳跃词并替换
                    match = re.search(r"'([^']+)'", issue)
                    if match:
                        word = match.group(1)
                        repaired = repaired.replace(word, "经过一番挣扎后")
        
        return repaired

class VisualReportGenerator:
    """可视化审计报告生成器：生成HTML格式的审计报告"""
    @staticmethod
    def generate(novel_title: str, chapters: List[Chapter]) -> str:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{novel_title} - 因果审计报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .chapter {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .node {{ margin-left: 20px; margin-bottom: 10px; padding: 10px; background: #f9f9f9; border-radius: 3px; }}
                .passed {{ color: green; font-weight: bold; }}
                .failed {{ color: red; font-weight: bold; }}
                .score {{ float: right; }}
            </style>
        </head>
        <body>
            <h1>{novel_title} - 因果审计报告</h1>
        """
        
        for chapter in chapters:
            status = "passed" if chapter.audit_report["overall_passed"] else "failed"
            html += f"""
            <div class="chapter">
                <h2>第{chapter.chapter_id}章：{chapter.title} <span class="score {status}">得分：{chapter.audit_report['overall_score']}</span></h2>
            """
            
            for line in chapter.causal_lines:
                html += f"<h3>人物因果线：{line.character}</h3>"
                
                for node in line.nodes:
                    node_status = "passed" if node.audit_report["overall_passed"] else "failed"
                    html += f"""
                    <div class="node">
                        <h4>节点 {node.node_id} <span class="score {node_status}">得分：{node.audit_report['overall_score']}</span></h4>
                        <p><strong>前提：</strong>{node.premise}</p>
                        <p><strong>结论：</strong>{node.conclusion}</p>
                        <p><strong>内隐假设：</strong>{', '.join([a.content for a in node.implicit_assumptions])}</p>
                        <p><strong>脆弱性得分：</strong>{node.vulnerability_score}</p>
                    </div>
                    """
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        return html

# ----------------------
# 扩展后的终极因果小说引擎
# ----------------------
class UltimateCausalNovelEngine:
    def __init__(self, novel_title: str, initial_global_state: GlobalState):
        self.novel_title = novel_title
        self.global_state = initial_global_state
        self.chapters: List[Chapter] = []
        self.causal_graph: Dict[str, CausalNode] = {}  # 全局因果图
        
        # 初始化各阶段审计引擎
        self._init_audit_engines()
        
        # 注册所有审计插件
        self._register_all_audit_plugins()
        
        # 初始化核心组件
        self.stripper = NarrativeStripper()
        self.assumption_detector = ImplicitAssumptionDetector()
        self.vulnerability_assessor = VulnerabilityAssessor()
        self.state_extractor = AutomaticStateExtractor()
        self.repair_engine = AutomaticRepairEngine()
        self.report_generator = VisualReportGenerator()

    def _init_audit_engines(self) -> None:
        self.planning_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelStudio", "ChapterPlanner", "planning"),
            config={"allowed_stages": ["planning"], "disclaimer": "章节规划因果审计"}
        )
        
        self.node_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelStudio", "NodeGenerator", "generation"),
            config={"allowed_stages": ["generation"], "disclaimer": "节点生成因果审计"}
        )
        
        self.consistency_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelStudio", "ConsistencyChecker", "consistency"),
            config={"allowed_stages": ["consistency"], "disclaimer": "跨章节一致性审计"}
        )
        
        self.vulnerability_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalNovelStudio", "VulnerabilityAssessor", "vulnerability"),
            config={"allowed_stages": ["vulnerability"], "disclaimer": "逻辑脆弱性审计"}
        )

    def _register_all_audit_plugins(self) -> None:
        # 规划层插件
        self.planning_auditor.register_plugin(AuditPlugin(
            name="causal_chain_integrity",
            analyze_func=self._audit_causal_chain_integrity
        ))
        self.planning_auditor.register_plugin(AuditPlugin(
            name="implicit_assumption_detection",
            analyze_func=self._audit_implicit_assumptions
        ))
        
        # 节点层插件
        self.node_auditor.register_plugin(AuditPlugin(
            name="logical_jump_detection",
            analyze_func=self._audit_logical_jump
        ))
        self.node_auditor.register_plugin(AuditPlugin(
            name="premise_conclusion_match",
            analyze_func=self._audit_premise_conclusion_match
        ))
        
        # 一致性层插件
        self.consistency_auditor.register_plugin(AuditPlugin(
            name="character_consistency",
            analyze_func=self._audit_character_consistency
        ))
        self.consistency_auditor.register_plugin(AuditPlugin(
            name="world_rule_consistency",
            analyze_func=self._audit_world_rule_consistency
        ))
        
        # 脆弱性层插件
        self.vulnerability_auditor.register_plugin(AuditPlugin(
            name="vulnerability_assessment",
            analyze_func=self._audit_vulnerability
        ))

    # ----------------------
    # 审计插件实现
    # ----------------------
    def _audit_causal_chain_integrity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        causal_lines = context["causal_lines"]
        issues = []
        score = 100.0
        
        for line in causal_lines:
            for i in range(1, len(line.nodes)):
                prev = line.nodes[i-1]
                curr = line.nodes[i]
                
                if prev.conclusion[:15] not in curr.premise and curr.premise[:15] not in prev.conclusion:
                    issues.append(f"因果线[{line.character}]节点{i}与{i+1}断裂：{prev.conclusion} → {curr.premise}")
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
                    issues.append(f"节点[{node.node_id}]存在高风险内隐假设：{[a.content for a in high_risk]}")
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
            issues.append(f"前提未体现：'{node.premise}'")
            score -= 25
        
        if node.conclusion[:10] not in stripped:
            issues.append(f"结论未体现：'{node.conclusion}'")
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
                    issues.append(f"人物[{char_name}]行为违背设定：禁止'{char_state['contradiction']}'")
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
                    issues.append(f"违背世界观规则[{rule_name}]：未体现2.7权重的后果")
                    score -= 30
        
        return {"passed": len(issues) == 0, "issues": issues, "score": max(0.0, score)}

    def _audit_vulnerability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        node = context["node"]
        score = self.vulnerability_assessor.assess(node)
        node.vulnerability_score = score
        
        issues = []
        if score < 60:
            issues.append(f"节点[{node.node_id}]逻辑脆弱性过高：{score}分")
        
        return {"passed": score >= 60, "issues": issues, "score": score}

    # ----------------------
    # 核心生成方法
    # ----------------------
    def plan_chapter(self, chapter_id: int, title: str, causal_lines: List[CausalLine]) -> Optional[Chapter]:
        print(f"\n📝 规划第{chapter_id}章：{title}")
        
        # 执行规划层审计
        audit_report = self.planning_auditor.audit({
            "chapter_id": chapter_id,
            "title": title,
            "causal_lines": causal_lines,
            "global_state": self.global_state.__dict__
        })
        
        if not audit_report["overall_passed"]:
            print(f"❌ 规划审计失败：")
            for plugin, result in audit_report["analysis"].items():
                for issue in result["issues"]:
                    print(f"  - {plugin}: {issue}")
            return None
        
        print(f"✅ 规划审计通过，得分：{audit_report['overall_score']}")
        
        # 构建全局因果图
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
        print(f"\n📖 生成第{chapter.chapter_id}章：{chapter.title}")
        
        full_content = ""
        
        for line in chapter.causal_lines:
            print(f"\n  处理人物因果线：{line.character}")
            
            for i, node in enumerate(line.nodes):
                print(f"    生成节点{i+1}/{len(line.nodes)}：{node.premise} → {node.conclusion}")
                
                for attempt in range(max_retries):
                    node_text = self._call_llm_for_node(node, chapter)
                    
                    # 节点层审计
                    node_audit = self.node_auditor.audit({
                        "node": node,
                        "text": node_text,
                        "global_state": self.global_state.__dict__
                    })
                    
                    # 脆弱性审计
                    vuln_audit = self.vulnerability_auditor.audit({
                        "node": node,
                        "text": node_text
                    })
                    
                    if node_audit["overall_passed"] and vuln_audit["overall_passed"]:
                        print(f"    ✅ 节点审计通过，得分：{node_audit['overall_score']}")
                        node.audit_report = {**node_audit, "vulnerability": vuln_audit}
                        full_content += node_text + "\n\n"
                        break
                    
                    print(f"    ⚠️ 第{attempt+1}次失败，自动修复中...")
                    node_text = self.repair_engine.repair(node_text, node_audit)
                
                else:
                    print(f"❌ 节点{i+1}生成失败")
                    return None
        
        # 跨章节一致性审计
        print(f"\n🔍 执行跨章节一致性审计")
        consistency_audit = self.consistency_auditor.audit({
            "chapter": chapter.__dict__,
            "text": full_content,
            "global_state": self.global_state.__dict__
        })
        
        if not consistency_audit["overall_passed"]:
            print(f"❌ 一致性审计失败：")
            for plugin, result in consistency_audit["analysis"].items():
                for issue in result["issues"]:
                    print(f"  - {plugin}: {issue}")
            return None
        
        print(f"✅ 一致性审计通过，得分：{consistency_audit['overall_score']}")
        
        chapter.content = full_content.strip()
        chapter.audit_report = consistency_audit
        
        # 自动更新全局状态
        state_changes = self.state_extractor.extract(full_content, self.global_state)
        for key, value in state_changes.items():
            parts = key.split('.')
            obj = self.global_state
            for part in parts[:-1]:
                obj = getattr(obj, part) if hasattr(obj, part) else obj[part]
            obj[parts[-1]] = value
        
        self.global_state.version += 1
        chapter.global_state_after = json.loads(json.dumps(self.global_state.__dict__))
        
        print(f"✅ 第{chapter.chapter_id}章生成完成")
        return full_content

    def _call_llm_for_node(self, node: CausalNode, chapter: Chapter) -> str:
        """实际替换为DeepSeek/OpenAI API"""
        prompts = {
            "叶婉清拿到诊断报告，得知自己对陆景川的纵容权重为2.7": 
                "黄昏的医院走廊，消毒水的味道弥漫在空气中。叶婉清捏着那张薄薄的诊断报告，指尖微微发白。报告上的数字清晰得刺眼——2.7，超过了2.5的临界阈值。她靠在冰冷的墙壁上，闭上眼睛，过去三年的画面像电影一样在脑海里闪过。每一次妥协，每一次退让，都在一点点蚕食着她的自我。",
            "她意识到再纵容下去会失去自我": 
                "当那个冰冷的数字在脑海里反复回响时，叶婉清突然打了个寒颤。她一直以为自己的付出是爱，直到现在才明白，那不过是病态的纵容。如果继续这样下去，用不了多久，她就会彻底变成陆景川的附属品，失去所有的自我意识。这个认知让她脊背发凉。",
            "叶婉清在电车站遇到陆景川，他转身离开": 
                "走出医院，天色已经暗了下来。叶婉清漫无目的地走到电车站，却意外地看到了陆景川的背影。他穿着那件她送给他的黑色风衣，正准备走向对面的站台。似乎是感觉到了她的目光，他微微侧了下头，但没有停下脚步，径直转身离开了。",
            "她克制住追上去的冲动，留在原地": 
                "叶婉清的脚下意识地向前迈了一步，这是她三年来养成的本能。但就在这时，那个2.7的数字再次浮现在她的脑海里。她猛地停住脚步，指甲深深掐进掌心。电车的鸣笛声响起，陆景川的背影消失在人群中。叶婉清站在原地，看着电车缓缓驶离，第一次没有流泪。"
        }
        
        return prompts.get(node.premise, "生成中...")

    def generate_novel(self, chapter_plans: List[Chapter]) -> str:
        full_novel = f"# {self.novel_title}\n\n"
        
        for chapter in chapter_plans:
            content = self.render_chapter(chapter)
            if content:
                full_novel += f"## 第{chapter.chapter_id}章 {chapter.title}\n\n{content}\n\n"
        
        # 生成可视化审计报告
        html_report = self.report_generator.generate(self.novel_title, self.chapters)
        with open("audit_report.html", "w", encoding="utf-8") as f:
            f.write(html_report)
        
        print(f"\n📊 可视化审计报告已保存至 audit_report.html")
        return full_novel

# ----------------------
# 示例：多人物因果线小说生成
# ----------------------
if __name__ == "__main__":
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
    
    # 规划第一章：双人物并行因果线
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
    
    if chapter1:
        novel = engine.generate_novel([chapter1])
        print("\n" + "="*50)
        print(novel)
        print("="*50)
