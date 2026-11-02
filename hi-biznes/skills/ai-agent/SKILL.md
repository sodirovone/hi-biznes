---
name: ai-agent
description: Diagnostikadan keyin tadbirkorning birinchi AI xodimini yasaydi — rol yo'riqnomasi va biznes xotirasi bilan tayyor Claude skill paketi (.zip), foydalanuvchi uni Customize → Skills orqali o'rnatib, darhol sinaydi. «AI xodim yasa», «birinchi agent», «agentni ishga tushir», /hi-biznes:ai-agent deganda ishlatiladi.
---

# Birinchi AI xodimni yasash

Diagnostika natijasidagi bitta agentni **foydalanuvchining shaxsiy skill paketiga** aylantirasan. Til — lotin o'zbek, «siz».

## Qat'iy qoidalar

- Yo'riqnoma matni, huquqlar (erkin / tugma / yopiq) va ishlar ro'yxati — faqat `hisob.py xodim` dan. O'zgartirma.
- Xotiraga faqat foydalanuvchi aytgan faktlarni yoz. Bilinmaganini «___» qoldir — agent u haqida «aniqlab beraman» deydi.
- Yasalgan xodim **L1 (yordamchi) rejimida** ishlaydi: tashqariga ketadigan har narsa qoralama, foydalanuvchi o'zi yuboradi.
- Bir xabarda bitta savol bloki. Variantli savol — har doim tanlov formasi vositasi bilan (claude.ai'da `ask_user_input_v0`,
  Claude Code'da `AskUserQuestion` — har savolda 2–4 variant), so'ramasdan; matnli ro'yxat faqat vosita yo'q bo'lsa.

## Skript

Qo'shni skill papkasida: `../diagnostika/scripts/hisob.py` (topilmasa — fayl qidirish vositasi bilan
`**/diagnostika/scripts/hisob.py`; butun diskni `find /` bilan aylanma). Linux/macOS'da `python3`, Windows'da `python`.

## Oqim

**1. Diagnostika bormi.** `javoblar.json` kerak: shu suhbatda yaratilgan bo'lsa — o'sha; Claude Code'da joriy papkadagi
`hi-biznes/javoblar.json` ni ham tekshir. Yo'q bo'lsa: «Avval diagnostikadan o'tamiz» deb `diagnostika` skillini boshla.

**2. Qaysi agent.** Sukut — natijadagi reja «1-hafta» agenti. Foydalanuvchiga jamoadagi agentlarni tanlov qilib ber,
birinchisini «(tavsiya)» deb belgila.

**3. Paketni yasash.**

```
python3 hisob.py xodim javoblar.json --rol <rol> --chiqish <ishchi papka>
```

Natija: `<slug>/SKILL.md`, `<slug>/xotira.md`, `<slug>.zip` va 3 ta sinov topshirig'i (JSON).
«Jamoa bo'sh» desa — foydalanuvchiga 0-hafta vazifalarini eslat va to'xta.

**4. Xotirani to'ldirish (5 daqiqa).** `xotira.md` dagi bo'limlar bo'yicha **2 ta savol bloki** ber — eng muhim faktlar:
narx/tariflar, 3 ta eng ko'p beriladigan savol va javob, ish vaqti/manzil, chegirma qoidasi (rolga qarab tanla).
Javoblarni `xotira.md` dagi tegishli «___» o'rniga yoz. Qolganini «___» qoldir. Keyin zip'ni qayta yig'
(tashqi `zip` buyrug'i kerak emas, Windows'da ham ishlaydi):

```
python3 hisob.py zip <ishchi papka>/<slug>
```

**5. Topshirish.** Zip'ni chiqish papkasiga (claude.ai'da `/mnt/user-data/outputs/`) ko'chir va fayl qilib ber. Keyin:

> **O'rnatish (1 daqiqa):** Customize → Skills → «+» → «Upload a skill» → shu zip.
> Skill yoqilganini tekshiring. Settings → Capabilities'da «Code execution» yoqiq bo'lishi kerak.

Claude Code'da: `<slug>` papkasini `~/.claude/skills/` ga ko'chirish kifoya (foydalanuvchi rozi bo'lsa, o'zing ko'chir).

**6. Sinov.** Skript bergan 3 ta sinovni ko'rsat — har biri alohida, nusxalash uchun:
1-sinov va 2-sinov — oddiy ish; **3-sinov — nazorat sinovi**: agent rad etishi va qarorni foydalanuvchiga qoldirishi kerak.
«Yangi chat oching va shu matnni yozing» de. Natijani foydalanuvchi aytsa — baholab ber: xotirada fakt yetmagan bo'lsa,
qaysi «___» ni to'ldirish kerakligini ayt.

**7. Keyingi qadam** (1–2 qator): 20 ta real holatda sinash; 16 tasi tuzatishsiz o'tsa — rejaning 1-oy bosqichi
(ulanish va tasdiq tugmasi). AI xodimni biznesingizga to'liq ulab berish — hiworld.club: Telegram @Sodirov_U.
