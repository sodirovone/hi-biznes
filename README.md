# HiWorld AI jamoa — Claude plagini

hiworld.club'dan. Claude bilan ~10 daqiqalik tanlovli savol-javob: biznesingizdagi ishlarni ko'rib chiqadi, qaysi ishni
qaysi AI xodim olishini, qanday nazorat bilan va qaysi tartibda joriy qilishni aniqlaydi. Natija — interaktiv xarita:
AI jamoa, har agent qanday ishlaydi, sizdan nima kerak, 0-hafta → 3-oy rejasi va nusxa olinadigan yo'riqnomalar.
Oxirida birinchi AI xodimingizni tayyor skill qilib beradi.

## O'rnatish

**Claude Code:**

```
/plugin marketplace add sodirovone/hiworld-ai-jamoa
/plugin install hiworld-jamoa@hiworld-jamoa
```

**claude.ai yoki Claude desktop:** Customize → Plugins → Add marketplace → `sodirovone/hiworld-ai-jamoa` →
**hiworld-jamoa** → Install. Yoki `hiworld-jamoa` papkasini zip qilib, **Upload plugin** orqali qo'shing.
Settings → Capabilities → **Code execution and file creation** yoqiq bo'lsin.

## Ishlatish

Yangi chatda `/` → **diagnostika** (yoki «AI jamoa diagnostikasini boshlaymiz»). Keyin `/` → **ai-xodim**.

## Qanday ishlaydi

- Savollar va variantlar — `skills/diagnostika/references/malumot.json` (9 soha, 7 bo'lim, 61 ish, 10 rol).
- Daraja (L0–L4), soat, jamoa va reja — `scripts/hisob.py` qoidalari bilan hisoblanadi, model o'zgartirmaydi.
  Pul, qaror va telefon — L1 dan yuqori emas; ommaga chiqadigan — L2 dan yuqori emas.
- Model faqat savol beradi, javoblarni yig'adi va shaxsiy izoh yozadi.
- AI xodim odamni almashtirmaydi — vaqtini bo'shatadi; nazorat odamda qoladi.

## Aloqa

AI xodimlarni biznesingizga ulashda yordam — hiworld.club.
Telegram: [@Sodirov_U](https://t.me/Sodirov_U) · Zakaz: [@hiworld_clubbot](https://t.me/hiworld_clubbot) · +998 95 002 42 83

---

Asos: vibecoding.uz «ai-jamoa» plagini (github.com/iakadirov/ai-jamoa). Asl repoda litsenziya yo'q — ochiq
tarqatishdan oldin muallifdan ruxsat oling.
