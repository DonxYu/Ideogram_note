# 小红书内容工作流 - 前端

Notion 风格的 AI 内容创作平台，基于 Next.js 14 + TailwindCSS + shadcn/ui 构建。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **样式**: TailwindCSS v4 + shadcn/ui
- **状态管理**: Zustand (持久化)
- **动画**: Framer Motion
- **字体**: Plus Jakarta Sans + JetBrains Mono

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.local
# 编辑 .env.local 设置后端 API 地址
```

### 3. 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 运行。

### 4. 启动后端服务

确保后端 API 服务已启动（默认 `http://localhost:8000`）：

```bash
cd ../backend
pip install -r requirements.txt
python main.py
```

## 项目结构

```
src/
├── app/
│   ├── page.tsx          # 主页面
│   ├── layout.tsx        # 根布局
│   └── globals.css       # 全局样式
├── components/
│   ├── ui/               # shadcn 组件
│   ├── layout/           # 布局组件 (Sidebar, Header)
│   └── blocks/           # 业务组件
│       ├── TopicRadar.tsx      # 选题雷达
│       ├── PersonaConfig.tsx   # 人设配置
│       ├── ContentPreview.tsx  # 内容预览
│       └── MediaStudio.tsx     # 素材工作室
├── lib/
│   ├── api.ts            # API 调用层
│   └── utils.ts          # 工具函数
└── store/
    └── workflow.ts       # Zustand 状态管理
```

## 功能特性

- **选题雷达**: 联网搜索热门话题，获取爆款大纲
- **人设配置**: 选择/自定义博主人设风格
- **内容生成**: AI 生成图文/视频脚本
- **素材工作室**: 批量生成配图/音频，合成视频
- **主题切换**: 支持浅色/深色模式
- **状态持久化**: 刷新页面保留进度

## 设计语言

参考 Notion 的设计原则：
- **内容优先**: 大量留白，无边框卡片
- **Hover 交互**: 操作按钮悬浮显示
- **微动效**: 列表交错入场、hover 缩放
- **精致排版**: 合理行高/字重

## 开发命令

```bash
npm run dev      # 开发模式
npm run build    # 构建生产版本
npm run start    # 启动生产服务
npm run lint     # 代码检查
```
