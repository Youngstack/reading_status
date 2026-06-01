"""Generate Kindle reading page with Daily Calendar integration - GitHub Dark Mode & Year-Start"""

import json
import os
from datetime import datetime, timedelta

from config import DATA_DIR, READING_DATA_FILE


def load_reading_data():
    """Load reading data from JSON file"""
    if not os.path.exists(READING_DATA_FILE):
        return {"reading_days": {}, "total_days": 0, "last_updated": ""}
    
    with open(READING_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_stats(reading_days):
    """Calculate reading statistics"""
    if not reading_days:
        return {
            "total_days": 0,
            "this_year_days": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "this_month_days": 0
        }
    
    total_days = len(reading_days)
    current_year = datetime.now().year
    this_year_days = len([d for d in reading_days.keys() if d.startswith(str(current_year))])
    current_month = datetime.now().strftime("%Y-%m")
    this_month_days = len([d for d in reading_days.keys() if d.startswith(current_month)])
    
    sorted_dates = sorted(reading_days.keys(), reverse=True)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    
    # Calculate current streak: count consecutive days from yesterday backwards
    current_streak = 0
    check_date = yesterday
    while check_date.strftime("%Y-%m-%d") in reading_days:
        current_streak += 1
        check_date = check_date - timedelta(days=1)
    
    # Calculate longest streak
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
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }


def generate_heatmap_data(reading_days, months=12):
    """Generate heatmap data starting strictly from January 1st of the current year"""
    today = datetime.now()
    current_year = today.year
    
    # 🌟 核心时间算法改动：死锁在当年的 1 月 1 日
    start_date = datetime(current_year, 1, 1)
    weeks = []
    
    # 📅 物理对齐：从 1 月 1 日所在周的周一开始绘制（防止第一周网格错位）
    current_date = start_date - timedelta(days=start_date.weekday())
    
    # 🔄 结束条件：绘制到今年 12 月 31 日，展现完整自然年全景
    end_of_year = datetime(current_year, 12, 31)
    
    while current_date <= end_of_year:
        week = []
        for i in range(7):
            day_date = current_date + timedelta(days=i)
            date_str = day_date.strftime("%Y-%m-%d")
            has_reading = date_str in reading_days
            
            # 过滤判定：由于对齐周一，可能夹带上一年的残余日子，将其强制变透明
            is_past_year = day_date.year < current_year
            
            week.append({
                "date": date_str,
                "day": day_date.day,
                "month": day_date.month,
                "year": day_date.year,
                "weekday": i,
                "has_reading": has_reading if not is_past_year else False,
                "is_future": day_date > today or is_past_year # 未来的日子或去年的残余都算作空白块
            })
        
        weeks.append(week)
        current_date += timedelta(days=7)
    
    return weeks


