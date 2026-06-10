import uuid
import json
import dataclasses
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable, Optional, Protocol, Set, Tuple
from collections import defaultdict

# =============================================================================
# PROTOCOLS & CONFIGURATION
# =============================================================================
class LLMProvider(Protocol):
    """大模型提供者标准接口，外壳渲染器（Scribe）的技术实现基础"""
    def generate(self, prompt: str, **kwargs) -> str:
        ...

@dataclass
class ResponsibilityAccount:
    """责任闭环锚定：确立计算内核与渲染主体的确权标签"""
    organization: str
    role: str
    stage: str
    nonce: Optional[str] = field(default_factory=lambda: uuid.uuid4().hex[:8])

# =============================================================================
# 连续相空间情感动力学组件 (Continuous Emotional Phase Space)
# ✅ 优化1：扩展情感维度（适配禁忌恋/复杂人物关系）
# ✅ 优化2：修复边界截断精度问题
# =============================================================================
@dataclass
class CharacterPhaseSpace:
    """
    角色情感动力学相空间
    通过一阶常微分方程(ODE)欧拉近似，模拟人类情感惯性、阻尼衰减与外部脉冲冲击
    """
    character_name: str
    attachment: float = 0.5  # 依恋度 [0,1]
    restraint: float = 0.5   # 克制力 [0,1]
    anxiety: float = 0.5     # 焦虑/恐惧度 [0,1]
    guilt: float = 0.0       # 愧疚/背德感 [0,1]（禁忌恋核心）
    desire: float = 0.0      # 欲望/吸引力 [0,1]（禁忌恋核心）
    resentment: float = 0.0  # 怨恨/不满 [0,1]
    damping: float = 0.15    # 情绪阻尼系数（记忆衰减率）

    def apply_event_impulse(self, impulse: Dict[str, float], dt: float = 1.0) -> Dict[str, float]:
        """
        数学算子：dE/dt = -damping * E + Impulse
        计算外部事件冲击导致的情感轨迹瞬时倾斜与漂移值
        """
        old_state = self.to_dict()
        all_fields = [f.name for f in dataclasses.fields(self) if f.name not in ["character_name", "damping"]]
        
        # 带有阻尼约束的平滑状态演化
        for field_name in all_fields:
            current_value = getattr(self, field_name)
            delta = (-self.damping * current_value + impulse.get(field_name, 0.0)) * dt
            setattr(self, field_name, current_value + delta)
        
        # 高精度边界极值硬控截断
        for field_name in all_fields:
            value = getattr(self, field_name)
            setattr(self, field_name, max(0.0, min(1.0, round(value, 6))))
        
        # 计算增量变化
        delta_report = {}
        new_state = self.to_dict()
        for k in old_state:
            delta_report[f"delta_{k}"] = round(new_state[k] - old_state[k], 6)
        
        return delta_report

    def to_dict(self) -> Dict[str, float]:
        return {
            "attachment": round(self.attachment, 4),
            "restraint": round(self.restraint, 4),
            "anxiety": round(self.anxiety, 4),
            "guilt": round(self.guilt, 4),
            "desire": round(self.desire, 4),
            "resentment": round(self.resentment, 4)
        }

# =============================================================================
# 高阶因果拓扑图谱数据结构 (Causal DAG Topology)
# ✅ 优化1：封装因果势能计算方法
# ✅ 优化2：增加节点权重与优先级字段
# =============================================================================
@dataclass
class ImplicitAssumption:
    content: str
    confidence: float
    risk_level: str

