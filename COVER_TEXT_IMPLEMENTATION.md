# 主图文字和浅色系优化 - 实施总结

## 完成时间
2024年12月6日

## 需求

主图（第1张图）新增功能：
1. ✅ 包含文字内容（LLM自动生成核心文案）
2. ✅ 文字位置：画面中心叠加
3. ✅ 背景色：白色/米白色浅色系
4. ✅ 实现方式：在 Gemini prompt 中描述

---

## 实施内容

### ✅ 1. LLM 生成主图文字

**文件**: `modules/writer.py`

#### A. 新增字段要求

在配图设计字段说明中增加：

```python
4. cover_text（仅第一张主图需要）：3-8个汉字的核心文案，用于叠加显示
   - 要求：提炼文章核心观点或最吸睛的一句话
   - 示例："职场穿搭自由"、"拒绝内耗"、"年终奖攻略"
```

#### B. 输出格式示例更新

```json
{
  "index": 1,
  "description": "封面图：职场女性角色...",
  "sentiment": "职场日常",
  "prompt": "anime style office girl...",
  "cover_text": "职场穿搭自由"  // 新增
}
```

#### C. 写作规则强化

新增规则：
- **第一张图片（主图）必须包含 cover_text 字段**
- 配图（第2-6张）不需要 cover_text 字段

**效果**: LLM 会自动为主图生成 3-8 字的核心文案

---

### ✅ 2. Gemini Prompt 增强

**文件**: `modules/painter.py` - `_generate_single_gemini` 函数

#### 新增逻辑判断

```python
cover_text = scene.get('cover_text', '')

if cover_text:
    # 主图模式：文字 + 浅色背景
    enhanced_prompt = f"""Generate a clean anime-style illustration with white/cream background:
- Main visual: {base_prompt}
- Background: White or off-white color, minimal and clean design
- Text overlay in center: "{cover_text}" in bold modern Chinese font, dark color for readability
- Style: Professional poster design, high quality, masterpiece, 4k, sharp focus
- Atmosphere: Light and bright, fresh and clean, minimalist composition
- Color scheme: Pastel and soft colors, avoid dark or saturated backgrounds"""
else:
    # 配图模式：原有逻辑
    enhanced_prompt = f"Generate an image: High quality, professional illustration, masterpiece, best quality, {base_prompt}, detailed, 4k, sharp focus"
```

#### 关键特性

**浅色系控制**:
- `white/cream background` - 强制白色或米白色背景
- `light and bright atmosphere` - 明亮氛围
- `pastel and soft colors` - 柔和色调
- `avoid dark or saturated backgrounds` - 避免深色

**文字叠加**:
- `text overlay in center` - 中心位置
- `"{cover_text}"` - 直接嵌入文字内容
- `bold modern Chinese font` - 粗体现代中文字体
- `dark color for readability` - 深色文字（与浅色背景对比）

**日志增强**:
```python
print(f"[Gemini] 主图 {index+1} 生成中（带文字: {cover_text}）...")
```

---

### ✅ 3. API 类型定义更新

**文件**: `backend/routers/content.py`

在 `ImageDesign` 模型中增加字段：

```python
class ImageDesign(BaseModel):
    index: int = 0
    description: str = ""
    prompt: str = ""
    sentiment: str = ""
    cover_text: Optional[str] = None  # 新增：主图文字
```

**效果**: 支持前后端传递主图文字字段

---

## 技术实现详解

### Gemini 2.5 Flash Image 文字渲染能力

Gemini Imagen 3 原生支持文字渲染：
- ✅ 支持中英文文字
- ✅ 可指定文字位置、大小、风格
- ✅ 可控制文字颜色和字体
- ✅ 文字与画面自然融合

### 浅色系 Prompt 策略

通过多重约束确保浅色背景：

```
第1层：白色背景 → "white/cream background"
第2层：明亮氛围 → "light and bright atmosphere"  
第3层：柔和色调 → "pastel and soft colors"
第4层：禁止深色 → "avoid dark or saturated backgrounds"
```

### 完整 Prompt 示例

**输入**（LLM 生成）:
```json
{
  "prompt": "anime style office girl wearing casual cardigan",
  "cover_text": "职场穿搭自由"
}
```

**输出**（发送给 Gemini）:
```
Generate a clean anime-style illustration with white/cream background:
- Main visual: anime style office girl wearing casual cardigan
- Background: White or off-white color, minimal and clean design
- Text overlay in center: "职场穿搭自由" in bold modern Chinese font, dark color for readability
- Style: Professional poster design, high quality, masterpiece, 4k, sharp focus
- Atmosphere: Light and bright, fresh and clean, minimalist composition
- Color scheme: Pastel and soft colors, avoid dark or saturated backgrounds
```

---

## 工作流程

```
LLM生成内容
  ↓
生成主图设计（包含cover_text: "职场穿搭自由"）
  ↓
调用 Gemini API
  ↓
Gemini根据prompt渲染：
  - 白色背景
  - 二次元职场女性
  - 中心大字"职场穿搭自由"
  ↓
下载保存为主图
```

---

## 预期效果

### 改进前

```
┌─────────────────────┐
│                     │
│  [二次元职场女性]   │
│  （随机背景色）     │
│                     │
└─────────────────────┘
无文字，信息密度低
```

### 改进后

```
┌─────────────────────┐
│                     │
│  职场穿搭自由  ← 核心文案
│                     │
│  [二次元职场女性]   │
│                     │
│                     │
└─────────────────────┘
白色背景，明亮清爽
```

**特点**:
- ✅ 文字醒目，信息密度高
- ✅ 白色背景，清爽明亮
- ✅ 符合小红书封面图风格
- ✅ 一眼能抓住核心主题

---

## 文件修改清单

- ✅ `modules/writer.py` - LLM 生成主图文字字段
- ✅ `modules/painter.py` - Gemini prompt 增强（文字+浅色）
- ✅ `backend/routers/content.py` - 类型定义更新

---

## 测试建议

1. **生成内容后检查**:
   - [ ] 第一张 image_design 包含 cover_text 字段
   - [ ] cover_text 长度为 3-8 个汉字
   - [ ] cover_text 是核心观点提炼

2. **生成主图后检查**:
   - [ ] 图片背景为白色/米白色
   - [ ] 画面中心有清晰文字
   - [ ] 文字为深色（与浅色背景对比）
   - [ ] 整体明亮清爽

3. **对比配图**:
   - [ ] 配图无 cover_text 字段
   - [ ] 配图使用豆包生成（非 Gemini）
   - [ ] 配图可以有其他背景色

---

## 后续优化建议

1. **文字可编辑**: 前端添加编辑框，允许用户修改主图文字
2. **文字样式可调**: 支持字号、颜色、位置调整
3. **多语言支持**: 支持英文主图文案
4. **A/B测试**: 生成两个版本（有/无文字）让用户选择
5. **文字位置优化**: 根据画面构图智能调整文字位置

---

## 完成状态

✅ 所有功能已实现  
✅ 无 Linter 错误  
✅ 所有 TODO 已完成  

**后端需要重启生效**:
```bash
cd /Users/0xNiedlichX/Code/Ideogram_note/backend
# 停止现有进程，然后：
uvicorn main:app --reload --port 8501
```

---

## 验证步骤

1. 重启后端
2. 前端生成内容（职场主题）
3. 查看生成结果的 image_designs[0]
4. 检查是否有 cover_text 字段
5. 点击"生成所有图片"
6. 观察主图是否有文字和浅色背景

