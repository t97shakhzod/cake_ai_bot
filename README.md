# Ushbu bot Telegram kanallarini avtomatlashtirish, kontent aylanishini boshqarish va mijozlar bilan ishonchli muloqot o'rnatish uchun mo'ljallangan professional yordamchidir.

## 🎯 Loyiha Maqsadi
Kanalda "jonli" savdo muhitini yaratish, foydalanuvchilar ishonchini oshirish va sun'iy intellekt yordamida kanal egasiga kontent yaratishda ko'maklashish.

## ✨ Asosiy Imkoniyatlar
- **Dynamic Rotation:** Kanaldagi mavjud xabarlarni tahlil qilish va ularni avtomatik tarzda "lenta" ko'rinishida qayta aylantirish.
- **Expert Tips & Education:** Bot ichiga o'rnatilgan `owner_growth.tips` va haftalik o'quv modullari orqali biznesni rivojlantirish bo'yicha maslahatlar berish.
- **Smart CRM:** Mijoz guruhga yozganda muloyim javob qaytarish va darhol kanal egasini xabardor qilish.
- **Content Discovery:** Kanal egasiga qiziqarli va trenddagi ma'lumotlarni topish bo'yicha yo'riqnomalar berish.

## 🛠 Texnologiyalar
- **Python 3.x**
- **python-telegram-bot** — Telegram API bilan ishlash uchun.
- **JobQueue** — Xabarlarni vaqtga qo'yish (scheduling) va avtomatik aylantirish uchun.
- **Python-dotenv** — Maxfiy ma'lumotlarni xavfsiz saqlash uchun.

## ⚙️ Sozlash va O'rnatish

> **Muhim:** Xavfsizlik nuqtai nazaridan barcha sozlamalar faqat `.env` fayli orqali amalga oshiriladi.

1. Loyihani yuklab oling:
   ```bash
   git clone https://github.com
   ```
2. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` faylini yarating va quyidagi ma'lumotlarni to'ldiring:
   ```env
   BOT_TOKEN=sizning_bot_tokeningiz
   ADMIN_ID=sizning_telegram_idyingiz
   CHANNEL_ID=@kanalingiz_yuzernami
   ```
4. Botni ishga tushiring:
   ```bash
   python main.py
   ```

## 📂 Loyiha Tuzilishi
- `main.py` — Botning asosiy kirish nuqtasi.
- `owner_growth.tips` — Expert darajasidagi biznes maslahatlari.
- `channel_rotation.json` — Kontent aylanishi uchun ma'lumotlar bazasi.
