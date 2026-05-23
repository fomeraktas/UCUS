import os
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "8912653563:AAFXKvL3pxm_YM0kOR2WfHxrC3HO43fIXzQ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6604274615")

ROTALAR = [
    {"hedef": "IST", "sehir": "İstanbul 🇹🇷",       "esik": 150},
    {"hedef": "SAW", "sehir": "İstanbul Sabiha 🇹🇷", "esik": 150},
    {"hedef": "NRT", "sehir": "Tokyo 🇯🇵",           "esik": 500},
    {"hedef": "BKK", "sehir": "Bangkok 🇹🇭",         "esik": 300},
    {"hedef": "DXB", "sehir": "Dubai 🇦🇪",           "esik": 200},
    {"hedef": "KUL", "sehir": "Kuala Lumpur 🇲🇾",    "esik": 300},
    {"hedef": "SIN", "sehir": "Singapur 🇸🇬",        "esik": 400},
    {"hedef": "ICN", "sehir": "Seul 🇰🇷",            "esik": 400},
    {"hedef": "DOH", "sehir": "Doha 🇶🇦",            "esik": 200},
    {"hedef": "TAS", "sehir": "Taşkent 🇺🇿",         "esik": 80},
    {"hedef": "TBS", "sehir": "Tiflis 🇬🇪",          "esik": 120},
    {"hedef": "GYD", "sehir": "Bakü 🇦🇿",            "esik": 120},
    {"hedef": "FRU", "sehir": "Bişkek 🇰🇬",          "esik": 60},
    {"hedef": "CMN", "sehir": "Kazablanka 🇲🇦",      "esik": 400},
    {"hedef": "TUN", "sehir": "Tunus 🇹🇳",           "esik": 350},
    {"hedef": "SEZ", "sehir": "Seyşeller 🇸🇨",       "esik": 600},
    {"hedef": "BEG", "sehir": "Belgrad 🇷🇸",         "esik": 300},
]

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mesaj,
            "parse_mode": "HTML"
        }, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram mesajı gönderildi!")
        else:
            print(f"❌ Telegram hatası: {r.text}")
    except Exception as e:
        print(f"❌ Telegram bağlantı hatası: {e}")

def fiyat_getir(varis):
    """
    Aviasales v3 get_one_way_prices endpoint
    """
    bugun = datetime.now()

    # 3 farklı endpoint dene
    endpointler = [
        {
            "url": "https://api.aviasales.com/aviasales/v3/get_one_way_prices",
            "params": {
                "origin": "ALA",
                "destination": varis,
                "currency": "usd",
                "token": "pubtoken",
                "limit": 1,
            }
        },
        {
            "url": "https://api.travelpayouts.com/v1/prices/cheap",
            "params": {
                "origin": "ALA",
                "destination": varis,
                "currency": "usd",
                "token": "pubtoken",
                "page": 1,
                "limit": 1,
            }
        },
        {
            "url": "https://api.travelpayouts.com/v2/prices/month-matrix",
            "params": {
                "currency": "usd",
                "origin": "ALA",
                "destination": varis,
                "show_to_affiliates": "true",
                "month": (bugun + timedelta(days=30)).strftime("%Y-%m-01"),
                "token": "pubtoken",
            }
        },
    ]

    for ep in endpointler:
        try:
            r = requests.get(ep["url"], params=ep["params"], timeout=10)
            raw = r.text.strip()
            print(f"   [{ep['url'].split('/')[-1]}] status={r.status_code} raw_ilk_100={raw[:100]!r}")

            if r.status_code != 200:
                continue

            # JSON parse dene
            try:
                data = r.json()
            except Exception:
                print(f"   JSON parse hata, raw: {raw[:200]}")
                continue

            # Farklı response formatlarını dene
            # Format 1: {"data": {"IST": {"price": 100, ...}}}
            if data.get("data") and isinstance(data["data"], dict):
                hedef_data = data["data"].get(varis)
                if hedef_data:
                    if isinstance(hedef_data, dict):
                        fiyat = hedef_data.get("price")
                        tarih = hedef_data.get("depart_date", "bilinmiyor")
                        if fiyat:
                            return fiyat, tarih
                    elif isinstance(hedef_data, list) and hedef_data:
                        fiyat = hedef_data[0].get("price")
                        tarih = hedef_data[0].get("depart_date", "bilinmiyor")
                        if fiyat:
                            return fiyat, tarih

            # Format 2: {"data": [{"price": 100, ...}]}
            if data.get("data") and isinstance(data["data"], list) and data["data"]:
                fiyat = data["data"][0].get("price")
                tarih = data["data"][0].get("depart_date", data["data"][0].get("departure_at", "bilinmiyor"))[:10]
                if fiyat:
                    return fiyat, tarih

            # Format 3: {"price": 100, ...} direkt
            if data.get("price"):
                return data["price"], data.get("depart_date", "bilinmiyor")

            print(f"   Tanınan format yok. Tam JSON: {str(data)[:300]}")

        except Exception as e:
            print(f"   hata: {e}")

    return None, None

def ucus_kontrol():
    print(f"\n{'='*50}")
    print(f"🔍 Kontrol: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*50}\n")

    firsatlar = []
    veri_gelen = 0

    # İlk önce sadece IST ile test et
    test_rotalar = ROTALAR[:3]  # İlk 3 rotayı test et

    for rota in test_rotalar:
        hedef = rota["hedef"]
        sehir = rota["sehir"]
        esik  = rota["esik"]

        print(f"🔎 ALA → {hedef} ({sehir})...")
        fiyat, tarih = fiyat_getir(hedef)

        if fiyat is None:
            print(f"   ⚠️  Veri yok\n")
            continue

        veri_gelen += 1
        print(f"   ✅ En ucuz: ${fiyat} (eşik: ${esik}) [{tarih}]\n")

        if fiyat <= esik:
            indirim = round((1 - fiyat / esik) * 100)
            firsatlar.append({
                "sehir": sehir, "hedef": hedef,
                "fiyat": fiyat, "tarih": tarih,
                "esik":  esik,  "indirim": indirim
            })

    print(f"\nTest sonucu — veri gelen: {veri_gelen}/{len(test_rotalar)}")

    # Telegram'a test sonucunu gönder
    mesaj = (
        f"🔧 <b>API Test Sonucu</b>\n\n"
        f"Veri gelen: {veri_gelen}/{len(test_rotalar)} rota\n"
    )
    if firsatlar:
        for f in firsatlar:
            mesaj += f"\n✈️ {f['sehir']}: ${f['fiyat']}"
    mesaj += f"\n\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    telegram_gonder(mesaj)

    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    ucus_kontrol()
