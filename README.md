# Ideogram Note - 小红书爆款内容工作流

> 基于 Next.js + FastAPI 的 AI 驱动内容创作平台  
> 支持图文、视频、公众号三种模式，从选题到成品一站式完成

## ✨ 核心功能

### 1. 选题雷达
- **热门关键词**: 预设 10 个高频领域关键词，一键搜索
- **AI 推荐模式**: DeepSeek 快速生成 10 个爆款选题（3-5秒）
- **实时搜索模式**: 火山引擎联网搜索小红书热点（20-30秒）
- **智能缓存**: 6 小时缓存，相同关键词秒返

### 2. 人设配置
- **5 大领域人设库**: 职场/美妆/生活/宠物/技术
- **双模型对比**: 并行生成两个版本，选择最优结果
- **Temperature 控制**: 0.3-1.0 创意度调节
- **参考链接**: 支持输入小红书笔记 URL，模仿风格

### 3. 内容生成
- **多模型支持**: DeepSeek/Claude/GPT-4o/Gemini/Grok
- **结构化输出**: 5 个备选标题 + 800 字正文 + 配图大纲
- **模式切换**:
  - 图文模式: 生成小红书图文内容 + 3-6 张配图方案
  - 视频模式: 生成视频脚本 + 分镜设计 + 口播词
  - 公众号模式: 长文章 + 技术架构图设计

### 4. 提示词预览（生图功能已隐藏）
- **中英文 Prompt**: 完整展示画面描述和生图提示词
- **一键复制**: 支持单个/全部场景信息复制
- **外部生图**: 将 prompt 复制到 Midjourney/Stable Diffusion 等工具

### 5. 导出功能
- **Obsidian 集成**: 一键导出 Markdown 笔记
- **图片关联**: 自动下载并关联配图 URL
- **标签分类**: 自动添加话题标签

## 🏗️ 技术架构

### 前端（Next.js）
```
frontend/
├── src/
│   ├── app/                # Next.js App Router
│   │   ├── page.tsx        # 主页面
│   │   └── layout.tsx      # 全局布局
│   ├── components/
│   │   ├── blocks/         # 业务组件
│   │   │   ├── TopicRadar.tsx      # 选题雷达
│   │   │   ├── PersonaConfig.tsx   # 人设配置
│   │   │   ├── ContentPreview.tsx  # 内容预览
│   │   │   └── MediaStudio.tsx     # 提示词预览
│   │   ├── layout/         # 布局组件
│   │   │   ├── Header.tsx
│   │   │   └── Sidebar.tsx
│   │   └── ui/             # shadcn/ui 组件
│   ├── lib/
│   │   ├── api.ts          # API 客户端
│   │   ├── progress-utils.ts   # 进度模拟工具
│   │   └── utils.ts
│   └── store/
│       └── workflow.ts     # Zustand 状态管理
```

**技术栈**:
- Next.js 16 (App Router)
- TypeScript 5
- Tailwind CSS 4
- Framer Motion (动画)
- Zustand (状态管理)
- shadcn/ui (UI 组件)

### 后端（FastAPI）
```
backend/
├── main.py             # FastAPI 入口
├── routers/
│   ├── topics.py       # 选题分析 API
│   ├── content.py      # 内容生成 API
│   ├── media.py        # 图片/音频生成 API
│   ├── video.py        # 视频合成 API
│   └── config.py       # 配置 API
└── requirements.txt

modules/
├── trend.py            # 热点分析（火山引擎联网搜索）
├── writer.py           # 文案生成（OpenRouter）
├── painter.py          # 配图生成（Replicate/豆包/Nano Banana Pro）
├── audio.py            # 音频生成（Edge TTS/火山引擎）
├── editor.py           # 视频合成（MoviePy）
├── storage.py          # OSS 存储
├── persona.py          # 人设管理
├── quality_checker.py  # 质量检测
└── md_exporter.py      # Markdown 导出
```

## 🚀 快速启动

### 环境要求
- Python 3.10+
- Node.js 18+
- Chrome 浏览器（如需爬虫功能）

### 1. 克隆项目
```bash
git clone <repo_url>
cd Ideogram_note
```

### 2. 配置环境变量
创建 `.env` 文件：
```env
# LLM 文案生成（必需）
OPENROUTER_API_KEY=sk-or-xxx

# 火山引擎（选题搜索 + TTS）
ARK_API_KEY=xxx
VOLC_ACCESS_KEY=xxx
VOLC_SECRET_KEY=xxx
VOLC_APP_ID=xxx

# 图片生成（可选，生图功能已隐藏）
REPLICATE_API_TOKEN=r8_xxx

# 阿里云 OSS（图片存储，可选）
OSS_ACCESS_KEY_ID=xxx
OSS_ACCESS_KEY_SECRET=xxx
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your-bucket
OSS_URL_PREFIX=https://your-bucket.oss-cn-hangzhou.aliyuncs.com

# Obsidian 导出路径（可选）
OBSIDIAN_VAULT_PATH=/Users/你的用户名/Documents/Obsidian/笔记库
```

