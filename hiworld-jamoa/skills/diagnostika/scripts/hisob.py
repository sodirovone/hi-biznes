#!/usr/bin/env python3
"""hiworld.club AI jamoa diagnostikasi — qoidaga asoslangan hisob.

Buyruqlar:
  savollar  --soha SOHA [--bolim B ...]        tanlov uchun ishlar ro'yxati (JSON)
  natija    JAVOBLAR.json [--izoh IZOH.json] --html CHIQISH.html [--json CHIQISH.json]
  xodim     JAVOBLAR.json --rol ROL --chiqish PAPKA   birinchi AI xodimni skill paketi (.zip) qilib yasaydi
  zip       PAPKA                              xotira to'ldirilgandan keyin skill zip'ini qayta yig'adi

Daraja (L0–L4), darvoza (pul/qaror/telefon → L1, ommaga → L2), jamoa va reja faqat shu yerda hisoblanadi.
Model bu natijani o'zgartirmaydi — faqat izoh qo'shadi.
"""
import argparse, json, os, re, sys, zipfile

# Windows konsolida o'zbekcha belgilar (« » – ʻ) chiqishda yiqilmasin
for _o in (sys.stdout, sys.stderr):
    try: _o.reconfigure(encoding="utf-8")
    except Exception: pass

ASOS = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(ASOS, "..", "references", "malumot.json"), encoding="utf-8"))
ROLLAR, ISHLAR, TIZIM = M["ROLLAR"], M["ISHLAR"], M["TIZIM"]
SOAT = [s[1] for s in M["SOAT"]]
# Chat oqimi: bo'limga jami haftalik soat (keyin ishlar orasida R bo'yicha taqsimlanadi)
BOLIM_SOAT = [["3 soatgacha", 2], ["3–10 soat", 6], ["10–20 soat", 15], ["20–40 soat", 30], ["40+ soat", 50]]
MALUMOT = M["MALUMOT"]
ULUSH = M["ULUSH"]
DARAJA = M["DARAJA"]
OYLIK = M["OYLIK"]

# ---------- yordamchilar ----------

def soha_nomi(j): return next((s[1] for s in M["SOHALAR"] if s[0] == j.get("soha")), "Biznes")
def biznes_nomi(j): return (j.get("nom") or "").strip() or "biznesimiz"

def rol_r(j, r):
    x = dict(ROLLAR[r]); x.update((ROLLAR[r].get("sohaga") or {}).get(j.get("soha"), {}))
    return x

def rol_nomi(j, r):
    return (ROLLAR[r].get("nomlar") or {}).get(j.get("soha")) or ROLLAR[r]["nom"]

def ish_nomi(j, p):
    return (p.get("nomlar") or {}).get(j.get("soha")) or p["nom"]

def mln(s):
    v = s / 1e6
    t = str(round(v)) if v >= 10 else f"{round(v, 1):g}"
    return t.replace(".", ",")

def oraliq(x, f): return f"{f(x * .75)}–{f(x * 1.25)}"
def soat_f(h): return str(round(h))

def royxat(j):
    kut = [p for p in ISHLAR if not p.get("sohalar") or j.get("soha") in p["sohalar"]]
    tur = M["TUR"]
    for q in j.get("qoshimcha", []):
        # noma'lum tur (masalan «pul») — eng ehtiyotkor tur: qaror
        if q.get("tur") not in tur: q["tur"] = "qaror"
        t = tur[q["tur"]]
        b = q["b"]
        rol = "direktor" if q.get("tur") == "hisob" and b != "mol" else ("operator" if q.get("tur") == "javob" and b in ("sot", "mij") else M["BOLIM_ROL"][b])
        kut.append({"id": q["id"], "b": b, "nom": q["nom"], "rol": rol, "R": t["R"], "V": t["V"], "a": t["a"], "t": t["t"],
                    "E": 3 if t["a"] == "qaror" else 2, "sohalar": None, "nomlar": None})
    bol = j.get("bolimlar") or [b[0] for b in M["BOLIMLAR"]]
    return [p for p in kut if p["b"] in bol]

def tizim_t(j, t):
    x = TIZIM.get(t)
    if not x: return .3, [], None
    if "_" in x: return x["_"], [], None
    T, vos, eng = 0, [], None
    for k, v in x.items():
        if k in j.get("vositalar", []):
            vos.append(k)
            if v > T: T, eng = v, k
    return (T or .3), vos, eng

