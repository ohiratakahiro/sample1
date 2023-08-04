# group_e

メディアファイルを使ったサンプルプロジェクトです。

デプロイについても触れているので、デプロイしたい際は参考にしてください。


## 動かし方 開発環境

```
(仮想環境を有効化する)
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

その後、 http://127.0.0.1:8000 にブラウザでアクセスしてください。


## 本番環境へのデプロイについて


### 対象のLinuxディストリビューション

Ubuntu, 22.04 LTS で動作を確認しています。

### サーバーで使用しているソフトウェア一覧
* 
* Python
* Django
* Gunicorn (Djangoを動作させるもの)
* Nginx (Webサーバー)
* PostgreSQL (DBサーバー)

### 手順

```
       →      →
ブラウザ   Nginx   Gunicorn+Django
       ←       ←
```
       
#### 初期設定

```
sudo apt update
sudo apt upgrade
```

インストール可能なパッケージの一覧の更新(update)と、インストール済みのパッケージ一覧を更新する(upgrade)



#### PythonとDjangoインストール

Pythonのコンパイルに必要なパッケージをインストールする

```
sudo apt install build-essential libbz2-dev libdb-dev \
  libreadline-dev libffi-dev libgdbm-dev liblzma-dev \
  libncursesw5-dev libsqlite3-dev libssl-dev \
  zlib1g-dev uuid-dev tk-dev
```

Pythonのダウンロードと、解答

```
wget  https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tar.xz
tar xJf Python-3.11.1.tar.xz

```

Pythonのコンパイル

```
cd Python-3.11.1
./configure
make
sudo make altinstall
```

Pythonが使えるか、ここで確認しておく
```
sudo python3.11 -V
```

#### Nginxインストール

```
sudo apt install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

AWSの場合、セキュリティグループを設定し、パブリックIPアドレスをコピーしてページにアクセスして、無事に表示できるか一度確認する


次に、Nginxの設定ファイルを作成する

```
sudo nano /etc/nginx/conf.d/django.conf
```

中身を次のようにする

```
server {
    listen 80;
    server_name IPアドレスを入れる;
    location /static {
        alias /var/www/static;
       }
    location /media {
        alias /var/www/media;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```


設定ファイルを作成したので、nginxを再起動する
```
sudo systemctl reload nginx
```

ブラウザでアクセスして確認してみる、現段階では 502 Bad Gatewayと出る


#### Djangoソースコードのクローンと、起動確認

Djangoなど、必要なライブラリをインストールする

```
sudo python3.11 -m pip install django gunicorn psycopg2-binary pillow
```

Djangoソースコードをクローンする

```
cd ~
git clone https://github.com/naritotakizawa/group_e
```

本番環境ようのsettingsを作成する

```commandline
cd group_e
nano conf/production_settings.py
```

中身を次のようにする

```
import os
from .settings import *

ALLOWED_HOSTS = ['54.250.226.14']

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'djangodb',
        'USER': 'django_user',
        'PASSWORD': 'django',
        'HOST': '',
        'PORT': 5432,
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"

        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/django.log',
            'formatter': 'standard',
            'when': 'W0',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
        },
    },
}

STATIC_ROOT = '/var/www/static'

MEDIA_ROOT = '/var/www/media'

```


ログファイルにエラーを書くようにするので、ログファイル作成と権限の設定

```
sudo touch /var/log/django.log
sudo chmod 777 /var/log/django.log
```

gunicornコマンドで、動作を確認してみる
```
/usr/local/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 conf.wsgi:application --env DJANGO_SETTINGS_MODULE=conf.production_settings
```

ブラウザでアクセスすると500エラーになる。これは Django側でエラーがあった場合に見るエラー。ログファイルを確認してみる

```
sudo cat /var/log/django.log
```


#### PostgreSQLインストール

```
sudo apt install postgresql postgresql-contrib
```

ポスグレのデータベース作成や、データベースで使うユーザーを設定する

```
sudo -u postgres psql
CREATE DATABASE djangodb;
CREATE USER django_user WITH PASSWORD 'django';
ALTER ROLE django_user SET client_encoding TO 'utf8';
ALTER ROLE django_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE django_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE djangodb TO django_user;
```

Ctrl + Z などで、ポスグレ画面から抜けます、

認証方式を少しかえる
```
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

次の、local all all peer部分をtrustに書き換える

```
local   all             all                                     peer
↓
local   all             all                                     trust
```

設定ファイルを変更したので、再起動する

```
sudo systemctl restart postgresql
```

#### Gunicornインストールと、systemdでの起動

マイグレート、コレクトスタティックを行う

```
sudo python3.11 manage.py migrate --settings=conf.production_settings
sudo python3.11 manage.py collectstatic --settings=conf.production_settings
```

メディアファイル置き場を作り、それぞれに権限を設定し、djangoがファイルを作成できるようにする

```
sudo mkdir /var/www/media
sudo chmod 775 /var
sudo chmod 775 /var/www
sudo chmod 777 /var/www/media
sudo chmod 777 /var/www/static
```


gunicornコマンドで、動作できるか確認する

```
/usr/local/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 conf.wsgi:application --env DJANGO_SETTINGS_MODULE=conf.production_settings
```

systemdで起動できるようにする

```
sudo nano /etc/systemd/system/django.service
```

中身を次のようにする
```
[Unit]
    Description=gunicorn
    After=network.target
[Service]
    WorkingDirectory=/home/ubuntu/group_e
    ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 conf.wsgi:application
    Environment="DJANGO_SETTINGS_MODULE=conf.production_settings"
[Install]
    WantedBy=multi-user.target
```

systemdで起動する。また、enableで自動起動するようにし、statusでちゃんと動作するかを確認してみる

```
sudo systemctl start django
sudo systemctl enable django
sudo systemctl status django
```


## 研修受講生へ

長い間お疲れ様でした。これからも頑張ってください。
