# Narrative-Generator
A story generator that keeps characters and plot consistent, without logical holes.

# 逻辑叙事引擎 (Logical Story Engine)

> 让 AI 写出前后一致、不会“写崩”的故事。

## 🚀 它能做什么？
- 输入一个故事开头或一句话，自动生成逻辑通顺的完整章节。
- 保证主角性格从头到尾不“变味”，世界观规则不会前后矛盾。
- 自动检测故事里的“不合理跳跃”（比如前一秒还在医院，后一秒突然出现在海边）。
- 提醒作者：之前埋下的伏笔，后面有没有忘记回收。

## 🎯 解决什么痛点？
- AI 写长篇小说经常“忘了自己是谁”，角色性格飘忽不定。
- 写了后面忘了前面，情节前后打架。
- 编剧团队花大量时间修补逻辑 bug。
- 读者吐槽“剧情崩了”、“人设塌了”。

## 🧠 怎么做到的？
- **逻辑校验**：把故事拆成“因为 → 所以”的小链条，逐一检查是否通顺。
- **一致性守护**：记住主角的年龄、性格、人际关系，生成新内容时自动核对。
- **跳跃侦测**：发现“毫无理由”的剧情转折，及时提醒修改。
- **智能润色**：对有问题的段落自动给出修改建议。

## 🛠 快速开始
```bash
git clone https://github.com/nohn3043-arch/logical-story-engine.git
cd logical-story-engine
python story_engine.py