### 3. 安装依赖

**后端依赖**:
```bash
cd backend
pip install -r requirements.txt
cd ..
```

**前端依赖**:
```bash
cd frontend
npm install
cd ..
```

### 4. 启动项目

**方式一：从根目录启动（推荐）**

在项目根目录打开两个终端：

终端1 - 启动后端:
```bash
python3 -m uvicorn backend.main:app --reload --port 8501
```

终端2 - 启动前端:
```bash
cd frontend && npm run dev
```

**方式二：分别启动**

后端:
```bash
cd backend
uvicorn main:app --reload --port 8501
```

前端:
```bash
cd frontend
npm run dev
```

**访问地址**:
- 前端: http://localhost:3000
- 后端: http://localhost:8501
- API 文档: http://localhost:8501/docs

## 📦 依赖服务

| 服务 | 用途 | 必需性 | 成本 |
|------|------|--------|------|
| OpenRouter | LLM 文案生成 | ✅ 必需 | 按量计费，约 $0.001/千字 |
| 火山引擎 ARK | 联网搜索热点 | ✅ 必需 | 按调用计费 |
| 火山引擎 TTS | 音频生成（视频模式） | 视频模式必需 | 按字符计费 |
| Replicate | 图片生成（已隐藏） | 可选 | 约 $0.04/张 |
| 阿里云 OSS | 图片存储 | 可选 | 存储+流量费用 |
| Edge TTS | 免费音频生成 | 可选 | 免费 |

## 🎯 使用流程

### 图文模式（小红书）
1. **输入关键词** → 点击热门关键词或手动输入（如：职场晋升）
2. **AI 推荐** → 快速获取 10 个爆款选题
3. **选择话题** → 点击感兴趣的选题
4. **配置人设** → 选择赛道和人设风格（如：职场反共识观察者）
5. **生成内容** → 启用双模型对比（可选），点击"开始生成"
6. **查看 Prompt** → 在提示词预览中复制生图 prompt
7. **导出笔记** → 一键导出到 Obsidian

### 视频模式
1-5 步同上
6. **查看分镜** → 口播词 + 画面描述 + 生图 prompt
7. 复制 prompt 到外部生图工具制作视频

### 公众号模式
1-5 步同上
6. **查看架构图** → 技术描述 + 生图 prompt
7. 导出长文到 Obsidian

## 🧩 核心模块说明

### writer.py - 文案生成引擎
- **结构化输出**: JSON Schema 强制格式化
- **人设融合**: 根据选择的人设调整语言风格
- **大纲扩展**: 基于热点大纲深度创作
- **多模型支持**: 5 个主流 LLM 可选

### trend.py - 热点分析引擎
- **联网搜索**: 火山引擎 Web Search 插件实时搜索小红书
- **智能降级**: 联网失败自动降级到 LLM 推测
- **结果缓存**: 6 小时内相同关键词直接返回缓存

### painter.py - 生图 Prompt 生成器
- **三种生图服务**:
  - Replicate (二次元风格)
  - 火山引擎豆包 (Seedream)
  - Nano Banana Pro (超高质量)
- **风格库**: 预设多种情感风格（可爱治愈/严肃深度/职场日常等）
- **中英文适配**: 根据服务商自动使用中文或英文 prompt

### quality_checker.py - 质量检测
- 标题吸引力检测
- 内容完整性验证
- 敏感词过滤

## 🎨 人设库

### 职场赛道
- 职场反共识观察者（冷幽默拆解职场迷思）
- 职场清醒女王（犀利冷艳，只谈利益）
- 腹黑HR姐姐（揭秘潜规则，话术SOP）
- 精英操盘手（逻辑严密，输出方法论）
- 90后精神离职艺术家（糊弄学大师）

### 美妆赛道
- 专业成分党（理性分析，数据说话）
- 贵妇种草机（高端大气，品质生活）

### 生活赛道
- 治愈系姐姐（温暖陪伴，情绪价值）
- 搞钱女孩（副业干货，变现路径）

### 宠物萌宠赛道
- 硬核成分党兽医（科学养宠，拒绝智商税）
- 精致富养铲屎官（颜值正义，治愈氛围）
- 金牌训宠师（SOP化教学，行为矫正）

### 硬核技术/AI赛道
- 全栈AI架构师（深度技术文章，架构图设计）

## 🔧 开发相关

