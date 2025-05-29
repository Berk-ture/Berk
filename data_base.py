# kullanıcı bilgilerinin kaydedildiği yer
import json
import os
import bcrypt
import random
import re
import requests
from datetime import datetime
import matplotlib.pyplot as plt

gecmis_dosyasi = "islem_gecmisi.json"
veri_dosyasi = "./data.json"
TCMB_API_URL = "https://evds2.tcmb.gov.tr/service/evds/series=TP.DK.USD.A,TP.DK.EUR.A,TP.DK.XAU.A&startDate=TODAY&endDate=TODAY&type=json&key=API_KEY"

if not os.path.exists(veri_dosyasi):
    with open(veri_dosyasi, "w") as dosya:
        json.dump({}, dosya)
if not os.path.exists(gecmis_dosyasi):
    with open(gecmis_dosyasi, "w") as dosya:
        json.dump({}, dosya)
def kullanicilari_yukle():
    with open(veri_dosyasi, "r", encoding="utf-8") as dosya:
        return json.load(dosya)

def kullanicilari_kaydet(kullanicilar):
    with open(veri_dosyasi, "w", encoding="utf-8") as dosya:
        json.dump(kullanicilar, dosya, indent=4, ensure_ascii=False)

def sifre_kontrol(sifre):
    if len(sifre) < 8:
        return False,str("şifre en az 8 karakter, bir büyük harf, bir küçük harf, bir rakam ve bir özel karakter içermelidir")
    if not re.search("[a-z]", sifre):
        return False,str("şifre en az 8 karakter, bir büyük harf, bir küçük harf, bir rakam ve bir özel karakter içermelidir")
    if not re.search("[A-Z]", sifre):
        return False,str("şifre en az 8 karakter, bir büyük harf, bir küçük harf, bir rakam ve bir özel karakter içermelidir")
    if not re.search("[0-9]", sifre):
        return False,str("şifre en az 8 karakter, bir büyük harf, bir küçük harf, bir rakam ve bir özel karakter içermelidir")
    if not re.search("[_@.]", sifre):
        return False,str("şifre en az 8 karakter, bir büyük harf, bir küçük harf, bir rakam ve bir özel karakter içermelidir")
    return True, "şifre geçerli"

def sifre_hashle(sifre):
    tuz = bcrypt.gensalt()
    hashlenmis_sifre = bcrypt.hashpw(sifre.encode("utf-8"), tuz)
    return hashlenmis_sifre.decode("utf-8"), tuz.decode("utf-8")

def hesap_olustur(isim, soyisim, sifre):
    if not sifre:
        return False, "şifre boş"
    gecerli, mesaj = sifre_kontrol(sifre)
    if not gecerli:
        return False, mesaj
    kullanicilar = kullanicilari_yukle()
    hesap_numarasi = str(random.randint(100000, 999999))
    while hesap_numarasi in kullanicilar:
        hesap_numarasi = str(random.randint(100000, 999999))
    hash_sifre, tuz = sifre_hashle(sifre)
    kullanicilar[hesap_numarasi] = {
        "isim": isim,
        "soyisim": soyisim,
        "sifre": hash_sifre,
        "tuz": tuz,
        "bakiye": {
            "USD": 0,
            "EUR": 0,
            "vadeli_hesap": 0,
            "vadesiz_hesap": 0,
            "altin_hesabi": 0,
            "bireysel_emeklilik": 0
        }
    }
    kullanicilari_kaydet(kullanicilar)
    return True, hesap_numarasi

def sifre_dogrula(hesap_numarasi, girilen_sifre):
    kullanicilar = kullanicilari_yukle()
    if hesap_numarasi in kullanicilar and girilen_sifre:
        tuz = kullanicilar[hesap_numarasi]["tuz"].encode("utf-8")
        yeni_hash = bcrypt.hashpw(girilen_sifre.encode(), tuz)
        return yeni_hash.decode() == kullanicilar[hesap_numarasi]["sifre"]
    return False
def islem_guncelle(hesap, islem_turu, miktar):
    if not miktar:
        return
    try:
        miktar = float(miktar)
    except:
        return
    with open(gecmis_dosyasi, "r", encoding="utf-8") as dosya:
        veriler = json.load(dosya)
    if hesap not in veriler:
        veriler[hesap] = []
    veriler[hesap].append({
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "islem": islem_turu,
        "miktar": miktar
    })
    with open(gecmis_dosyasi, "w", encoding="utf-8") as dosya:
        json.dump(veriler, dosya, indent=4, ensure_ascii=False)

def islem_gecmisi_getir(hesap):
    with open(gecmis_dosyasi, "r", encoding="utf-8") as dosya:
        veriler = json.load(dosya)
    return veriler.get(hesap, []) #Eğer hesap yoksa boş liste döndürür

