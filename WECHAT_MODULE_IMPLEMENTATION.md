# 微信公众号写作模块 - 实施总结

## 完成时间
2024年12月6日

## 需求概述

新增微信公众号写作模式，与小红书图文/视频模式平级，支持：
- 技术深度长文（不限字数）
- 架构图/示意图生成（极客美学）
- 全栈AI架构师人设
- 赛博朋克视觉风格

---

## 实施内容

### ✅ 1. 类型系统扩展

#### 前端类型 (`frontend/src/store/workflow.ts`, `frontend/src/lib/api.ts`)

```typescript
// Mode 扩展为三种
export type WorkflowMode = "image" | "video" | "wechat";

// 新增 Diagram 接口
export interface Diagram {
  index: number;
  title: string;
  description: string;
  diagram_type: "architecture" | "flow" | "comparison";
  prompt: string;
}

// GenerateResponse 扩展
export interface GenerateResponse {
  titles: string[];
  content: string;
  image_designs?: ImageDesign[];
  visual_scenes?: VisualScene[];
  diagrams?: Diagram[];  // 新增
}
```

#### 后端类型 (`backend/routers/content.py`)

```python
class Diagram(BaseModel):
    index: int = 0
    title: str = ""
    description: str = ""
    diagram_type: str = "architecture"
    prompt: str = ""

class GenerateResponse(BaseModel):
    titles: List[str] = []
    content: str = ""
    image_designs: Optional[List[ImageDesign]] = None
    visual_scenes: Optional[List[VisualScene]] = None
    diagrams: Optional[List[Diagram]] = None  # 新增
```

---

### ✅ 2. 后端 - 公众号生成函数

**文件**: `modules/writer.py`

新增 `generate_wechat_article()` 函数：

**核心特性**:
- 字数不限，建议 2000-5000 字
- 结构化输出（金字塔原理）
- 生成 2-4 张架构图设计
- 每个架构图包含 title、description、diagram_type、prompt

**System Prompt 要点**:
```
1. 深度优先：背景/痛点 → 现有方案局限 → 深度原理拆解 → 架构设计/代码思路 → 商业/未来价值
2. 工程视角：讲算法+部署+成本+延迟优化
3. 对比分析：必须有 Pros & Cons
4. 通俗化表达：用类比解释复杂概念
5. 架构图要求：每个 diagram 有 type（architecture/flow/comparison）
```

**输出格式**:
```json
{
  "titles": ["RAG已死？深度解析Long Context的工程边界", ...],
  "content": "深度技术长文...",
  "diagrams": [
    {
      "index": 1,
      "title": "RAG架构对比",
      "description": "传统RAG vs Long Context的架构差异",
      "diagram_type": "comparison",
      "prompt": "cyberpunk system comparison, RAG pipeline vs Long Context..."
    }
  ]
}
```

---

### ✅ 3. 人设数据扩展

**文件**: `data/personas.json`

新增 "硬核技术/AI" 分类：

```json
{
  "硬核技术/AI": [
    {
      "name": "全栈AI架构师",
      "prompt": "你是一位拥有15年一线经验的资深技术专家..."
    }
  ]
}
```

**人设特点**:
- 技术视野：上帝视角（God View）
- 语气风格：极度理性、硬核、逻辑严密
- 受众：中高级工程师、架构师、CTO
- 写作要求：金字塔原理、技术原理、工程落地、对比分析

---

### ✅ 4. 极客美学风格

**文件**: `modules/painter.py`

新增风格库：

```python
GEEK_STYLES_EN = {
    "architecture": "cyberpunk style, system architecture diagram, glowing nodes and connections, dark blue/purple background, neon accents, futuristic tech aesthetic, holographic UI elements...",
    "flow": "dark mode technical diagram, data flow visualization, glowing arrows and boxes, minimalist cyber aesthetic...",
    "comparison": "tech comparison infographic, split view design, dark background, neon color coding (electric blue vs orange)..."
}

GEEK_STYLES_CN = {
    "architecture": "赛博朋克风格，系统架构图，发光节点和连接线，深蓝紫色背景，霓虹灯强调色...",
    "flow": "深色模式技术示意图，数据流可视化，发光箭头和方框...",
    "comparison": "科技对比信息图，分屏设计，深色背景，霓虹色彩编码..."
}
```