@dataclass
class CausalNode:
    node_id: str
    character: str
    premise: str
    conclusion: str
    emotional_impulse: Dict[str, float] = field(default_factory=dict)
    spatial_mutually_exclusive_tag: Optional[str] = None
    parent_nodes: List[str] = field(default_factory=list)
    child_nodes: List[str] = field(default_factory=list)
    implicit_assumptions: List[ImplicitAssumption] = field(default_factory=list)
    priority: int = 0  # 节点执行优先级
    causal_potential: float = 0.0
    audit_report: Optional[Dict[str, Any]] = None

    def calculate_causal_potential(self, registry: Dict[str, CharacterPhaseSpace]) -> float:
        """✅ 优化：节点自身计算因果势能，解耦与Broker的依赖"""
        space = registry.get(self.character)
        if not space:
            return 1.0
        
        # 精细化势能公式：不同情感维度对行为驱动力的贡献不同
        # 欲望>怨恨>焦虑>愧疚（克制力会抑制所有驱动力）
        drive = (
            space.desire * 0.8 +
            space.resentment * 0.7 +
            space.anxiety * 0.6 +
            space.guilt * 0.3  # 愧疚会阻碍行动
        )
        
        # 克制力的非线性抑制效应（克制力越高，抑制越强）
        inhibition = 1.0 - (space.restraint ** 1.5)
        base_potential = drive * inhibition + 0.5
        
        # 剧情惯性：节点深度越深，势能越高
        depth_bonus = 1.0 + len(self.parent_nodes) * 0.15
        final_potential = round(base_potential * depth_bonus, 4)
        
        self.causal_potential = final_potential
        return final_potential

@dataclass
class ChapterGraph:
    chapter_id: int
    title: str
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    content: str = ""
    audit_report: Optional[Dict[str, Any]] = None

# =============================================================================
# 全局因果状态 (Global Causal State)
# ✅ 优化1：增加动态添加角色方法，修复KeyError
# ✅ 优化2：增加状态快照与回滚机制
# =============================================================================
@dataclass
class GlobalCausalState:
    """全局世界稳态看板，完全数值化呈现，剥离文本不确定性"""
    characters_profile: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    emotional_registry: Dict[str, CharacterPhaseSpace] = field(default_factory=dict)
    world_rules: Dict[str, Any] = field(default_factory=dict)
    established_facts: Set[str] = field(default_factory=set)
    version: int = 0
    history_snapshots: List[Dict[str, Any]] = field(default_factory=list)

    def add_character(self, name: str, profile: Dict[str, Any], initial_phase: CharacterPhaseSpace) -> None:
        """动态添加角色，避免KeyError"""
        self.characters_profile[name] = profile
        self.emotional_registry[name] = initial_phase

    def save_snapshot(self) -> None:
        """保存当前状态快照，用于回滚"""
        self.history_snapshots.append(dataclasses.asdict(self))
        if len(self.history_snapshots) > 10:  # 最多保留10个快照
            self.history_snapshots.pop(0)

    def rollback(self, version: int = -1) -> bool:
        """回滚到指定版本的状态快照"""
        if not self.history_snapshots:
            return False
        
        snapshot = self.history_snapshots[version]
        self.characters_profile = snapshot["characters_profile"]
        self.emotional_registry = {
            k: CharacterPhaseSpace(**v) for k, v in snapshot["emotional_registry"].items()
        }
        self.world_rules = snapshot["world_rules"]
        self.established_facts = set(snapshot["established_facts"])
        self.version = snapshot["version"]
        return True

# =============================================================================
# 因果网拓扑冲突仲裁器 (Causal Intersection Broker)
# ✅ 优化1：使用节点自身的势能计算方法
# ✅ 优化2：增加优先级排序，支持强制指定剧情走向
# =============================================================================
class CausalIntersectionBroker:
    """
    拓扑级冲突仲裁器：穿透多平行世界线的异步擦写冲突
    当多角色在同一时空产生互斥的行为走向时，计算因果势能进行收敛剪枝
    """
    def arbitrate_and_prune(self, nodes: List[CausalNode], registry: Dict[str, CharacterPhaseSpace]) -> List[CausalNode]:
        conflict_groups = defaultdict(list)
        for n in nodes:
            n.calculate_causal_potential(registry)
            if n.spatial_mutually_exclusive_tag:
                conflict_groups[n.spatial_mutually_exclusive_tag].append(n)
        
        pruned_ids: Set[str] = set()
        for tag, group in conflict_groups.items():
            if len(group) <= 1:
                continue
            
            # 优先按用户指定的优先级排序，再按因果势能排序
            group.sort(key=lambda x: (-x.priority, -x.causal_potential))
            winner = group[0]
            
            for loser in group[1:]:
                pruned_ids.add(loser.node_id)
                print(f"✂️ 因果拓扑剪枝：时空互斥标记 [{tag}] 触发。")
                print(f"   优胜者：角色 [{winner.character}] | 优先级={winner.priority} | 势能={winner.causal_potential}")
                print(f"   剔除者：角色 [{loser.character}] | 优先级={loser.priority} | 势能={loser.causal_potential}")
        
        return [n for n in nodes if n.node_id not in pruned_ids]