def murakkablik(T, eng):
    if eng == "1c" or T < .6: return 3
    return 1 if T >= .9 else 2

def sukut_d(j, p):
    _, vos, _ = tizim_t(j, p["t"])
    v = j.get("vositalar", [])
    tizimli = any(x not in ("excel", "sheets") for x in vos)
    jadvalli = "sheets" in v or "excel" in v
    t = p["t"]
    if t in ("chat", "sosial", "telefon"): return 2
    if t == "hujjat": return 3
    if t == "kalendar": return 4 if "google" in v else 2
    if t == "ads": return 4 if "meta" in v else 2
    return 4 if tizimli else (3 if jadvalli else 1)

def darvoza(a, E):
    return {"pul": 1, "qaror": 1, "omma": 2,
            "tashqi": 3 if E <= 2 else 2,
            "qoralama": 1 if E >= 4 else 2,
            "ichki": 2 if E >= 4 else (3 if E == 3 else 4),
            "tahlil": 3 if E >= 3 else 4}.get(a, 2)

DS = M["DARVOZA_SABAB"]

def baholash(j, p, b):
    H = b["H"] if "H" in b else SOAT[b["soat"]]
    di = b.get("d", sukut_d(j, p))
    if "d" not in b and j.get("malumot") is not None and p["t"] not in ("chat", "sosial", "hujjat"):
        di = min(di, j["malumot"])
    D = MALUMOT[di][1]
    E = b.get("e", p["E"])
    T, vos, eng = tizim_t(j, p["t"])
    S = round(100 * (.30 * p["R"] + .25 * D + .20 * p["V"] + .25 * T))
    Ls = 4 if S >= 75 else 3 if S >= 60 else 2 if S >= 45 else 1 if S >= 30 else 0
    g = 1 if p["t"] == "telefon" else darvoza(p["a"], E)
    L = min(Ls, g)
    sabab = []
    if di == 1 and L > 1:
        L = 1; sabab.append("ma'lumot qog'ozda — hozircha yordamchi; jadvalga o'tkazilsa avtomatga o'tadi")
    if di > 0 and L > 1 and j.get("malumot") == 0 and p["t"] in ("chat", "sosial", "hujjat"):
        # chat ishida ma'lumot chatda, lekin narx va javoblar faqat boshda — agent to'qib chiqarmasin
        L = 1; sabab.append("narx va javoblar hozircha boshingizda — yozib chiqilguncha agent faqat qoralama beradi")
    if di == 0:
        L = 0; sabab.append("ma'lumot faqat boshingizda — avval yozib chiqing, keyin agentga beriladi")
    else:
        if p["t"] == "telefon": sabab.append("ovozli qo'ng'iroqni odam qiladi — agent ro'yxat va skript tayyorlaydi")
        elif g < Ls: sabab.append(DS["tashqiQimmat" if E >= 3 else "tashqi"] if p["a"] == "tashqi" else DS.get(p["a"], DS["qimmat"]))
        if p["R"] >= .8: sabab.append("tez-tez takrorlanadi")
        if D >= .8: sabab.append("ma'lumot allaqachon raqamli")
        if p["V"] >= .8: sabab.append("natijani tekshirish oson")
        if T < .5 and p["t"] != "hujjat": sabab.append(M["TIZIM_NOM"].get(p["t"], "tizim") + "ga ulanish hozircha murakkab")
    kim = b.get("kim", "xodim")
    oy = OYLIK[j["oylik"]][1] if j.get("oylik") is not None else 4
    narx = oy * 1e6 / 176 * (2 if kim == "men" else 1)
    bosh = 0 if kim == "hech" else H * ULUSH[L]
    yangi = H * ULUSH[L] if kim == "hech" else 0
    return {"p": p, "H": H, "D": D, "di": di, "E": E, "T": T, "vos": vos, "eng": eng, "S": S, "L": L, "sabab": sabab,
            "kim": kim, "bosh": bosh, "yangi": yangi, "som": bosh * 4.3 * narx, "yangi_som": yangi * 4.3 * narx, "eff": murakkablik(T, eng)}

