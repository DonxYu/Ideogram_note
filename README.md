# 小红书爆款工作流

Streamlit 驱动的小红书内容创作工作流：选题 → 文案 → 配图 → 导出

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 3. 启动
streamlit run app.py
```

## 环境变量配置

创建 `.env` 文件：

```env
# LLM (OpenRouter)
OPENROUTER_API_KEY=sk-or-xxx

# 图片生成 (Replicate)
REPLICATE_API_TOKEN=r8_xxx

# 阿里云 OSS (图片存储)
OSS_ACCESS_KEY_ID=xxx
OSS_ACCESS_KEY_SECRET=xxx
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your-bucket
OSS_URL_PREFIX=https://your-bucket.oss-cn-hangzhou.aliyuncs.com
```

## 功能模块

| 模块 | 功能 | 依赖服务 |
|------|------|----------|
| `crawler` | 爬取小红书笔记 | DrissionPage (本地Chrome) |
| `writer` | 文案生成 | OpenRouter API |
| `painter` | 配图生成 | Replicate (Flux 1.1 Pro) |
| `storage` | 图片存储 | 阿里云 OSS |

## 注意事项

- DrissionPage 需要本地安装 Chrome 浏览器
- Replicate 生图有费用，约 $0.04/张

