import os
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "8912653563:AAFXKvL3pxm_YM0kOR2WfHxrC3HO43fIXzQ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6604274615")
TP_TOKEN         = os.environ.get("TP_TOKEN",         "da9c5980e5f451f6be1fdd3eea455b62")

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
    bugun = datetime.now()

    # 1. DENEME: En ucuz biletler (genel)
    try:
        r = requests.get(
            "https://api.travelpayouts.com/v1/prices/cheap",
            params={
                "origin": "ALA",
                "destination": varis,
                "currency": "usd",
                "token": TP_TOKEN,
            },
            timeout=10
        )
        print(f"   [cheap] status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            hedef = data.get("data", {}).get(varis)
            if hedef:
                # birden fazla tarih olabilir, en ucuzunu bul
                en_ucuz = min(hedef.values(), key=lambda x: x.get("price", 999999))
                fiyat = en_ucuz.get("price")
                tarih = en_ucuz.get("depart_date", "bilinmiyor")
                if fiyat:
                    print(f"   ✅ ${fiyat} — {tarih}")
                    return fiyat, tarih
    except Exception as e:
        print(f"   [cheap] hata: {e}")

    # 2. DENEME: Aylık en ucuz fiyatlar
    try:
        for ay_offset in range(1, 7):
            ay = (bugun + timedelta(days=30 * ay_offset)).strftime("%Y-%m-01")
            r = requests.get(
                "https://api.travelpayouts.com/v2/prices/month-matrix",
                params={
                    "currency": "usd",
                    "origin": "ALA",
                    "destination": varis,
                    "show_to_affiliates": "true",
                    "month": ay,
                    "token": TP_TOKEN,
                },
                timeout=10
            )
            print(f"   [month-matrix {ay[:7]}] status={r.status_code}")
            if r.status_code == 200:
                data = r.json()
                if data.get("data"):
                    en_ucuz = min(data["data"], key=lambda x: x.get("price", 999999))
                    fiyat = en_ucuz.get("price")
                    tarih = en_ucuz.get("depart_date", "bilinmiyor")
                    if fiyat:
                        print(f"   ✅ ${fiyat} — {tarih}")
                        return fiyat, tarih
    except Exception as e:
        print(f"   [month-matrix] hata: {e}")

    # 3. DENEME: Latest prices
    try:
        r = requests.get(
            "https://api.travelpayouts.com/v1/prices/latest",
            params={
                "currency": "usd",
                "origin": "ALA",
                "destination": varis,
                "period_type": "month",
                "one_way": "true",
                "limit": 1,
                "sorting": "price",
                "token": TP_TOKEN,
            },
            timeout=10
        )
        print(f"   [latest] status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                fiyat = data["data"][0].get("value")
                tarih = data["data"][0].get("depart_date", "bilinmiyor")
                if fiyat:
                    print(f"   ✅ ${fiyat} — {tarih}")
                    return fiyat, tarih
    except Exception as e:
        print(f"   [latest] hata: {e}")

    return None, None

def ucus_kontrol():
    print(f"\n{'='*50}")
    print(f"🔍 Kontrol: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*50}\n")

    firsatlar = []
    veri_gelen = 0

    for rota in ROTALAR:
        hedef = rota["hedef"]
        sehir = rota["sehir"]
        esik  = rota["esik"]

        print(f"🔎 ALA → {hedef} ({sehir})...")
        fiyat, tarih = fiyat_getir(hedef)

        if fiyat is None:
            print(f"   ⚠️  Veri yok\n")
            continue

        veri_gelen += 1
        print(f"   💰 En ucuz: ${fiyat} (eşik: ${esik}) [{tarih}]\n")

        if fiyat <= esik:
            indirim = round((1 - fiyat / esik) * 100)
            firsatlar.append({
                "sehir": sehir, "hedef": hedef,
                "fiyat": fiyat, "tarih": tarih,
                "esik":  esik,  "indirim": indirim
            })

    print(f"Toplam veri gelen: {veri_gelen}/{len(ROTALAR)}")

    if firsatlar:
        mesaj  = "🚨 <b>UCUZ UÇUŞ FIRSATI!</b> 🚨\n\n"
        mesaj += "📍 <b>Kalkış:</b> Almatı (ALA)\n\n"
        for f in sorted(firsatlar, key=lambda x: x["fiyat"]):
            mesaj += (
                f"✈️ <b>{f['sehir']}</b>\n"
                f"   💵 <b>${f['fiyat']}</b>  (normal ~${f['esik']})\n"
                f"   🔥 %{f['indirim']} indirimli!\n"
                f"   📅 {f['tarih']}\n\n"
            )
        mesaj += "🔗 <a href='https://www.aviasales.com/search/ALA'>Hemen bak →</a>\n"
        mesaj += f"\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        telegram_gonder(mesaj)
    elif veri_gelen > 0:
        mesaj = (
            f"✈️ <b>Günlük Rapor</b>\n\n"
            f"📍 Kalkış: Almatı (ALA)\n"
            f"🔍 {veri_gelen}/{len(ROTALAR)} rota kontrol edildi\n"
            f"😴 Eşiğin altında fiyat yok.\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        telegram_gonder(mesaj)
    else:
        mesaj = (
            f"⚠️ <b>API Sorunu</b>\n\n"
            f"Hiçbir rotadan veri alınamadı.\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        telegram_gonder(mesaj)

    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    ucus_kontrol()
