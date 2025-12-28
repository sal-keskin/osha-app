# OSHA App Deployment Guide

This guide will walk you through a fresh installation of the OSHA App on a VPS (Virtual Private Server). It assumes you are using **Ubuntu 20.04/22.04**.

## 1. Preparation

First, update your system and install necessary packages.

```bash
sudo apt update
sudo apt install python3-pip python3-venv python3-dev nginx git
```

## 2. Project Setup

Navigate to your web directory (or wherever you want the app to live).

```bash
cd /var/www
# Clone your repository (Replace URL with your actual GitHub URL)
sudo git clone https://github.com/YOUR_USERNAME/osha_app.git
cd osha_app
```

### Virtual Environment

It is best practice to run Python apps in a virtual environment.

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

## 3. Environment Configuration

Create a `.env` file to store your secrets.

```bash
nano .env
```

Paste the following content (Customize the values!):

```env
# Security
SECRET_KEY=change-this-to-a-very-long-random-string
DEBUG=0
ALLOWED_HOSTS=213.238.180.147,yourdomain.com,localhost

# Database (Default is SQLite, no change needed)
```

Save and exit (`Ctrl+X`, `Y`, `Enter`).

## 4. Database & Static Files

Initialize the database and prepare static assets (CSS/JS).

```bash
# Apply migrations (This creates the DB tables)
python manage.py migrate

# Collect static files (Moves all assets to the 'static' folder for Nginx)
python manage.py collectstatic --noinput

# Create a Superuser (Admin account)
python manage.py createsuperuser
```

**Permission Fix:**
Ensure the web server user (`www-data`) handles the files correctly.

```bash
# Give ownership to your user (so you can edit) but allow www-data to read
sudo chown -R $USER:www-data /var/www/osha_app
sudo chmod -R 775 /var/www/osha_app
sudo chown :www-data db.sqlite3
sudo chmod 664 db.sqlite3
# Ensure the folder containing db.sqlite3 is writable
sudo chown :www-data /var/www/osha_app
sudo chmod 775 /var/www/osha_app
```

## 5. Gunicorn Setup (Application Server)

Create a systemd service file to keep the app running.

```bash
sudo nano /etc/systemd/system/osha_app.service
```

Paste the following:

```ini
[Unit]
Description=gunicorn daemon for OSHA App
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/osha_app
ExecStart=/var/www/osha_app/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/var/www/osha_app/osha_app.sock \
          osha_app.wsgi:application

[Install]
WantedBy=multi-user.target
```
*(Note: Changing `User=root` to your specific non-root user is safer, but `root` is used here for simplicity if you are the only admin. Ideally use `User=ubuntu` or similar).*

Start the service:

```bash
sudo systemctl start osha_app
sudo systemctl enable osha_app
```

## 6. Nginx Setup (Web Server)

Configure Nginx to serve the site.

```bash
sudo nano /etc/nginx/sites-available/osha_app
```

Paste the following:

```nginx
server {
    listen 80;
    server_name 213.238.180.147;  # Or your domain name

    location = /favicon.ico { access_log off; log_not_found off; }

    # Serve Static Files
    location /static/ {
        root /var/www/osha_app;
    }

    # Proxy to Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/osha_app/osha_app.sock;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/osha_app /etc/nginx/sites-enabled
sudo nginx -t  # Test config
sudo systemctl restart nginx
```

## 7. How to Reset / Clean Install

If you want to completely wipe the data and start over:

```bash
# 1. Stop services
sudo systemctl stop osha_app nginx

# 2. Delete database
rm /var/www/osha_app/db.sqlite3

# 3. Re-run migrations
source /var/www/osha_app/venv/bin/activate
cd /var/www/osha_app
python manage.py migrate
python manage.py createsuperuser

# 4. Start services
sudo systemctl start osha_app nginx
```
