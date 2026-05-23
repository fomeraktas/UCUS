import os
import json
import requests
from datetime import datetime, timedelta

# ─── AYARLAR ─────────────────────────────────────────────────────────────────

AVIATION_KEY = os.environ.get("AVIATION_KEY", "e9795d80b207f98c1099015367033f72")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8912653563:AAFXKvL3pxm_YM0kOR2WfHxrC3HO43fIXzQ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6604274615")

# Türk pasaportuyla vizesiz/eTA ile gidilen destinasyonlar (ALA çıkışlı)
ROTALAR = [
    # ASYA
    {"hedef": "IST", "sehir": "İstanbul 🇹🇷",        "esik_fiyat": 150},
    {"hedef": "TYO", "sehir": "Tokyo 🇯🇵",            "esik_fiyat": 400},
    {"hedef": "BKK", "sehir": "Bangkok 🇹🇭",          "esik_fiyat": 250},
    {"hedef": "DXB", "sehir": "Dubai 🇦🇪",            "esik_fiyat": 200},
    {"hedef": "KUL", "sehir": "Kuala Lumpur 🇲🇾",     "esik_fiyat": 300},
    {"hedef": "SIN", "sehir": "Singapur 🇸🇬",         "esik_fiyat": 350},
    {"hedef": "ICN", "sehir": "Seul 🇰🇷",             "esik_fiyat": 350},
    {"hedef": "DOH", "sehir": "Doha 🇶🇦",             "esik_fiyat": 200},
    # ORTA ASYA / KAFKASYA
    {"hedef": "TAS", "sehir": "Taşkent 🇺🇿",          "esik_fiyat": 80},
    {"hedef": "TBS", "sehir": "Tiflis 🇬🇪",           "esik_fiyat": 100},
    {"hedef": "GYD", "sehir": "Bakü 🇦🇿",             "esik_fiyat": 100},
    {"hedef": "FRU", "sehir": "Bişkek 🇰🇬",           "esik_fiyat": 60},
    # AVRUPA (Balkalar - vizesiz)
    {"hedef": "TIA", "sehir": "Tiran 🇦🇱",            "esik_fiyat": 250},
    {"hedef": "SKP", "sehir": "Üsküp 🇲🇰",            "esik_fiyat": 250},
    {"hedef": "BEG", "sehir": "Belgrad 🇷🇸",          "esik_fiyat": 280},
    # AFRİKA
    {"hedef": "CMN", "sehir": "Kazablanka 🇲🇦",       "esik_fiyat": 350},
    {"hedef": "TUN", "sehir": "Tunus 🇹🇳",            "esik_fiyat": 300},
    {"hedef": "SEZ", "sehir": "Seyşeller 🇸🇨",        "esik_fiyat": 500},
]

# ─── FIYAT ÇEKME ─────────────────────────────────────────────────────────────

def fiyat_kontrol_et(kalkis, varis, tarih):
    """Aviationstack API ile uçuş bilgisi çek"""
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": AVIATION_KEY,
        "dep_iata": kalkis,
        "arr_iata": varis,
        "flight_date": tarih,
        "limit": 5
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get("data"):
            return data["data"]
        return []
    except Exception as e:
        print(f"API hatası ({kalkis}→{varis}): {e}")
        return []


def travelpayouts_fiyat(kalkis, varis):
    """Travelpayouts API ile ucuz bilet ara (ücretsiz)"""
    # Önümüzdeki 90 gün içindeki en ucuz fiyatı çek
    url = "https://api.travelpayouts.com/v1/prices/cheap"
    params = {
        "origin": kalkis,
        "destination": varis,
        "currency": "usd",
        "token": "pubtoken"  # Travelpayouts public token
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get("data") and data["data"].get(varis):
            fiyatlar = data["data"][varis]
            en_ucuz = min(fiyatlar.values(), key=lambda x: x.get("price", 99999))
            return en_ucuz.get("price"), en_ucuz.get("depart_date")
        return None, None
    except Exception as e:
        print(f"Travelpayouts hatası ({kalkis}→{varis}): {e}")
        return None, None

# ─── TELEGRAM MESAJ ──────────────────────────────────────────────────────────

def telegram_gonder(mesaj):
    """Telegram'a mesaj gönder"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram mesajı gönderildi!")
        else:
            print(f"❌ Telegram hatası: {r.text}")
    except Exception as e:
        print(f"❌ Telegram bağlantı hatası: {e}")


def test_mesaji_gonder():
    """Botun çalıştığını test et"""
    mesaj = (
        "✈️ <b>Uçuş Alarm Botu Aktif!</b>\n\n"
        "Merhaba! Bot başarıyla kuruldu.\n"
        f"🕐 Kontrol saati: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"🗺️ Takip edilen rota sayısı: {len(ROTALAR)}\n"
        "Ucuz uçuş bulduğumda sana haber vereceğim! 🚀"
    )
    telegram_gonder(mesaj)

# ─── ANA KONTROL ─────────────────────────────────────────────────────────────

def ucus_kontrol():
    print(f"\n{'='*50}")
    print(f"🔍 Uçuş kontrolü başlıyor: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*50}\n")

    bulunan_firsatlar = []

    for rota in ROTALAR:
        hedef = rota["hedef"]
        sehir = rota["sehir"]
        esik = rota["esik_fiyat"]

        print(f"🔎 ALA → {hedef} ({sehir}) kontrol ediliyor...")

        fiyat, tarih = travelpayouts_fiyat("ALA", hedef)

        if fiyat is None:
            print(f"   ⚠️  Fiyat bilgisi alınamadı")
            continue

        print(f"   💰 En ucuz: ${fiyat} ({tarih})")

        if fiyat <= esik:
            bulunan_firsatlar.append({
                "sehir": sehir,
                "hedef": hedef,
                "fiyat": fiyat,
                "tarih": tarih,
                "esik": esik,
                "indirim": round((1 - fiyat / esik) * 100)
            })
            print(f"   🔥 FIRSAT BULUNDU! Eşik: ${esik}")

    # Fırsat varsa Telegram'a gönder
    if bulunan_firsatlar:
        mesaj = "🚨 <b>UCUZ UÇUŞ FIRSATI!</b> 🚨\n\n"
        mesaj += f"📍 <b>Kalkış:</b> Almatı (ALA)\n\n"

        for f in sorted(bulunan_firsatlar, key=lambda x: x["fiyat"]):
            mesaj += (
                f"✈️ <b>{f['sehir']}</b>\n"
                f"   💵 Fiyat: <b>${f['fiyat']}</b> (normal: ${f['esik']})\n"
                f"   🔥 %{f['indirim']} daha ucuz!\n"
                f"   📅 Tarih: {f['tarih']}\n\n"
            )

        mesaj += "🔗 Hemen bak: https://www.aviasales.com/search/ALA\n"
        mesaj += f"\n⏰ Kontrol: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        telegram_gonder(mesaj)
        print(f"\n🎉 {len(bulunan_firsatlar)} fırsat Telegram'a gönderildi!")
    else:
        print("\n😴 Şu an fırsat yok. Yarın tekrar kontrol edeceğim.")

    print(f"\n{'='*50}\n")


# ─── ÇALIŞTIR ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_mesaji_gonder()
    else:
        ucus_kontrol()
