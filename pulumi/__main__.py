import pulumi
import pulumi_digitalocean as digitalocean

from config import (
    DEFAULT_REGION,
    DEFAULT_IMAGE,
    TLD,
    WEB_CNAME_TARGET,
    SSH_PUBKEY_NAME,
    SSH_PUBKEY,
    LETSENCRYPT_EMAIL,
    TAILSCALE_AUTH_KEY,
    DO_API_TOKEN,
    ST2_AUTH_USERNAME,
    ST2_AUTH_PASSWORD,
)

vpc = digitalocean.get_vpc(name=f"default-{DEFAULT_REGION}")

domain_analogpuddle_cloud = digitalocean.Domain(
    TLD,
    name=TLD,
    opts=pulumi.ResourceOptions(protect=True),
)

domain_record_web_cname = digitalocean.DnsRecord(
    "web",
    domain=TLD,
    name="web",
    ttl=300,
    type="CNAME",
    value=WEB_CNAME_TARGET,
    opts=pulumi.ResourceOptions(protect=True),
)

sshkey = digitalocean.SshKey(
    SSH_PUBKEY_NAME,
    name=SSH_PUBKEY_NAME,
    public_key=SSH_PUBKEY,
    opts=pulumi.ResourceOptions(protect=True),
)

cloud_init_drip = f"""#cloud-config
write_files:
- path: /var/tmp/cloud-init.sh
  content: |
    #!/usr/bin/env bash
    set -e -o pipefail -u
    export DEBIAN_FRONTEND=noninteractive
    apt-get -y update
    echo
    echo ">>>> TAILSCALE <<<<"
    echo
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.noarmor.gpg \
      | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.tailscale-keyring.list \
      | sudo tee /etc/apt/sources.list.d/tailscale.list
    apt-get -y update
    apt-get -y install tailscale
    sudo tailscale up --authkey "{TAILSCALE_AUTH_KEY}"
    tailscale ip -4
    echo
    echo ">>>> CERTBOT <<<<"
    echo
    snap install core
    snap refresh core
    snap install --classic certbot
    ln -s /snap/bin/certbot /usr/bin/certbot
    touch /root/digitalocean.ini
    chmod 600 /root/digitalocean.ini
    echo "dns_digitalocean_token = {DO_API_TOKEN}" >/root/digitalocean.ini
    snap set certbot trust-plugin-with-root=ok
    snap install certbot-dns-digitalocean
    certbot certonly \
      --agree-tos \
      --email "{LETSENCRYPT_EMAIL}" \
      --non-interactive \
      --dns-digitalocean \
      --dns-digitalocean-propagation-seconds 300 \
      --dns-digitalocean-credentials /root/digitalocean.ini \
      --domains "drip.{TLD}"
    echo
    echo ">>>> LASTMILE <<<<"
    echo
    apt-get install -y nginx
- path: /etc/nginx/sites-enabled/default
  content: |
    server {{
      listen 80 default_server;
      listen [::]:80 default_server;
      server_name drip.{TLD};
      rewrite ^ https://$host$request_uri? permanent;
    }}
    server {{
      listen 443 ssl default_server;
      listen [::]:443 ssl default_server;
      server_name thelounge.{TLD};
      ssl_certificate /etc/letsencrypt/live/drip.{TLD}/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/drip.{TLD}/privkey.pem;
      ssl_protocols TLSv1.3 TLSv1.2;
      ssl_prefer_server_ciphers on;
      ssl_ecdh_curve secp521r1:secp384r1;
      ssl_ciphers EECDH+AESGCM:EECDH+AES256;
      ssl_session_cache shared:TLS:2m;
      ssl_buffer_size 4k;
      # openssl dhparam 4096 -out /etc/ssl/dhparam.pem
      # ssl_dhparam /etc/ssl/dhparam.pem;
      ssl_stapling on;
      ssl_stapling_verify on;
      resolver 1.1.1.1 1.0.0.1 [2606:4700:4700::1111] [2606:4700:4700::1001]; # Cloudflare
      add_header Strict-Transport-Security 'max-age=31536000; includeSubDomains; preload' always;
      root /var/www/html;
      index index.html index.htm index.nginx-debian.html;
      server_name _;
      location / {{
        try_files $uri $uri/ =404;
      }}
    }}
runcmd:
    - - bash
      - /var/tmp/cloud-init.sh
"""

droplet_drip = digitalocean.Droplet(
    "drip",
    image=DEFAULT_IMAGE,
    name="drip",
    region=DEFAULT_REGION,
    size="s-2vcpu-4gb",
    ssh_keys=[sshkey.fingerprint],
    vpc_uuid=vpc.id,
    user_data=cloud_init_drip,
)

domain_record_drip_a = digitalocean.DnsRecord(
    "drip",
    domain=TLD,
    name="drip",
    ttl=300,
    type="A",
    value=droplet_drip.ipv4_address,
)

