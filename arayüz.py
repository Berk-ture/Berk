import customtkinter as ctk
import time
import json
import os
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from data_base import (
    hesap_olustur, sifre_dogrula, para_yatir, para_cek, para_transferi,
    islem_gecmisi_getir, doviz_kurlari,
    aylik_ozet_grafik, varlıklarım
)
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

blokeli_kullanicilar = {}

def aylik_ozet_grafik_figure(hesap):
    ay = time.strftime("%Y-%m")
    veriler = islem_gecmisi_getir(hesap)
    yatirilan = 0
    cekilen = 0
    for islem in veriler:
        if islem["tarih"].startswith(ay):
            if islem["islem"] == "Yatırma":
                yatirilan += float(islem["miktar"])
            elif islem["islem"] == "Çekme":
                cekilen += float(islem["miktar"])
    fig = Figure(figsize=(5, 5)) # 5x5 boyutunda bir figür oluşturuyoruz
    ax = fig.add_subplot(111) # 1x1'lik bir ızgarada 1. alt grafiği oluşturuyoruz
    ax.pie([yatirilan, cekilen], labels=["Yatırılan", "Çekilen"], autopct='%1.1f%%')
    ax.set_title("Aylık İşlem Özeti")
    return fig

def varliklarim_figure(hesap):
    from data_base import kullanicilari_yukle
    kullanicilar = kullanicilari_yukle()
    bakiye = kullanicilar[hesap]["bakiye"]
    etiketler = []
    degerler = []
    for tur, miktar in bakiye.items():
        if isinstance(miktar, (int, float)) and miktar > 0: #belirli bir türe ait olup olmadığı kontrol ediliyor Sayı olup olmadığı ve pozitif mi diye  
            etiketler.append(tur)
            degerler.append(miktar)
    fig = Figure(figsize=(5, 5)) # 5x5 boyutunda bir figür oluşturuyoruz
    ax = fig.add_subplot(111) # 1x1'lik bir ızgarada 1. alt grafiği oluşturuyoruz
    ax.pie(degerler, labels=etiketler, autopct='%1.1f%%', startangle=90)
    ax.set_title("Hesap Türlerine Göre Varlıklar")
    return fig

class BankaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Banka Giriş Ekranı")
        self.geometry("500x400")
        self.frames = {}
        self.giris_haklari = {}
        self.giris_hesap = None

        for F in (IntroEkrani, GirisEkrani, OturumAcilirEkrani, KayitEkrani, AnaMenu, ParaYatirFrame, ParaCekFrame, ParaTransferFrame, IslemGecmisiFrame, AylikOzetFrame, DovizKurlariFrame, VarliklarimFrame):
            frame = F(self) #bir sınıftan nesne oluşturuyoruz
            self.frames[F] = frame #Oluşturduğumuz nesneyi frames sözlüğüne ekliyoruz
            frame.place(relwidth=1, relheight=1)

        self.show_frame(IntroEkrani)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class] #frames sözlüğünden frame_class anahtarına karşılık gelen frame nesnesini alıyoruz
        frame.tkraise() #frame'i ön plana getiriyoruz



