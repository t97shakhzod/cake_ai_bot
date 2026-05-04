# Cake AI bot — GitHub va portfolio uchun xavfsiz yo‘l-yo‘riq

Bu qo‘llanma loyihani **portfolio / ta’lim profilida** ko‘rsatish va **onlayn serverda** xavfsiz ishga tushirish uchun.

## 1. Xavfsizlik: nimani hech qachon GitHubga yuklamang

- **`.env`** — `BOT_TOKEN`, `CHANNEL_ID`, `OWNER_USER_ID` va boshqalar. Fayl `.gitignore` da bo‘lishi kerak (loyihada bor).
- **Shaxsiy telefon raqami, mijozlar bazasi, toʻlov kalitlari** — repoda joylashmasin.
- Token oqib ketgan bo‘lsa: [@BotFather](https://t.me/BotFather) orqali `/revoke` qilib yangi token oling va serverdagi `.env` ni yangilang.

## 2. Repozitoriyani tayyorlash

1. GitHubda yangi **public** yoki **private** repo yarating.
2. Loyihani yuklang; ishonch hosil qiling: repoda `.env` yo‘q.
3. `README` da qisqa: loyiha maqsadi, texnologiyalar (`Python`, `python-telegram-bot`, `JobQueue`), **sozlash faqat `.env` orqali** ekanini yozing.
4. Portfolio uchun: 2–3 ta skrin (bot javobi, kanal posti) — **skrinda token, telefon yoki shaxsiy ID bo‘lmasin**.

## 3. Onlayn ishga tushirish (tanlov)

Bot doimiy ishlashi uchun dastur **24/7** qayerdadir yurishi kerak: uy kompyuteri o‘chsa bot ham to‘xtaydi.

### Variant A: Railway, Render, Fly.io (PaaS)

- Loyihani GitHub bilan ulang.
- **Environment variables** panelida `.env` dagi o‘zgaruvchilarni qo‘lda kiriting (fayl yuklamang).
- **Start command** odatda: `python main.py`
- **Eslatma:** ba’zi bepul rejalar uxlash rejimiga o‘tadi — bot kechikishi mumkin; tijorat uchun pulli reja yaxshiroq.

### Variant B: VPS (DigitalOcean, Hetzner, va h.k.) + `systemd`

1. Serverda Python 3.9+ o‘rnating, reponi klonlang.
2. Virtual muhit: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
3. `/etc/systemd/system/cake-ai-bot.service` kabi servis yarating:

```ini
[Unit]
Description=Cake AI Telegram Bot
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/home/deploy/cake_ai_bot
EnvironmentFile=/home/deploy/cake_ai_bot/.env
ExecStart=/home/deploy/cake_ai_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. `sudo systemctl enable --now cake-ai-bot.service`

`.env` faylini serverda faqat egasi o‘qiy oladigan huquq bilan saqlang (`chmod 600 .env`).

## 4. Telegram tomonda

- Bot **kanalda admin** (xabar yuborish).
- Bot **izohlar guruhi**da xabar yuborishi mumkin.
- **Muhim:** Telegram Bot API kanal **tarixini** o‘qiy olmaydi — shuning uchun yangi postlar avtomatik yig‘iladi; eski postlar uchun `/qosh` ishlatiladi.

## 5. Portfolio / GitHub Education profili

- **Pinned** repoda: qisqa tavsif, stack, diagramma (ixtiyoriy).
- **Topics** qo‘ying: `python`, `telegram-bot`, `automation`, `small-business`.
- Agar talaba bo‘lsangiz: README da o‘z hissangiz (nima o‘rgandingiz) — kopipast emas, qisqa va halol bo‘lsin.

## 6. Tekshiruv ro‘yxati (deploy oldidan)

- [ ] Repoda `.env` yo‘q
- [ ] `BOT_TOKEN` faqat server/PaaS secretlarida
- [ ] `CHANNEL_ID`, `COMMENTS_GROUP_ID`, `OWNER_USER_ID` to‘g‘ri
- [ ] Ega botga `/start` yuborgan
- [ ] `pip install` da `python-telegram-bot[job-queue]` o‘rnatilgan
- [ ] Vaqt zonasi (`TIMEZONE`) mos

## 7. Yuridik va axloq

- Mijoz ma’lumotlarini maxfiy saqlang.
- Reklama va tavsiflar haqiqiy bo‘lsin — noto‘g‘ri va’dalar portfolio emas, risk.

---

*Bu fayl loyiha bilan birga berilgan — o‘qib, keyin o‘zingiz moslashtiring.*
