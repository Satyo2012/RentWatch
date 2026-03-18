"""Parse SUUMO/HOME'S search URLs to extract human-readable condition tags."""

from urllib.parse import urlparse, parse_qs

# SUUMO area codes (都道府県)
SUUMO_PREFECTURES = {
    "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県", "05": "秋田県",
    "06": "山形県", "07": "福島県", "08": "茨城県", "09": "栃木県", "10": "群馬県",
    "11": "埼玉県", "12": "千葉県", "13": "東京都", "14": "神奈川県", "15": "新潟県",
    "16": "富山県", "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
    "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県", "25": "滋賀県",
    "26": "京都府", "27": "大阪府", "28": "兵庫県", "29": "奈良県", "30": "和歌山県",
    "31": "鳥取県", "32": "島根県", "33": "岡山県", "34": "広島県", "35": "山口県",
    "36": "徳島県", "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
    "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県", "45": "宮崎県",
    "46": "鹿児島県", "47": "沖縄県",
}

# SUUMO layout codes
SUUMO_LAYOUTS = {
    "01": "ワンルーム", "02": "1K", "03": "1DK", "04": "1LDK",
    "05": "2K", "06": "2DK", "07": "2LDK",
    "08": "3K", "09": "3DK", "10": "3LDK",
    "11": "4K", "12": "4DK", "13": "4LDK以上",
}

# Tokyo ward codes (13xxx)
TOKYO_WARDS = {
    "13101": "千代田区", "13102": "中央区", "13103": "港区", "13104": "新宿区",
    "13105": "文京区", "13106": "台東区", "13107": "墨田区", "13108": "江東区",
    "13109": "品川区", "13110": "目黒区", "13111": "大田区", "13112": "世田谷区",
    "13113": "渋谷区", "13114": "中野区", "13115": "杉並区", "13116": "豊島区",
    "13117": "北区", "13118": "荒川区", "13119": "板橋区", "13120": "練馬区",
    "13121": "足立区", "13122": "葛飾区", "13123": "江戸川区",
}

# Major city ward codes
OSAKA_WARDS = {
    "27102": "都島区", "27103": "福島区", "27104": "此花区", "27106": "西区",
    "27107": "港区", "27108": "大正区", "27109": "天王寺区", "27111": "浪速区",
    "27113": "西淀川区", "27114": "東淀川区", "27115": "東成区", "27116": "生野区",
    "27117": "旭区", "27118": "城東区", "27119": "阿倍野区", "27120": "住吉区",
    "27121": "東住吉区", "27122": "西成区", "27123": "淀川区", "27124": "鶴見区",
    "27125": "住之江区", "27126": "平野区", "27127": "北区", "27128": "中央区",
}

ALL_AREAS = {**TOKYO_WARDS, **OSAKA_WARDS}


def parse_suumo_url(url: str) -> list[str]:
    """Extract search condition tags from a SUUMO URL."""
    tags = []
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Prefecture
    ta_list = params.get("ta", [])
    for ta in ta_list:
        name = SUUMO_PREFECTURES.get(ta)
        if name:
            tags.append(name)

    # City/Ward
    sc_list = params.get("sc", [])
    for sc in sc_list:
        name = ALL_AREAS.get(sc)
        if name:
            tags.append(name)

    # Price range (万円)
    cb = params.get("cb", [None])[0]
    ct = params.get("ct", [None])[0]
    if cb and ct:
        if cb == "0.0" or cb == "0":
            tags.append(f"〜{ct}万円")
        else:
            tags.append(f"{cb}〜{ct}万円")
    elif cb and cb != "0.0" and cb != "0":
        tags.append(f"{cb}万円〜")
    elif ct:
        tags.append(f"〜{ct}万円")

    # Layout
    md_list = params.get("md", [])
    for md in md_list:
        name = SUUMO_LAYOUTS.get(md)
        if name:
            tags.append(name)

    # Walk minutes from station
    et = params.get("et", [None])[0]
    if et and et != "9999999":
        tags.append(f"徒歩{et}分以内")

    # Area (専有面積)
    mb = params.get("mb", [None])[0]
    mt = params.get("mt", [None])[0]
    if mb and mt:
        tags.append(f"{mb}〜{mt}m²")
    elif mb:
        tags.append(f"{mb}m²〜")
    elif mt:
        tags.append(f"〜{mt}m²")

    # Building age
    nk = params.get("nk", [None])[0]
    if nk and nk != "9999999":
        tags.append(f"築{nk}年以内")

    # Extract from URL path (e.g., station name in path)
    path = parsed.path
    if "/eki/" in path:
        parts = path.split("/eki/")
        if len(parts) > 1:
            station_part = parts[1].strip("/")
            if station_part:
                tags.append(f"駅:{station_part}")

    return tags