def aylik_ozet_grafik(hesap):
    gecmis = islem_gecmisi_getir(hesap)
    ay = datetime.now().strftime("%Y-%m")
    yatirilan = 0
    cekilen = 0
    for islem in gecmis:
        if islem["tarih"].startswith(ay):
            if islem["islem"] == "Yatırma":
                yatirilan += float(islem["miktar"])
            elif islem["islem"] == "Çekme":
                cekilen += float(islem["miktar"])
    labels = ['Yatırılan', 'Çekilen']
    values = [yatirilan, cekilen]
    plt.figure(figsize=(6,6))
    plt.pie(values, labels=labels, autopct='%1.1f%%')
    plt.title("Aylık İşlem Özeti")
    plt.axis("equal")
    plt.show()
    return True, "Grafik gösterildi"

def doviz_kurlari():
    try:
        yanit = requests.get(TCMB_API_URL)
        if yanit.status_code == 200:
            veri = yanit.json()
            usd = veri["items"][0]["value"]
            eur = veri["items"][1]["value"]
            altin = veri["items"][2]["value"]
            return True, usd, eur, altin
        else:
            # API'den veri alınamazsa sabit değerler döndür
            return True, 28.5, 30.2, 1800.0  # Örnek değerler
    except Exception:
        # Hata durumunda da sabit değerler döndür
        return True, 28.5, 30.2, 1800.0  # Örnek değerler
def ilk_giris(kullanicilar, hesap_numarasi, hesap_turu):
    if "ilk_giris" not in kullanicilar[hesap_numarasi]["bakiye"]:
        kullanicilar[hesap_numarasi]["bakiye"]["ilk_giris"] = {}
    if hesap_turu not in kullanicilar[hesap_numarasi]["bakiye"]["ilk_giris"]:
        kullanicilar[hesap_numarasi]["bakiye"]["ilk_giris"][hesap_turu] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def para_yatir(hesap_numarasi, hesap_turu, miktar):
    kullanicilar = kullanicilari_yukle()
    if hesap_numarasi not in kullanicilar:
        return False, "Geçersiz hesap numarası"

    try:
        miktar = float(miktar)
        if miktar <= 0:
            return False, "Geçersiz miktar"
    except:
        return False, "Geçersiz miktar"

    basarili, usd, eur, altin = doviz_kurlari()

    if hesap_turu in ["vadeli_hesap", "bireysel_emeklilik"]:
        if hesap_turu not in kullanicilar[hesap_numarasi].get("ilk_giris", {}):
            kullanicilar[hesap_numarasi].setdefault("ilk_giris", {})[hesap_turu] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if hesap_turu == "vadeli_hesap":
        if miktar < 1000:
            return False, "Vadeli hesap için minimum 1000 TL gerekli."
        yatirilan_miktar = miktar * 1.25
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] += yatirilan_miktar
        mesaj = f"Vadeli hesaba {miktar:.2f} TL yatırıldı ve %25 faiz ile {yatirilan_miktar:.2f} TL oldu."

    elif hesap_turu == "bireysel_emeklilik":
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] += miktar
        mesaj = f"Bireysel emeklilik hesabına {miktar:.2f} TL yatırıldı."

    elif hesap_turu == "altin_hesabi":
        altin_miktari = miktar / altin
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] += altin_miktari
        mesaj = f"Altın hesabına {altin_miktari:.6f} gram altın yatırıldı."

    elif hesap_turu == "USD":
        usd_miktar = miktar / usd
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] += usd_miktar
        mesaj = f"USD hesabına {usd_miktar:.2f} USD yatırıldı."

    elif hesap_turu == "EUR":
        eur_miktar = miktar / eur
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] += eur_miktar
        mesaj = f"EUR hesabına {eur_miktar:.2f} EUR yatırıldı."

    elif hesap_turu == "vadesiz_hesap":
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] += miktar
        mesaj = f"Vadesiz hesaba {miktar:.2f} TL yatırıldı."

    else:
        return False, "Geçersiz hesap türü."

    kullanicilari_kaydet(kullanicilar)
    islem_guncelle(hesap_numarasi, "Yatırma", miktar) 
    return True, mesaj