cloud_init_stackstorm = f"""#cloud-config
write_files:
- path: /var/tmp/stackstorm-inventory.yml
  content: |
    all:
      hosts:
        localhost:
          ansible_connection: local
          st2_auth_username: "{ST2_AUTH_USERNAME}"
          st2_auth_password: "{ST2_AUTH_PASSWORD}"
          st2web_ssl_certificate: |
            {{{{ lookup('ansible.builtin.file', '/etc/letsencrypt/live/stackstorm.{TLD}/fullchain.pem') }}}}
          st2web_ssl_certificate_key: |
            {{{{ lookup('ansible.builtin.file', '/etc/letsencrypt/live/stackstorm.{TLD}/privkey.pem') }}}}
- path: /var/tmp/cloud-init.sh
  content: |
    #!/usr/bin/env bash
    set -e -o pipefail -u
    export DEBIAN_FRONTEND=noninteractive
    apt-get -y update
    echo
    echo ">>>> TAILSCALE <<<<"
    echo
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.noarmor.gpg \
      | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.tailscale-keyring.list \
      | sudo tee /etc/apt/sources.list.d/tailscale.list
    apt-get -y update
    apt-get -y install tailscale
    sudo tailscale up --authkey "{TAILSCALE_AUTH_KEY}"
    tailscale ip -4
    echo
    echo ">>>> CERTBOT <<<<"
    echo
    snap install core
    snap refresh core
    snap install --classic certbot
    ln -s /snap/bin/certbot /usr/bin/certbot
    touch /root/digitalocean.ini
    chmod 600 /root/digitalocean.ini
    echo "dns_digitalocean_token = {DO_API_TOKEN}" >/root/digitalocean.ini
    snap set certbot trust-plugin-with-root=ok
    snap install certbot-dns-digitalocean
    certbot certonly \
      --agree-tos \
      --email "{LETSENCRYPT_EMAIL}" \
      --non-interactive \
      --dns-digitalocean \
      --dns-digitalocean-propagation-seconds 300 \
      --dns-digitalocean-credentials /root/digitalocean.ini \
      --domains "stackstorm.{TLD}" \
      --domains "x.stackstorm.{TLD}"
    echo
    echo ">>>> STACKSTORM <<<<"
    echo
    sudo apt-get -y install python3-pip
    sudo pip3 install ansible
    git clone https://github.com/StackStorm/ansible-st2
    pushd ansible-st2
    ansible-playbook stackstorm.yml -i /var/tmp/stackstorm-inventory.yml -v
    popd
runcmd:
    - - bash
      - /var/tmp/cloud-init.sh
"""

droplet_stackstorm = digitalocean.Droplet(
    "stackstorm",
    image=DEFAULT_IMAGE,
    name="stackstorm",
    region=DEFAULT_REGION,
    size="g-2vcpu-8gb",
    ssh_keys=[sshkey.fingerprint],
    vpc_uuid=vpc.id,
    user_data=cloud_init_stackstorm,
)

domain_record_stackstorm_a = digitalocean.DnsRecord(
    "stackstorm",
    domain=TLD,
    name="stackstorm",
    ttl=300,
    type="A",
    value=droplet_stackstorm.ipv4_address,
)

