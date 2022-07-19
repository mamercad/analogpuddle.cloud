import os

import pulumi
import pulumi_digitalocean as digitalocean

from constants import (
    DEFAULT_REGION,
    TLD,
    SSH_PUBKEY_NAME,
    SSH_PUBKEY,
    LETSENCRYPT_EMAIL,
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
    value="mamercad.github.io.",
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
    os.getenv("TAILSCALE_AUTH_KEY"),
    TLD,
    os.getenv("DO_API_TOKEN"),
    LETSENCRYPT_EMAIL,
)

droplet_drip = digitalocean.Droplet(
    "drip",
    image="ubuntu-20-04-x64",
    name="drip",
    region=DEFAULT_REGION,
    size="s-2vcpu-4gb",
    ssh_keys=[sshkey.fingerprint],
    vpc_uuid=vpc.id,
    user_data=cloud_init_drip,
)

domain_record_drip_a = digitalocean.DnsRecord(
    "drip",
    domain="analogpuddle.cloud",
    name="drip",
    ttl=300,
    type="A",
    value=droplet_drip.ipv4_address,
)

# cloud_init_stackstorm = """#cloud-config
# write_files:
# - path: /var/tmp/cloud-init.sh
#   content: |
#     #!/usr/bin/env bash
#     set -e -o pipefail -u
#     export DEBIAN_FRONTEND=noninteractive
#     sudo apt-get -y update
#     echo
#     echo ">>>> TAILSCALE <<<<"
#     echo
#     curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.noarmor.gpg \
#       | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg
#     curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.tailscale-keyring.list \
#       | sudo tee /etc/apt/sources.list.d/tailscale.list
#     sudo apt-get -y install tailscale
#     sudo tailscale up --authkey "{0}"
#     tailscale ip -4
#     echo
#     echo ">>>> STACKSTORM <<<<"
#     echo
#     sudo apt-get -y install python3-pip
#     sudo pip3 install ansible
#     git clone https://github.com/StackStorm/ansible-st2
#     pushd ansible-st2
#     ansible-playbook stackstorm.yml -i localhost, -c local -v
#     popd
# runcmd:
#     - - bash
#       - /var/tmp/cloud-init.sh
# """.format(
#     os.getenv("TAILSCALE_AUTH_KEY")
# )

# droplet_stackstorm = digitalocean.Droplet(
#     "stackstorm",
#     image="ubuntu-20-04-x64",
#     name="stackstorm",
#     region="nyc3",
#     size="g-2vcpu-8gb",
#     ssh_keys=[sshkey_mamercad.fingerprint],
#     vpc_uuid=default_vpc_nyc3.id,
#     user_data=cloud_init,
# )

# domain_record_stackstorm_a = digitalocean.DnsRecord(
#     "stackstorm",
#     domain="analogpuddle.cloud",
#     name="stackstorm",
#     ttl=300,
#     type="A",
#     value=droplet_stackstorm.ipv4_address,
# )