def tekshir(j):
    """javoblar.json dagi jim yo'qoladigan xatolarni oldindan aytadi."""
    ishlar = {p["id"]: p for p in royxat(j)}
    baho = j.setdefault("baho", {})
    for q in j.get("qoshimcha", []):
        baho.setdefault(q["id"], {})  # qo'shimcha ish baho'ga yozilmagan bo'lsa ham hisobga kirsin
    xato = []
    yoq = [k for k in baho if k not in ishlar]
    if yoq: xato.append(f"baho'dagi ishlar ro'yxatda yo'q (soha yoki bo'lim mos emas): {', '.join(yoq)}")
    soat = j.get("bolim_soat") or {}
    for b in dict.fromkeys(ishlar[k]["b"] for k in baho if k in ishlar and baho[k].get("soat") is None and not baho[k].get("yoq")):
        if b not in soat: xato.append(f"'{b}' bo'limi ishlari tanlangan, lekin bolim_soat'da uning soati yo'q")
    for b, idx in soat.items():
        if not isinstance(idx, int) or not 0 <= idx < len(BOLIM_SOAT): xato.append(f"bolim_soat['{b}'] = {idx!r} — 0..{len(BOLIM_SOAT) - 1} indeks bo'lishi kerak")
    if xato: sys.exit("javoblar.json xato:\n- " + "\n- ".join(xato))

def hisob(j):
    nat = []
    ishlar = royxat(j)
    baho = {k: dict(v) for k, v in j.get("baho", {}).items()}
    for bk, idx in (j.get("bolim_soat") or {}).items():
        tan = [p for p in ishlar if p["b"] == bk and p["id"] in baho and not baho[p["id"]].get("yoq") and baho[p["id"]].get("soat") is None]
        bor = [p for p in tan if baho[p["id"]].get("kim") != "hech"]
        # bo'lim soati — bugun qilinayotgan ishlarniki; «hech kim qilmaydi» ishi undan ulush olmaydi,
        # uning hajmi hamma ishlar qatorida bo'lganda qancha bo'lishi bo'yicha alohida baholanadi
        jamR, hammaR = sum(p["R"] for p in bor), sum(p["R"] for p in tan)
        for p in tan:
            ul = p["R"] / hammaR if baho[p["id"]].get("kim") == "hech" else p["R"] / jamR
            baho[p["id"]]["H"] = BOLIM_SOAT[idx][1] * ul
    for p in ishlar:
        b = baho.get(p["id"])
        if not b or b.get("yoq") or (b.get("soat") is None and "H" not in b): continue
        nat.append(baholash(j, p, b))
    jami = {"soat": 0, "som": 0, "yangi": 0, "audit": 0, "L4": 0}
    for x in nat:
        jami["soat"] += x["bosh"]; jami["som"] += x["som"]; jami["yangi"] += x["yangi"]
        if x["kim"] != "hech": jami["audit"] += x["H"]
        if x["L"] == 4: jami["L4"] += 1
    return nat, jami

def bolim_hisob(j, nat):
    out = []
    for k, n in M["BOLIMLAR"]:
        if k not in (j.get("bolimlar") or [b[0] for b in M["BOLIMLAR"]]): continue
        xs = [x for x in nat if x["p"]["b"] == k]
        if not xs: continue
        L = [0] * 5; jami = ai = avto = 0
        for x in xs:
            if x["kim"] == "hech": continue
            L[x["L"]] += x["H"]; jami += x["H"]; ai += x["bosh"]
            if x["L"] == 4: avto += x["bosh"]
        out.append({"k": k, "n": n, "L": [round(v, 1) for v in L], "jami": round(jami), "ai": round(ai), "avto": round(avto),
                    "foiz": round(100 * ai / jami) if jami else 0})
    return out