def generate_month_labels(weeks):
    """Generate month labels based on calendar weeks layout"""
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
    """Generate HTML page with stats, daily calendar, and strict year-start heatmap"""
    
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
        last_updated = ""
    
    stats = calculate_stats(reading_days)
    weeks = generate_heatmap_data(reading_days)
    month_labels = generate_month_labels(weeks)
    
    # Generate heatmap HTML months header
    heatmap_html = '<div class="heatmap-months">\n'
    for month in month_labels:
        heatmap_html += f'  <div class="month-label" style="grid-column: {month["index"] + 1};">{month["name"]}</div>\n'
    heatmap_html += '</div>\n'
    
    # Generate heatmap HTML cells grid
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
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="我的阅读记录 - GitHub 自然年绿墙风格">
    <title>阅读记录</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            /* 🍏 全面对齐 GitHub 经典暗黑极客配色 */
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --text-primary: #e6edf3;
            --text-secondary: #7d8590;
            --text-tertiary: #6e7681;
            --border-color: #30363d;
            --accent: #58a6ff;
            --shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
            
            /* GitHub 经典色阶 */
            --color-calendar-graph-day-bg: #161b22;
            --color-calendar-graph-day-read-bg: #39d353;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: var(--bg-primary);
            padding: 2rem 1.5rem;
        }}
        
        header {{
            text-align: left;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }}
        
        .subtitle {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 400;
            letter-spacing: 0.5px;
        }}
        
        .main-layout {{
            display: grid;
            grid-template-columns: 1fr 340px;
            gap: 2rem;
            margin-bottom: 3rem;
            align-items: stretch;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            height: 100%;
        }}
        
        .stat-item {{
            text-align: left;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            transition: all 0.2s ease;
            background: var(--bg-secondary);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        .stat-item:hover {{
            border-color: #8b949e;
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 0.5rem;
            letter-spacing: 0.5px;
        }}
        
        .stat-value {{
            font-size: 2.2rem;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.1;
        }}
        
        .stat-unit {{
            font-size: 1rem;
            color: var(--text-secondary);
            margin-left: 0.3rem;
            font-weight: 400;
        }}
        
        .daily-calendar {{
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        
        .daily-calendar-wrapper {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.5rem;
            text-align: center;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }}
        
        .daily-calendar-image {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            border-radius: 4px;
            cursor: pointer;
            transition: transform 0.2s ease;
            filter: invert(0.9) hue-rotate(180deg); /* 🌟 物理滤镜：智能化反转白底，完美融入黑暗风 */
        }}
        
        .daily-calendar-image:hover {{
            transform: scale(1.01);
        }}
        
        .daily-calendar-loading {{
            width: 100%;
            height: 100%;
            color: var(--text-tertiary);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .heatmap-section {{
            margin-bottom: 3rem;
            padding: 1.5rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
        }}
        
        .section-title {{
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 0.25rem;
            color: var(--text-primary);
            letter-spacing: 0.5px;
        }}
        
        .section-subtitle {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }}
        
        .heatmap-wrapper {{
            overflow-x: auto;
            padding: 0.5rem 0;
        }}
        
        .heatmap-wrapper::-webkit-scrollbar {{
            height: 6px;
        }}
        
        .heatmap-wrapper::-webkit-scrollbar-track {{
            background: var(--bg-primary);
        }}
        
        .heatmap-wrapper::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 3px;
        }}
        
        .heatmap-container {{
            display: inline-grid;
            grid-template-rows: auto 1fr;
            gap: 4px;
            min-width: 100%;
        }}
        
        .heatmap-months {{
            display: grid;
            grid-template-columns: repeat(53, 1fr);
            gap: 3px;
            padding-bottom: 2px;
        }}
        
        .month-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-align: left;
        }}
        
        .heatmap-grid {{
            display: grid;
            grid-template-columns: repeat(53, 1fr);
            grid-auto-flow: column;
            grid-template-rows: repeat(7, 1fr);
            gap: 3px;
            min-height: 100px;
        }}
        
        .day-cell {{
            width: 100%;
            aspect-ratio: 1 / 1;
            min-width: 10px;
            background: var(--color-calendar-graph-day-bg);
            border: 1px solid rgba(27, 31, 35, 0.04);
            border-radius: 2px;
            cursor: pointer;
            transition: background-color 0.1s ease;
        }}
        
        .day-cell.read {{
            background: var(--color-calendar-graph-day-read-bg);
        }}
        
        .day-cell.future {{
            background: #0d1117;
            border: 1px solid var(--border-color);
            opacity: 0.12;
            cursor: default;
        }}
        
        .day-cell:not(.future):hover {{
            outline: 2px solid var(--text-primary);
            outline-offset: -1px;
            z-index: 10;
        }}
        
        footer {{
            text-align: center;
            padding-top: 2rem;
            margin-top: 2rem;
            border-top: 1px solid var(--border-color);
            color: var(--text-tertiary);
            font-size: 0.8rem;
        }}
        
        footer a {{
            color: var(--accent);
            text-decoration: none;
        }}
        
        footer a:hover {{
            text-decoration: underline;
        }}
        
        .last-updated {{
            margin-top: 0.75rem;
            font-size: 0.75rem;
            color: var(--text-tertiary);
        }}
        
        .tooltip {{
            position: fixed;
            background: #6e7681;
            color: #ffffff;
            padding: 5px 8px;
            font-size: 11px;
            border-radius: 6px;
            white-space: nowrap;
            pointer-events: none;
            z-index: 1000;
            font-weight: 500;
            box-shadow: var(--shadow);
        }}
        
        @media (max-width: 1024px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
            .daily-calendar {{
                order: -1;
                margin-bottom: 2rem;
                min-height: 350px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 1rem; }}
            h1 {{ font-size: 1.6rem; }}
            .stats {{ grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }}
            .stat-value {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>阅读记录</h1>
            <p class="subtitle">Reading Activity Journal</p>
        </header>
        
        <div class="main-layout">
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-label">Total Days</div>
                    <div class="stat-value">{stats['total_days']}<span class="stat-unit">days</span></div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">This Month</div>
                    <div class="stat-value">{stats['this_month_days']}<span class="stat-unit">days</span></div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Current Streak</div>
                    <div class="stat-value">{stats['current_streak']}<span class="stat-unit">days</span></div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Longest Streak</div>
                    <div class="stat-value">{stats['longest_streak']}<span class="stat-unit">days</span></div>
                </div>
            </div>
            
            <div class="daily-calendar">
                <div class="daily-calendar-wrapper" id="dailyCalendarWrapper">
                    <div id="dailyCalendarContent" class="daily-calendar-loading">
                        Loading...
                    </div>
                </div>
            </div>
        </div>
        
        <section class="heatmap-section">
            <h2 class="section-title">Contribution Graph</h2>
            <p class="section-subtitle">今年共阅读 {stats['this_year_days']} 天</p>
            
            <div class="heatmap-wrapper">
                <div class="heatmap-container">
{heatmap_html}
                </div>
            </div>
        </section>
        
        <footer>
            <p>Keep Reading · Keep Growing</p>
            <p style="margin-top: 0.5rem;">
                <a href="https://github.com" target="_blank">GitHub</a>
                <span style="margin: 0 0.5rem;">·</span>
                <a href="https://www.amazon.com/kindle/reading/insights" target="_blank">Kindle</a>
            </p>
            {f'<p class="last-updated">Last updated: {last_updated}</p>' if last_updated else ''}
        </footer>
    </div>
    
    <script>
        // 异步加载并清洗单向历图片
        function loadDailyCalendar() {{
            var d = new Date();
            var y = d.getFullYear();
            var m = d.getMonth() + 1;
            var n = d.getDate();
            var mm = m > 9 ? m : "0" + m;
            var dd = n > 9 ? n : "0" + n;
            
            var imgSources = [
                "https://img.owspace.com/Public/uploads/Download/" + y + "/" + mm + dd + ".jpg",
                "https://img.owspace.com/Public/uploads/Download/" + y + "/" + m + n + ".jpg"
            ];
            
            tryLoadImage(0);
            
            function tryLoadImage(index) {{
                if (index >= imgSources.length) {{
                    document.getElementById("dailyCalendarContent").innerHTML = 
                        '<div class="daily-calendar-loading" style="padding: 3rem 1rem; text-align: center;">' +
                        '<p style="font-size: 3rem; margin-bottom: 1rem;">📚</p>' +
                        '<p style="font-size: 1.2rem; margin-bottom: 0.5rem; color: var(--text-primary);">' + y + ' 年 ' + parseInt(m) + ' 月 ' + parseInt(n) + ' 日</p>' +
                        '<p style="font-size: 0.85rem; color: var(--text-tertiary); margin-top: 1rem;">Keep Reading · Keep Growing</p>' +
                        '</div>';
                    return;
                }}
                
                var img = new Image();
                img.onload = function() {{
                    document.getElementById("dailyCalendarContent").innerHTML = 
                        '<img class="daily-calendar-image" src="' + imgSources[index] + '" alt="单向历" referrerpolicy="no-referrer" />';
                }};
                img.onerror = function() {{
                    tryLoadImage(index + 1);
                }};
                img.referrerPolicy = 'no-referrer';
                img.src = imgSources[index];
            }}
        }}
        
        window.onload = function() {{
            loadDailyCalendar();
        }};
        
        // Tooltip for custom heatmap
        document.querySelectorAll('.day-cell:not(.future)').forEach(cell => {{
            cell.addEventListener('mouseenter', (e) => {{
                const rect = e.target.getBoundingClientRect();
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = e.target.getAttribute('title');
                tooltip.style.cssText = `
                    top: ${{rect.top - 28}}px;
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
    
    print(f"✅ Page with daily calendar generated: {output_file}")
    print(f"📊 Stats: {stats}")


def main():
    """Main function"""
    print("📖 Generating reading page with GitHub Style & Year-Start...")
    
    reading_data = load_reading_data()
    generate_html(reading_data)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()
