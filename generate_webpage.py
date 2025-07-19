#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成广告数据展示网页
"""

import pandas as pd
import re
import os
from datetime import datetime

def extract_bilibili_id(filename):
    """
    从文件名中提取B站视频ID
    格式: [BV1xx4y1x7xx] 或其他B站ID格式
    """
    # 匹配B站视频ID格式
    bv_pattern = r'\[(BV[a-zA-Z0-9]+)\]'
    av_pattern = r'\[(av\d+)\]'
    
    bv_match = re.search(bv_pattern, filename)
    if bv_match:
        return bv_match.group(1)
    
    av_match = re.search(av_pattern, filename)
    if av_match:
        return av_match.group(1)
    
    return None

def generate_bilibili_url(video_id, timestamp=None):
    """
    生成B站视频链接
    """
    if not video_id:
        return None
    
    base_url = f"https://www.bilibili.com/video/{video_id}"
    
    if timestamp:
        # 将 MM:SS 格式转换为秒数
        try:
            parts = timestamp.split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                total_seconds = minutes * 60 + seconds
                return f"{base_url}?t={total_seconds}"
        except:
            pass
    
    return base_url

def format_timestamp(timestamp_str):
    """
    格式化时间戳显示
    """
    if not timestamp_str or pd.isna(timestamp_str) or str(timestamp_str).strip() == '':
        return "/"
    
    timestamps = str(timestamp_str).split('; ')
    formatted = []
    for ts in timestamps:
        if ts.strip():
            formatted.append(ts.strip())
    
    return '; '.join(formatted) if formatted else "/"

def generate_bilibili_url_with_time(video_id, timestamp):
    """
    生成带时间戳的B站视频链接
    """
    if not video_id:
        return None
    
    base_url = f"https://www.bilibili.com/video/{video_id}"
    
    if timestamp and timestamp != "/":
        # 将 MM:SS 格式转换为秒数
        try:
            parts = timestamp.split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                total_seconds = minutes * 60 + seconds
                return f"{base_url}?t={total_seconds}"
        except:
            pass
    
    return base_url

def format_timestamps_with_links(timestamp_str, bilibili_id):
    """
    格式化时间戳，为每个时间生成独立的链接
    """
    if not timestamp_str or pd.isna(timestamp_str) or str(timestamp_str).strip() == '':
        return '<span class="time-text">/</span>'
    
    timestamps = str(timestamp_str).split('; ')
    formatted_links = []
    
    for ts in timestamps:
        if ts.strip():
            if bilibili_id:
                time_url = generate_bilibili_url_with_time(bilibili_id, ts.strip())
                if time_url:
                    formatted_links.append(f'<a href="{time_url}" target="_blank" class="time-link">{ts.strip()}</a>')
                else:
                    formatted_links.append(f'<span class="time-text">{ts.strip()}</span>')
            else:
                formatted_links.append(f'<span class="time-text">{ts.strip()}</span>')
    
    if formatted_links:
        return '<br>'.join(formatted_links)
    else:
        return '<span class="time-text">/</span>'

def count_brand_videos(df):
    """
    统计品牌识别视频数量（商品名称不为空的视频）
    """
    brand_count = 0
    for _, row in df.iterrows():
        product_name = row.get('商品名称', '')
        
        # 转换为字符串并去除空格
        if pd.isna(product_name):
            product_name = ''
        else:
            product_name = str(product_name).strip()
        
        # 排除空值、nan、'无'、'未识别'等无效值
        if (product_name and 
            product_name != 'nan' and 
            product_name != '无' and 
            product_name != '未识别' and
            product_name != '无特定产品名称'):
            brand_count += 1
    return brand_count

def generate_html(df):
    """
    生成HTML页面
    """
    # 过滤包含广告的视频
    ad_videos = df[df['是否包含广告'] == True].copy()
    
    # 计算统计数据
    total_videos = len(df)
    ad_videos_count = len(ad_videos)
    brand_videos_count = count_brand_videos(df)
    soft_ad_videos_count = ad_videos_count - brand_videos_count  # 疑似软广视频 - 品牌识别视频
    
    if len(ad_videos) == 0:
        html_content = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    margin: 0; 
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .no-data { 
                    text-align: center; 
                    color: #666; 
                    font-size: 18px;
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    backdrop-filter: blur(10px);
                }
            </style>
        </head>
        <body>
            <div class="no-data">暂无广告数据</div>
        </body>
        </html>
        """
        return html_content
    
    # 生成表格行
    table_rows = ""
    for index, row in ad_videos.iterrows():
        filename = row['文件名']
        product_name = row['商品名称'] if not pd.isna(row['商品名称']) else ''
        ad_text = row['广告文本'] if not pd.isna(row['广告文本']) else ''
        confidence = row['置信度'] if not pd.isna(row['置信度']) else 0
        ads_time = format_timestamp(row.get('ads_time', ''))
        publish_date = row.get('发布时间', '') # 新增发布时间列
        
        # 提取B站ID
        bilibili_id = extract_bilibili_id(filename)
        
        # 生成视频链接
        video_url = generate_bilibili_url(bilibili_id, ads_time) if bilibili_id else None
        
        # 处理商品名称显示
        product_display = product_name if product_name else "未识别"
        
        # 处理广告文本显示（截取前50字符）
        ad_text_display = ad_text[:50] + "..." if len(ad_text) > 50 else ad_text
        
        # 生成时间链接
        time_links = format_timestamps_with_links(ads_time, bilibili_id)
        
        # 生成行HTML
        row_html = f"""
        <tr>
            <td class="filename-cell">{filename}</td>
            <td class="publish-cell">{publish_date}</td>
            <td class="product-cell">{product_display}</td>
            <td class="text-cell" title="{ad_text}">{ad_text_display}</td>
            <td class="confidence-cell">{confidence:.2f}</td>
            <td class="time-cell">{time_links}</td>
            <td class="link-cell">
        """
        
        if video_url:
            row_html += f'<a href="{video_url}" target="_blank" class="video-btn">观看视频</a>'
        else:
            row_html += '<span class="no-link">无法生成链接</span>'
        
        row_html += "</td></tr>"
        table_rows += row_html
    
    # 生成完整HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            
            .header .subtitle {{
                font-size: 1.1rem;
                opacity: 0.9;
                font-weight: 300;
            }}
            
            .stats {{
                padding: 25px 30px;
                margin: 0;
            }}
            
            .stats-content {{
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                gap: 20px;
            }}
            
            .stat-item {{
                text-align: center;
                flex: 1;
                min-width: 150px;
            }}
            
            .stat-number {{
                font-size: 2rem;
                font-weight: 700;
                display: block;
            }}
            
            .stat-label {{
                font-size: 0.9rem;
                opacity: 0.9;
                margin-top: 5px;
            }}
            
            .filter-section {{
                background: #f8f9fa;
                padding: 20px 30px;
                border-bottom: 1px solid #e9ecef;
            }}
            
            .filter-row {{
                display: flex;
                gap: 20px;
                align-items: center;
                flex-wrap: wrap;
            }}
            
            .filter-group {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .filter-label {{
                font-weight: 500;
                color: #495057;
                font-size: 0.9rem;
            }}
            
            .filter-input {{
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 0.9rem;
                min-width: 120px;
            }}
            
            .filter-select {{
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 0.9rem;
                background: white;
            }}
            
            .filter-btn {{
                padding: 8px 16px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.3s ease;
            }}
            
            .filter-btn:hover {{
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }}
            
            .sortable {{
                cursor: pointer;
                position: relative;
                user-select: none;
            }}
            
            .sortable:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
            
            .sortable::after {{
                content: '↕';
                position: absolute;
                right: 8px;
                opacity: 0.7;
                font-size: 12px;
            }}
            
            .sortable.asc::after {{
                content: '↑';
                opacity: 1;
            }}
            
            .sortable.desc::after {{
                content: '↓';
                opacity: 1;
            }}
            
            .table-container {{
                padding: 30px;
                overflow-x: auto;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}
            
            th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 18px 15px;
                font-weight: 600;
                font-size: 0.95rem;
                text-align: left;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            
            td {{
                padding: 16px 15px;
                border-bottom: 1px solid #f0f0f0;
                vertical-align: top;
            }}
            
            tr:hover {{
                background: linear-gradient(135deg, #f8f9ff 0%, #f0f2ff 100%);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }}
            
            .filename-cell {{
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.9rem;
                color: #555;
                max-width: 300px;
                min-width: 250px;
                word-break: break-all;
            }}
            
            .publish-cell {{
                font-size: 0.9rem;
                color: #666;
                text-align: center;
                max-width: 100px;
                min-width: 80px;
            }}
            
            .product-cell {{
                font-weight: 500;
                color: #2c3e50;
                max-width: 150px;
                min-width: 120px;
            }}
            
            .text-cell {{
                max-width: 400px;
                min-width: 300px;
                line-height: 1.5;
                color: #666;
            }}
            
            .confidence-cell {{
                font-weight: 600;
                text-align: center;
            }}
            
            .time-cell {{
                text-align: center;
            }}
            
            .time-link {{
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 6px;
                background: rgba(102, 126, 234, 0.1);
                transition: all 0.3s ease;
            }}
            
            .time-link:hover {{
                background: rgba(102, 126, 234, 0.2);
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
            }}
            
            .time-text {{
                color: #999;
                font-style: italic;
            }}
            
            .video-btn {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 500;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }}
            
            .video-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }}
            
            .no-link {{
                color: #999;
                font-style: italic;
            }}
            
            .confidence-high {{
                color: #27ae60;
                background: rgba(39, 174, 96, 0.1);
                padding: 4px 8px;
                border-radius: 6px;
            }}
            
            .confidence-medium {{
                color: #f39c12;
                background: rgba(243, 156, 18, 0.1);
                padding: 4px 8px;
                border-radius: 6px;
            }}
            
            .confidence-low {{
                color: #e74c3c;
                background: rgba(231, 76, 60, 0.1);
                padding: 4px 8px;
                border-radius: 6px;
            }}
            
            .hidden {{
                display: none !important;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    margin: 10px;
                    border-radius: 15px;
                }}
                
                .header {{
                    padding: 30px 20px;
                }}
                
                .header h1 {{
                    font-size: 2rem;
                }}
                
                .table-container {{
                    padding: 20px;
                }}
                
                th, td {{
                    padding: 12px 10px;
                    font-size: 0.9rem;
                }}
                
                .stats-content {{
                    flex-direction: column;
                    gap: 15px;
                }}
                
                .filter-row {{
                    flex-direction: column;
                    align-items: stretch;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="stats">
                <div class="stats-content">
                    <div class="stat-item">
                        <span class="stat-number">{total_videos}</span>
                        <div class="stat-label">视频总计</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{brand_videos_count}</span>
                        <div class="stat-label">品牌识别视频</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{soft_ad_videos_count}</span>
                        <div class="stat-label">疑似软广视频</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{datetime.now().strftime('%m-%d')}</span>
                        <div class="stat-label">更新日期</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{datetime.now().strftime('%H:%M')}</span>
                        <div class="stat-label">更新时间</div>
                    </div>
                </div>
            </div>
            
            <div class="filter-section">
                <div class="filter-row">
                    <div class="filter-group">
                        <label class="filter-label">文件名:</label>
                        <input type="text" id="filenameFilter" class="filter-input" placeholder="搜索文件名...">
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">商品名称:</label>
                        <input type="text" id="productFilter" class="filter-input" placeholder="搜索商品...">
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">置信度:</label>
                        <select id="confidenceFilter" class="filter-select">
                            <option value="">全部</option>
                            <option value="high">高 (≥0.8)</option>
                            <option value="medium">中 (0.6-0.8)</option>
                            <option value="low">低 (<0.6)</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">发布时间:</label>
                        <input type="text" id="publishFilter" class="filter-input" placeholder="YYYY-MM-DD">
                    </div>
                    <button onclick="clearFilters()" class="filter-btn">清除过滤</button>
                </div>
            </div>
            
            <div class="table-container">
                <table id="dataTable">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="filename">📁 文件名</th>
                            <th class="sortable" data-sort="publish_date">📅 发布时间</th>
                            <th class="sortable" data-sort="product_name">🛍️ 商品名称</th>
                            <th class="sortable" data-sort="ad_text">📝 广告文本</th>
                            <th class="sortable" data-sort="confidence">🎯 置信度</th>
                            <th class="sortable" data-sort="ads_time">⏰ 广告时间</th>
                            <th class="sortable" data-sort="video_url">🔗 视频链接</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            let currentSort = {{
                column: null,
                direction: 'asc'
            }};
            
            // 排序功能
            function sortTable(column) {{
                const table = document.getElementById('dataTable');
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr:not(.hidden)'));
                
                // 清除之前的排序状态
                document.querySelectorAll('.sortable').forEach(th => {{
                    th.classList.remove('asc', 'desc');
                }});
                
                // 设置新的排序状态
                const header = document.querySelector(`[data-sort="${{column}}"]`);
                if (currentSort.column === column) {{
                    currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
                }} else {{
                    currentSort.column = column;
                    currentSort.direction = 'asc';
                }}
                
                header.classList.add(currentSort.direction);
                
                // 排序行
                rows.sort((a, b) => {{
                    let aValue = getCellValue(a, column);
                    let bValue = getCellValue(b, column);
                    
                    // 特殊处理日期排序
                    if (column === 'publish_date') {{
                        aValue = parseDate(aValue);
                        bValue = parseDate(bValue);
                    }}
                    
                    // 特殊处理置信度排序
                    if (column === 'confidence') {{
                        aValue = parseFloat(aValue) || 0;
                        bValue = parseFloat(bValue) || 0;
                    }}
                    
                    // 字符串比较
                    if (typeof aValue === 'string' && typeof bValue === 'string') {{
                        aValue = aValue.toLowerCase();
                        bValue = bValue.toLowerCase();
                    }}
                    
                    let comparison = 0;
                    if (aValue > bValue) {{
                        comparison = 1;
                    }} else if (aValue < bValue) {{
                        comparison = -1;
                    }}
                    
                    return currentSort.direction === 'asc' ? comparison : -comparison;
                }});
                
                // 重新插入排序后的行
                rows.forEach(row => {{
                    tbody.appendChild(row);
                }});
            }}
            
            function getCellValue(row, column) {{
                const columnMap = {{
                    'filename': 0,
                    'publish_date': 1,
                    'product_name': 2,
                    'ad_text': 3,
                    'confidence': 4,
                    'ads_time': 5,
                    'video_url': 6
                }};
                
                const cellIndex = columnMap[column];
                if (cellIndex !== undefined) {{
                    const cell = row.cells[cellIndex];
                    if (cell) {{
                        // 获取文本内容，去除HTML标签
                        return cell.textContent || cell.innerText || '';
                    }}
                }}
                return '';
            }}
            
            function parseDate(dateStr) {{
                if (!dateStr || dateStr === '/') return new Date(0);
                const parts = dateStr.split('-');
                if (parts.length === 3) {{
                    return new Date(parts[0], parts[1] - 1, parts[2]);
                }}
                return new Date(0);
            }}
            
            // 过滤功能
            function filterTable() {{
                const filenameFilter = document.getElementById('filenameFilter').value.toLowerCase();
                const productFilter = document.getElementById('productFilter').value.toLowerCase();
                const confidenceFilter = document.getElementById('confidenceFilter').value;
                const publishFilter = document.getElementById('publishFilter').value;
                
                const rows = document.querySelectorAll('#dataTable tbody tr');
                let visibleCount = 0;
                
                rows.forEach(row => {{
                    const filename = row.cells[0].textContent.toLowerCase();
                    const publishDate = row.cells[1].textContent;
                    const product = row.cells[2].textContent.toLowerCase();
                    const confidence = parseFloat(row.cells[4].textContent);
                    
                    let show = true;
                    
                    // 文件名过滤
                    if (filenameFilter && !filename.includes(filenameFilter)) {{
                        show = false;
                    }}
                    
                    // 商品名称过滤
                    if (productFilter && !product.includes(productFilter)) {{
                        show = false;
                    }}
                    
                    // 置信度过滤
                    if (confidenceFilter) {{
                        if (confidenceFilter === 'high' && confidence < 0.8) {{
                            show = false;
                        }} else if (confidenceFilter === 'medium' && (confidence < 0.6 || confidence >= 0.8)) {{
                            show = false;
                        }} else if (confidenceFilter === 'low' && confidence >= 0.6) {{
                            show = false;
                        }}
                    }}
                    
                    // 发布时间过滤
                    if (publishFilter && !publishDate.includes(publishFilter)) {{
                        show = false;
                    }}
                    
                    if (show) {{
                        row.classList.remove('hidden');
                        visibleCount++;
                    }} else {{
                        row.classList.add('hidden');
                    }}
                }});
                
                // 更新统计信息
                updateStats(visibleCount);
                
                // 重新应用排序
                if (currentSort.column) {{
                    sortTable(currentSort.column);
                }}
            }}
            
            function clearFilters() {{
                document.getElementById('filenameFilter').value = '';
                document.getElementById('productFilter').value = '';
                document.getElementById('confidenceFilter').value = '';
                document.getElementById('publishFilter').value = '';
                filterTable();
            }}
            
            function updateStats(visibleCount) {{
                const statNumber = document.querySelector('.stat-number');
                if (statNumber) {{
                    statNumber.textContent = visibleCount;
                }}
            }}
            
            // 为置信度添加颜色
            document.addEventListener('DOMContentLoaded', function() {{
                const confidenceCells = document.querySelectorAll('.confidence-cell');
                confidenceCells.forEach(cell => {{
                    const confidence = parseFloat(cell.textContent);
                    if (confidence >= 0.8) {{
                        cell.className = 'confidence-cell confidence-high';
                    }} else if (confidence >= 0.6) {{
                        cell.className = 'confidence-cell confidence-medium';
                    }} else {{
                        cell.className = 'confidence-cell confidence-low';
                    }}
                }});
                
                // 添加过滤事件监听
                document.getElementById('filenameFilter').addEventListener('input', filterTable);
                document.getElementById('productFilter').addEventListener('input', filterTable);
                document.getElementById('confidenceFilter').addEventListener('change', filterTable);
                document.getElementById('publishFilter').addEventListener('input', filterTable);
                
                // 添加排序事件监听
                document.querySelectorAll('.sortable').forEach(header => {{
                    header.addEventListener('click', function() {{
                        const column = this.getAttribute('data-sort');
                        sortTable(column);
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    return html_content

def main():
    """
    主函数
    """
    csv_path = os.path.join('output', 'ads_summary.csv')
    html_path = os.path.join('output', 'ads_display.html')
    
    print("开始生成广告数据展示网页...")
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_path):
        print(f"错误: 文件不存在 {csv_path}")
        return
    
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_path)
        print(f"成功加载 {len(df)} 条记录")
        
        # 生成HTML
        html_content = generate_html(df)
        
        # 保存HTML文件
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"网页生成成功！")
        print(f"文件保存到: {html_path}")
        print(f"包含广告的视频数: {len(df[df['是否包含广告'] == True])}")
        
        # 在浏览器中打开（可选）
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(html_path)}')
        
    except Exception as e:
        print(f"生成网页失败: {e}")

if __name__ == '__main__':
    main() 