def para_cek(hesap_numarasi, hesap_turu, miktar):
    kullanicilar = kullanicilari_yukle()
    if hesap_numarasi not in kullanicilar:
        return False, "Geçersiz hesap numarası"

    try:
        miktar = float(miktar)
        if miktar <= 0:
            return False, "Geçersiz miktar"
    except:
        return False, "Geçersiz miktar"

    basarili, usd, eur, altin = doviz_kurlari()

    bakiye = kullanicilar[hesap_numarasi]["bakiye"].get(hesap_turu, 0)

    if hesap_turu in ["vadeli_hesap", "bireysel_emeklilik"]:
        ilk_giris(kullanicilar, hesap_numarasi, hesap_turu)
        ilk_giris_tarihi = kullanicilar[hesap_numarasi]["bakiye"]["ilk_giris"].get(hesap_turu)
        if not ilk_giris_tarihi:
            return False, "İlk giriş tarihi bulunamadı"
        tarih = datetime.strptime(ilk_giris_tarihi, "%Y-%m-%d %H:%M:%S")
        simdi = datetime.now()
        gecen_sure = (simdi - tarih).days / 365

        if hesap_turu == "vadeli_hesap":
            if gecen_sure < 1:
                ceza_orani = 0.25
                ceza = miktar * ceza_orani
                toplam_cekilecek = miktar + ceza
            else:
                toplam_cekilecek = miktar
        elif hesap_turu == "bireysel_emeklilik":
            if gecen_sure < 5:
                ceza_orani = 0.30
                ceza = miktar * ceza_orani
                toplam_cekilecek = miktar + ceza
            else:
                toplam_cekilecek = miktar

        if bakiye < toplam_cekilecek:
            return False, "Yetersiz bakiye"
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] -= toplam_cekilecek
        mesaj = f"{hesap_turu.replace('_', ' ').title()} hesabından {miktar:.2f} TL kesildi."

    elif hesap_turu == "altin_hesabi":
        if miktar > bakiye * altin:
            return False, "Yetersiz bakiye"
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] -= miktar / altin
        mesaj = f"Altın hesabından {miktar:.2f} TL'lik altın kesildi."

    elif hesap_turu == "USD":
        if miktar > bakiye * usd:
            return False, "Yetersiz bakiye"
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] -= miktar / usd
        mesaj = f"USD hesabından {miktar:.2f} TL karşılığı USD kesildi."

    elif hesap_turu == "EUR":
        if miktar > bakiye * eur:
            return False, "Yetersiz bakiye"
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] -= miktar / eur
        mesaj = f"EUR hesabından {miktar:.2f} TL karşılığı EUR kesildi."

    elif hesap_turu == "vadesiz_hesap":
        if bakiye < miktar:
            return False, "Yetersiz bakiye"
        kullanicilar[hesap_numarasi]["bakiye"][hesap_turu] -= miktar
        mesaj = f"Vadesiz hesaptan {miktar:.2f} TL kesildi."

    else:
        return False, "Geçersiz hesap türü."

    kullanicilari_kaydet(kullanicilar)
    islem_guncelle(hesap_numarasi, "Çekme", miktar)
    return True, mesaj

    return True, "para çekildi"      
def para_transferi(gonderici_numara, alici_numara, hesap_turu, miktar):
    kullanicilar = kullanicilari_yukle()
    if gonderici_numara not in kullanicilar or alici_numara not in kullanicilar:
        return False, "geçersiz gönderici veya alıcı numarası"
    try:
        miktar = float(miktar)
        if miktar <= 0:
            return False, "geçersiz miktar"
    except ValueError:
        return False, "geçersiz miktar"
    if kullanicilar[gonderici_numara]["bakiye"][hesap_turu] < miktar:
        return False, "yetersiz bakiye"

    simdi = datetime.now()
    saat = simdi.hour
    gun = simdi.weekday()

    if gonderici_numara[:3] == alici_numara[:3]:
        islem_turu = "HAVALE"
        kesinti = 0.0025
    else:
        islem_turu = "EFT"
        if 0 <= gun <= 4 and 9 <= saat <= 17:
            kesinti = 0.005
        else:
            kesinti = 0.01

    kesinti_miktari = miktar * kesinti
    toplam_miktar = miktar + kesinti_miktari

    if kullanicilar[gonderici_numara]["bakiye"][hesap_turu] < toplam_miktar:
        return False, "yetersiz bakiye"

    kullanicilar[gonderici_numara]["bakiye"][hesap_turu] -= toplam_miktar
    kullanicilar[alici_numara]["bakiye"][hesap_turu] += miktar
    kullanicilari_kaydet(kullanicilar)
    islem_guncelle(gonderici_numara, "Transfer", miktar)
    return True, f"{miktar:.2f} TL transfer edildi"

    return True, f"{miktar:.3f} TL {islem_turu} işlemi başarıyla gerçekleştirildi. Kesilen ücret: {kesinti_miktari:.3f} TL"
def varlıklarım (kullanici):
    kullanicilar = kullanicilari_yukle()
    if kullanici not in kullanicilar:
        return False, "geçersiz hesap numarası"
    bakiye = kullanicilar[kullanici]["bakiye"]
    # Pasta grafiği çizimi
    etiketler = []
    degerler = []
    for tur, miktar in bakiye.items():
        if isinstance(miktar, (int, float)) and miktar > 0:
            etiketler.append(tur)
            degerler.append(miktar)
    if not etiketler:
        return False, "hiç bakiye yok"
    plt.figure(figsize=(6, 6))
    plt.pie(degerler, labels=etiketler, autopct='%1.1f%%', startangle=90)
    plt.title("Hesap Türlerine Göre Varlıklar")
    plt.axis("equal")
    plt.show()
    return True, "grafik gösterildi"

