"""Generate GitHub Dark Style Reading Dashboard v3 - Fixed Grid & Full Stats Edition"""

import json
import os
import re
import calendar
from datetime import datetime, timedelta
from pathlib import Path

# 🍏 引入核心配置路径
from config import DATA_DIR, READING_DATA_FILE, CLIPPINGS_FILE


def parse_clippings_to_json():
    """
    第一性原理数据审计：
    全量解析本地 My Clippings.txt，自动提取打卡日期，并按书名归类划线笔记
    """
    reading_days = {}
    books_dict = {}
    
    clippings_path = str(CLIPPINGS_FILE)
    reading_data_path = str(READING_DATA_FILE)
    
    if not os.path.exists(clippings_path):
        if os.path.exists(reading_data_path):
            with open(reading_data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"reading_days": {}, "books": {}, "total_days": 0, "last_updated": ""}

    with open(clippings_path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    
    entries = content.split("==========\n")
    
    for entry in entries:
        lines = [line.strip() for line in entry.split("\n") if line.strip()]
        if len(lines) < 3:
            continue
            
        book_title_raw = lines[0]
        meta_line = lines[1]
        clipping_text = "\n".join(lines[2:])
        
        # 提取书名与作者 (对齐标准：书名 (作者))
        author = "Unknown Author"
        book_title = book_title_raw
        author_match = re.search(r"\(([^)]+)\)$", book_title_raw)
        if author_match:
            author = author_match.group(1)
            book_title = book_title_raw[:author_match.start()].strip()
        
        # 兼容中英文系统清洗绝对时间戳
        date_str = None
        zh_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", meta_line)
        if zh_match:
            year, month, day = zh_match.groups()
            date_str = f"{year}-{int(month):02d}-{int(day):02d}"
        else:
            en_match = re.search(r"Added on .*, (\w+) (\d{1,2}), (\d{4})", meta_line)
            if en_match:
                month_str, day, year = en_match.groups()
                try:
                    dt = datetime.strptime(f"{year} {month_str} {day}", "%Y %B %d")
                    date_str = dt.strftime("%Y-%m-%d")
                except:
                    try:
                        dt = datetime.strptime(f"{year} {month_str} {day}", "%Y %b %d")
                        date_str = dt.strftime("%Y-%m-%d")
                    except:
                        pass
        
        if date_str:
            reading_days[date_str] = reading_days.get(date_str, 0) + 1
            
            if book_title not in books_dict:
                books_dict[book_title] = {
                    "title": book_title,
                    "author": author,
                    "last_read": date_str,
                    "count": 0,
                    "clippings": []
                }
            
            if date_str > books_dict[book_title]["last_read"]:
                books_dict[book_title]["last_read"] = date_str
                
            books_dict[book_title]["count"] += 1
            books_dict[book_title]["clippings"].append({
                "date": date_str,
                "text": clipping_text
            })
            
    sorted_books = dict(sorted(books_dict.items(), key=lambda item: item[1]["last_read"], reverse=True))
    
    result = {
        "reading_days": {d: {"count": c} for d, c in reading_days.items()},
        "books": sorted_books,
        "total_days": len(reading_days),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(reading_data_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
        
    return result


def calculate_stats(reading_days):
    """🌟 核心复活：完美对齐原先 3x2 看板的 6 大指标审计模型"""
    if not reading_days:
        return {
            "total_days": 0, "this_year_days": 0, "this_month_days": 0, "last_month_days": 0,
            "current_streak": 0, "longest_streak": 0, "largest_streak": 0, "days_in_month": 30, "this_month_percent": 0
        }
    
    now = datetime.now()
    total_days = len(reading_days)
    current_year = now.year
    this_year_days = len([d for d in reading_days.keys() if d.startswith(str(current_year))])
    
    # 1. 当月数据
    current_month_str = now.strftime("%Y-%m")
    this_month_days = len([d for d in reading_days.keys() if d.startswith(current_month_str)])
    
    # 动态获取当前月份绝对物理总天数，计算进度条
    _, days_in_month = calendar.monthrange(now.year, now.month)
    this_month_percent = round((this_month_days / days_in_month) * 100, 1) if days_in_month > 0 else 0
    
    # 2. 上月数据
    first_of_this_month = now.replace(day=1)
    last_day_of_last_month = first_of_this_month - timedelta(days=1)
    last_month_str = last_day_of_last_month.strftime("%Y-%m")
    last_month_days = len([d for d in reading_days.keys() if d.startswith(last_month_str)])
    
    sorted_dates = sorted(reading_days.keys(), reverse=True)
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 3. 连续打卡风控风味逻辑（支持今天还没阅读时的安全回推）
    current_streak = 0
    check_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if today_str not in reading_days and yesterday_str in reading_days:
        check_date = check_date - timedelta(days=1)
    elif today_str not in reading_days and yesterday_str not in reading_days:
        check_date = None
        
    if check_date:
        while check_date.strftime("%Y-%m-%d") in reading_days:
            current_streak += 1
            check_date = check_date - timedelta(days=1)
            
    # 4. 历史最长连续打卡与最大连续
    longest_streak = 0
    temp_streak = 0
    if sorted_dates:
        sorted_date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
        for i, current_date in enumerate(sorted_date_objs):
            if i == 0:
                temp_streak = 1
            else:
                prev_date = sorted_date_objs[i-1]
                if (prev_date - current_date).days == 1:
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
        "largest_streak": longest_streak, # 保持物理逻辑统合
        "days_in_month": days_in_month,
        "this_month_percent": this_month_percent
    }


def generate_heatmap_data(reading_days):
    """Generate heatmap data starting strictly from January 1st of the current year"""
    today = datetime.now()
    start_date = datetime(today.year, 1, 1)
    weeks = []
    current_date = start_date - timedelta(days=start_date.weekday())
    end_of_year = datetime(today.year, 12, 31)
    
    while current_date <= end_of_year:
        week = []
        for i in range(7):
            day_date = current_date + timedelta(days=i)
            date_str = day_date.strftime("%Y-%m-%d")
            is_past_year = day_date.year < today.year
            week.append({
                "date": date_str,
                "has_reading": date_str in reading_days if not is_past_year else False,
                "is_future": day_date > today or is_past_year
            })
        weeks.append(week)
        current_date += timedelta(days=7)
    return weeks


def generate_html(reading_data, output_file=None):
    """Generate HTML layout with unified card dimensions and complete 3x2 stats grid"""
    
    now = datetime.now()
    month_en = now.strftime("%B").upper()
    day_num = now.day
    full_date_en = now.strftime("%B %d, %Y")
    
    reading_days = reading_data.get("reading_days", {})
    books = reading_data.get("books", {})
    
    stats = calculate_stats(reading_days)
    weeks = generate_heatmap_data(reading_days)
    
    # 渲染热力图网格
    heatmap_html = '<div class="heatmap-grid">\n'
    for week in weeks:
        for day in week:
            css_class = "day-cell"
            if day["is_future"]: css_class += " future"
            elif day["has_reading"]: css_class += " read"
            heatmap_html += f'  <div class="{css_class}" title="{day["date"]}"></div>\n'
    heatmap_html += '</div>\n'
    
    # 渲染 V3 版 Book Highlights 模块卡片网格
    books_html = ""
    js_clippings_payload = {}
    
    for idx, (title, info) in enumerate(books.items()):
        safe_id = f"book_id_{idx}"
        js_clippings_payload[safe_id] = {
            "title": title,
            "author": info["author"],
            "clippings": info["clippings"]
        }
        
        gradient_index = (idx % 4) + 1
        
        books_html += f"""
        <div class="premium-book-item" onclick="openClippingModal('{safe_id}')">
            <div class="book-cover-plate gradient-skin-{gradient_index}">
                <div class="book-cover-core-icon">📖</div>
            </div>
            <div class="book-info-panel">
                <div class="premium-book-title" title="{title}">{title}</div>
                <div class="premium-book-author" title="{info['author']}">{info['author']}</div>
                <div class="premium-book-highlights-count">❞ {info['count']} HIGHLIGHTS</div>
            </div>
        </div>"""

    last_updated = now.strftime('%Y-%m-%d')
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Minimalist Reading Dashboard v3</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --bg-main: #0a0b0d;
            --bg-card: #141619;
            --text-white: #ffffff;
            --text-muted: #62676b;
            --accent-green: #3cd070;
            --border-default: #222428;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
            background-color: var(--bg-main); color: var(--text-white);
            padding: 3rem 2rem; display: flex; justify-content: center;
            -webkit-font-smoothing: antialiased;
        }}
        .dashboard-container {{ width: 100%; max-width: 1200px; }}
        header {{ margin-bottom: 2.5rem; }}
        h1 {{ font-size: 2.2rem; font-weight: 600; letter-spacing: -0.5px; margin-bottom: 0.4rem; }}
        .description {{ color: var(--text-muted); }}
        
        .main-grid {{ display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem; margin-bottom: 2rem; }}
        
        .left-calendar-card {{
            background-color: var(--bg-card); border: 1px solid var(--border-default);
            border-radius: 16px; padding: 2rem 1.8rem; display: flex; flex-direction: column; min-height: 600px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .left-calendar-card:hover {{ border-color: var(--accent-green); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4); }}
        .calendar-date-group {{ border-bottom: 1px solid var(--border-default); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        .cal-month-day {{ font-size: 2.4rem; font-weight: 700; color: var(--text-white); line-height: 1.1; transition: color 0.2s ease; }}
        .left-calendar-card:hover .cal-month-day {{ color: var(--accent-green); }}
        .cal-full-date {{ font-size: 0.95rem; color: var(--text-muted); margin-top: 0.5rem; }}
        .quote-content {{ font-family: "STSong", "SimSun", serif; font-size: 1.2rem; line-height: 1.8; color: #d1d1d1; text-align: justify; margin-bottom: auto; }}
        .quote-meta {{ font-size: 0.8rem; color: var(--text-muted); line-height: 1.6; margin-top: 2rem; }}
        
        .right-layout {{ display: flex; flex-direction: column; gap: 1.5rem; }}
        
        /* 3×2 数据网格 - 强控完美还原布局 */
        .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; }}
        .stat-card {{
            background-color: var(--bg-card); border: 1px solid var(--border-default); border-radius: 16px;
            padding: 1.8rem 1.6rem; display: flex; flex-direction: column; justify-content: space-between;
            min-height: 140px; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .stat-card:hover {{ border-color: var(--accent-green); transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4); }}
        .stat-card:hover .stat-value-box {{ color: var(--accent-green); }}
        .stat-label {{ font-size: 0.75rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }}
        .stat-value-box {{ font-size: 3.2rem; font-weight: 700; color: var(--text-white); line-height: 1; margin-top: 0.6rem; letter-spacing: -1px; transition: color 0.2s ease; }}
        .stat-unit {{ font-size: 0.95rem; color: var(--text-muted); margin-left: 0.3rem; }}
        
        .progress-container {{ width: 100%; height: 5px; background-color: #222428; border-radius: 3px; margin-top: auto; overflow: hidden; }}
        .progress-bar {{ height: 100%; background-color: var(--accent-green); border-radius: 3px; }}
        
        .heatmap-card {{ background-color: var(--bg-card); border: 1px solid var(--border-default); border-radius: 16px; padding: 2rem; transition: all 0.25s ease; }}
        .heatmap-card:hover {{ border-color: var(--accent-green); }}
        .heatmap-title {{ font-size: 1.15rem; font-weight: 600; margin-bottom: 0.2rem; }}
        .heatmap-subtitle {{ font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.5rem; }}
        .heatmap-grid {{ display: grid; grid-template-columns: repeat(53, 1fr); grid-auto-flow: column; grid-template-rows: repeat(7, 1fr); gap: 4px; }}
        .day-cell {{ width: 12px; height: 12px; background-color: #0a0b0d; border-radius: 3px; }}
        .day-cell.read {{ background-color: var(--accent-green); }}
        .day-cell.future {{ opacity: 0.15; }}
        
        .library-section-container {{ margin-top: 2rem; }}
        .library-block-header {{ display: flex; align-items: center; gap: 0.6rem; font-size: 1.3rem; font-weight: 600; margin-bottom: 1.5rem; }}
        .library-block-header span.icon {{ color: var(--accent-green); }}
        
        /* 1、书摘卡片强制尺寸一致 */
        .premium-library-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }}
        
        .premium-book-item {{ 
            cursor: pointer; 
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1); 
            display: flex;
            flex-direction: column;
            height: 380px; /* 🌟 物理硬管控：把整本书籍区块的高度死锁，彻底消除大有小 */
        }}
        
        .book-cover-plate {{
            width: 100%; 
            height: 260px; /* 🌟 物理死锁封面卡片高度 */
            border-radius: 14px;
            background-color: #1a1d21; border: 1px solid var(--border-default);
            display: flex; align-items: center; justify-content: center;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative; overflow: hidden;
            flex-shrink: 0;
        }}
        
        .premium-book-item:hover {{ transform: scale(1.03); }}
        .premium-book-item:hover .book-cover-plate {{
            border-color: var(--accent-green);
            box-shadow: 0 0 20px rgba(60, 208, 112, 0.2), inset 0 0 24px rgba(60, 208, 112, 0.4); 
        }}
        
        .book-cover-core-icon {{ font-size: 2.2rem; opacity: 0.3; transition: all 0.25s ease; }}
        .premium-book-item:hover .book-cover-core-icon {{ opacity: 0.8; transform: scale(1.1); }}
        
        .gradient-skin-1 {{ background: linear-gradient(135deg, #1b2820 0%, #141619 100%); }}
        .gradient-skin-2 {{ background: linear-gradient(135deg, #19222d 0%, #141619 100%); }}
        .gradient-skin-3 {{ background: linear-gradient(135deg, #2a251b 0%, #141619 100%); }}
        .gradient-skin-4 {{ background: linear-gradient(135deg, #241c2d 0%, #141619 100%); }}
        
        /* 1、书摘说明排版强制文本截断 */
        .book-info-panel {{ 
            padding: 0.8rem 0.2rem 0 0.2rem; 
            display: flex;
            flex-direction: column;
            flex-grow: 1;
            justify-content: flex-start;
            overflow: hidden;
        }}
        /* 🌟 使用多行截断防御，不管书名多长，超过两行自动吐出省略号，死锁空间 */
        .premium-book-title {{ 
            font-size: 0.95rem; 
            font-weight: 600; 
            color: var(--text-white); 
            margin-bottom: 0.2rem; 
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: normal;
            line-height: 1.3;
            height: 2.6em; /* 锁死双行高度占位，不管一行还是两行，底部标签绝对对齐 */
        }}
        .premium-book-author {{ 
            font-size: 0.8rem; 
            color: #8a8e94; 
            margin-bottom: 0.4rem; 
            white-space: nowrap; 
            overflow: hidden; 
            text-overflow: ellipsis; 
        }}
        .premium-book-highlights-count {{ font-size: 0.75rem; font-weight: 700; color: var(--accent-green); letter-spacing: 0.5px; margin-top: auto; }}
        
        /* Modal Window Box Drawer Styles */
        .modal-overlay {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(5, 6, 8, 0.9); backdrop-filter: blur(10px);
            display: flex; align-items: center; justify-content: center;
            z-index: 2000; opacity: 0; pointer-events: none;
            transition: opacity 0.3s ease;
        }}
        .modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
        
        .modal-window-wrapper {{
            width: 100%; max-width: 780px; background-color: #141619;
            border: 1px solid var(--border-default); border-radius: 16px;
            display: flex; flex-direction: column; max-height: 85vh;
            box-shadow: 0 20px 50px rgba(0,0,0,0.6); transform: translateY(20px);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .modal-overlay.active .modal-window-wrapper {{ transform: translateY(0); }}
        
        .modal-header-bar {{ padding: 1.5rem 2rem; border-bottom: 1px solid var(--border-default); display: flex; justify-content: space-between; align-items: center; }}
        .modal-book-title {{ font-size: 1.3rem; font-weight: 600; color: var(--text-white); }}
        .modal-book-author {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 0.2rem; }}
        .modal-close-btn {{ font-size: 1.5rem; color: var(--text-muted); cursor: pointer; transition: color 0.2s; background: none; border: none; }}
        .modal-close-btn:hover {{ color: var(--text-white); }}
        
        .modal-scroll-body {{ padding: 1.5rem 2rem; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 1.2rem; }}
        .modal-scroll-body::-webkit-scrollbar {{ width: 6px; }}
        .modal-scroll-body::-webkit-scrollbar-thumb {{ background-color: #2b2e33; border-radius: 3px; }}
        
        .modal-clipping-card {{ background-color: #1a1d21; border: 1px solid var(--border-default); border-radius: 12px; padding: 1.5rem; }}
        .modal-clipping-text {{ font-size: 1.05rem; color: #e2e2e2; line-height: 1.7; font-style: italic; font-family: "STSong", "SimSun", serif; text-align: justify; }}
        .modal-clipping-text::before {{ content: "“"; font-size: 1.5rem; color: var(--accent-green); margin-right: 0.2rem; }}
        .modal-clipping-text::after {{ content: "”"; font-size: 1.5rem; color: var(--accent-green); margin-left: 0.2rem; }}
        
        .modal-footer-bar {{ padding: 1.2rem 2rem; border-top: 1px solid var(--border-default); display: flex; justify-content: flex-end; }}
        .modal-done-btn {{ background-color: var(--accent-green); color: #000000; font-weight: 700; border: none; padding: 0.6rem 2rem; border-radius: 8px; cursor: pointer; font-size: 0.95rem; }}
        
        footer {{ text-align: center; margin-top: 3rem; color: var(--text-muted); font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header>
            <h1>Creative Minimalist Reading Dashboard v3</h1>
            <p class="description">A premium reading activity journal and micro-database tracker.</p>
        </header>
        
        <div class="main-grid">
            <div class="left-calendar-card">
                <div class="calendar-date-group">
                    <div class="cal-month-day">{month_en} {day_num}</div>
                    <div class="cal-full-date">{full_date_en}</div>
                </div>
                <div class="quote-content">“读书不是为了雄辩 and 驳斥，也不是为了轻信 and 盲从，而是为了思考 and 权衡。”</div>
                <div class="quote-meta">《谈读书》 · 弗朗西斯·培根</div>
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
                        <div class="progress-container"><div class="progress-bar" style="width: {stats['this_month_percent']}%"></div></div>
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
                    {heatmap_html}
                </div>
            </div>
        </div>
        
        <section class="library-section-container">
            <div class="library-block-header">
                <span class="icon">📗</span>
                <span>Book Highlights (书摘记录)</span>
            </div>
            <div class="premium-library-grid">
                {books_html}
            </div>
        </section>
    </div>
    
    <div class="modal-overlay" id="clippingModal" onclick="closeClippingModal(event)">
        <div class="modal-window-wrapper" onclick="event.stopPropagation()">
            <div class="modal-header-bar">
                <div>
                    <div class="modal-book-title" id="modalBookTitle">Book Title</div>
                    <div class="modal-book-author" id="modalBookAuthor">Author Name</div>
                </div>
                <button class="modal-close-btn" onclick="closeClippingModal(null)">✕</button>
            </div>
            <div class="modal-scroll-body" id="modalScrollBody"></div>
            <div class="modal-footer-bar">
                <button class="modal-done-btn" onclick="closeClippingModal(null)">Done</button>
            </div>
        </div>
    </div>
    
    <script>
        const LAUNCHPAD_DATABASE = {json.dumps(js_clippings_payload, ensure_ascii=False)};
        
        function openClippingModal(bookId) {{
            const bookData = LAUNCHPAD_DATABASE[bookId];
            if (!bookData) return;
            
            document.getElementById('modalBookTitle').textContent = bookData.title;
            document.getElementById('modalBookAuthor').textContent = bookData.author;
            
            const scrollBody = document.getElementById('modalScrollBody');
            scrollBody.innerHTML = '';
            
            bookData.clippings.forEach(clip => {{
                const card = document.createElement('div');
                card.className = 'modal-clipping-card';
                card.innerHTML = `<div class="modal-clipping-text">${{clip.text}}</div>`;
                scrollBody.appendChild(card);
            }});
            
            document.getElementById('clippingModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}
        
        function closeClippingModal(event) {{
            if (event && event.target !== document.getElementById('clippingModal') && event !== null) return;
            document.getElementById('clippingModal').classList.remove('active');
            document.body.style.overflow = '';
        }}
    </script>
</body>
</html>"""
    
    if output_file is None:
        try:
            project_root = Path(str(READING_DATA_FILE)).parent.parent
            output_path = project_root / "index.html"
        except:
            output_path = Path(__file__).parent.parent / "index.html"
    else:
        output_path = Path(output_file)
        
    with open(str(output_path), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"🚀 V3 Master Dashboard successfully compiled to: {output_path.resolve()}")


def main():
    print("📖 Initializing V3 Premium Analytical Engine...")
    combined_data = parse_clippings_to_json()
    generate_html(combined_data)
    print("🏁 Version 3 Core通关!")


if __name__ == "__main__":
    main()
