#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据视频ID抓取B站发布时间
"""

import requests
import json
import os
import re
import time
from typing import Dict, List

def extract_bilibili_id(filename):
    """
    从文件名中提取B站视频ID
    """
    bv_pattern = r'\[(BV[a-zA-Z0-9]+)\]'
    av_pattern = r'\[(av\d+)\]'
    
    bv_match = re.search(bv_pattern, filename)
    if bv_match:
        return bv_match.group(1)
    
    av_match = re.search(av_pattern, filename)
    if av_match:
        return av_match.group(1)
    
    return None

def get_video_info(video_id):
    """
    获取B站视频信息
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com'
    }
    
    try:
        # B站API接口
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={video_id}"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data['code'] == 0:
            return data['data']
        else:
            print(f"API返回错误: {data['message']}")
            return None
            
    except Exception as e:
        print(f"获取视频信息失败 {video_id}: {e}")
        return None

def main():
    """
    主函数
    """
    csv_path = os.path.join('output', 'ads_summary.csv')
    published_path = os.path.join('output', 'published.json')
    
    if not os.path.exists(csv_path):
        print(f"错误: 文件不存在 {csv_path}")
        return
    
    # 读取CSV文件
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        print(f"成功加载 {len(df)} 条记录")
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return
    
    # 提取所有B站ID
    video_ids = {}
    for index, row in df.iterrows():
        filename = row['文件名']
        bilibili_id = extract_bilibili_id(filename)
        if bilibili_id:
            video_ids[bilibili_id] = filename
    
    print(f"找到 {len(video_ids)} 个B站视频ID")
    
    # 获取发布时间
    publish_dates = {}
    success_count = 0
    
    for video_id, filename in video_ids.items():
        print(f"获取视频信息: {video_id} ({filename})")
        
        video_info = get_video_info(video_id)
        if video_info:
            publish_time = video_info.get('pubdate', 0)
            if publish_time > 0:
                # 转换为可读格式
                from datetime import datetime
                publish_date = datetime.fromtimestamp(publish_time).strftime('%Y-%m-%d')
                publish_dates[video_id] = {
                    'filename': filename,
                    'publish_date': publish_date,
                    'title': video_info.get('title', ''),
                    'duration': video_info.get('duration', 0)
                }
                success_count += 1
                print(f"  ✓ 发布时间: {publish_date}")
            else:
                print(f"  ✗ 无法获取发布时间")
        else:
            print(f"  ✗ 获取视频信息失败")
        
        # 添加延迟避免请求过快
        time.sleep(1)
    
    # 保存结果
    try:
        with open(published_path, 'w', encoding='utf-8') as f:
            json.dump(publish_dates, f, ensure_ascii=False, indent=2)
        
        print(f"\n抓取完成!")
        print(f"成功获取: {success_count} 个视频的发布时间")
        print(f"结果保存到: {published_path}")
        
    except Exception as e:
        print(f"保存文件失败: {e}")

if __name__ == '__main__':
    main() 