import os
from PIL import Image, ImageDraw, ImageFont

def generate_locked_report_image(
    instrument="NIFTY 50",
    date_str="11-SEP-2026 (FRIDAY)",
    nakshatra="PURVA PHALGUNI (VENUS) - PADA 3",
    day_grade="💎 DIAMOND MASTER (95/100)",
    volatility="NORMAL",
    annual_degree="172.71°",
    ruling_planet="VENUS (SHUKRA)",
    moon_longitude="142.12°",
    key_pivot="09:15 AM OPENING MASTER EXPLOSION",
    slots=[], # List of dicts: {"time": "09:49 AM", "session": "MORNING", "rating": "4.0 STAR ★★★★ MASTER 🔥🚨", "vol": "NORMAL", "notes": "...", "is_master": True, "star_val": "4.0"}
    trading_rules=[],
    output_path=r"C:\Users\welcome\Desktop\nifty_group_report.png"
):
    width = 1100
    row_height = 42
    num_slots = len(slots)
    height = 200 + 35 + (num_slots * row_height) + 110

    img = Image.new("RGB", (width, height), "#0F172A")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 24)
        font_subtitle = ImageFont.truetype("arialbd.ttf", 15)
        font_header = ImageFont.truetype("arialbd.ttf", 14)
        font_body = ImageFont.truetype("arial.ttf", 13)
        font_bold = ImageFont.truetype("arialbd.ttf", 13)
        font_small = ImageFont.truetype("arial.ttf", 11)
    except:
        font_title = font_subtitle = font_header = font_body = font_bold = font_small = ImageFont.load_default()

    # 1. Title Banner (Purple)
    draw.rectangle([0, 0, width, 70], fill="#6B21A8")
    draw.text((20, 14), f"☸ SMALLSTOPLOSS ASTRO MASTER ENGINE — {instrument.upper()}", fill="#FFFFFF", font=font_title)
    loop_txt = "(1-MIN LOOP PRECISION)" if "NIFTY" in instrument.upper() else "(5-MIN LOOP)"
    draw.text((20, 44), f"DAILY REVERSAL PREDICTION REPORT {loop_txt}", fill="#E9D5FF", font=font_subtitle)

    # 2. Date & Status Banner (Orange)
    draw.rectangle([0, 70, width, 115], fill="#EA580C")
    draw.text((20, 82), f"DATE: {date_str}  |  NAKSHATRA: {nakshatra}", fill="#FFFFFF", font=font_bold)
    draw.text((680, 82), f"DAY GRADE: {day_grade}", fill="#FEF08A", font=font_bold)

    # 3. Metadata Panel (Dark Grey)
    draw.rectangle([20, 130, width - 20, 185], fill="#1E293B", outline="#475569", width=1)
    draw.text((35, 142), f"⚡ VOLATILITY STATUS: {volatility}", fill="#22C55E", font=font_bold)
    draw.text((35, 162), f"📐 ANNUAL DEGREE: {annual_degree}", fill="#CBD5E1", font=font_body)
    draw.text((320, 142), f"🪐 RULING PLANET: {ruling_planet}", fill="#F472B6", font=font_bold)
    draw.text((320, 162), f"🗓️ TREND CHANGE DATES: 18-Sep & 19-Sep", fill="#FFD700", font=font_bold)
    draw.text((650, 142), f"🔥 KEY PIVOT: {key_pivot}", fill="#EF4444", font=font_bold)
    slots_txt = f"{num_slots} REFINED WINDOWS" if "NIFTY" in instrument.upper() else "SESSIONS COVERED: ASIAN, LONDON, NEW YORK"
    draw.text((650, 162), f"🎯 REVERSAL SLOTS: {slots_txt}", fill="#FACC15", font=font_bold)

    # 4. Table Headers (Blue)
    table_top = 200
    draw.rectangle([20, table_top, width - 20, table_top + 35], fill="#0284C7")
    headers = [("TIME (IST)", 35), ("SESSION", 160), ("REVERSAL LEVEL & RATING", 310), ("VOLATILITY", 680), ("ASTRO ENGINE NOTES", 820)]
    for text, x in headers:
        draw.text((x, table_top + 8), text, fill="#FFFFFF", font=font_header)

    # 5. Table Rows
    current_y = table_top + 35
    for s in slots:
        is_master = s.get("is_master", False) or "MASTER" in s.get("rating", "") or "4.0" in s.get("rating", "")
        star_str = s.get("star_val", "2.0")
        
        if is_master or "4.0" in star_str:
            bg_color = "#FEE2E2"
            text_color = "#DC2626"
        elif "3.0" in star_str:
            bg_color = "#FEFCE8"
            text_color = "#CA8A04"
        elif "2.5" in star_str:
            bg_color = "#FEF08A"
            text_color = "#D97706"
        else:
            bg_color = "#F8FAFC"
            text_color = "#1E293B"

        draw.rectangle([20, current_y, width - 20, current_y + row_height], fill=bg_color, outline="#CBD5E1", width=1)
        if is_master:
            draw.rectangle([20, current_y, 26, current_y + row_height], fill="#DC2626")

        draw.text((35, current_y + 11), s.get("time", ""), fill=text_color, font=font_bold)
        draw.text((160, current_y + 11), s.get("session", ""), fill="#475569", font=font_bold)
        draw.text((310, current_y + 11), s.get("rating", ""), fill=text_color, font=font_bold)
        draw.text((680, current_y + 11), s.get("vol", "NORMAL"), fill="#22C55E" if s.get("vol", "NORMAL") == "NORMAL" else "#C026D3", font=font_bold)
        draw.text((820, current_y + 11), s.get("notes", ""), fill="#1E293B", font=font_body)

        current_y += row_height

    # 6. Footer Rules Banner
    footer_top = current_y + 15
    rules_height = 30 + (len(trading_rules) * 20)
    draw.rectangle([20, footer_top, width - 20, footer_top + rules_height], fill="#1E293B", outline="#475569", width=1)
    draw.text((35, footer_top + 10), f"📌 TRADING RULES FOR {instrument.upper()}:", fill="#FACC15", font=font_bold)
    
    for idx, rule in enumerate(trading_rules):
        draw.text((35, footer_top + 30 + (idx * 18)), f"{idx+1}. {rule}", fill="#E2E8F0", font=font_small)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"✅ Locked Template Report PNG generated successfully at: {output_path}")

if __name__ == "__main__":
    print("Locked Report Image Generator Master Module Ready!")