def jamoa(nat):
    rollar = {}
    for x in nat:
        if x["L"] < 1: continue
        r = rollar.setdefault(x["p"]["rol"], {"rol": x["p"]["rol"], "ishlar": [], "soat": 0, "yangi": 0, "som": 0, "ysom": 0, "Ssum": 0, "eff": 1})
        r["ishlar"].append(x); r["soat"] += x["bosh"]; r["yangi"] += x["yangi"]; r["som"] += x["som"]; r["ysom"] += x["yangi_som"]; r["Ssum"] += x["S"]
        if x["L"] >= 2: r["eff"] = max(r["eff"], x["eff"])
    lst = []
    for r in rollar.values():
        S = r["Ssum"] / len(r["ishlar"])
        lst.append(dict(r, S=S, P=(r["som"] + .5 * r["ysom"]) * S / r["eff"]))  # yangi ish — yarim vazn
    # faqat L1 ishlardan iborat va 3 soatdan kam rol — alohida agent emas
    lst = [r for r in lst if (r["soat"] >= 1.5 or r["yangi"] >= 3 or len(lst) == 1)
           and (max(x["L"] for x in r["ishlar"]) >= 2 or r["soat"] >= 3 or len(lst) == 1)]
    lst.sort(key=lambda r: -r["P"])
    dr = next((r for r in lst if r["rol"] == "direktor"), None)
    tan = [r for r in lst if r["rol"] != "direktor"][:5]
    if dr: tan.append(dr)
    elif len(tan) >= 2:
        tan.append({"rol": "direktor", "ishlar": [], "soat": 0, "yangi": 0, "som": 0, "S": 70, "eff": 2, "P": 0, "sintetik": True})
    tan = tan[:6]
    ids = {r["rol"] for r in tan}
    keyin = [r["rol"] for r in rollar.values() if r["rol"] not in ids]
    for a in tan:
        maxL = max([x["L"] for x in a["ishlar"]] or [0])
        L4 = sum(1 for x in a["ishlar"] if x["L"] == 4)
        a["daraja"] = "C" if (a["rol"] == "direktor" and len(tan) >= 3) else "A" if maxL <= 1 else "C" if (a["eff"] >= 3 or L4 >= 3) else "B"
        a["vos"] = list(dict.fromkeys(x["eng"] for x in a["ishlar"] if x["eng"]))
        a["tizimlar"] = list(dict.fromkeys(x["p"]["t"] for x in a["ishlar"]))
    return tan, keyin

def reja(agentlar):
    tartib = [a for a in agentlar if a["rol"] != "direktor"]
    dr = next((a for a in agentlar if a["rol"] == "direktor"), None)
    bir = next((a for a in tartib if a["eff"] <= 2), tartib[0] if tartib else dr)
    qol = [a for a in tartib if a is not bir]
    oy1, oy3 = qol[:2], qol[2:]
    if dr and dr is not bir: oy3.append(dr)
    return bir, oy1, oy3

def indeks(j, nat):
    ha = sum(1 for t in j.get("tayyor", []) if t is True)
    avgD = sum(x["D"] for x in nat) / len(nat) if nat else 0
    return round(.5 * ha * 25 + .5 * avgD * 100)

# ---------- matnlar ----------

def huquqlar(j, a, l1=False):
    # l1 — yasalgan xodimning boshlang'ich rejimi: hech bir ish erkin emas, hammasi qoralama
    erkin, tugma, qor = ["xotiradagi hujjatlarni o'qish, tahlil va qoralama"], [], []
    for x in a["ishlar"]:
        n = ish_nomi(j, x["p"]).lower()
        if l1: qor.append(n + " (faqat qoralama — siz yuborasiz)")
        elif x["L"] >= 3: erkin.append(n)
        elif x["L"] == 2: tugma.append(n)
        else: qor.append(n + " (faqat qoralama — siz yuborasiz)")
    return {"erkin": erkin, "tugma": tugma + qor, "yopiq": rol_r(j, a["rol"])["yopiq"] + M["UMUMIY_YOPIQ"]}

