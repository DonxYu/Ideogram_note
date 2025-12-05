"""
视频剪辑模块 (MoviePy)
实现分镜对齐的画音同步视频合成 + Ken Burns 动态运镜 + BGM 混音
支持主题命名：视频和字幕按主题组织
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from modules.utils import sanitize_filename, get_unique_dir
from modules.storage import upload_file_to_oss_by_topic

load_dotenv()

# 默认输出目录
DEFAULT_OUTPUT_DIR = Path("output/video")
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 视频尺寸 (9:16 竖屏)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def _apply_ken_burns(image_clip, duration: float, zoom_ratio: float = 0.15):
    """
    应用 Ken Burns 效果（缓慢推拉）
    
    原理：
    1. 先将图片放大到 (1 + zoom_ratio) 倍，确保动画过程中不会出现黑边
    2. 然后通过 crop 动画实现从中心向外的缓慢推进效果
    
    Args:
        image_clip: ImageClip 对象
        duration: 片段时长
        zoom_ratio: 缩放比例 (0.15 = 最终放大 15%)
    
    Returns:
        带 Ken Burns 效果的 clip
    """
    from moviepy import vfx
    
    # 获取原始尺寸
    w, h = image_clip.size
    
    # 先放大图片以留出动画空间
    scale_factor = 1 + zoom_ratio
    enlarged = image_clip.resized(scale_factor)
    new_w, new_h = enlarged.size
    
    # 计算 crop 区域（保持目标尺寸）
    def make_frame_crop(get_frame):
        def crop_frame(t):
            # 线性插值：从 1.0 放大到 (1 + zoom_ratio)
            progress = t / duration if duration > 0 else 0
            current_scale = 1 + (zoom_ratio * progress)
            
            # 计算当前 crop 区域大小
            crop_w = w / current_scale
            crop_h = h / current_scale
            
            # 居中 crop
            x1 = (new_w - crop_w) / 2
            y1 = (new_h - crop_h) / 2
            x2 = x1 + crop_w
            y2 = y1 + crop_h
            
            frame = get_frame(t)
            # 裁切并缩放回原尺寸
            cropped = frame[int(y1):int(y2), int(x1):int(x2)]
            return cropped
        return crop_frame
    
    # 使用 resize 实现动态缩放效果（更简单可靠的方式）
    def zoom_func(t):
        progress = t / duration if duration > 0 else 0
        return 1 + (zoom_ratio * progress)
    
    zoomed = image_clip.resized(zoom_func)
    
    # 裁切到目标尺寸（居中）
    final_w, final_h = TARGET_WIDTH, TARGET_HEIGHT
    zoomed = zoomed.with_position(('center', 'center'))
    
    return zoomed


def _prepare_image_clip(img_path: str, duration: float, apply_zoom: bool = True) -> Optional[any]:
    """
    准备单个图片 clip：调整尺寸 + Ken Burns 效果
    
    Args:
        img_path: 图片路径
        duration: 片段时长
        apply_zoom: 是否应用 Ken Burns 效果
    
    Returns:
        处理后的 ImageClip
    """
    from moviepy import ImageClip
    from PIL import Image
    import numpy as np
    
    # 加载并调整图片尺寸
    img = Image.open(img_path)
    img_w, img_h = img.size
    
    # 计算缩放比例，确保覆盖目标尺寸（用于 Ken Burns 动画空间）
    zoom_buffer = 1.2 if apply_zoom else 1.0  # 预留 20% 空间给动画
    scale = max(TARGET_WIDTH * zoom_buffer / img_w, TARGET_HEIGHT * zoom_buffer / img_h)
    
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 居中裁切到目标尺寸（带缓冲）
    crop_w = int(TARGET_WIDTH * zoom_buffer)
    crop_h = int(TARGET_HEIGHT * zoom_buffer)
    left = (new_w - crop_w) // 2
    top = (new_h - crop_h) // 2
    img = img.crop((left, top, left + crop_w, top + crop_h))
    
    # 转换为 numpy array
    img_array = np.array(img.convert('RGB'))
    
    # 创建 ImageClip
    clip = ImageClip(img_array, duration=duration)
    
    if apply_zoom:
        # 应用 Ken Burns 效果
        def zoom_func(t):
            progress = t / duration if duration > 0 else 0
            return 1.0 / (1 + 0.15 * progress)  # 从 1.0 缩小到 ~0.87，实现 zoom in 效果
        
        clip = clip.resized(zoom_func)
    
    # 最终裁切到精确的目标尺寸
    clip = clip.cropped(
        x_center=clip.w / 2,
        y_center=clip.h / 2,
        width=TARGET_WIDTH,
        height=TARGET_HEIGHT
    )
    
    return clip


def create_video(
    image_paths: list, 
    audio_paths: list, 
    output_path: str = None,
    bgm_path: str = None,
    bgm_volume: float = 0.12,
    scenes: list = None,
    topic: str = None
) -> str:
    """
    拉链式组合图片和音频，生成画音同步视频 + SRT 字幕
    
    文件按主题命名，重复生成时自动添加数字后缀。
    
    Args:
        image_paths: 图片路径列表
        audio_paths: 音频路径列表（长度必须与 image_paths 相等）
        output_path: 输出视频路径，为空则自动生成
        bgm_path: 背景音乐路径（可选）
        bgm_volume: BGM 音量 (0.0-1.0)，默认 0.12
        scenes: 分镜列表（含 narration），用于生成 SRT 字幕
        topic: 主题名称（用于文件命名）
    
    Returns:
        成功返回视频文件路径，失败返回 None
    
    核心逻辑：
        每张图片的展示时长 = 对应音频的时长
        clips[N] = image[N] + audio[N] + Ken Burns 效果
        final_video = concat(clips) + BGM 混音
        同时生成 .srt 字幕文件（与视频同名）
    """
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    from moviepy import audio as afx
    
    if len(image_paths) != len(audio_paths):
        print(f"[Editor Error] 图片数量({len(image_paths)})与音频数量({len(audio_paths)})不匹配")
        return None
    
    # 创建主题目录并生成文件路径
    if not output_path:
        if topic:
            output_dir = get_unique_dir(DEFAULT_OUTPUT_DIR, topic)
            safe_topic = sanitize_filename(topic)
            output_path = str(output_dir / f"{safe_topic}.mp4")
            print(f"[Editor] 输出目录: {output_dir}")
        else:
            output_path = str(DEFAULT_OUTPUT_DIR / "output.mp4")
    
    clips = []
    voice_clips = []  # 收集所有人声音频
    
    for i, (img_path, aud_path) in enumerate(zip(image_paths, audio_paths)):
        # 跳过缺失的素材
        if not img_path or not os.path.exists(img_path):
            print(f"[Editor Warning] 场景 {i+1} 图片不存在，跳过")
            continue
        if not aud_path or not os.path.exists(aud_path):
            print(f"[Editor Warning] 场景 {i+1} 音频不存在，跳过")
            continue
        
        try:
            # 1. 加载音频
            audio_clip = AudioFileClip(aud_path)
            duration = audio_clip.duration
            voice_clips.append(audio_clip)
            
            # 2. 加载图片 + Ken Burns 效果
            image_clip = _prepare_image_clip(img_path, duration, apply_zoom=True)
            
            if image_clip is None:
                print(f"[Editor Warning] 场景 {i+1} 图片处理失败，使用原始方式")
                image_clip = ImageClip(img_path, duration=duration)
            
            # 3. 设置帧率
            image_clip = image_clip.with_fps(24)
            
            # 4. 绑定音频
            video_clip = image_clip.with_audio(audio_clip)
            
            clips.append(video_clip)
            print(f"[Editor] 场景 {i+1} 处理完成 (时长: {duration:.2f}s, Ken Burns: ✓)")
            
        except Exception as e:
            print(f"[Editor Error] 场景 {i+1} 处理失败: {e}")
            continue
    
    if not clips:
        print("[Editor Error] 没有可用的视频片段")
        return None
    
    try:
        # 为分镜添加淡入淡出过渡效果
        CROSSFADE_DURATION = 0.3  # 过渡时长（秒）
        
        if len(clips) > 1:
            print(f"[Editor] 正在添加分镜过渡效果 ({CROSSFADE_DURATION}s crossfade)...")
            from moviepy import vfx
            
            processed_clips = []
            for i, clip in enumerate(clips):
                # 第一个片段只加淡出
                if i == 0:
                    clip = clip.with_effects([vfx.CrossFadeOut(CROSSFADE_DURATION)])
                # 最后一个片段只加淡入
                elif i == len(clips) - 1:
                    clip = clip.with_effects([vfx.CrossFadeIn(CROSSFADE_DURATION)])
                # 中间片段加淡入淡出
                else:
                    clip = clip.with_effects([
                        vfx.CrossFadeIn(CROSSFADE_DURATION),
                        vfx.CrossFadeOut(CROSSFADE_DURATION)
                    ])
                processed_clips.append(clip)
            clips = processed_clips
        
        # 拼接所有片段（使用 compose 方法支持过渡）
        print(f"[Editor] 正在拼接 {len(clips)} 个片段...")
        final_clip = concatenate_videoclips(clips, method="compose", padding=-CROSSFADE_DURATION if len(clips) > 1 else 0)
        total_duration = final_clip.duration
        
        # BGM 混音
        if bgm_path and os.path.exists(bgm_path):
            print(f"[Editor] 正在混入 BGM: {bgm_path}")
            try:
                bgm_clip = AudioFileClip(bgm_path)
                
                # 循环或截取 BGM 到视频长度
                if bgm_clip.duration < total_duration:
                    # BGM 比视频短，循环播放
                    loops_needed = int(total_duration / bgm_clip.duration) + 1
                    bgm_clip = afx.audio_loop(bgm_clip, nloops=loops_needed)
                
                # 截取到视频长度
                bgm_clip = bgm_clip.subclipped(0, total_duration)
                
                # 调整 BGM 音量
                bgm_clip = bgm_clip.with_volume_scaled(bgm_volume)
                
                # 合成人声（音量保持 1.0）和 BGM
                original_audio = final_clip.audio
                mixed_audio = CompositeAudioClip([original_audio, bgm_clip])
                final_clip = final_clip.with_audio(mixed_audio)
                
                print(f"[Editor] BGM 混音完成 (音量: {bgm_volume})")
            except Exception as e:
                print(f"[Editor Warning] BGM 混音失败: {e}，继续无 BGM 导出")
        
        # 导出视频
        print(f"[Editor] 正在导出视频: {output_path}")
        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="medium",
            threads=4,
            logger=None  # 减少日志输出
        )
        
        # 清理资源
        final_clip.close()
        for clip in clips:
            clip.close()
        
        print(f"[Editor] 视频导出成功: {output_path} (总时长: {total_duration:.2f}s)")
        
        # 自动生成 SRT 字幕文件
        srt_path = None
        if scenes:
            srt_path = output_path.rsplit('.', 1)[0] + '.srt'
            generate_srt(scenes, audio_paths, srt_path)
        
        # 上传到 OSS（按主题分类）
        video_url = output_path
        srt_url = srt_path
        if topic:
            oss_video_url = upload_file_to_oss_by_topic(output_path, topic, "video")
            if oss_video_url:
                video_url = oss_video_url
            if srt_path and os.path.exists(srt_path):
                oss_srt_url = upload_file_to_oss_by_topic(srt_path, topic, "video")
                if oss_srt_url:
                    srt_url = oss_srt_url
        
        return video_url
        
    except Exception as e:
        print(f"[Editor Error] 视频导出失败: {e}")
        return None


def get_audio_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    from moviepy import AudioFileClip
    
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        audio.close()
        return duration
    except Exception as e:
        print(f"[Editor Error] 获取音频时长失败: {e}")
        return 0.0


def get_total_duration(audio_paths: list) -> float:
    """计算所有音频的总时长"""
    total = 0.0
    for path in audio_paths:
        if path and os.path.exists(path):
            total += get_audio_duration(path)
    return total


def _format_srt_time(seconds: float) -> str:
    """将秒数转换为 SRT 时间格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(scenes: list, audio_paths: list, output_path: str = None, topic: str = None) -> Optional[str]:
    """
    根据分镜和音频时长生成 SRT 字幕文件
    
    Args:
        scenes: 分镜列表，每个元素需包含 'narration' 字段
        audio_paths: 音频路径列表（用于计算时间轴）
        output_path: 输出路径，为空则自动生成
        topic: 主题名称（用于文件命名）
    
    Returns:
        SRT 文件路径，失败返回 None
    """
    if not scenes or not audio_paths:
        print("[SRT] 缺少分镜或音频数据")
        return None
    
    if not output_path:
        if topic:
            output_dir = get_unique_dir(DEFAULT_OUTPUT_DIR, topic)
            safe_topic = sanitize_filename(topic)
            output_path = str(output_dir / f"{safe_topic}.srt")
        else:
            output_path = str(DEFAULT_OUTPUT_DIR / "output.srt")
    
    srt_lines = []
    current_time = 0.0
    subtitle_index = 1
    
    for i, (scene, aud_path) in enumerate(zip(scenes, audio_paths)):
        # 获取该段音频时长
        if aud_path and os.path.exists(aud_path):
            duration = get_audio_duration(aud_path)
        else:
            duration = 3.0  # 默认 3 秒
        
        # 获取字幕文本
        narration = scene.get('narration', '')
        if not narration:
            current_time += duration
            continue
        
        # 计算时间戳
        start_time = current_time
        end_time = current_time + duration
        
        # 写入 SRT 格式
        srt_lines.append(str(subtitle_index))
        srt_lines.append(f"{_format_srt_time(start_time)} --> {_format_srt_time(end_time)}")
        srt_lines.append(narration)
        srt_lines.append("")  # 空行分隔
        
        subtitle_index += 1
        current_time = end_time
    
    if not srt_lines:
        print("[SRT] 无有效字幕内容")
        return None
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))
        print(f"[SRT] 字幕文件生成成功: {output_path}")
        return output_path
    except Exception as e:
        print(f"[SRT Error] 字幕文件生成失败: {e}")
        return None

