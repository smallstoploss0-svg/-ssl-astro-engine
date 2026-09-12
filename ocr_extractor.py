import re
import os
import json
from PIL import Image

def get_ocr_lines_with_coords(image_path):
    if not os.path.exists(image_path):
        return []
    try:
        import winocr
        img = Image.open(image_path)
        # 2X resize for high-resolution WinRT OCR accuracy
        img2 = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        res_op = winocr.recognize_pil(img2, lang="en-US")
        if hasattr(res_op, 'get'):
            res = res_op.get()
        else:
            res = res_op
        
        lines = []
        for line in getattr(res, 'lines', []):
            txt = line.text.strip()
            if not txt or not line.words:
                continue
            rect = line.words[0].bounding_rect
            lines.append({
                'text': txt,
                'y': rect.y,
                'x': rect.x
            })
        return lines
    except Exception as e:
        print(f"[winocr error] {e}")
        return []

def parse_report_from_ocr(image_path, asset_type="NIFTY"):
    lines = get_ocr_lines_with_coords(image_path)
    if not lines:
        return {}, []

    full_text = " ".join([l['text'] for l in lines])
    meta = {}

    # 1. Metadata Parsing
    nak_m = re.search(r'NAKSHATRA:\s*([A-Za-z0-9\s\(\)\-]+)', full_text, re.IGNORECASE)
    if nak_m:
        meta['nakshatra'] = nak_m.group(1).split('-')[0].strip()

    pada_m = re.search(r'PADA\s*([1-4])', full_text, re.IGNORECASE)
    if pada_m:
        meta['pada'] = f"PADA {pada_m.group(1)}"

    grade_m = re.search(r'DAY GRADE:\s*([A-Za-z0-9\s\(\)\/]+)', full_text, re.IGNORECASE)
    if grade_m:
        raw_g = grade_m.group(1).strip()
        clean_g = raw_g.replace('Z ', '').replace('z ', '').strip()
        meta['day_grade'] = "💎 " + clean_g

    vol_m = re.search(r'VOLATILITY STATUS:\s*([A-Za-z0-9\s]+)', full_text, re.IGNORECASE)
    if vol_m:
        meta['volatility_status'] = vol_m.group(1).split('-')[0].strip()

    # 2. Time & Rating Extraction paired by Y-coordinate
    items = []
    for line in lines:
        txt = line['text']
        y_val = line['y']

        # Time extraction
        tm = re.search(r'(\d{1,2})[:\.](\d{2})\s*(AM|PM)', txt, re.IGNORECASE)
        if tm:
            hr = int(tm[1])
            mn = int(tm[2])
            ampm = tm[3].upper()
            if ampm == 'PM' and hr < 12: hr += 12
            if ampm == 'AM' and hr == 12: hr = 0
            time_val = f"{(hr%12 or 12):02d}:{mn:02d} {ampm}"
            is_key_pivot = ('KEY PIVOT' in txt or 'MASTER EXPLOSION' in txt)
            items.append({
                'type': 'time',
                'y': y_val,
                'hr': hr,
                'mn': mn,
                'time_val': time_val,
                'raw': txt,
                'is_key_pivot': is_key_pivot
            })

        # Rating extraction
        sm = re.search(r'(\d\.\d)\s*STAR', txt, re.IGNORECASE)
        if sm:
            items.append({'type': 'star', 'y': y_val, 'rating': f"{sm[1]} STAR"})
        elif 'MASTER' in txt and not any(k in txt for k in ['ENGINE', 'DIAMOND', 'RULES', 'REVERSAL']):
            items.append({'type': 'star', 'y': y_val, 'rating': '4.0 STAR MASTER'})

    time_items = [i for i in items if i['type'] == 'time']
    star_items = [i for i in items if i['type'] == 'star']

    # Filter out footer text (Y > 1100 in Nifty 2X, Y > 1500 in Gold 2X)
    table_times = []
    for t in time_items:
        if asset_type == 'NIFTY' and t['y'] > 1100:
            continue
        if asset_type == 'GOLD' and t['y'] > 1500:
            continue
        table_times.append(t)

    slots = []
    seen = set()

    for t in table_times:
        if t['time_val'] in seen:
            continue
        seen.add(t['time_val'])

        # Pair rating by Y-coordinate
        matching_star = '2.0 STAR'
        if t['is_key_pivot']:
            matching_star = '4.0 STAR MASTER'
        else:
            min_dist = 999
            for s in star_items:
                dist = abs(s['y'] - t['y'])
                if dist < min_dist and dist < 45:
                    min_dist = dist
                    matching_star = s['rating']

        is_master = ('MASTER' in matching_star or '4.0' in matching_star or t['is_key_pivot'])

        if is_master or '4.0' in matching_star:
            rating_text = '4.0 STAR ★★★★☆ (MASTER)'
            score = 4.5
        elif '3.0' in matching_star:
            rating_text = '3.0 STAR ★★★☆☆ (MAJOR)'
            score = 3.5
        elif '2.5' in matching_star:
            rating_text = '2.5 STAR ★★½☆☆'
            score = 3.0
        elif '2.0' in matching_star:
            rating_text = '2.0 STAR ★★☆☆☆'
            score = 2.5
        elif '1.5' in matching_star:
            rating_text = '1.5 STAR ★½☆☆☆'
            score = 2.0
        else:
            rating_text = f"{matching_star}"
            score = 2.5

        formatted = f"{t['time_val']}"

        slots.append({
            'formatted': formatted,
            'time_str': t['time_val'],
            'hour': t['hr'],
            'minute': t['mn'],
            'rating': rating_text,
            'score': score,
            'is_master': is_master
        })

    slots.sort(key=lambda x: (x['hour'], x['minute']))
    return meta, slots

if __name__ == '__main__':
    for path, asset in [(r"D:\Projects\reports\nifty_raw.png", 'NIFTY'), (r"D:\Projects\reports\gold_raw.png", 'GOLD')]:
        if os.path.exists(path):
            meta, slots = parse_report_from_ocr(path, asset)
            print(f"=== {asset} METADATA ===", meta)
            print(f"=== {asset} SLOTS ({len(slots)}) ===")
            for s in slots:
                print(f"  {s['time_str']} -> {s['rating']}")