def yoriqnoma(j, a, l1=False):
    R, h = rol_r(j, a["rol"]), huquqlar(j, a, l1)
    ishlar = [f"- {ish_nomi(j, x['p'])}" for x in a["ishlar"]] or ["- boshqa agentlar hisobotini yig'ish va rahbarga bitta xulosa berish", "- kunlik raqamlarni ko'rib, eng katta muammoni topish"]
    mah = f", asosiy mahsulot: {j['mahsulot'].strip()}" if (j.get("mahsulot") or "").strip() else ""
    return f"""Sen — {biznes_nomi(j)}ning AI xodimisan. Roling: {rol_nomi(j, a['rol'])}. Soha: {soha_nomi(j).lower()}{mah}.

MAQSAD: {R['maqsad']}.
O'LCHOV: {R['metrika']}.

JAVOBGARLIGING:
{chr(10).join(ishlar)}

ISHDAN OLDIN O'QIYSAN (xotira): {'; '.join(R['xotira'])}.
Hujjatda yo'q faktni (narx, muddat, va'da) o'ylab topma — «aniqlab beraman» de va rahbarga savol qoldir.

OHANG: o'zbek tilida, «siz»da, qisqa va xushmuomala; mijoz rus tilida yozsa — rus tilida. Xushomad va ortiqcha emoji yo'q.

HUQUQLARING:
- Erkin: {'; '.join(h['erkin'])}
- Tasdiq bilan (avval rahbarga ko'rsatasan): {'; '.join(h['tugma']) or '—'}
- Yopiq (hech qachon): {'; '.join(h['yopiq'])}

ESKALATSIYA: {R['eskalatsiya']} → darhol rahbarga xabar; mijozga «mutaxassis javob beradi» deysan.

HISOBOT: {R['ritm']}. Format: nima qildim · raqamlar · muammo · sizdan nima kerak."""

def argument(j, a):
    if a.get("sintetik") or not a["ishlar"]:
        return "Boshqa agentlar ishlay boshlagach, ularning hisobotlarini bitta ertalabki xulosaga yig'adi. Siz har birini alohida kuzatmaysiz — bitta xabar: raqamlar, eng katta muammo, sizdan nima kerak."
    top = sorted(a["ishlar"], key=lambda x: -x["bosh"])[:2]
    top = " va ".join(f"«{ish_nomi(j, x['p'])}»" for x in top)
    tak = sum(1 for x in a["ishlar"] if x["p"]["R"] >= .8)
    raq = sum(1 for x in a["ishlar"] if x["D"] >= .8)
    arz = sum(1 for x in a["ishlar"] if x["E"] <= 2)
    bosh = min(x["L"] for x in a["ishlar"])
    q = []
    if tak: q.append(f"{tak} ta ish muntazam takrorlanadi")
    if raq: q.append(f"{raq} tasida ma'lumot allaqachon raqamli")
    if arz: q.append(f"{arz} tasida xato arzon")
    t = f"Haftasiga ~{soat_f(a['soat'])} soatingizni oladi, asosan {top}. "
    if q: t += ", ".join(q) + " — shuning uchun "
    t += f"{DARAJA[max(1, bosh)][1].lower()} rejimida boshlash xavfsiz."
    if a["yangi"] >= 1: t += f" Qo'shimcha: hozir hech kim qilmayotgan ~{soat_f(a['yangi'])} soatlik ishni ham bajara boshlaydi."
    return t

DARAJA_YOL = M["DARAJA_YOL"]

def sizdan(j, a):
    R = rol_r(j, a["rol"])
    out = [f"Xotira hujjati: {d}" for d in R["xotira"]]
    for v in a["vos"]:
        nom = next(x[1] for x in M["VOSITALAR"] if x[0] == v)
        out.append(f"{nom}ga ulanish ruxsati (faqat kerakli huquq bilan)")
    return out + R["sizdan"]

SIZDAN_UMUMIY = ["Tasdiq tugmasini kim bosadi — bitta mas'ul odam",
                 "Birinchi 2 hafta: kuniga ~15 daqiqa agent javoblarini ko'rib chiqish",
                 "Claude obunasi (Pro yoki undan yuqori) va AI xarajatiga oylik limit"]

def xavflar(j, nat, idx):
    x = []
    if idx < 50: x.append(["Poydevor yo'q", "ma'lumot ko'p joyda boshda va qog'ozda. Agent faqat yozilgan narsani biladi — 0-hafta vazifalarisiz boshlamang."])
    x.append(["To'qib chiqarish", "agent bilmagan narxni yoki muddatni o'ylab topishi mumkin. Davo: «hujjatda yo'q — bilmayman» qoidasi va to'liq xotira."])
    if any(n["p"]["a"] == "tashqi" and n["L"] >= 3 for n in nat): x.append(["Mijozga avtomat javob", "birinchi 2 hafta har javobni tugma bilan o'tkazing. Instagram va WhatsApp'da 24 soatlik javob oynasi qoidasi bor."])
    if any("1c" in n["vos"] for n in nat): x.append(["1C ulanishi", "OData publikatsiyasi va administrator kerak. Boshida faqat o'qish huquqi bering."])
    if any(n["p"]["b"] == "mol" for n in nat): x.append(["Pul va kalitlar", "to'lov kabinetlari kalitlari yo'riqnomada emas, faqat ulanish sozlamasida turadi. Pul o'tkazish — har doim odamda."])
    x.append(["Bitta odamga bog'liqlik", "yo'riqnoma va xotira bir kishining boshida emas, yozma va jamoaga ochiq bo'lsin."])
    x.append(["Xarajat", "AI to'lovi ishlatishga qarab o'sadi — oylik limit qo'ying va 1-oy oxirida foyda bilan solishtiring."])
    return x[:5]

