#!/bin/bash

# Stop on error
set -e

echo "==========================================="
echo "   ISG Takip Uygulaması Kurulum Sihirbazı"
echo "==========================================="

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "HATA: Docker bulunamadı."
    echo "Lütfen önce Docker'ı yükleyin: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    # In newer docker versions, it's 'docker compose' (plugin) not 'docker-compose' (standalone)
    if ! docker compose version &> /dev/null; then
        echo "HATA: Docker Compose bulunamadı."
        echo "Lütfen Docker Compose'u yükleyin."
        exit 1
    fi
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

echo "Docker kontrolü başarılı..."

# 2. Create .env file if missing
if [ ! -f .env ]; then
    echo "Ayarlar dosyası (.env) oluşturuluyor..."
    
    # Generate a random secret key
    SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    
    # Ask for IP address
    read -p "VPS Sunucu IP Adresinizi girin (Örn: 192.168.1.1): " VPS_IP
    
    cat > .env <<EOF
DEBUG=0
SECRET_KEY=$SECRET
ALLOWED_HOSTS=localhost,127.0.0.1,$VPS_IP
EOF
    echo ".env dosyası oluşturuldu."
else
    echo ".env dosyası zaten mevcut, atlanıyor."
fi

# 3. Build and Start
echo "Uygulama derleniyor ve başlatılıyor (Bu işlem birkaç dakika sürebilir)..."
$DOCKER_COMPOSE_CMD up -d --build

# 4. Migrations
echo "Veritabanı tabloları oluşturuluyor..."
$DOCKER_COMPOSE_CMD exec -T web python manage.py migrate

# 5. Create Superuser
echo ""
echo "==========================================="
echo "Yönetici Hesabı Oluşturma"
echo "==========================================="
read -p "Yönetici hesabı oluşturmak ister misiniz? (e/h): " CREATE_ADMIN
if [[ "$CREATE_ADMIN" =~ ^[Ee]$ ]]; then
    $DOCKER_COMPOSE_CMD exec -it web python manage.py createsuperuser
fi

# 6. Finish
echo ""
echo "==========================================="
echo "KURULUM BAŞARIYLA TAMAMLANDI!"
echo "==========================================="
echo "Uygulamaya şu adresten erişebilirsiniz:"
if [ -z "$VPS_IP" ]; then
    echo "http://LOCALHOST:8000"
else
    echo "http://$VPS_IP:8000"
fi
echo ""
echo "Durdurmak için: $DOCKER_COMPOSE_CMD down"
echo "Günlükleri görmek için: $DOCKER_COMPOSE_CMD logs -f"
