"""Generate GitHub Dark Style Reading Dashboard v2 - Enhanced UI Edition"""

import json
import os
import calendar
from datetime import datetime, timedelta

from config import DATA_DIR, READING_DATA_FILE


def load_reading_data():
    """Load reading data from JSON file"""
    if not os.path.exists(READING_DATA_FILE):
        return {"reading_days": {}, "total_days": 0, "last_updated": ""}
    
    with open(READING_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_stats(reading_days):
    """Calculate reading statistics matching enhanced dashboard"""
    if not reading_days:
        return {
            "total_days": 0,
            "this_year_days": 0,
            "this_month_days": 0,
            "last_month_days": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "largest_streak": 0,
            "days_in_month": 30,  # 默认兜底
            "this_month_percent": 0
        }
    
    now = datetime.now()
    total_days = len(reading_days)
    current_year = now.year
    this_year_days = len([d for d in reading_days.keys() if d.startswith(str(current_year))])
    
    # 当月统计与百分比动态计算
    current_month_str = now.strftime("%Y-%m")
    this_month_days = len([d for d in reading_days.keys() if d.startswith(current_month_str)])
    
    # 🌟 第一性原理：动态获取当前月份的绝对物理总天数（防爆闰年与大小月）
    _, days_in_month = calendar.monthrange(now.year, now.month)
    this_month_percent = round((this_month_days / days_in_month) * 100, 1) if days_in_month > 0 else 0
    
    # 上月统计
    first_of_this_month = now.replace(day=1)
    last_day_of_last_month = first_of_this_month - timedelta(days=1)
    last_month_str = last_day_of_last_month.strftime("%Y-%m")
    last_month_days = len([d for d in reading_days.keys() if d.startswith(last_month_str)])
    
    sorted_dates = sorted(reading_days.keys(), reverse=True)
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 计算当前连续打卡 Current Streak
    current_streak = 0
    check_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if today_str not in reading_days and yesterday_str in reading_days:
        check_date = check_date - timedelta(days=1)
    elif today_str not in reading_days and yesterday_str not in reading_days:
        current_streak = 0
        check_date = None
        
    if check_date:
        while check_date.strftime("%Y-%m-%d") in reading_days:
            current_streak += 1
            check_date = check_date - timedelta(days=1)
    
    # 计算历史最长连续 Longest Streak
    longest_streak = 0
    temp_streak = 0
    if sorted_dates:
        sorted_date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
        for i, current_date in enumerate(sorted_date_objs):
            if i == 0:
                temp_streak = 1
            else:
                prev_date = sorted_date_objs[i-1]
                days_diff = (prev_date - current_date).days
                if days_diff == 1:
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
        longest_streak = max(longest_streak, temp_streak)
    
    return {
        "total_days": total_days,
        "this_year_days": this_year_days,
        "this_month_days": this_month_days,
        "last_month_days": last_month_days,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "largest_streak": longest_streak,
        "days_in_month": days_in_month,
        "this_month_percent": this_month_percent
    }


def generate_heatmap_data(reading_days):
    """Generate heatmap data starting strictly from January 1st of the current year"""
    today = datetime.now()
    current_year = today.year
    
    start_date = datetime(current_year, 1, 1)
    weeks = []
    
    current_date = start_date - timedelta(days=start_date.weekday())
    end_of_year = datetime(current_year, 12, 31)
    
    while current_date <= end_of_year:
        week = []
        for i in range(7):
            day_date = current_date + timedelta(days=i)
            date_str = day_date.strftime("%Y-%m-%d")
            has_reading = date_str in reading_days
            is_past_year = day_date.year < current_year
            
            week.append({
                "date": date_str,
                "day": day_date.day,
                "month": day_date.month,
                "year": day_date.year,
                "weekday": i,
                "has_reading": has_reading if not is_past_year else False,
                "is_future": day_date > today or is_past_year
            })
        
        weeks.append(week)
        current_date += timedelta(days=7)
    
    return weeks


def generate_month_labels(weeks):
    """Generate month labels accurately aligned with grid columns"""
    months = []
    current_month = None
    
    for i, week in enumerate(weeks):
        first_day = week[0]
        if first_day["month"] != current_month:
            current_month = first_day["month"]
            month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            months.append({
                "index": i,
                "name": month_names[current_month]
            })
    
    return months


def generate_html(reading_data, output_file="index.html"):
    """Generate HTML layout with enhanced high-contrast text and interactive selection hover effects"""
    
    reading_days = reading_data.get("reading_days", {})
    last_updated_raw = reading_data.get("last_updated", "")
    
    if last_updated_raw:
        try:
            if 'T' in last_updated_raw or ' ' in last_updated_raw:
                dt = datetime.fromisoformat(last_updated_raw.replace('Z', '+00:00'))
                last_updated = dt.strftime('%Y-%m-%d')
            else:
                last_updated = last_updated_raw.split()[0] if ' ' in last_updated_raw else last_updated_raw
        except:
            last_updated = last_updated_raw.split()[0] if last_updated_raw and ' ' in last_updated_raw else last_updated_raw
    else:
        last_updated = datetime.now().strftime('%Y-%m-%d')
    
    stats = calculate_stats(reading_days)
    weeks = generate_heatmap_data(reading_days)
    month_labels = generate_month_labels(weeks)
    
    # 动态构建热力图
    heatmap_html = '<div class="heatmap-months">\n'
    for month in month_labels:
        heatmap_html += f'  <div class="month-label" style="grid-column: {month["index"] + 1};">{month["name"]}</div>\n'
    heatmap_html += '</div>\n'
    
    heatmap_html += '<div class="heatmap-grid">\n'
    for week_idx, week in enumerate(weeks):
        for day in week:
            css_class = "day-cell"
            if day["is_future"]:
                css_class += " future"
            elif day["has_reading"]:
                css_class += " read"
            
            title = day["date"]
            if day["has_reading"]:
                title += " · 已阅读"
            
            heatmap_html += f'  <div class="{css_class}" title="{title}" data-date="{day["date"]}"></div>\n'
    heatmap_html += '</div>\n'
    
    # 时间面板解析
    now = datetime.now()
    month_en = now.strftime("%B").upper()
    day_num = now.day
    full_date_en = now.strftime("%B %d, %Y")
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Minimalist Reading Dashboard v2</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --bg-main: #0d0e10;          /* 深黑色科技质感底色 */
            --bg-card: #18191b;          /* 卡片内敛深灰色 */
            --text-white: #ffffff;       /* 纯白数字，拉满对比度 */
            --text-muted: #62676b;        /* 灰色小标签，对齐参考图 */
            --accent-green: #3cd070;      /* 高亮翠绿 */
            --border-default: #26282b;    /* 暗色默认轻边框 */
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", sans-serif;
            background-color: var(--bg-main);
            color: var(--text-white);
            line-height: 1.5;
            padding: 3rem 2rem;
            display: flex;
            justify-content: center;
            -webkit-font-smoothing: antialiased;
        }}
        
        .dashboard-container {{
            width: 100%;
            max-width: 1200px;
        }}
        
        header {{
            margin-bottom: 2.5rem;
        }}
        
        h1 {{
            font-size: 2.2rem;
            font-weight: 600;
            letter-spacing: -0.5px;
            margin-bottom: 0.4rem;
        }}
        
        .description {{
            font-size: 1rem;
            color: var(--text-muted);
        }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 1.5rem;
            align-items: start;
        }}
        
        /* 左侧金句卡片 */
        .left-calendar-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-default);
            border-radius: 16px;
            padding: 2rem 1.8rem;
            display: flex;
            flex-direction: column;
            min-height: 620px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        /* 2、卡片增加选中态 Hover 特效 */
        .left-calendar-card:hover {{
            border-color: var(--accent-green);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }}
        
        .calendar-date-group {{
            border-bottom: 1px solid var(--border-default);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .cal-month-day {{
            font-size: 2.4rem;
            font-weight: 700;
            color: var(--accent-green);
            letter-spacing: -0.5px;
            line-height: 1.1;
        }}
        
        .cal-full-date {{
            font-size: 1rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }}
        
        .bookmark-image-container {{
            width: 100%;
            height: 160px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            background: #111214;
            border-radius: 12px;
            overflow: hidden;
        }}
        
        .custom-bookmark-img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            filter: grayscale(100%) contrast(120%);
            opacity: 0.7;
        }}
        
        .quote-content {{
            font-family: "STSong", "SimSun", "Georgia", serif;
            font-size: 1.2rem;
            line-height: 1.8;
            color: #d1d1d1;
            text-align: justify;
            margin-bottom: auto;
        }}
        
        .quote-meta {{
            font-size: 0.8rem;
            color: var(--text-muted);
            line-height: 1.6;
            margin-top: 2rem;
        }}
        
        .right-layout {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}
        
        /* 3×2 数据网格 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.2rem;
        }}
        
        .stat-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-default);
            border-radius: 16px;
            padding: 1.8rem 1.6rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 140px;
            position: relative;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        /* 2、卡片增加选中态悬浮效果，且边缘变绿 */
        .stat-card:hover {{
            border-color: var(--accent-green);
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }}
        
        /* 1、对齐参考图：大写置灰小标签 */
        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}
        
        /* 1、对齐参考图：放大、纯白色字体的强悍数值展示 */
        .stat-value-box {{
            font-size: 3.2rem;  /* 强行膨胀放大字体 */
            font-weight: 700;
            color: var(--text-white); /* 强行纯白化 */
            line-height: 1;
            margin-top: 0.6rem;
            letter-spacing: -1px;
        }}
        
        .stat-unit {{
            font-size: 0.95rem;
            color: var(--text-muted);
            font-weight: 500;
            margin-left: 0.3rem;
            letter-spacing: 0;
        }}
        
        /* 3、This Month 指标底部的隐藏百分比横条进度条通道 */
        .progress-container {{
            width: 100%;
            height: 5px;
            background-color: #26282b;
            border-radius: 3px;
            margin-top: auto;
            overflow: hidden;
        }}
        
        .progress-bar {{
            height: 100%;
            background-color: var(--accent-green); /* 仅用亮绿色填充区分 */
            border-radius: 3px;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        /* 贡献图主卡片 */
        .heatmap-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-default);
            border-radius: 16px;
            padding: 2rem;
            transition: all 0.25s ease;
        }}
        
        .heatmap-card:hover {{
            border-color: var(--accent-green);
        }}
        
        .heatmap-title {{
            font-size: 1.15rem;
            font-weight: 600;
            margin-bottom: 0.2rem;
        }}
        
        .heatmap-subtitle {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 1.8rem;
        }}
        
        .heatmap-wrapper {{
            overflow-x: auto;
            padding-bottom: 0.5rem;
        }}
        
        .heatmap-container {{
            display: inline-grid;
            grid-template-rows: auto 1fr;
            gap: 6px;
        }}
        
        .heatmap-months {{
            display: grid;
            grid-template-columns: repeat(53, 1fr);
            gap: 4px;
            padding-bottom: 4px;
        }}
        
        .month-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 500;
        }}
        
        .heatmap-grid {{
            display: grid;
            grid-template-columns: repeat(53, 1fr);
            grid-auto-flow: column;
            grid-template-rows: repeat(7, 1fr);
            gap: 4px;
        }}
        
        .day-cell {{
            width: 12px;
            height: 12px;
            background-color: #0d0e10;
            border-radius: 3px;
            cursor: pointer;
            transition: all 0.1s ease;
        }}
        
        .day-cell.read {{
            background-color: var(--accent-green);
        }}
        
        .day-cell.future {{
            opacity: 0.15;
            cursor: default;
        }}
        
        .day-cell:not(.future):hover {{
            outline: 2px solid var(--text-white);
            outline-offset: -1px;
            z-index: 10;
        }}
        
        footer {{
            text-align: center;
            margin-top: 3rem;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
        
        .footer-links a {{
            color: var(--accent-green);
            text-decoration: none;
            margin: 0 0.4rem;
        }}
        
        .footer-links a:hover {{
            text-decoration: underline;
        }}
        
        .last-updated {{
            margin-top: 0.6rem;
            font-size: 0.75rem;
            color: #3e4145;
        }}
        
        .tooltip {{
            position: fixed;
            background: #26282b;
            color: var(--text-white);
            border: 1px solid #3e4145;
            padding: 6px 10px;
            font-size: 11px;
            border-radius: 6px;
            white-space: nowrap;
            pointer-events: none;
            z-index: 1000;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        }}
        
        @media (max-width: 968px) {{
            .main-grid {{ grid-template-columns: 1fr; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header>
            <h1>Creative Minimalist Reading Dashboard v2</h1>
            <p class="description">A reading activity journal and tracker dashboard for book lovers.</p>
        </header>
        
        <div class="main-grid">
            <div class="left-calendar-card">
                <div class="calendar-date-group">
                    <div class="cal-month-day">{month_en} {day_num}</div>
                    <div class="cal-full-date">{full_date_en}</div>
                </div>
                <div class="bookmark-image-container">
                    <img class="custom-bookmark-img" src="bookmark.png" alt="Bookmark Visual Anchor" onerror="this.style.display='none';">
                </div>
                <div class="quote-content">
                    “我们皆说起阳光与歌声，说起我们小时候夏天的事情，那些童年的日子悠长恬静，一天有现在二十天那样长。”
                </div>
                <div class="quote-meta">
                    《我孤独地漫游，如一朵云：华兹华斯抒情诗选》之《蝴蝶》<br>
                    诗人：威廉·华兹华斯 (William Wordsworth)
                </div>
            </div>
            
            <div class="right-layout">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Days</div>
                        <div class="stat-value-box">{stats['total_days']}<span class="stat-unit">days</span></div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">This Month</div>
                        <div class="stat-value-box">{stats['this_month_days']}<span class="stat-unit">days</span></div>
                        <div style="margin-top: 1rem; width: 100%;">
                            <div class="progress-container" title="本月进度: {stats['this_month_percent']}%">
                                <div class="progress-bar" style="width: {stats['this_month_percent']}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Last Month</div>
                        <div class="stat-value-box">{stats['last_month_days']}<span class="stat-unit">days</span></div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Current Streak</div>
                        <div class="stat-value-box">{stats['current_streak']}<span class="stat-unit">days</span></div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Longest Streak</div>
                        <div class="stat-value-box">{stats['longest_streak']}<span class="stat-unit">days</span></div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Largest Streak</div>
                        <div class="stat-value-box">{stats['largest_streak']}<span class="stat-unit">days</span></div>
                    </div>
                </div>
                
                <div class="heatmap-card">
                    <div class="heatmap-title">Contribution Graph</div>
                    <div class="heatmap-subtitle">今年共阅读 {stats['this_year_days']} 天</div>
                    
                    <div class="heatmap-wrapper">
                        <div class="heatmap-container">
{heatmap_html}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>Keep Reading · Keep Growing</p>
            <div class="footer-links">
                <a href="https://github.com" target="_blank">GitHub</a> · 
                <a href="https://www.amazon.com/kindle/reading/insights" target="_blank">Kindle</a>
            </div>
            <p class="last-updated">Last updated: {last_updated}</p>
        </footer>
    </div>
    
    <script>
        // 高性能原生 Tooltip 悬浮节点引擎
        document.querySelectorAll('.day-cell:not(.future)').forEach(cell => {{
            cell.addEventListener('mouseenter', (e) => {{
                const rect = e.target.getBoundingClientRect();
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = e.target.getAttribute('title');
                tooltip.style.cssText = `
                    top: ${{rect.top - 32}}px;
                    left: ${{rect.left + rect.width / 2}}px;
                    transform: translateX(-50%);
                `;
                document.body.appendChild(tooltip);
                e.target._tooltip = tooltip;
            }});
            
            cell.addEventListener('mouseleave', (e) => {{
                if (e.target._tooltip) {{
                    e.target._tooltip.remove();
                    delete e.target._tooltip;
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Enhanced Dashboard v2 HTML generated successfully: {output_file}")


def main():
    print("📖 Running Premium Dynamic Analytics Engine...")
    reading_data = load_reading_data()
    generate_html(reading_data)
    print("🏁 Optimization Done!")


if __name__ == "__main__":
    main()