# ---------- natija ----------

def natija_data(j, izoh):
    nat, jami = hisob(j)
    if not nat: sys.exit("Baholangan ish yo'q: javoblar.json da baho bo'sh")
    agentlar, keyin = jamoa(nat)
    bir, oy1, oy3 = reja(agentlar)
    idx = indeks(j, nat)
    poy, kor = [], set()
    for a in agentlar:
        for d in rol_r(j, a["rol"])["xotira"]:
            if d not in kor: kor.add(d); poy.append(d)
    qogoz = [ish_nomi(j, x["p"]) for x in nat if x["di"] <= 1]
    savol_yoq = [t[0].rstrip("?") for i, t in enumerate(M["TAYYORLIK"]) if i < len(j.get("tayyor", [])) and j["tayyor"][i] is False]
    ag = []
    for a in agentlar:
        R = rol_r(j, a["rol"]); h = huquqlar(j, a); yol = DARAJA_YOL[a["daraja"]]
        ag.append({
            "rol": a["rol"], "nom": rol_nomi(j, a["rol"]), "rang": ROLLAR[a["rol"]]["rang"],
            "soat": round(a["soat"]), "som": mln(a["som"]), "yangi": round(a["yangi"]),
            "argument": argument(j, a), "izoh": (izoh.get("agentlar") or {}).get(a["rol"], ""),
            "ishlar": [{"n": ish_nomi(j, x["p"]), "L": x["L"]} for x in sorted(a["ishlar"], key=lambda x: -x["L"])] or [{"n": "Agentlar hisobotini yig'ish, ertalabki xulosa", "L": 4}],
            "tartib": R["tartib"], "huquq": h, "xotira": R["xotira"], "ritm": R["ritm"],
            "vositalar": [[next(x[1] for x in M["VOSITALAR"] if x[0] == v), M["VOS_IZOH"].get(v, "")] for v in a["vos"]],
            "yol": {"daraja": a["daraja"], "nom": yol[0], "qanday": yol[1], "muddat": yol[2]},
            "sizdan": sizdan(j, a), "maqsad": R["maqsad"], "metrika": R["metrika"], "eskalatsiya": R["eskalatsiya"],
        })
    nom = lambda a: rol_nomi(j, a["rol"])
    rj = [{"vaqt": "0-hafta", "sar": "Poydevor", "ishlar": poy[:6] + ([f"Jadvalga o'tkazish: {', '.join(qogoz[:3])}"] if qogoz else []) + [f"{s} — hal qilish" for s in savol_yoq] + ["Kim nimani tasdiqlashini yozib qo'yish"], "mezon": "Har agentning xotira hujjatlari yozilgan"}]
    if bir: rj.append({"vaqt": "1-hafta", "sar": nom(bir), "ishlar": ["Kodsiz: Claude'da skill yoki Project", "Faqat qoralama rejimi (L1) — siz yuborasiz", "20 ta real holatda sinash"], "mezon": "20 holatdan 16+ javob tuzatishsiz"})
    rj.append({"vaqt": "1-oy", "sar": "Ulanish va tugma", "ishlar": ([f"{nom(bir)} — tasdiq bilan (L2), avtomat ishlar L3 ga"] if bir else []) + [f"{nom(a)} — qoralamadan boshlaydi" for a in oy1] + ["Telegram'da tasdiq tugmasi, har agentga bitta o'lchov"], "mezon": "Agentlar ulangan, har biriga haftalik raqam"})
    rj.append({"vaqt": "3-oy", "sar": "Jamoa va ritm", "ishlar": [nom(a) for a in oy3] + ["L3–L4 ishlar avtomatga (stajirovkadan o'tganlari)", "Kunlik ritm va qarorlar jurnali"], "mezon": "Ertalab bitta xabar: raqamlar, muammo, sizdan nima kerak"})
    guruh = lambda f: [{"n": ish_nomi(j, x["p"]), "s": x["sabab"][0] if x["sabab"] else DARAJA[x["L"]][2], "L": x["L"]} for x in sorted(nat, key=lambda x: -x["H"]) if f(x["L"])]
    return {
        "biznes": biznes_nomi(j) if (j.get("nom") or "").strip() else "", "soha": soha_nomi(j), "mahsulot": (j.get("mahsulot") or "").strip(),
        "soni": len(nat), "soat": oraliq(jami["soat"], soat_f), "som": oraliq(jami["som"], mln),
        "foiz": round(100 * jami["soat"] / jami["audit"]) if jami["audit"] else 0, "L4": jami["L4"], "yangi": round(jami["yangi"]), "indeks": idx,
        "umumiy_izoh": izoh.get("umumiy", ""),
        "nomi": biznes_nomi(j), "bolimlar": bolim_hisob(j, nat), "agentlar": ag, "keyin": [rol_nomi(j, r) for r in keyin],
        "guruhlar": [["Hozir beriladi", 3, guruh(lambda L: L >= 3)], ["Nazorat bilan", 2, guruh(lambda L: L in (1, 2))], ["Hali bermang", 0, guruh(lambda L: L == 0)]],
        "reja": rj, "xavflar": xavflar(j, nat, idx), "sizdan_umumiy": SIZDAN_UMUMIY,
    }

