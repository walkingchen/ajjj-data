#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据~/Downloads/ajjj/文件夹下视频文件大小判断，
如果小于5M，则删除项目下output/transcript/和output/analysis/文件夹下对应的文件
"""

import os
import argparse

def get_video_files(dir_path):
    """
    遍历目录，返回所有mp4文件的绝对路径和大小信息
    """
    video_files = []
    min_size_mb = 5  # 最小文件大小（MB）
    min_size_bytes = min_size_mb * 1024 * 1024  # 转换为字节
    
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith('.mp4'):
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    video_files.append({
                        'path': file_path,
                        'size_bytes': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'filename': os.path.basename(file_path)
                    })
                except OSError as e:
                    print(f"无法获取文件大小: {file_path}, 错误: {e}")
    return video_files

def delete_output_files(video_filename, output_dirs):
    """
    删除指定视频文件对应的输出文件
    """
    base_name = os.path.splitext(video_filename)[0]
    deleted_files = []
    
    for output_dir in output_dirs:
        if os.path.exists(output_dir):
            # 查找对应的输出文件
            for file in os.listdir(output_dir):
                if file.startswith(base_name):
                    file_path = os.path.join(output_dir, file)
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                        print(f"已删除: {file_path}")
                    except OSError as e:
                        print(f"删除失败: {file_path}, 错误: {e}")
    
    return deleted_files

def main():
    parser = argparse.ArgumentParser(description='根据视频文件大小过滤输出文件')
    parser.add_argument('-d', '--dry-run', action='store_true', help='仅显示将要删除的文件，不实际删除')
    args = parser.parse_args()
    
    # 配置路径
    video_dir = os.path.expanduser('~/Downloads/ajjj/')
    output_dirs = [
        os.path.join('output', 'transcript'),
        os.path.join('output', 'analysis')
    ]
    
    print(f"扫描视频目录: {video_dir}")
    video_files = get_video_files(video_dir)
    
    if not video_files:
        print("未找到任何mp4文件")
        return
    
    print(f"共找到 {len(video_files)} 个mp4文件")
    
    # 统计信息
    small_files = []
    large_files = []
    
    for video in video_files:
        if video['size_mb'] < 5:
            small_files.append(video)
        else:
            large_files.append(video)
    
    print(f"\n文件大小统计:")
    print(f"小于5MB的文件: {len(small_files)} 个")
    print(f"大于等于5MB的文件: {len(large_files)} 个")
    
    if not small_files:
        print("没有小于5MB的文件需要处理")
        return
    
    print(f"\n小于5MB的文件列表:")
    for video in small_files:
        print(f"  {video['filename']} ({video['size_mb']:.1f}MB)")
    
    # 删除对应的输出文件
    total_deleted = 0
    
    for video in small_files:
        print(f"\n处理文件: {video['filename']} ({video['size_mb']:.1f}MB)")
        
        if args.dry_run:
            # 仅显示将要删除的文件
            base_name = os.path.splitext(video['filename'])[0]
            for output_dir in output_dirs:
                if os.path.exists(output_dir):
                    for file in os.listdir(output_dir):
                        if file.startswith(base_name):
                            file_path = os.path.join(output_dir, file)
                            print(f"将要删除: {file_path}")
        else:
            # 实际删除文件
            deleted_files = delete_output_files(video['filename'], output_dirs)
            total_deleted += len(deleted_files)
    
    if args.dry_run:
        print(f"\n[DRY RUN] 将删除 {total_deleted} 个输出文件")
    else:
        print(f"\n实际删除了 {total_deleted} 个输出文件")

if __name__ == '__main__':
    main()
