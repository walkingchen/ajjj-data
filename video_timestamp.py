#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据ads_summary.csv中的广告信息，查找商品名称或广告文本在视频中的出现时间
"""

import pandas as pd
import json
import os
import re
from typing import List, Dict, Tuple

def load_ads_summary(csv_path: str) -> pd.DataFrame:
    """
    加载ads_summary.csv文件
    """
    if not os.path.exists(csv_path):
        print(f"错误: 文件不存在 {csv_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        print(f"成功加载 {len(df)} 条记录")
        
        # 检查是否有发布时间列
        if '发布时间' not in df.columns:
            print("警告: CSV文件中没有发布时间列")
            df['发布时间'] = ''
        
        return df
    except Exception as e:
        print(f"加载CSV文件失败: {e}")
        return None

def load_transcript(transcript_path: str) -> Dict:
    """
    加载transcript JSON文件
    """
    if not os.path.exists(transcript_path):
        print(f"警告: transcript文件不存在 {transcript_path}")
        return None
    
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载transcript文件失败 {transcript_path}: {e}")
        return None

def find_text_timestamps(transcript_data: Dict, search_texts: List[str]) -> List[str]:
    """
    在transcript中查找指定文本的出现时间
    """
    timestamps = []
    segments = transcript_data.get('segments', [])
    
    for segment in segments:
        segment_text = segment.get('text', '').lower()
        start_time = segment.get('start', 0)
        
        for search_text in search_texts:
            search_text_lower = search_text.lower()
            if search_text_lower in segment_text:
                # 格式化时间为 MM:SS
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                timestamp = f"{minutes:02d}:{seconds:02d}"
                timestamps.append(timestamp)
                break  # 找到就跳出内层循环，避免重复
    
    return list(set(timestamps))  # 去重

def format_time(seconds: float) -> str:
    """
    将秒数转换为 MM:SS 格式
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def process_video_timestamps(row: pd.Series, transcript_dir: str) -> str:
    """
    处理单个视频的时间戳查找
    """
    filename = row['文件名']
    is_ad = row['是否包含广告']
    
    # 如果不是广告，返回空
    if not is_ad or (isinstance(is_ad, str) and is_ad.lower() != 'true'):
        return ''
    
    # 构建transcript文件路径
    base_name = os.path.splitext(filename)[0]
    transcript_filename = f"{base_name}.json"
    transcript_path = os.path.join(transcript_dir, transcript_filename)
    
    # 加载transcript数据
    transcript_data = load_transcript(transcript_path)
    if not transcript_data:
        return ''
    
    # 确定搜索文本
    search_texts = []
    
    # 1. 优先使用商品名称
    product_name = row.get('商品名称', '')
    # 处理NaN值
    if pd.isna(product_name):
        product_name = ''
    else:
        product_name = str(product_name)
    
    if product_name and product_name.strip():
        # 分割商品名称（可能包含多个商品）
        products = [p.strip() for p in product_name.split('、') if p.strip()]
        search_texts.extend(products)
    
    # 2. 如果商品名称为空，使用广告文本
    if not search_texts:
        ad_text = row.get('广告文本', '')
        # 处理NaN值
        if pd.isna(ad_text):
            ad_text = ''
        else:
            ad_text = str(ad_text)
        
        if ad_text and ad_text.strip():
            # 分割广告文本（可能包含多个句子）
            sentences = [s.strip() for s in ad_text.split('。') if s.strip()]
            search_texts.extend(sentences)
    
    if not search_texts:
        print(f"警告: {filename} 没有可搜索的文本")
        return ''
    
    # 查找时间戳
    timestamps = find_text_timestamps(transcript_data, search_texts)
    
    if timestamps:
        return '; '.join(sorted(timestamps))
    else:
        print(f"警告: {filename} 未找到匹配的时间戳")
        return ''

def main():
    # 配置路径
    csv_path = os.path.join('output', 'ads_summary.csv')
    transcript_dir = os.path.join('output', 'transcript')
    
    print("开始处理视频时间戳...")
    
    # 加载CSV文件
    df = load_ads_summary(csv_path)
    if df is None:
        return
    
    # 检查必要的列是否存在
    required_columns = ['文件名', '是否包含广告', '商品名称', '广告文本']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"错误: CSV文件缺少必要的列: {missing_columns}")
        return
    
    # 添加ads_time列（如果不存在）
    if 'ads_time' not in df.columns:
        df['ads_time'] = ''
    
    # 处理每个包含广告的视频
    ad_count = 0
    processed_count = 0
    
    for index, row in df.iterrows():
        is_ad = row['是否包含广告']
        
        # 检查是否为广告
        if is_ad and (isinstance(is_ad, bool) or (isinstance(is_ad, str) and is_ad.lower() == 'true')):
            ad_count += 1
            print(f"\n处理广告视频 {ad_count}: {row['文件名']}")
            
            # 查找时间戳
            timestamps = process_video_timestamps(row, transcript_dir)
            
            # 更新DataFrame
            df.at[index, 'ads_time'] = timestamps
            
            if timestamps:
                processed_count += 1
                print(f"找到时间戳: {timestamps}")
            else:
                print("未找到时间戳")
    
    # 保存更新后的CSV文件
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n处理完成!")
        print(f"总广告视频数: {ad_count}")
        print(f"成功找到时间戳的视频数: {processed_count}")
        print(f"更新后的文件已保存到: {csv_path}")
    except Exception as e:
        print(f"保存CSV文件失败: {e}")

if __name__ == '__main__':
    main()
