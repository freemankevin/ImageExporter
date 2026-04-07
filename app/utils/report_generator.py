#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML报告生成器"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def generate_html_report(report_data: Dict[str, Any], output_path: Path) -> None:
    successful = report_data.get('successful_images', [])
    failed = report_data.get('failed_images', [])
    
    total_size_mb = sum(img.get('file_size_mb', 0) for img in successful)
    total_size_gb = total_size_mb / 1024
    
    success_rate = (report_data['successful_count'] / report_data['total_processed'] * 100) if report_data['total_processed'] > 0 else 0
    
    timestamp = datetime.fromisoformat(report_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docker镜像导出报告 - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e0e0e0;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        .header .timestamp {{
            color: #888;
            font-size: 0.95rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(0, 212, 255, 0.1);
        }}
        
        .stat-card.success {{
            border-color: rgba(34, 197, 94, 0.3);
        }}
        
        .stat-card.failed {{
            border-color: rgba(239, 68, 68, 0.3);
        }}
        
        .stat-card.total {{
            border-color: rgba(124, 58, 237, 0.3);
        }}
        
        .stat-card.size {{
            border-color: rgba(59, 130, 246, 0.3);
        }}
        
        .stat-icon {{
            font-size: 2rem;
            margin-bottom: 12px;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .stat-card.success .stat-value {{
            color: #22c55e;
        }}
        
        .stat-card.failed .stat-value {{
            color: #ef4444;
        }}
        
        .stat-card.total .stat-value {{
            color: #7c3aed;
        }}
        
        .stat-card.size .stat-value {{
            color: #3b82f6;
        }}
        
        .stat-label {{
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 12px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #22c55e, #00d4ff);
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        
        .section {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
        }}
        
        .section-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .section-title .icon {{
            font-size: 1.5rem;
        }}
        
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .badge.success {{
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }}
        
        .badge.failed {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}
        
        .table-wrapper {{
            overflow-x: auto;
            border-radius: 12px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        
        th, td {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        th {{
            background: rgba(255, 255, 255, 0.05);
            font-weight: 600;
            color: #00d4ff;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
        }}
        
        tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}
        
        .image-name {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85rem;
            color: #a5d6ff;
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .arch-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            background: rgba(124, 58, 237, 0.2);
            color: #a78bfa;
            border: 1px solid rgba(124, 58, 237, 0.3);
        }}
        
        .size-cell {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            color: #10b981;
        }}
        
        .error-message {{
            color: #ef4444;
            font-size: 0.85rem;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #666;
            font-size: 0.85rem;
        }}
        
        .footer a {{
            color: #00d4ff;
            text-decoration: none;
        }}
        
        .status-icon {{
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            text-align: center;
            line-height: 24px;
            font-size: 0.9rem;
        }}
        
        .status-icon.success {{
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }}
        
        .status-icon.failed {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        
        .empty-state .icon {{
            font-size: 3rem;
            margin-bottom: 16px;
            opacity: 0.5;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8rem;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .stat-value {{
                font-size: 1.8rem;
            }}
            
            th, td {{
                padding: 10px 12px;
                font-size: 0.8rem;
            }}
            
            .image-name {{
                max-width: 200px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Docker 镜像导出报告</h1>
            <div class="timestamp">生成时间: {timestamp}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card total">
                <div class="stat-icon">📦</div>
                <div class="stat-value">{report_data['total_processed']}</div>
                <div class="stat-label">总处理数</div>
            </div>
            <div class="stat-card success">
                <div class="stat-icon">✓</div>
                <div class="stat-value">{report_data['successful_count']}</div>
                <div class="stat-label">成功导出</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {success_rate:.1f}%"></div>
                </div>
            </div>
            <div class="stat-card failed">
                <div class="stat-icon">✗</div>
                <div class="stat-value">{report_data['failed_count']}</div>
                <div class="stat-label">导出失败</div>
            </div>
            <div class="stat-card size">
                <div class="stat-icon">💾</div>
                <div class="stat-value">{total_size_gb:.2f} GB</div>
                <div class="stat-label">总大小 ({total_size_mb:.0f} MB)</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">
                <span class="icon">✓</span>
                成功导出的镜像
                <span class="badge success">{report_data['successful_count']} 个</span>
            </h2>
            <div class="table-wrapper">
                {'<table><thead><tr><th>状态</th><th>镜像名称</th><th>架构</th><th>文件大小</th></tr></thead><tbody>' + ''.join([f'<tr><td><span class="status-icon success">✓</span></td><td class="image-name" title="{img["image"]}">{img["image"]}</td><td><span class="arch-badge">{img["arch"]}</span></td><td class="size-cell">{img["file_size_mb"]:.2f} MB</td></tr>' for img in successful]) + '</tbody></table>' if successful else '<div class="empty-state"><div class="icon">📭</div><p>暂无成功导出的镜像</p></div>'}
            </div>
        </div>
        
        {'<div class="section"><h2 class="section-title"><span class="icon">✗</span>导出失败的镜像<span class="badge failed">' + str(report_data['failed_count']) + ' 个</span></h2><div class="table-wrapper"><table><thead><tr><th>状态</th><th>镜像名称</th><th>架构</th><th>错误信息</th></tr></thead><tbody>' + ''.join([f'<tr><td><span class="status-icon failed">✗</span></td><td class="image-name" title="{img["image"]}">{img["image"]}</td><td><span class="arch-badge">{img["arch"]}</span></td><td class="error-message" title="{img.get("error_message", "未知错误")}">{img.get("error_message", "未知错误")}</td></tr>' for img in failed]) + '</tbody></table></div></div>' if failed else ''}
        
        <div class="footer">
            <p>ImageExporter · Docker镜像离线导出工具</p>
        </div>
    </div>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)