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

def generate_html(df):
    """
    生成HTML页面
    """
    # 过滤包含广告的视频
    ad_videos = df[df['是否包含广告'] == True].copy()
    
    if len(ad_videos) == 0:
        html_content = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>广告数据展示</title>
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
        <title>数据展示</title>
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
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
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
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>数据展示</h1>
            </div>
            
            <div class="stats">
                <div class="stats-content">
                    <div class="stat-item">
                        <span class="stat-number">{len(ad_videos)}</span>
                        <div class="stat-label">广告视频</div>
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
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>📁 文件名</th>
                            <th>🛍️ 商品名称</th>
                            <th>📝 广告文本</th>
                            <th>🎯 置信度</th>
                            <th>⏰ 广告时间</th>
                            <th>🔗 视频链接</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
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