# =============================================================================
# 认知审计与连续稳态校验内核 (Cognitive Audit Engine)
# ✅ 优化1：扩展审计规则，覆盖新增的情感维度
# ✅ 优化2：增加审计等级，区分警告与致命错误
# =============================================================================
class CognitiveAuditEngine:
    def __init__(self, account: ResponsibilityAccount, allowed_stages: List[str]):
        self.account = account
        self.allowed_stages = allowed_stages
        if account.stage not in allowed_stages:
            raise ValueError(f"CRITICAL: Phase identity mismatch: {account.stage}")

    def audit_phase_space_safety(self, registry: Dict[str, CharacterPhaseSpace]) -> Dict[str, Any]:
        """稳态校验：校验角色的相空间状态坐标是否逼近人设自毁崩溃极限"""
        issues = []
        warnings = []
        score = 100.0
        
        for name, space in registry.items():
            # 致命错误阈值
            if space.anxiety > 0.95:
                issues.append(f"FATAL: 角色 [{name}] 焦虑度 ({space.anxiety}) 突破极限，行为将完全失控。")
                score -= 25
            if space.desire > 0.95 and space.restraint < 0.1:
                issues.append(f"FATAL: 角色 [{name}] 欲望完全失控，将突破所有道德与理性约束。")
                score -= 25
            
            # 警告阈值
            if space.anxiety > 0.85:
                warnings.append(f"WARN: 角色 [{name}] 焦虑度 ({space.anxiety}) 逼近阈值，存在非理性行为风险。")
                score -= 10
            if space.attachment < 0.05 and space.restraint > 0.9:
                warnings.append(f"WARN: 角色 [{name}] 处于绝对情感冰封相点，深度交互逻辑脆性极高。")
                score -= 15
        
        return {
            "passed": score >= 60.0,
            "is_fatal": len(issues) > 0,
            "issues": issues,
            "warnings": warnings,
            "score": max(0.0, score)
        }

    def audit_rule_violation(self, nodes: List[CausalNode], state: GlobalCausalState) -> Dict[str, Any]:
        """校验因果图谱推演结论是否击穿物理/设定等底层世界规则"""
        issues = []
        warnings = []
        score = 100.0
        
        for n in nodes:
            # 示例规则：纵容度阈值校验
            if "纵容权重为2.7" in n.premise and state.world_rules.get("纵容阈值上限", 2.5) < 2.7:
                space = state.emotional_registry.get(n.character)
                if space and space.restraint < 0.6:
                    issues.append(f"FATAL: 因果节点 [{n.node_id}] 逻辑断裂：纵容已打破系统阈值，但克制力未完成觉醒响应。")
                    score -= 30
        
        return {
            "passed": len(issues) == 0,
            "is_fatal": len(issues) > 0,
            "issues": issues,
            "warnings": warnings,
            "score": max(0.0, score)
        }

# =============================================================================
# 外壳序列化叙事渲染器 (The Stylistic Scribe)
# ✅ 优化1：接入DeepSeek-v4-flash官方接口
# ✅ 优化2：增强渲染约束，进一步限制LLM加戏
# =============================================================================
class DeepSeekProvider(LLMProvider):
    """✅ 新增：DeepSeek-v4-flash 官方接口实现"""
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_model = "deepseek-chat"

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.default_model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.5),
            max_tokens=kwargs.get("max_tokens", 1000),
            stream=False
        )
        return response.choices[0].message.content.strip()