def xulosa_matn(d):
    q = [f"Ish baholandi: {d['soni']} · bo'shaydi: {d['soat']} soat/hafta · {d['som']} mln so'm/oy · L4: {d['L4']} · tayyorlik: {d['indeks']}/100"]
    for a in d["agentlar"]:
        q.append(f"- {a['rol']} | {a['nom']} | {a['yol']['daraja']} | ~{a['soat']} soat | ishlar: " + "; ".join(f"{x['n']} L{x['L']}" for x in a["ishlar"]))
    if d["keyin"]: q.append("Keyingi bosqich: " + ", ".join(d["keyin"]))
    return "\n".join(q)

# ---------- AI xodim skill paketi ----------

def xodim(j, rol, chiqish):
    nat, _ = hisob(j)
    agentlar, _ = jamoa(nat)
    a = next((x for x in agentlar if x["rol"] == rol), None)
    if not agentlar: sys.exit("Jamoa bo'sh: hamma ish hozircha odamda (L0). Avval xaritadagi 0-hafta vazifalarini bajaring.")
    if not a: sys.exit(f"'{rol}' jamoada yo'q. Bor: {', '.join(x['rol'] for x in agentlar)}")
    R = rol_r(j, rol)
    # rol qismi kesilmasin — bitta biznesning ikki agenti bir xil nom olmasin
    bz = re.sub(r"[^a-z0-9]+", "-", biznes_nomi(j).lower()).strip("-")[:59 - len(rol)].strip("-")
    slug = f"{bz}-{rol}" if bz else rol
    tavsif = f"{biznes_nomi(j)} uchun {rol_nomi(j, rol).lower()}. Ishlari: " + "; ".join(ish_nomi(j, x["p"]).lower() for x in a["ishlar"][:4])
    tavsif = (tavsif + ". Shu ishlar so'ralganda yoki biznes mijozlari, narxlari, jarayonlari haqida savol bo'lganda ishlatiladi.")[:1000].replace("\n", " ")
    xot = [f"# {biznes_nomi(j)} — xotira", f"Soha: {soha_nomi(j)}" + (f" · Mahsulot: {j['mahsulot'].strip()}" if (j.get('mahsulot') or '').strip() else ""), ""]
    for d in R["xotira"]:
        xot.append(f"## {d}")
        if "FAQ" in d: xot += ["S: ___", "J: ___", "", "S: ___", "J: ___", ""]
        elif re.search("Narx|Tarif|Offer", d): xot += ["- ___ — ___ so'm (nima kiradi: ___)", "- Chegirma qoidasi: ___ (kim tasdiqlaydi: ___)", ""]
        elif "E'tiroz" in d: xot += ["- «Qimmat» → ___", "- «O'ylab ko'raman» → ___", ""]
        else: xot += ["- ___", "- ___", ""]
    skill = f"""---
name: {slug}
description: {json.dumps(tavsif, ensure_ascii=False)}
---

{yoriqnoma(j, a, l1=True)}

ISH TARTIBI:
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(R['tartib']))}

XOTIRA: har ishdan oldin `xotira.md` ni o'qi. Unda «___» qolgan joy — hali to'ldirilmagan fakt: u haqida so'ralsa, «aniqlab beraman» de.
REJIM: hozir L1 (yordamchi) — hamma tashqi xabar qoralama bo'lib chiqadi, foydalanuvchi o'zi yuboradi.
"""
    papka = os.path.join(chiqish, slug)
    os.makedirs(papka, exist_ok=True)
    open(os.path.join(papka, "SKILL.md"), "w", encoding="utf-8").write(skill)
    open(os.path.join(papka, "xotira.md"), "w", encoding="utf-8").write("\n".join(xot))
    z = zip_yig(papka)
    print(json.dumps({"zip": z, "papka": papka, "nom": rol_nomi(j, rol), "sinov": R["sinov"]}, ensure_ascii=False, indent=1))

