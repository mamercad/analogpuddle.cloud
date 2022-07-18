import os

import pulumi
import pulumi_digitalocean as digitalocean

default_vpc_nyc3 = digitalocean.get_vpc(name="default-nyc3")

domain_analogpuddle_cloud = digitalocean.Domain(
    "analogpuddle.cloud",
    name="analogpuddle.cloud",
    opts=pulumi.ResourceOptions(protect=True),
)

domain_record_web_cname = digitalocean.DnsRecord(
    "web",
    domain="analogpuddle.cloud",
    name="web",
    ttl=300,
    type="CNAME",
    value="mamercad.github.io.",
    opts=pulumi.ResourceOptions(protect=True),
)

sshkey_mamercad = digitalocean.SshKey(
    "mamercad@gmail.com",
    name="mamercad@gmail.com",
    public_key=(lambda path: open(path).read())("/Users/mark/.ssh/personal.key.pub"),
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
runcmd:
    - - bash
      - /var/tmp/cloud-init.sh
""".format(
    os.getenv("TAILSCALE_AUTH_KEY")
)

droplet_drip = digitalocean.Droplet(
    "drip",
    image="ubuntu-20-04-x64",
    name="drip",
    region="nyc3",
    size="s-2vcpu-4gb",
    ssh_keys=[sshkey_mamercad.fingerprint],
    vpc_uuid=default_vpc_nyc3.id,
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