class StylisticScribe:
    """
    外壳解压渲染层：将确定性的高维计算内核输出数值解压为平滑的文学叙事
    LLM 在此被严密监管，剥离了剧情走向的裁量权，仅作为“叙事风格翻译官”
    """
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider

    def render_node_to_text(self, node: CausalNode, space_snapshot: Dict[str, float], profiles: Dict[str, Any]) -> str:
        if self.provider is not None:
            prompt = f"""[COMPUTATIONAL KERNEL FORCE CONSTRAINTS - STRICT LAYER INTERFACE]
【角色档案】{json.dumps(profiles, ensure_ascii=False)}
【情感相空间坐标】{json.dumps(space_snapshot, ensure_ascii=False)}
【因果前提（不可修改）】{node.premise}
【因果结论（不可修改）】{node.conclusion}

【渲染规则】
1. 你是一个专业的文学风格转换器，没有任何剧情修改权限。
2. 将上述因果关系扩展为150-250字的描写，严格遵循情感坐标：
   - 高克制(>0.7)：语言冰冷、动作克制、内心活动压抑
   - 高焦虑(>0.7)：加入生理细节（心跳、手抖、呼吸急促）
   - 高愧疚(>0.5)：加入自我谴责、回避眼神等细节
   - 高欲望(>0.5)：加入眼神拉丝、身体本能反应等细节
3. 绝对禁止添加任何不在前提和结论中的事件、人物或反转。
4. 绝对禁止使用"突然"、"不知为何"、"莫名其妙"等模糊表述。
5. 所有行为和心理活动必须是情感坐标的直接产物。
"""
            return self.provider.generate(prompt, temperature=0.4, max_tokens=600)
        
        # 确定性保底演示解压逻辑
        return f"（系统确定性数值解压：[{node.character}] 在相空间坐标 {space_snapshot} 约束下，严密推演事实：从「{node.premise}」必然收敛至「{node.conclusion}」，完成行为渲染。）"