def zip_yig(papka):
    # tashqi `zip` buyrug'isiz (Windows'da yo'q) — papka yonida <slug>.zip
    papka = os.path.normpath(papka)
    slug = os.path.basename(papka)
    z = os.path.join(os.path.dirname(papka), slug + ".zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for n in ("SKILL.md", "xotira.md"): f.write(os.path.join(papka, n), f"{slug}/{n}")
    return z

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("savollar"); s.add_argument("--soha", required=True); s.add_argument("--bolim", nargs="*")
    n = sub.add_parser("natija"); n.add_argument("javoblar"); n.add_argument("--izoh"); n.add_argument("--html", required=True); n.add_argument("--json")
    x = sub.add_parser("xodim"); x.add_argument("javoblar"); x.add_argument("--rol", required=True); x.add_argument("--chiqish", required=True)
    z = sub.add_parser("zip"); z.add_argument("papka")
    a = ap.parse_args()
    if a.cmd == "zip": print(zip_yig(a.papka)); return
    if a.cmd == "savollar":
        j = {"soha": a.soha, "bolimlar": a.bolim or [b[0] for b in M["BOLIMLAR"]]}
        out = {"bolimlar": []}
        for k, nom in M["BOLIMLAR"]:
            if k not in j["bolimlar"]: continue
            out["bolimlar"].append({"k": k, "nom": nom, "ishlar": [{"id": p["id"], "nom": ish_nomi(j, p)} for p in royxat(j) if p["b"] == k]})
        out["bolim_soat"] = [s[0] for s in BOLIM_SOAT]; out["malumot"] = [m[0] for m in MALUMOT]
        out["profil"] = {"sohalar": M["SOHALAR"], "xodimlar": M["XODIMLAR"], "oylik": [o[0] for o in OYLIK], "vositalar": M["VOSITALAR"], "manbalar": M["MANBALAR"], "tayyorlik": [t[0] for t in M["TAYYORLIK"]]}
        print(json.dumps(out, ensure_ascii=False, indent=1)); return
    j = json.load(open(a.javoblar, encoding="utf-8"))
    tekshir(j)
    if a.cmd == "xodim": return xodim(j, a.rol, a.chiqish)
    izoh = json.load(open(a.izoh, encoding="utf-8")) if a.izoh else {}
    d = natija_data(j, izoh)
    shablon = open(os.path.join(ASOS, "..", "assets", "xarita.html"), encoding="utf-8").read()
    data = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    shablon = re.sub(r"\n[ \t]+", "\n", shablon)  # artifact qisqaroq bo'lsin
    open(a.html, "w", encoding="utf-8").write(shablon.replace("/*__DATA__*/null", data))
    if a.json: json.dump(d, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(xulosa_matn(d))
    print(f"\nHTML: {a.html} ({os.path.getsize(a.html)//1024} KB)")

if __name__ == "__main__":
    main()