class IntroEkrani(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.bg_label = None
        try:
            if os.path.exists("anaekran.png"):
                bg_image = Image.open("anaekran.png")
                bg_image = bg_image.resize((1000, 750))
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
                self.bg_label.place(relwidth=1, relheight=1)
        except Exception as e:
            print("Resim yüklenemedi:", e)

        ctk.CTkButton(self, text="Bankamıza Hoş Geldiniz", command=lambda: master.show_frame(GirisEkrani)).place(relx=0.5, rely=0.8, anchor="center")

class GirisEkrani(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        ctk.CTkLabel(self, text="Banka Giriş Sistemi", font=("Arial", 20)).pack(pady=30)

        ctk.CTkButton(self, text="Oturum Aç", command=lambda: master.show_frame(OturumAcilirEkrani)).pack(pady=10)
        ctk.CTkButton(self, text="Kayıt Ol", command=lambda: master.show_frame(KayitEkrani)).pack()

class OturumAcilirEkrani(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        ctk.CTkLabel(self, text="Oturum Aç", font=("Arial", 20)).pack(pady=10)

        ctk.CTkLabel(self, text="Hesap Numarası").pack()
        self.hesap_numarasi_entry = ctk.CTkEntry(self)
        self.hesap_numarasi_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Şifre").pack()
        self.sifre_entry = ctk.CTkEntry(self, show="*")
        self.sifre_entry.pack(pady=5)

        self.goster_var = ctk.BooleanVar() #True veya False tutarak bize şifreyi göstere tıklanıldığını veya tıklanılmadığını gösteriyor 
        self.goster_sifre_cb = ctk.CTkCheckBox(self, text="Şifreyi Göster", variable=self.goster_var, command=self.sifre_goster_gizle)
        self.goster_sifre_cb.pack(pady=2)

        self.mesaj_label = ctk.CTkLabel(self, text="")
        self.mesaj_label.pack(pady=5)

        ctk.CTkButton(self, text="Giriş Yap", command=self.oturum_ac).pack(pady=10)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(GirisEkrani)).pack(pady=5)

    def sifre_goster_gizle(self):
        if self.goster_var.get():
            self.sifre_entry.configure(show="")
        else:
            self.sifre_entry.configure(show="*")

    def oturum_ac(self):
        hesap = self.hesap_numarasi_entry.get()
        sifre = self.sifre_entry.get()
        simdi = time.time()

        if hesap in blokeli_kullanicilar:
            if simdi < blokeli_kullanicilar[hesap]:
                kalan = int((blokeli_kullanicilar[hesap] - simdi) / 60)
                self.mesaj_label.configure(text=f"Bu hesap bloke. Kalan süre: {kalan} dk")
                return
            else:
                del blokeli_kullanicilar[hesap]

        if sifre_dogrula(hesap, sifre):
            self.master.giris_hesap = hesap
            self.master.show_frame(AnaMenu)
        else:
            self.master.giris_haklari[hesap] = self.master.giris_haklari.get(hesap, 3) - 1
            kalan_hak = self.master.giris_haklari[hesap]
            if kalan_hak <= 0:
                blokeli_kullanicilar[hesap] = time.time() + 3600
                self.mesaj_label.configure(text="3 kez yanlış girdiniz. 1 saat bloke.")
            else:
                self.mesaj_label.configure(text=f"Hatalı şifre. Kalan hak: {kalan_hak}")


class KayitEkrani(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        ctk.CTkLabel(self, text="Kayıt Ol", font=("Arial", 20)).pack(pady=20)

        ctk.CTkLabel(self, text="İsim").pack()
        self.isim_entry = ctk.CTkEntry(self)
        self.isim_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Soyisim").pack()
        self.soyisim_entry = ctk.CTkEntry(self)
        self.soyisim_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Şifre").pack()
        self.sifre_entry = ctk.CTkEntry(self, show="*")
        self.sifre_entry.pack(pady=5)

        self.goster_var = ctk.BooleanVar()
        self.goster_sifre_cb = ctk.CTkCheckBox(self, text="Şifreyi Göster", variable=self.goster_var, command=self.sifre_goster_gizle)
        self.goster_sifre_cb.pack(pady=2)

        self.mesaj_label = ctk.CTkLabel(self, text="")
        self.mesaj_label.pack(pady=5)

        ctk.CTkButton(self, text="Kayıt Ol", command=self.kayit_ol).pack(pady=10)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(GirisEkrani)).pack(pady=5)
    def sifre_goster_gizle(self):
        if self.goster_var.get():
            self.sifre_entry.configure(show="")
        else:
            self.sifre_entry.configure(show="*")

    def kayit_ol(self):
        isim = self.isim_entry.get()
        soyisim = self.soyisim_entry.get()
        sifre = self.sifre_entry.get()
        basarili, sonuc = hesap_olustur(isim, soyisim, sifre)
        if basarili:
            self.mesaj_label.configure(text=f"Başarılı! Hesap No: {sonuc}")
            self.after(3600, lambda: self.master.show_frame(GirisEkrani))
        else:
            detay = "\n\nŞifre en az 8 karakter olmalı,\nBüyük harf, küçük harf, rakam ve özel karakter (_ @ .) içermelidir."
            self.mesaj_label.configure(text=f"Şifreniz geçersiz: {sonuc}{detay}")

class AnaMenu(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Ana Menü", font=("Arial", 20)).pack(pady=20)
        ctk.CTkButton(self, text="Para Yatır", command=lambda: master.show_frame(ParaYatirFrame)).pack(pady=5)
        ctk.CTkButton(self, text="Para Çek", command=lambda: master.show_frame(ParaCekFrame)).pack(pady=5)
        ctk.CTkButton(self, text="Para Transferi", command=lambda: master.show_frame(ParaTransferFrame)).pack(pady=5)
        ctk.CTkButton(self, text="Varlıklarım", command=lambda: master.show_frame(VarliklarimFrame)).pack(pady=5)
        ctk.CTkButton(self, text="İşlem Geçmişi", command=lambda: master.show_frame(IslemGecmisiFrame)).pack(pady=5)
        ctk.CTkButton(self, text="Aylık Özet", command=lambda: master.show_frame(AylikOzetFrame)).pack(pady=5)
        ctk.CTkButton(self, text="Çıkış Yap", command=self.quit).pack(pady=20)

class VarliklarimFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Varlıklarım", font=("Arial", 20)).pack(pady=10)
        ctk.CTkButton(self, text="Grafiği Göster", command=self.goster).pack(pady=10)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(AnaMenu)).pack(pady=5)
        self.canvas = None

    def goster(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        hesap = self.master.giris_hesap
        try:
            fig = varliklarim_figure(hesap)
            self.canvas = FigureCanvasTkAgg(fig, master=self)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()
        except Exception as e:
            print(f"Grafik gösterilemedi: {str(e)}")
            
class ParaYatirFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Para Yatır", font=("Arial", 20)).pack(pady=10)
        self.hesap_turu = ctk.CTkComboBox(self, values=["vadesiz_hesap", "vadeli_hesap", "bireysel_emeklilik", "altin_hesabi", "USD", "EUR"])
        self.hesap_turu.pack(pady=5)
        self.miktar = ctk.CTkEntry(self, placeholder_text="Miktar")
        self.miktar.pack(pady=5)
        self.mesaj = ctk.CTkLabel(self, text="")
        self.mesaj.pack(pady=5)
        ctk.CTkButton(self, text="Yatır", command=self.yatir).pack(pady=5)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(AnaMenu)).pack(pady=5)

    def yatir(self):
        hesap = self.master.giris_hesap
        tur = self.hesap_turu.get()
        miktar = self.miktar.get()
        try:
            sonuc, mesaj = para_yatir(hesap, tur, miktar)
            if sonuc:
                self.mesaj.configure(text=mesaj, text_color="green")
            else:
                self.mesaj.configure(text=f"Hata: {mesaj}", text_color="red")
        except Exception as e:
            self.mesaj.configure(text=f"Bir hata oluştu: {str(e)}", text_color="red")


class ParaCekFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Para Çek", font=("Arial", 20)).pack(pady=10)
        self.hesap_turu = ctk.CTkComboBox(self, values=["vadesiz_hesap", "vadeli_hesap", "bireysel_emeklilik", "altin_hesabi", "USD", "EUR"])
        self.hesap_turu.pack(pady=5)
        self.miktar = ctk.CTkEntry(self, placeholder_text="Miktar")
        self.miktar.pack(pady=5)
        self.mesaj = ctk.CTkLabel(self, text="")
        self.mesaj.pack(pady=5)
        ctk.CTkButton(self, text="Çek", command=self.cek).pack(pady=5)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(AnaMenu)).pack(pady=5)

    def cek(self):
        hesap = self.master.giris_hesap
        tur = self.hesap_turu.get()
        miktar = self.miktar.get()
        try:
            sonuc, mesaj = para_cek(hesap, tur, miktar)
            if sonuc:
                self.mesaj.configure(text=mesaj, text_color="green")
            else:
                self.mesaj.configure(text=f"Hata: {mesaj}", text_color="red")
        except Exception as e:
            self.mesaj.configure(text=f"Bir hata oluştu: {str(e)}", text_color="red")


class ParaTransferFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Para Transferi", font=("Arial", 20)).pack(pady=10)
        self.alici = ctk.CTkEntry(self, placeholder_text="Alıcı Hesap No")
        self.alici.pack(pady=5)
        self.hesap_turu = ctk.CTkComboBox(self, values=["vadesiz_hesap", "vadeli_hesap", "bireysel_emeklilik", "altin_hesabi", "USD", "EUR"])
        self.hesap_turu.pack(pady=5)
        self.miktar = ctk.CTkEntry(self, placeholder_text="Miktar")
        self.miktar.pack(pady=5)
        self.mesaj = ctk.CTkLabel(self, text="")
        self.mesaj.pack(pady=5)
        ctk.CTkButton(self, text="Transfer Et", command=self.transfer_et).pack(pady=5)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(AnaMenu)).pack(pady=5)

    def transfer_et(self):
        gonderici = self.master.giris_hesap
        alici = self.alici.get()
        tur = self.hesap_turu.get()
        miktar = self.miktar.get()
        try:
            sonuc, mesaj = para_transferi(gonderici, alici, tur, miktar)
            if sonuc:
                self.mesaj.configure(text=mesaj, text_color="green")
            else:
                self.mesaj.configure(text=f"Hata: {mesaj}", text_color="red")
        except Exception as e:
            self.mesaj.configure(text=f"Bir hata oluştu: {str(e)}", text_color="red")
class IslemGecmisiFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        ctk.CTkLabel(self, text="İşlem Geçmişi", font=("Arial", 20)).pack(pady=10)

        self.textbox = ctk.CTkTextbox(self, width=450, height=200)  # 450 genişlik, 200 yükseklik
        self.textbox.pack(pady=10)

        ctk.CTkButton(self, text="Görüntüle", command=self.goruntule).pack(pady=5)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(AnaMenu)).pack(pady=5)

    def goruntule(self):
        self.textbox.delete("1.0", "end")
        hesap = self.master.giris_hesap
        try:
            veriler = islem_gecmisi_getir(hesap)
            if not veriler:
                self.textbox.insert("end", "İşlem bulunamadı.")
            else:
                for islem in veriler:
                    try:
                        satir = f"{islem['tarih']} - {islem['islem']}: {islem['miktar']}\n"
                        self.textbox.insert("end", satir)
                    except (KeyError, TypeError) as e:
                        self.textbox.insert("end", f"Hatalı işlem kaydı: {e}\n")
        except Exception as e:
            self.textbox.insert("end", f"İşlem geçmişi yüklenirken hata oluştu:\n{str(e)}")


class AylikOzetFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Aylık Özet", font=("Arial", 20)).pack(pady=10)
        ctk.CTkButton(self, text="Grafiği Göster", command=self.goster).pack(pady=10)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(AnaMenu)).pack(pady=5)
        self.canvas = None

    def goster(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        hesap = self.master.giris_hesap
        try:
            fig = aylik_ozet_grafik_figure(hesap)
            self.canvas = FigureCanvasTkAgg(fig, master=self)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()
        except Exception as e:
            print(f"Grafik gösterilemedi: {str(e)}")

class DovizKurlariFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Döviz Kurları", font=("Arial", 20)).pack(pady=10)
        self.label = ctk.CTkLabel(self, text="")
        self.label.pack(pady=10)
        ctk.CTkButton(self, text="Güncelle", command=self.guncelle).pack(pady=10)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(AnaMenu)).pack(pady=10)
        ctk.CTkButton(self, text="Geri", command=lambda: master.show_frame(GirisEkrani)).pack(pady=5)

    def guncelle(self):
        sonuc = doviz_kurlari()
        if sonuc[0]:
            _, usd, eur, altin = sonuc
            self.label.configure(text=f"USD: {usd} TL\nEUR: {eur} TL\nAltın: {altin} TL")
        else:
            self.label.configure(text="Döviz kurları alınamadı.")

if __name__ == "__main__":
    app = BankaApp()
    app.mainloop()
