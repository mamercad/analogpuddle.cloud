import pulumi
import pulumi_digitalocean as digitalocean

domain_analogpuddle_cloud = digitalocean.Domain(
    "analogpuddle.cloud",
    name="analogpuddle.cloud",
    opts=pulumi.ResourceOptions(protect=True),
)

domain_record_stackstorm_a = digitalocean.DnsRecord(
    "stackstorm_record",
    domain="analogpuddle.cloud",
    name="stackstorm",
    ttl=300,
    type="A",
    value="134.209.170.133",
    opts=pulumi.ResourceOptions(protect=True),
)

domain_record_web_cname = digitalocean.DnsRecord(
    "web_record",
    domain="analogpuddle.cloud",
    name="web",
    ttl=300,
    type="CNAME",
    value="mamercad.github.io.",
    opts=pulumi.ResourceOptions(protect=True),
)

droplet_stackstorm = digitalocean.Droplet(
    "stackstorm",
    image="ubuntu-20-04-x64",
    name="stackstorm",
    region="nyc3",
    size="g-2vcpu-8gb",
    vpc_uuid="30f86d25-414e-434f-852d-993ed8d6815e",
    opts=pulumi.ResourceOptions(protect=True),
)