cloud_init_thelounge = f"""#cloud-config
groups:
  - thelounge
users:
  - name: thelounge
    gecos: The Lounge
    primary_group: thelounge
    lock_passwd: true
write_files:
- path: /var/tmp/cloud-init.sh
  content: |
    #!/usr/bin/env bash
    set -e -o pipefail -u
    export DEBIAN_FRONTEND=noninteractive
    apt-get -y update
    echo
    echo ">>>> TAILSCALE <<<<"
    echo
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.noarmor.gpg \
      | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.tailscale-keyring.list \
      | sudo tee /etc/apt/sources.list.d/tailscale.list
    apt-get -y update
    apt-get -y install tailscale
    tailscale up --authkey "{TAILSCALE_AUTH_KEY}"
    tailscale ip -4
    echo
    echo ">>>> CERTBOT <<<<"
    echo
    snap install core
    snap refresh core
    snap install --classic certbot
    ln -s /snap/bin/certbot /usr/bin/certbot
    touch /root/digitalocean.ini
    chmod 600 /root/digitalocean.ini
    echo "dns_digitalocean_token = {DO_API_TOKEN}" >/root/digitalocean.ini
    snap set certbot trust-plugin-with-root=ok
    snap install certbot-dns-digitalocean
    certbot certonly \
      --agree-tos \
      --email "{LETSENCRYPT_EMAIL}" \
      --non-interactive \
      --dns-digitalocean \
      --dns-digitalocean-propagation-seconds 300 \
      --dns-digitalocean-credentials /root/digitalocean.ini \
      --domains "thelounge.{TLD}" \
      --domains "x.thelounge.{TLD}"
    echo
    echo ">>>> THELOUNGE <<<<"
    echo
    apt-get install -y nginx
    curl -sL https://deb.nodesource.com/setup_18.x -o /var/tmp/nodesource_setup.sh
    bash -x /var/tmp/nodesource_setup.sh
    apt-get install -y nodejs
    node -v
    wget -c https://github.com/thelounge/thelounge/releases/download/v4.3.1/thelounge_4.3.1-2_all.deb
    dpkg -i thelounge_4.3.1-2_all.deb
- path: /etc/nginx/sites-enabled/default
  content: |
    server {{
      listen 80 default_server;
      listen [::]:80 default_server;
      server_name thelounge.{TLD};
      rewrite ^ https://$host$request_uri? permanent;
    }}
    server {{
      listen 443 ssl default_server;
      listen [::]:443 ssl default_server;
      server_name thelounge.{TLD};
      ssl_certificate /etc/letsencrypt/live/thelounge.{TLD}/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/thelounge.{TLD}/privkey.pem;
      ssl_protocols TLSv1.3 TLSv1.2;
      ssl_prefer_server_ciphers on;
      ssl_ecdh_curve secp521r1:secp384r1;
      ssl_ciphers EECDH+AESGCM:EECDH+AES256;
      ssl_session_cache shared:TLS:2m;
      ssl_buffer_size 4k;
      # openssl dhparam 4096 -out /etc/ssl/dhparam.pem
      # ssl_dhparam /etc/ssl/dhparam.pem;
      ssl_stapling on;
      ssl_stapling_verify on;
      resolver 1.1.1.1 1.0.0.1 [2606:4700:4700::1111] [2606:4700:4700::1001]; # Cloudflare
      add_header Strict-Transport-Security 'max-age=31536000; includeSubDomains; preload' always;
      root /var/www/html;
      index index.html index.htm index.nginx-debian.html;
      server_name _;
      location / {{
        # try_files $uri $uri/ =404;
        proxy_pass http://127.0.0.1:9000/;
        proxy_http_version 1.1;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        # by default nginx times out connections in one minute
        proxy_read_timeout 1d;
      }}
    }}
- path: /etc/thelounge/config.js
  owner: thelounge:thelounge
  permissions: '0644'
  content: |
    "use strict";
    module.exports = {{
      public: false,
      host: "127.0.0.1",
      port: 9000,
      bind: undefined,
      reverseProxy: true,
      maxHistory: 10000,
      https: {{
        enable: false,
        key: "",
        certificate: "",
        ca: "",
      }},
      theme: "default",
      prefetch: false,
      disableMediaPreview: false,
      prefetchStorage: false,
      prefetchMaxImageSize: 2048,
      prefetchMaxSearchSize: 50,
      fileUpload: {{
        enable: false,
        maxFileSize: 10240,
        baseUrl: null,
      }},
      transports: ["polling", "websocket"],
      leaveMessage: "The Lounge - https://thelounge.chat",
      defaults: {{
        name: "Libera.Chat",
        host: "irc.libera.chat",
        port: 6697,
        password: "",
        tls: true,
        rejectUnauthorized: true,
        nick: "thelounge%%",
        username: "thelounge",
        realname: "The Lounge User",
        join: "#thelounge",
        leaveMessage: "",
      }},
      lockNetwork: false,
      messageStorage: ["sqlite", "text"],
      useHexIp: false,
      webirc: null,
      identd: {{
        enable: false,
        port: 113,
      }},
      oidentd: null,
      ldap: {{
        enable: false,
        url: "ldaps://example.com",
        tlsOptions: {{}},
        primaryKey: "uid",
        searchDN: {{
          rootDN: "cn=thelounge,ou=system-users,dc=example,dc=com",
          rootPassword: "1234",
          filter: "(objectClass=person)(memberOf=ou=accounts,dc=example,dc=com)",
          base: "dc=example,dc=com",
          scope: "sub",
        }},
      }},
      debug: {{
        ircFramework: false,
        raw: false,
      }},
    }};
runcmd:
    - - bash
      - /var/tmp/cloud-init.sh
"""

droplet_thelounge = digitalocean.Droplet(
    "thelounge",
    image=DEFAULT_IMAGE,
    name="thelounge",
    region=DEFAULT_REGION,
    size="s-1vcpu-2gb",
    ssh_keys=[sshkey.fingerprint],
    vpc_uuid=vpc.id,
    user_data=cloud_init_thelounge,
)

domain_record_thelounge_a = digitalocean.DnsRecord(
    "thelounge",
    domain=TLD,
    name="thelounge",
    ttl=300,
    type="A",
    value=droplet_thelounge.ipv4_address,
)

with open("../README.md") as f:
    pulumi.export("readme", f.read())