新增 `generate_diagrams()` 函数：
- 根据 diagram_type 自动应用对应风格
- 使用火山引擎豆包（支持中文技术术语）
- 推荐使用 flux-anime 模型（更适合技术图）

---

### ✅ 5. UI - 三模式切换

**文件**: `frontend/src/components/layout/Sidebar.tsx`

新增第三个模式按钮：

```tsx
<Button onClick={() => setMode("wechat")}>
  <BookOpen className="w-4 h-4" />
  {!collapsed && <span>公众号</span>}
</Button>
```

**布局**: 三个按钮横向或纵向排列（根据 collapsed 状态）

---

### ✅ 6. 人设配置适配

**文件**: `frontend/src/components/blocks/PersonaConfig.tsx`

根据 mode 过滤人设分类：

```typescript
const categories = mode === "wechat"
  ? availablePersonas.filter((c) => c.category === "硬核技术/AI" || c.category === "自定义").map((c) => c.category)
  : availablePersonas.map((c) => c.category);
```

**效果**:
- 小红书模式：显示所有分类（职场、美妆、生活、宠物萌宠）
- 公众号模式：只显示"硬核技术/AI"和"自定义"

---

### ✅ 7. 内容预览适配

**文件**: `frontend/src/components/blocks/ContentPreview.tsx`

#### Tab 标签适配

```typescript
{mode === "wechat" ? "文章正文" : "正文内容"}
{mode === "wechat" ? `架构图 (${diagrams?.length || 0})` : `配图 (${image_designs?.length || 0})`}
```

#### Scenes Tab 内容适配

```typescript
const isDiagram = mode === "wechat" && "title" in scene;

// Header 显示
{isDiagram ? (
  <Badge>{diagram_type === "architecture" ? "架构" : diagram_type === "flow" ? "流程" : "对比"}</Badge>
) : (
  <Badge>{i + 1}</Badge>
)}

// Title 显示
{isDiagram ? scene.title || scene.description : ...}

// 详情字段
{isDiagram && <div>架构图标题: {scene.title}</div>}
{isDiagram && <Badge>图表类型: {diagram_type}</Badge>}
<label>{isDiagram ? "技术描述" : "画面描述"}</label>
```

---

### ✅ 8. 媒体工作室适配

**文件**: `frontend/src/components/blocks/MediaStudio.tsx`

#### scenes 数据源适配

```typescript
const scenes = mode === "video"
  ? generatedContent?.visual_scenes || []
  : mode === "wechat"
  ? generatedContent?.diagrams || []
  : generatedContent?.image_designs || [];
```

#### UI 文案适配

```typescript
{mode === "wechat" ? "生成技术架构图和示意图" : "生成小红书配图"}
{mode === "wechat" ? scene.title : scene.description}
```

#### 功能适配

- 公众号模式：只生成图片（架构图）
- 不显示音频生成按钮
- 不显示视频合成按钮
- 不显示BGM选择

---

## 模式对比

| 维度 | 小红书图文 | 小红书视频 | 微信公众号 |
|------|-----------|-----------|-----------|
| **人设** | 职场/美妆/生活/宠物 | 同图文 | 硬核技术/AI |
| **字数** | 800+ 字 | 200-300字简介 | 不限（建议2000-5000） |
| **视觉内容** | image_designs (2-6张配图) | visual_scenes (20-50个分镜) | diagrams (2-4张架构图) |
| **视觉风格** | 二次元、生活化、明亮 | 二次元、分镜感、动态 | 赛博朋克、深色、技术感 |
| **主图特殊** | Gemini生成+文字+浅色 | - | - |
| **配图生成** | Gemini(主)+豆包(配) | Replicate或豆包 | 豆包（极客美学） |
| **音频** | - | ✓ (TTS配音) | - |
| **视频** | - | ✓ (合成视频) | - |

---

## 工作流程

