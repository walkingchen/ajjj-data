import os
from pathlib import Path
import subprocess
import whisper
import json
import argparse
import requests
import pandas as pd
import re

# 指定视频目录
VIDEO_DIR = os.path.expanduser('~/Downloads/ajjj/')


def get_video_files(dir_path):
    """
    遍历目录，返回所有mp4文件的绝对路径（过滤5MB以下的文件）
    """
    video_files = []
    min_size_mb = 5  # 最小文件大小（MB）
    min_size_bytes = min_size_mb * 1024 * 1024  # 转换为字节
    
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith('.mp4'):
                file_path = os.path.join(root, file)
                # 检查文件大小
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size >= min_size_bytes:
                        video_files.append(file_path)
                    else:
                        print(f"跳过小文件 ({file_size / (1024*1024):.1f}MB): {file_path}")
                except OSError as e:
                    print(f"无法获取文件大小: {file_path}, 错误: {e}")
    return video_files


OUTPUT_AUDIO_DIR = os.path.join('output', 'audio')
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

def extract_audio(video_path, audio_path):
    """
    使用ffmpeg提取音频为16kHz单声道wav
    """
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取音频失败: {video_path}\n错误: {e}")
        return False


def transcribe_audio(audio_path, transcript_path, model_name="base"):
    """
    使用whisper将音频转为带时间戳的中文文本，保存为json
    """
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, language='zh')
    # 保存转写结果
    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

OUTPUT_TRANSCRIPT_DIR = os.path.join('output', 'transcript')
os.makedirs(OUTPUT_TRANSCRIPT_DIR, exist_ok=True)


def analyze_text_with_ollama(text, timestamps, model_name="qwen2:7b-instruct"):
    """
    使用Ollama分析文本，判断是否包含广告及商品信息
    """
    prompt = f"""
    你是一位专精于社交媒体内容剖析的中文广告识别专家。请你仔细分析以下文字，判断其是否通过日常生活记录或个人分享的方式，隐晦地植入了商品或品牌的宣传信息，即使没有任何推荐语、营销语或购买引导。

请特别关注以下类型的内容：
- 作者是否在介绍某项活动（如拍摄、运动、学习、日常生活等）时顺带提及某个具体品牌或产品；
- 是否描述了某个商品的使用体验、效果或性能，即使是以客观中性的口吻；
- 是否通过展示个人生活方式（如摄影设备、学习工具、家居用品等）间接地提升某个商品的曝光度；
- 是否出现可能引起观众兴趣或模仿欲望的物品描述；
- 是否有在不必要场景下提及产品的情况；
- 部分文本可能由英语歌词转换而来，需要注意排除；

即使没有推荐、购买、优惠等引导语，只要内容中出现真实商品、使用描述或可能对观众产生影响，都应视为潜在软广。

内容如下：
{text}

请以JSON格式返回结果，包含以下字段：
- is_ad: 是否包含广告（true/false）
- ad_type: 广告类型（硬广/软广/无）
- product_name: 商品名称（如有）
- ad_text: 广告文本片段（如有）
- confidence: 置信度（0-1）
- timestamp: 时间戳（如有）

只返回JSON格式结果，不要其他文字。"""

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model_name,
                'prompt': prompt,
                'stream': False
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        return result['response']
    except Exception as e:
        print(f"Ollama调用失败: {e}")
        return None

OUTPUT_ANALYSIS_DIR = os.path.join('output', 'analysis')
os.makedirs(OUTPUT_ANALYSIS_DIR, exist_ok=True)

def analyze_transcript(transcript_path, analysis_path):
    """
    分析转写文本，判断广告信息
    """
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    # 获取转写文本
    text = transcript_data.get('text', '')
    segments = transcript_data.get('segments', [])
    
    # 分析整个文本
    analysis_result = analyze_text_with_ollama(text, segments)
    
    # 保存分析结果
    result = {
        'transcript_path': transcript_path,
        'analysis_result': analysis_result,
        'segments': segments
    }
    
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result


def parse_args():
    parser = argparse.ArgumentParser(description='解析视频文件中的广告')
    parser.add_argument('-f', '--force', action='store_true', help='强制覆盖已存在的输出文件')
    return parser.parse_args()


