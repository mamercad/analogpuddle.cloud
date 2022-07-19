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

cloud_init_drip = """#cloud-config
write_files:
- path: /var/tmp/cloud-init.sh
  content: |
    #!/usr/bin/env bash
    set -e -o pipefail -u
    export DEBIAN_FRONTEND=noninteractive
    sudo apt-get -y update
    echo
    echo ">>>> TAILSCALE <<<<"
    echo
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.noarmor.gpg \
      | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.tailscale-keyring.list \
      | sudo tee /etc/apt/sources.list.d/tailscale.list
    sudo apt-get -y update
    sudo apt-get -y install tailscale
    sudo tailscale up --authkey "{0}"
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
    echo "dns_digitalocean_token = {2}" >/root/digitalocean.ini
    snap set certbot trust-plugin-with-root=ok
    snap install certbot-dns-digitalocean
    certbot certonly \
      --agree-tos \
      --email "{3}" \
      --non-interactive \
      --dns-digitalocean \
      --dns-digitalocean-propagation-seconds 300 \
      --dns-digitalocean-credentials /root/digitalocean.ini \
      --domains "{1}" \
      --domains "*.{1}"
runcmd:
    - - bash
      - /var/tmp/cloud-init.sh
""".format(
    TAILSCALE_AUTH_KEY,
    TLD,
    DO_API_TOKEN,
    LETSENCRYPT_EMAIL,
)

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

cloud_init_stackstorm = """#cloud-config
write_files:
- path: /var/tmp/stackstorm-inventory.yml
  content: |
    all:
      hosts:
        localhost:
          ansible_connection: local
          st2_auth_username: "{4}"
          st2_auth_password: "{5}"
          st2web_ssl_certificate: "{{{{ lookup('ansible.builtin.file', '{6}') }}}}\n"
          st2web_ssl_certificate_key: "{{{{ lookup('ansible.builtin.file', '{7}') }}}}\n"
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
    sudo tailscale up --authkey "{0}"
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
    echo "dns_digitalocean_token = {2}" >/root/digitalocean.ini
    snap set certbot trust-plugin-with-root=ok
    snap install certbot-dns-digitalocean
    certbot certonly \
      --agree-tos \
      --email "{3}" \
      --non-interactive \
      --dns-digitalocean \
      --dns-digitalocean-propagation-seconds 300 \
      --dns-digitalocean-credentials /root/digitalocean.ini \
      --domains "stackstorm.{1}"
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
""".format(
    TAILSCALE_AUTH_KEY,
    TLD,
    DO_API_TOKEN,
    LETSENCRYPT_EMAIL,
    ST2_AUTH_USERNAME,
    ST2_AUTH_PASSWORD,
    f"/etc/letsencrypt/live/stackstorm.{TLD}/chain.pem",
    f"/etc/letsencrypt/live/stackstorm.{TLD}/privkey.pem",
)

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
