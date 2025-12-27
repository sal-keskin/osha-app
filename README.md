# İSG Takip Sistemi (Occupational Safety and Health App)

Bu proje, İş Sağlığı ve Güvenliği süreçlerini takip etmek için geliştirilmiş, Docker üzerinde çalışan bir web uygulamasıdır.

## Özellikler
*   İşyeri, Çalışan, Eğitici ve Profesyonel (Hekim/Uzman) takibi.
*   Eğitim, Denetim ve Sağlık Muayenesi kayıtları.
*   TCKN ve Lisans No doğrulaması.
*   Mobil uyumlu arayüz (Türkçe).

## Proje Dosya Yapısı

```text
.
├── setup.sh                # Otomatik kurulum sihirbazı (VPS için)
├── Dockerfile              # Python/Django uygulama imajı
├── docker-compose.yml      # Docker servis yapılandırması
├── requirements.txt        # Gerekli Python kütüphaneleri
├── manage.py               # Django yönetim aracı
├── .gitignore              # Git tarafından yok sayılacak dosyalar
├── README.md               # Proje dokümantasyonu
├── osha_app/               # Ana proje ayarları
│   ├── settings.py         # Veritabanı, güvenlik ve uygulama ayarları
│   └── urls.py             # Ana URL yönlendirmeleri
└── core/                   # Uygulama mantığı (Modüller)
    ├── models.py           # Veritabanı tabloları (İşyeri, Çalışan, vb.)
    ├── views.py            # Sayfa fonksiyonları (Görüntüleme, Ekleme, Düzenleme)
    ├── forms.py            # Giriş formları ve doğrulama kuralları (TCKN kontrolü vb.)
    ├── urls.py             # Uygulama içi link yapıları
    ├── tests.py            # Test senaryoları
    ├── templatetags/       # Özel şablon filtreleri
    │   └── core_extras.py  # Dinamik veri okuma filtresi
    └── templates/core/     # Kullanıcı arayüzü (HTML)
        ├── base.html       # Ana şablon (Menü, Bootstrap yapıları)
        ├── dashboard.html  # Ana sayfa paneli
        ├── login.html      # Giriş ekranı
        └── ...             # Diğer listeleme ve form şablonları
```

## Kurulum (Linux VPS)

Bu uygulamayı sunucunuza kurmak için sadece Docker'a ihtiyacınız vardır.

### 1. Gereksinimler
Eğer sunucunuzda Docker kurulu değilse, şu komutla kurabilirsiniz:
```bash
curl -fsSL https://get.docker.com | sh
```

### 2. İndirme ve Kurulum
Projeyi sunucunuza indirdikten sonra, proje klasörü içinde şu komutu çalıştırın:

```bash
chmod +x setup.sh
./setup.sh
```

Bu sihirbaz size şunları soracaktır:
1.  **Sunucu IP Adresi**: Uygulamaya erişeceğiniz IP adresi (örneğin `192.168.1.100`).
2.  **Yönetici Hesabı**: Giriş yapmak için bir kullanıcı adı ve şifre belirlemenizi isteyecektir.

### 3. Kullanım
Kurulum bittikten sonra tarayıcınızdan şu adrese gidin:
`http://SUNUCU_IP_ADRESI:8000`

Belirlediğiniz yönetici kullanıcı adı ve şifresi ile giriş yapabilirsiniz.

## Yönetim Komutları

Uygulama arka planda çalışmaya devam eder.

*   **Durdurmak için:**
    ```bash
    docker-compose down
    ```
*   **Tekrar Başlatmak için:**
    ```bash
    docker-compose up -d
    ```
*   **Günlükleri (Logları) İzlemek için:**
    ```bash
    docker-compose logs -f
    ```

## Güncelleme
Eğer kodlarda değişiklik yaptıysanız ve güncellemek istiyorsanız:

```bash
docker-compose up -d --build
```