```
用户选择模式: 微信公众号
  ↓
Sidebar 切换到第三个 Tab "公众号"
  ↓
Step 1: 选题雷达（复用）
  输入关键词 → 获取热点
  ↓
Step 2: 人设配置
  - 只显示"硬核技术/AI"分类
  - 选择"全栈AI架构师"
  - 双模型对比生成（复用）
  ↓
Step 3: 内容预览
  - Tab1: 文章正文（深度长文）
  - Tab2: 架构图（2-4张）
    - 显示: title, diagram_type, description, prompt
  ↓
Step 4: 媒体工作室
  - 生成架构图（使用极客美学风格）
  - 不生成音频和视频
  ↓
导出笔记到 Obsidian
```

---

## 文件修改清单

### 后端
- ✅ `modules/writer.py` - 新增 `generate_wechat_article()`
- ✅ `modules/painter.py` - 新增极客美学风格 + `generate_diagrams()`
- ✅ `data/personas.json` - 新增"硬核技术/AI"分类
- ✅ `backend/routers/content.py` - 类型扩展（Diagram、GenerateResponse）

### 前端
- ✅ `frontend/src/store/workflow.ts` - mode 类型扩展
- ✅ `frontend/src/lib/api.ts` - mode + Diagram 类型扩展
- ✅ `frontend/src/components/layout/Sidebar.tsx` - 三模式切换Tab
- ✅ `frontend/src/components/blocks/PersonaConfig.tsx` - 人设分类过滤
- ✅ `frontend/src/components/blocks/ContentPreview.tsx` - diagrams 展示支持
- ✅ `frontend/src/components/blocks/MediaStudio.tsx` - 架构图生成适配

---

## 架构图类型说明

### 1. architecture（系统架构图）
**用途**: 展示系统组件和模块关系  
**风格**: 赛博朋克，发光节点和连接线，深蓝紫色背景  
**示例**: RAG系统架构、微服务拓扑、数据流架构

### 2. flow（流程图）
**用途**: 展示数据流转和处理步骤  
**风格**: 深色模式，发光箭头和方框，极简设计  
**示例**: 请求处理流程、模型推理pipeline、CI/CD流程

### 3. comparison（对比图）
**用途**: 并排对比两种技术方案  
**风格**: 分屏设计，霓虹色编码（蓝vs橙），深色背景  
**示例**: RAG vs Long Context、方案A vs 方案B

---

## 关键差异点

### 与小红书图文的区别

| 特性 | 小红书图文 | 微信公众号 |
|------|-----------|-----------|
| 字段名 | image_designs | diagrams |
| 字数要求 | 800+ | 不限（2000-5000建议） |
| 主图处理 | Gemini+文字+浅色 | 豆包+极客美学+深色 |
| 配图风格 | 生活化、二次元 | 技术图表、赛博朋克 |
| 人设分类 | 全部 | 仅技术类 |

---

## 使用示例

### 输入
- 模式：微信公众号
- 选题："RAG 检索增强生成"
- 人设：全栈AI架构师
- 模型A：deepseek-chat
- 模型B：gpt-4o

### 输出（LLM生成）

```json
{
  "titles": [
    "RAG已死？深度解析Long Context的工程边界",
    "检索增强生成(RAG)：从原理到生产的全链路实践",
    ...
  ],
  "content": "【背景】\n大模型的Context Window从4K扩展到128K，甚至1M。很多人开始质疑：RAG还有必要吗？\n\n这是一个典型的'技术泡沫'问题。Long Context确实是革命性进步，但如果你认为它能完全取代RAG，说明你还没有在生产环境踩过坑...\n\n（2000-5000字深度内容）",
  "diagrams": [
    {
      "index": 1,
      "title": "RAG vs Long Context 架构对比",
      "description": "左侧展示传统RAG的Embedding+检索+重排流程，右侧展示Long Context直接塞入的方式，标注成本和延迟差异",
      "diagram_type": "comparison",
      "prompt": "cyberpunk technical comparison diagram, left side shows RAG pipeline with vector database and retrieval, right side shows long context architecture, glowing data connections, dark background, neon blue and orange color coding"
    },
    {
      "index": 2,
      "title": "混合架构设计",
      "description": "展示Short Context RAG + Long Context备用的混合方案，包含路由层、缓存层、降级策略",
      "diagram_type": "architecture",
      "prompt": "cyberpunk system architecture, hybrid RAG and long context design, routing layer, cache layer, fallback mechanism, glowing nodes and connections, dark blue purple background, neon accents"
    }
  ]
}
```