# =============================================================================
# 终极因果动力学故事生成引擎 (Calculus & Topology Edition)
# ✅ 优化1：增加状态持久化（保存/加载）
# ✅ 优化2：完善错误处理与日志输出
# ✅ 优化3：增加单节点重新渲染功能
# =============================================================================
class UltimateDynamicCausalEngine:
    def __init__(self, novel_title: str, initial_state: Optional[GlobalCausalState] = None):
        self.novel_title = novel_title
        self.state = initial_state or GlobalCausalState()
        self.chapters: List[ChapterGraph] = []
        
        # 初始化高维核组件
        self.broker = CausalIntersectionBroker()
        self.scribe = StylisticScribe()
        
        # 建立闭环审计流水线
        self.kernel_auditor = CognitiveAuditEngine(
            account=ResponsibilityAccount("CausalBrain", "CoreMathEngineer", "kernel_verification"),
            allowed_stages=["kernel_verification"]
        )

    def set_llm_provider(self, provider: LLMProvider) -> None:
        self.scribe.provider = provider

    def inject_implicit_assumptions(self, node: CausalNode):
        """内隐假设动态识别算子（预留LLM自动提取接口）"""
        node.implicit_assumptions.clear()
        space = self.state.emotional_registry.get(node.character)
        
        # 物理空间先验假设
        if "电车站" in node.premise or "站台" in node.conclusion:
            node.implicit_assumptions.append(ImplicitAssumption(
                "涉事客体处于具备公共轨道交通网络的基础时空场中", 0.99, "low"
            ))
        
        # 动力学高风险假设审计
        if space and space.restraint > 0.8:
            node.implicit_assumptions.append(ImplicitAssumption(
                content=f"隐式判定角色 [{node.character}] 具备克服其深层焦虑执行超强克制策略的心理防御阈值",
                confidence=round(space.restraint, 2),
                risk_level="medium" if space.anxiety < 0.7 else "high"
            ))

    def process_and_render_chapter(self, chapter_id: int, title: str, raw_nodes: List[CausalNode]) -> ChapterGraph:
        print(f"\n==================================================")
        print(f"🚀 计算内核启动：正在计算第 [{chapter_id}] 章 拓扑层演进 -> 《{title}》")
        print(f"==================================================")
        
        # 保存生成前的状态快照，用于回滚
        self.state.save_snapshot()
        
        # 1. 运行因果拓扑图谱的冲突博弈与动态修剪
        valid_nodes = self.broker.arbitrate_and_prune(raw_nodes, self.state.emotional_registry)
        print(f"📊 拓扑剪枝完成：原始节点 {len(raw_nodes)} 个，保留有效节点 {len(valid_nodes)} 个")
        
        # 2. 注入隐式假设透视与潜在崩塌概率测算
        for node in valid_nodes:
            self.inject_implicit_assumptions(node)
            
        # 3. 运行核心规则与世界稳态前置审计
        rule_audit = self.kernel_auditor.audit_rule_violation(valid_nodes, self.state)
        space_audit = self.kernel_auditor.audit_phase_space_safety(self.state.emotional_registry)
        
        if not rule_audit["passed"] or not space_audit["passed"]:
            print("❌ KERNEL CRITICAL CRASH: 底层因果参数击穿世界线稳态边界，生成中断。")
            print(f"  - 致命错误: {rule_audit['issues'] + space_audit['issues']}")
            print(f"  - 警告信息: {rule_audit['warnings'] + space_audit['warnings']}")
            print("  - 正在自动回滚到上一个稳定状态...")
            self.state.rollback()
            raise ValueError("因果推导引发全局系统崩塌风险，已自动回滚。")
        
        if rule_audit["warnings"] or space_audit["warnings"]:
            print(f"⚠️  内核审计警告：{rule_audit['warnings'] + space_audit['warnings']}")
        
        print(f"✅ 内核前置审计全面收敛：稳态基准分={rule_audit['score']} | 动态相点分={space_audit['score']}")
        
        # 4. 连续相空间动力学演化迭代更新
        chapter_content_blocks = []
        chapter_graph = ChapterGraph(chapter_id=chapter_id, title=title)
        
        for i, node in enumerate(valid_nodes, 1):
            char_space = self.state.emotional_registry.get(node.character)
            
            # 执行连续变迁方程计算
            delta_report = {}
            if char_space and node.emotional_impulse:
                delta_report = char_space.apply_event_impulse(node.emotional_impulse, dt=1.0)
            
            # 捕获高维连续坐标状态快照
            space_snapshot = char_space.to_dict() if char_space else {}
            print(f"  [{i}/{len(valid_nodes)}] 角色 [{node.character}] 相空间更新 -> {space_snapshot}")
            if delta_report:
                print(f"      增量变化: {delta_report}")
            
            # 5. 调用外壳叙事序列化器执行严格受控文本降维解压
            rendered_text = self.scribe.render_node_to_text(
                node, space_snapshot, self.state.characters_profile.get(node.character, {})
            )
            chapter_content_blocks.append(rendered_text)
            
            # 将事实无害化沉淀至世界基底
            self.state.established_facts.add(node.conclusion)
            chapter_graph.nodes[node.node_id] = node
            
        # 6. 章稳态封包
        chapter_graph.content = "\n\n".join(chapter_content_blocks)
        chapter_graph.audit_report = {
            "rule_audit": rule_audit,
            "space_audit": space_audit,
            "global_version_before": self.state.version,
            "global_version_after": self.state.version + 1
        }
        
        self.state.version += 1
        self.chapters.append(chapter_graph)
        print(f"✅ 第 [{chapter_id}] 章 数值解压与拓扑收敛渲染圆满交付。")
        return chapter_graph

    def re_render_node(self, chapter_id: int, node_id: str) -> Optional[str]:
        """✅ 新增：单独重新渲染某个节点，不改变因果状态"""
        for ch in self.chapters:
            if ch.chapter_id == chapter_id and node_id in ch.nodes:
                node = ch.nodes[node_id]
                char_space = self.state.emotional_registry.get(node.character)
                space_snapshot = char_space.to_dict() if char_space else {}
                return self.scribe.render_node_to_text(
                    node, space_snapshot, self.state.characters_profile.get(node.character, {})
                )
        return None

    def save_state(self, path: str) -> None:
        """✅ 新增：保存整个引擎状态到文件"""
        data = {
            "novel_title": self.novel_title,
            "state": dataclasses.asdict(self.state),
            "chapters": [dataclasses.asdict(ch) for ch in self.chapters]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_state(cls, path: str) -> "UltimateDynamicCausalEngine":
        """✅ 新增：从文件加载整个引擎状态"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 反序列化全局状态
        state_dict = data["state"]
        state = GlobalCausalState(
            characters_profile=state_dict["characters_profile"],
            emotional_registry={
                k: CharacterPhaseSpace(**v) for k, v in state_dict["emotional_registry"].items()
            },
            world_rules=state_dict["world_rules"],
            established_facts=set(state_dict["established_facts"]),
            version=state_dict["version"],
            history_snapshots=state_dict["history_snapshots"]
        )
        
        # 反序列化章节
        engine = cls(novel_title=data["novel_title"], initial_state=state)
        for ch_dict in data["chapters"]:
            nodes = {k: CausalNode(**v) for k, v in ch_dict["nodes"].items()}
            chapter = ChapterGraph(
                chapter_id=ch_dict["chapter_id"],
                title=ch_dict["title"],
                nodes=nodes,
                content=ch_dict["content"],
                audit_report=ch_dict["audit_report"]
            )
            engine.chapters.append(chapter)
        
        return engine

    def compile_entire_novel(self) -> str:
        """打包聚合完整小说文本"""
        compiled = f"# 《{self.novel_title}》\n\n"
        for ch in self.chapters:
            compiled += f"## 第 {ch.chapter_id} 章：{ch.title}\n\n{ch.content}\n\n"
        return compiled

# =============================================================================
# 生产级测试用例（已适配新的情感维度）
# =============================================================================
class MockLLM:
    """外壳解压大模型测试桩：严格按照接口返回符合情绪向量的逼真文本描写"""
    def generate(self, prompt: str, **kwargs) -> str:
        if '"restraint": 0.9' in prompt:
            return "空气中还残存着消毒水那刺鼻的清冷感，叶婉清死死捏着那份诊断书，上面‘2.7’的数字如同烙印。可她胸腔中汹涌的战栗却在极高的克制下，被强行压缩成了一道冰冷的视线。当在黄昏的站台看见陆景川转头离去的风衣衣角时，她迈出脚步的肌肉硬生生在理性的钢索下死死锁住。她没有呼喊，没有追赶，只是以一种近乎审判的冷漠姿态留在原地，任由长风吹散头发，两人的因果轴自此断裂分流。"
        return "陆景川毫无顾忌地走上了电车，他的步伐带着特有的冷漠与惯常的笃定。在车门即将合拢的磁吸声中，他隐约察觉到了身后那道胶着、发烫的视线，那属于过去一贯对他百般纵容的叶婉清。然而，他内心深处的依恋曲线早已降至冰点，这种毫无波澜的相空间轨迹让他连一毫米的侧头都显得多余。电车发出沉闷的轰鸣，他连头也没回，顺理成章地将那个熟悉的身影抛在飞驰的钢铁阴影之外。"

if __name__ == "__main__":
    # 1. 构建高维确定性全局世界状态
    initial_world_state = GlobalCausalState(
        world_rules={
            "纵容阈值上限": 2.5,
            "系统稳态判据": "当纵容度突破上限时，必须爆发相空间的剧烈重组（克制力大幅跃升，焦虑阻尼激活）"
        }
    )
    
    # 使用动态添加角色方法，避免KeyError
    initial_world_state.add_character(
        name="叶婉清",
        profile={"occupation": "高级数据分析师", "archetype": "高智觉醒女性"},
        initial_phase=CharacterPhaseSpace(
            character_name="叶婉清",
            attachment=0.85,
            restraint=0.30,
            anxiety=0.60,
            guilt=0.20,
            desire=0.70
        )
    )
    
    initial_world_state.add_character(
        name="陆景川",
        profile={"occupation": "新锐先锋建筑师", "archetype": "极度自我中心者"},
        initial_phase=CharacterPhaseSpace(
            character_name="陆景川",
            attachment=0.15,
            restraint=0.70,
            anxiety=0.10,
            guilt=0.05,
            desire=0.10
        )
    )
    
    # 2. 组装高阶动态生成内核
    engine = UltimateDynamicCausalEngine(novel_title="因果相空间游戏", initial_state=initial_world_state)
    engine.set_llm_provider(MockLLM()) # 测试用MockLLM，生产环境替换为DeepSeekProvider
    
    # 生产环境接入真实LLM（取消注释并填入你的API Key）
    # engine.set_llm_provider(DeepSeekProvider(api_key="你的DeepSeek API Key"))
    
    # 3. 规划第1章混合交叉因果DAG拓扑节点
    node_ye_1 = CausalNode(
        node_id="YE_NODE_001",
        character="叶婉清",
        premise="叶婉清拿到诊断报告，得知自己对陆景川的纵容权重为2.7",
        conclusion="她意识到再纵容下去会失去自我并导致自身系统崩溃",
        emotional_impulse={"anxiety": 0.40, "attachment": -0.30, "restraint": 0.60, "guilt": 0.10}
    )
    
    # 时空互斥剧情对抗流（测试拓扑剪枝功能）
    node_ye_2_dominant = CausalNode(
        node_id="YE_NODE_002_A",
        character="叶婉清",
        premise="叶婉清在电车站遭遇陆景川的风衣背影且对方正准备无情离开",
        conclusion="她借助残存的极端克制力硬生生钉死在站台原地，拒绝做出追赶本能",
        spatial_mutually_exclusive_tag="STATION_STORYLINE_DECISION",
        parent_nodes=["YE_NODE_001"],
        priority=1  # 强制提高优先级，确保被选中
    )
    
    node_ye_2_loser = CausalNode(
        node_id="YE_NODE_002_B",
        character="叶婉清",
        premise="叶婉清在电车站遭遇陆景川的风衣背影且对方正准备无情离开",
        conclusion="她情绪大崩溃不顾一切在轨道边追赶推搡陆景川并失声大哭",
        spatial_mutually_exclusive_tag="STATION_STORYLINE_DECISION",
        parent_nodes=["YE_NODE_001"],
        priority=0
    )
    
    node_lu_1 = CausalNode(
        node_id="LU_NODE_001",
        character="陆景川",
        premise="陆景川感知到叶婉清在医院站台投射而来的微弱目光",
        conclusion="他没有产生任何侧头或停留动作，保持冷漠坐标径直登上车厢离去",
        emotional_impulse={"attachment": -0.05, "restraint": 0.10}
    )
    
    chapter_1_raw_blueprint = [node_ye_1, node_ye_2_dominant, node_ye_2_loser, node_lu_1]
    
    # 4. 内核执行核心计算、拓扑剪枝、相空间平滑演进与语言渲染
    engine.process_and_render_chapter(
        chapter_id=1,
        title="连续相变的奇点",
        raw_nodes=chapter_1_raw_blueprint
    )
    
    # 5. 保存状态（可选）
    # engine.save_state("causal_novel_state.json")
    
    # 6. 输出绝对责任锚定的最终小说文本
    final_prose = engine.compile_entire_novel()
    print("\n==================================================")
    print("✨ 终极因果动力学故事生成内核 完美交付输出：")
    print("==================================================")
    print(final_prose)
