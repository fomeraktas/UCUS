# ✈️ Almatı Uçuş Alarm Botu

Almatı'dan (ALA) Türk pasaportuyla vizesiz gidilen ülkelere ucuz uçuş bulduğunda Telegram'dan bildirim gönderir.

## 🗺️ Takip Edilen Rotalar

| Destinasyon | Fiyat Eşiği |
|-------------|-------------|
| İstanbul 🇹🇷 | $150 |
| Tokyo 🇯🇵 | $400 |
| Bangkok 🇹🇭 | $250 |
| Dubai 🇦🇪 | $200 |
| Singapur 🇸🇬 | $350 |
| Seul 🇰🇷 | $350 |
| Taşkent 🇺🇿 | $80 |
| Tiflis 🇬🇪 | $100 |
| Bakü 🇦🇿 | $100 |
| ve daha fazlası... | |

## ⚙️ GitHub Secrets Ayarları

Repository → Settings → Secrets → New repository secret:

| Secret Adı | Değer |
|------------|-------|
| `AVIATION_KEY` | Aviationstack API key'in |
| `TELEGRAM_TOKEN` | Telegram bot token'ın |
| `TELEGRAM_CHAT_ID` | Telegram chat ID'n |

## 🕐 Çalışma Saatleri

Her **6 saatte bir** otomatik kontrol yapar:
- 00:00 UTC (03:00 Almatı)
- 06:00 UTC (09:00 Almatı)  
- 12:00 UTC (15:00 Almatı)
- 18:00 UTC (21:00 Almatı)

## 🧪 Manuel Test

GitHub → Actions → "Uçuş Fiyat Kontrolü" → "Run workflow"

## 💡 Fiyat Eşiği Değiştirmek

`ucus_alarm.py` dosyasındaki `ROTALAR` listesinde `esik_fiyat` değerini değiştir.