### 生成的架构图效果

```
🎨 极客美学风格
- 深色背景（深蓝/紫/黑）
- 霓虹色强调（蓝、橙、紫）
- 发光节点和连接线
- 赛博朋克科技感
- 清晰的技术组件标注
```

---

## 后端路由逻辑

**文件**: `modules/writer.py` - `generate_note_package()`

```python
def generate_note_package(..., mode: str = "image", ...):
    if mode == "video":
        return generate_video_script(...)
    elif mode == "wechat":
        return generate_wechat_article(...)  # 新增
    else:
        return generate_image_note(...)
```

**API响应构造**: `backend/routers/content.py`

```python
if req.mode == "video":
    response.visual_scenes = [...]
elif req.mode == "wechat":
    response.diagrams = [...]  # 新增
else:
    response.image_designs = [...]
```

---

## 前端条件渲染

### PersonaConfig
```typescript
// 只显示技术分类
const categories = mode === "wechat"
  ? ["硬核技术/AI", "自定义"]
  : availablePersonas.map((c) => c.category);
```

### ContentPreview
```typescript
// Tab 标签
{mode === "wechat" ? `架构图 (${diagrams?.length || 0})` : `配图 (...)`}

// 架构图展示
{isDiagram && (
  <>
    <Badge>{diagram_type === "architecture" ? "架构" : ...}</Badge>
    <div>架构图标题: {scene.title}</div>
    <label>技术描述</label>
  </>
)}
```

### MediaStudio
```typescript
// 数据源
const scenes = mode === "wechat" ? diagrams : ...

// UI 文案
{mode === "wechat" ? "生成技术架构图" : "生成配图"}

// 功能隐藏
{mode !== "wechat" && <AudioGenButton />}
{mode !== "wechat" && <VideoGenButton />}
```

---

## 测试建议

1. **切换模式**:
   - [ ] Sidebar 显示三个 Tab
   - [ ] 点击"公众号"切换到 wechat 模式
   - [ ] 切换后自动重置下游步骤

2. **人设选择**:
   - [ ] 公众号模式只显示"硬核技术/AI"和"自定义"
   - [ ] 选择"全栈AI架构师"
   - [ ] Prompt 显示正确

3. **内容生成**:
   - [ ] 生成后包含 diagrams 字段
   - [ ] 每个 diagram 包含 title、description、diagram_type、prompt
   - [ ] 字数达到 2000+ 字

4. **内容预览**:
   - [ ] Tab2 显示"架构图 (2)"
   - [ ] 展开后显示架构图标题、类型、技术描述
   - [ ] diagram_type badge 正确显示

5. **媒体工作室**:
   - [ ] 显示架构图列表
   - [ ] 点击"生成所有图片"生成架构图
   - [ ] 不显示音频和视频相关按钮

---

## 完成状态

✅ 所有功能已实现  
✅ 无 Linter 错误  
✅ 所有 TODO 已完成  

**需要重启服务**:

```bash
# 后端
cd /Users/0xNiedlichX/Code/Ideogram_note/backend
# 停止现有进程
uvicorn main:app --reload --port 8501

# 前端
cd /Users/0xNiedlichX/Code/Ideogram_note/frontend
# Ctrl+C 停止
npm run dev
```

---

## 后续优化建议

1. **架构图生成优化**: 
   - 考虑使用专门的图表生成工具（如 Mermaid + 渲染）
   - 或使用 DALL-E 3（更擅长文字和图表）

2. **人设扩展**:
   - 添加更多技术垂直领域人设（如前端工程师、DevOps、安全专家）

3. **Markdown 格式化**:
   - 支持导出时自动格式化 markdown 代码块
   - 支持公众号富文本格式

4. **质量检测**:
   - 公众号模式的质量检测标准与小红书不同
   - 需要检测技术深度、代码示例、架构图完整性

5. **极客美学优化**:
   - 收集生成效果，迭代优化 prompt
   - 考虑增加更多风格变种（科技蓝、矩阵绿、霓虹粉）