def main():
    args = parse_args()
    video_files = get_video_files(VIDEO_DIR)
    print(f"共找到 {len(video_files)} 个mp4视频文件：")

    print("\n开始提取音频...")
    for video_path in video_files:
        audio_filename = os.path.splitext(os.path.basename(video_path))[0] + '.wav'
        audio_path = os.path.join(OUTPUT_AUDIO_DIR, audio_filename)
        
        # 检查是否已存在音频文件
        if os.path.exists(audio_path) and not args.force:
            print(f"音频文件已存在，跳过: {audio_path}")
            continue
            
        success = extract_audio(video_path, audio_path)
        if success:
            print(f"音频提取成功: {audio_path}")
        else:
            print(f"音频提取失败: {video_path}")

    print("\n开始音频转写...")
    for video_path in video_files:
        audio_filename = os.path.splitext(os.path.basename(video_path))[0] + '.wav'
        audio_path = os.path.join(OUTPUT_AUDIO_DIR, audio_filename)
        transcript_filename = os.path.splitext(os.path.basename(video_path))[0] + '.json'
        transcript_path = os.path.join(OUTPUT_TRANSCRIPT_DIR, transcript_filename)
        
        if not os.path.exists(audio_path):
            print(f"音频文件不存在，跳过: {audio_path}")
            continue
            
        # 检查是否已存在转写文件
        if os.path.exists(transcript_path) and not args.force:
            print(f"转写文件已存在，跳过: {transcript_path}")
            continue
            
        print(f"转写: {audio_path}")
        try:
            transcribe_audio(audio_path, transcript_path)
            print(f"转写完成: {transcript_path}")
        except Exception as e:
            print(f"转写失败: {audio_path}\n错误: {e}")

    print("\n开始广告分析...")
    for video_path in video_files:
        transcript_filename = os.path.splitext(os.path.basename(video_path))[0] + '.json'
        transcript_path = os.path.join(OUTPUT_TRANSCRIPT_DIR, transcript_filename)
        analysis_filename = os.path.splitext(os.path.basename(video_path))[0] + '_analysis.json'
        analysis_path = os.path.join(OUTPUT_ANALYSIS_DIR, analysis_filename)
        
        if not os.path.exists(transcript_path):
            print(f"转写文件不存在，跳过: {transcript_path}")
            continue
        
        # 检查是否需要执行分析
        should_analyze = True
        if os.path.exists(analysis_path) and not args.force:
            try:
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                # 检查analysis_result字段是否存在且不为null
                analysis_result = analysis_data.get('analysis_result')
                if analysis_result is not None and analysis_result.strip():
                    print(f"分析文件已存在且有效，跳过: {analysis_path}")
                    should_analyze = False
                else:
                    print(f"分析文件存在但结果为空，重新分析: {analysis_path}")
            except Exception as e:
                print(f"读取分析文件失败，重新分析: {analysis_path}\n错误: {e}")
        
        if should_analyze:
            print(f"分析: {transcript_path}")
            try:
                analyze_transcript(transcript_path, analysis_path)
                print(f"分析完成: {analysis_path}")
            except Exception as e:
                print(f"分析失败: {transcript_path}\n错误: {e}")

    # 汇总统计
    print("\n开始汇总统计...")
    summarize_results(video_files)


def parse_ollama_response(response_text):
    """
    解析Ollama返回的JSON格式响应
    """
    try:
        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            # 修复数组末尾多余的逗号
            json_str = re.sub(r',\s*\]', ']', json_str)
            json_str = re.sub(r',\s*}', '}', json_str)
            return json.loads(json_str)
        else:
            # 如果没有找到JSON，返回默认值
            return {
                'is_ad': False,
                'ad_type': '无',
                'product_name': '',
                'ad_text': '',
                'confidence': 0.0,
                'timestamp': ''
            }
    except Exception as e:
        print(f"解析Ollama响应失败: {e}")
        print(f"响应文本: {response_text}")
        return {
            'is_ad': False,
            'ad_type': '无',
            'product_name': '',
            'ad_text': '',
            'confidence': 0.0,
            'timestamp': ''
        }

def load_publish_dates():
    """
    加载发布时间数据
    """
    published_path = os.path.join('output', 'published.json')
    if not os.path.exists(published_path):
        print("警告: 发布时间文件不存在，将使用空值")
        return {}
    
    try:
        with open(published_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"读取发布时间文件失败: {e}")
        return {}

def get_publish_date(filename, publish_dates):
    """
    获取视频发布时间
    """
    for video_id, info in publish_dates.items():
        if info.get('filename') == filename:
            return info.get('publish_date', '')
    return ''

def update_analysis_with_publish_date(analysis_path, publish_date):
    """
    更新分析文件，添加发布时间信息
    """
    try:
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 添加发布时间信息
        analysis_data['publish_date'] = publish_date
        
        # 保存更新后的文件
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"更新分析文件失败 {analysis_path}: {e}")
        return False

def summarize_results(video_files):
    """
    汇总所有分析结果，输出为CSV
    """
    results = []
    
    # 加载发布时间数据
    publish_dates = load_publish_dates()
    
    for video_path in video_files:
        analysis_filename = os.path.splitext(os.path.basename(video_path))[0] + '_analysis.json'
        analysis_path = os.path.join(OUTPUT_ANALYSIS_DIR, analysis_filename)
        
        if not os.path.exists(analysis_path):
            continue
            
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # 解析Ollama响应
            ollama_response = analysis_data.get('analysis_result', '')
            parsed_result = parse_ollama_response(ollama_response)
            
            # 提取视频文件名（不含路径）
            video_filename = os.path.basename(video_path)
            
            # 获取发布时间
            publish_date = get_publish_date(video_filename, publish_dates)
            
            # 更新分析文件，添加发布时间
            if publish_date:
                update_analysis_with_publish_date(analysis_path, publish_date)
                print(f"已更新发布时间: {video_filename} -> {publish_date}")
            
            # 添加到结果列表
            results.append({
                '文件名': video_filename,
                '发布时间': publish_date,
                '是否包含广告': parsed_result.get('is_ad', False),
                '广告类型': parsed_result.get('ad_type', '无'),
                '商品名称': parsed_result.get('product_name', ''),
                '广告文本': parsed_result.get('ad_text', ''),
                '置信度': parsed_result.get('confidence', 0.0),
                '时间戳': parsed_result.get('timestamp', ''),
                '原始响应': ollama_response
            })
            
        except Exception as e:
            print(f"处理分析文件失败: {analysis_path}\n错误: {e}")
    
    # 创建DataFrame并保存为CSV
    if results:
        df = pd.DataFrame(results)
        output_csv = os.path.join('output', 'ads_summary.csv')
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\n汇总完成，结果保存到: {output_csv}")
        print(f"共分析 {len(results)} 个文件")
        
        # 统计广告数量
        ad_count = df[df['是否包含广告'] == True].shape[0]
        print(f"其中包含广告的文件: {ad_count} 个")
        
        return df
    else:
        print("没有找到任何分析结果")
        return None

if __name__ == '__main__':
    main()