### 后端 API 端点
```
GET  /health                      # 健康检查
POST /api/topics/analyze          # 选题分析
POST /api/content/generate        # 内容生成
POST /api/content/export          # 导出 Markdown
GET  /api/config/models           # LLM 模型列表
GET  /api/config/voices           # TTS 语音列表
GET  /api/config/personas         # 人设库
POST /api/media/images            # 批量生图（已禁用）
POST /api/media/audio             # 批量音频生成
POST /api/video/create            # 视频合成
GET  /api/video/bgm               # BGM 列表
```

### 前端状态管理（Zustand）
```typescript
// 全局状态
- mode: "image" | "video" | "wechat"
- currentStep: "topic" | "persona" | "preview" | "studio"
- keyword: string
- topics: TopicItem[]
- selectedTopic: TopicItem | null
- selectedPersona: string
- generatedContent: GenerateResponse | null
- dualModelMode: boolean
- temperature: number
```

### 关键配置
- **默认模式**: 图文模式（小红书）
- **默认人设**: 硬核技术/AI - 全栈AI架构师
- **默认 LLM**: deepseek/deepseek-chat
- **双模型**: 默认启用（DeepSeek + Claude 3.5 Sonnet）
- **Temperature**: 0.4

## 📝 最新更新

### v2.0 (2024-12-07)
- ✅ 热门关键词快捷入口（10个预设关键词）
- ✅ 修复模型B下拉框数据显示问题
- ✅ MediaStudio 添加完整中英文 prompt 显示
- ✅ 添加 Nano Banana Pro 生图模型支持
- ✅ 隐藏生图功能，仅保留 prompt 预览
- ✅ 修复搜索按钮独立 loading 状态
- ✅ 进度条动画优化
- ✅ 双模型对比 UI 增强

### v1.x
- 基础工作流实现
- Streamlit UI
- 单模型生成

## 🔒 数据安全

- **本地存储**: 所有生成的图片、音频、视频存储在 `output/` 目录
- **状态持久化**: Zustand persist 到 localStorage
- **API 调用**: 所有敏感信息通过环境变量配置
- **无数据上传**: 不收集用户数据，仅调用第三方 API

## 📂 项目结构

```
Ideogram_note/
├── backend/            # FastAPI 后端
│   ├── main.py
│   └── routers/
├── frontend/           # Next.js 前端
│   └── src/
├── modules/            # 核心业务逻辑
│   ├── trend.py        # 热点分析
│   ├── writer.py       # 文案生成
│   ├── painter.py      # Prompt 生成
│   ├── audio.py        # 音频生成
│   ├── editor.py       # 视频合成
│   └── ...
├── data/
│   ├── personas.json   # 人设库
│   └── monitor.db      # 内容记录
├── assets/
│   └── bgm/            # 背景音乐素材
├── output/             # 生成结果输出目录
│   ├── images/
│   ├── audio/
│   └── video/
└── .env                # 环境变量配置
```

## 🐛 常见问题

### 1. 后端启动失败
- 检查 `.env` 文件是否存在
- 检查 `OPENROUTER_API_KEY` 是否配置
- 确保端口 8501 未被占用

### 2. 前端连接失败
- 确保后端服务已启动（http://localhost:8501/health）
- 检查前端的 `.env.local` 中 `NEXT_PUBLIC_API_URL` 配置

### 3. 选题搜索失败
- 检查 `ARK_API_KEY` 是否有效
- 尝试切换到"AI推荐"模式（不依赖联网搜索）

### 4. 内容生成失败
- 检查 OpenRouter API 余额
- 尝试切换其他模型
- 查看后端日志排查具体错误

### 5. 模型B下拉框为空
- 刷新页面重新加载模型列表
- 检查后端 `/api/config/models` 端点是否正常

## 💡 最佳实践

### 1. 选题策略
- 使用热门关键词快速测试
- AI 推荐模式速度快，适合批量生产
- 实时搜索模式数据准确，适合追热点

### 2. 人设选择
- 根据目标受众选择合适人设
- 自定义人设时提供详细的风格描述
- 使用参考链接模仿成功笔记风格

### 3. 双模型对比
- 打开双模型模式生成两个版本
- 对比选择更优版本
- Temperature 较高时差异更明显

### 4. Prompt 使用
- 复制完整 prompt 到专业生图工具
- 根据需要微调 prompt
- 保存优质 prompt 复用

## 📄 许可证

MIT License

## 🙏 致谢

- OpenRouter - LLM API 聚合
- 火山引擎 - 联网搜索 + TTS
- Replicate - 模型托管平台
- shadcn/ui - UI 组件库
- Next.js - React 框架

---

**开发者**: 0xNiedlichX  
**更新日期**: 2024-12-07
