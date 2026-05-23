import os
import requests
from datetime import datetime, timedelta

# ─── AYARLAR ─────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN",  "8912653563:AAFXKvL3pxm_YM0kOR2WfHxrC3HO43fIXzQ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6604274615")

ROTALAR = [
    {"hedef": "IST", "sehir": "İstanbul 🇹🇷",      "esik": 150},
    {"hedef": "SAW", "sehir": "İstanbul Sabiha 🇹🇷","esik": 150},
    {"hedef": "TYO", "sehir": "Tokyo 🇯🇵",          "esik": 500},
    {"hedef": "BKK", "sehir": "Bangkok 🇹🇭",        "esik": 300},
    {"hedef": "DXB", "sehir": "Dubai 🇦🇪",          "esik": 200},
    {"hedef": "KUL", "sehir": "Kuala Lumpur 🇲🇾",   "esik": 300},
    {"hedef": "SIN", "sehir": "Singapur 🇸🇬",       "esik": 400},
    {"hedef": "ICN", "sehir": "Seul 🇰🇷",           "esik": 400},
    {"hedef": "DOH", "sehir": "Doha 🇶🇦",           "esik": 200},
    {"hedef": "TAS", "sehir": "Taşkent 🇺🇿",        "esik": 80},
    {"hedef": "TBS", "sehir": "Tiflis 🇬🇪",         "esik": 120},
    {"hedef": "GYD", "sehir": "Bakü 🇦🇿",           "esik": 120},
    {"hedef": "FRU", "sehir": "Bişkek 🇰🇬",         "esik": 60},
    {"hedef": "CMN", "sehir": "Kazablanka 🇲🇦",     "esik": 400},
    {"hedef": "TUN", "sehir": "Tunus 🇹🇳",          "esik": 350},
    {"hedef": "SEZ", "sehir": "Seyşeller 🇸🇨",      "esik": 600},
    {"hedef": "BEG", "sehir": "Belgrad 🇷🇸",        "esik": 300},
]

# ─── TELEGRAM ────────────────────────────────────────────────────────────────

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

# ─── FİYAT ÇEKME (Aviasales) ─────────────────────────────────────────────────

def fiyat_getir(varis):
    """
    Aviasales açık API - token gerektirmez.
    Önümüzdeki 6 ay içindeki en ucuz fiyatı döner.
    """
    # Önümüzdeki 6 ay için aylık en ucuz fiyatları çek
    en_ucuz_fiyat = None
    en_ucuz_tarih = None

    bugun = datetime.now()

    for ay_offset in range(1, 7):  # 1-6 ay sonrası
        hedef_ay = bugun + timedelta(days=30 * ay_offset)
        ay_str = hedef_ay.strftime("%Y-%m")

        url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
        params = {
            "origin": "ALA",
            "destination": varis,
            "departure_at": ay_str,
            "currency": "usd",
            "sorting": "price",
            "limit": 1,
            "unique": "false",
            "token": "pubtoken"  # Bu endpoint pubtoken kabul eder
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            if data.get("success") and data.get("data"):
                fiyat = data["data"][0].get("price")
                tarih = data["data"][0].get("departure_at", "")[:10]
                if fiyat and (en_ucuz_fiyat is None or fiyat < en_ucuz_fiyat):
                    en_ucuz_fiyat = fiyat
                    en_ucuz_tarih = tarih
        except Exception as e:
            print(f"   Hata ({ay_str}): {e}")

    return en_ucuz_fiyat, en_ucuz_tarih

# ─── ANA KONTROL ─────────────────────────────────────────────────────────────

def ucus_kontrol():
    print(f"\n{'='*50}")
    print(f"🔍 Kontrol: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*50}\n")

    firsatlar = []

    for rota in ROTALAR:
        hedef = rota["hedef"]
        sehir = rota["sehir"]
        esik  = rota["esik"]

        print(f"🔎 ALA → {hedef} ({sehir})...")
        fiyat, tarih = fiyat_getir(hedef)

        if fiyat is None:
            print(f"   ⚠️  Veri yok")
            continue

        print(f"   💰 En ucuz: ${fiyat}  (eşik: ${esik})  [{tarih}]")

        if fiyat <= esik:
            indirim = round((1 - fiyat / esik) * 100)
            firsatlar.append({
                "sehir": sehir, "hedef": hedef,
                "fiyat": fiyat, "tarih": tarih,
                "esik": esik,   "indirim": indirim
            })
            print(f"   🔥 FIRSAT! %{indirim} daha ucuz!")

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
        print(f"\n🎉 {len(firsatlar)} fırsat Telegram'a gönderildi!")
    else:
        # Fırsat yoksa da günlük özet gönder
        mesaj = (
            f"✈️ <b>Günlük Uçuş Raporu</b>\n\n"
            f"📍 Kalkış: Almatı (ALA)\n"
            f"🔍 {len(ROTALAR)} rota kontrol edildi\n"
            f"😴 Şu an eşiğin altında fiyat yok.\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        telegram_gonder(mesaj)
        print("\n😴 Fırsat yok, özet gönderildi.")

    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    ucus_kontrol()