def parse_homes_url(url: str) -> list[str]:
    """Extract search condition tags from a HOME'S URL."""
    tags = []
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    path = parsed.path

    # Extract area from path segments
    # HOME'S URLs often contain area info in the path like /chintai/tokyo/shibuya/
    path_parts = [p for p in path.split("/") if p]

    # Prefecture mapping from URL slug
    prefecture_slugs = {
        "tokyo": "東京都", "kanagawa": "神奈川県", "osaka": "大阪府",
        "saitama": "埼玉県", "chiba": "千葉県", "kyoto": "京都府",
        "hyogo": "兵庫県", "aichi": "愛知県", "fukuoka": "福岡県",
        "hokkaido": "北海道",
    }

    ward_slugs = {
        "shibuya": "渋谷区", "shinjuku": "新宿区", "minato": "港区",
        "setagaya": "世田谷区", "meguro": "目黒区", "shinagawa": "品川区",
        "nakano": "中野区", "suginami": "杉並区", "toshima": "豊島区",
        "chiyoda": "千代田区", "chuo": "中央区", "bunkyo": "文京区",
        "taito": "台東区", "sumida": "墨田区", "koto": "江東区",
        "ota": "大田区", "kita": "北区", "arakawa": "荒川区",
        "itabashi": "板橋区", "nerima": "練馬区", "adachi": "足立区",
        "katsushika": "葛飾区", "edogawa": "江戸川区",
    }

    for part in path_parts:
        part_lower = part.lower()
        if part_lower in prefecture_slugs:
            tags.append(prefecture_slugs[part_lower])
        elif part_lower in ward_slugs:
            tags.append(ward_slugs[part_lower])

    # Price range from query params
    price_min = params.get("rent_low", params.get("priceLow", [None]))[0] if params.get("rent_low") or params.get("priceLow") else None
    price_max = params.get("rent_high", params.get("priceHigh", [None]))[0] if params.get("rent_high") or params.get("priceHigh") else None
    if price_min and price_max:
        tags.append(f"{price_min}〜{price_max}万円")
    elif price_min:
        tags.append(f"{price_min}万円〜")
    elif price_max:
        tags.append(f"〜{price_max}万円")

    # Layout
    layout_params = params.get("layout", params.get("madori", []))
    layout_names = {
        "1": "ワンルーム", "2": "1K", "3": "1DK", "4": "1LDK",
        "5": "2K", "6": "2DK", "7": "2LDK",
        "8": "3K", "9": "3DK", "10": "3LDK",
    }
    for lp in layout_params:
        name = layout_names.get(lp)
        if name:
            tags.append(name)

    # Walk minutes
    walk = params.get("walkMinutes", params.get("wm", [None]))
    if walk and walk[0]:
        tags.append(f"徒歩{walk[0]}分以内")

    return tags


def extract_tags(url: str, site: str) -> list[str]:
    """Extract search condition tags from a URL based on the site type."""
    if site == "suumo":
        return parse_suumo_url(url)
    elif site == "homes":
        return parse_homes_url(url)
    return []
