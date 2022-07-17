import pulumi
import pulumi_digitalocean as digitalocean

analogpuddle_cloud = digitalocean.Domain(
    "analogpuddle.cloud",
    name="analogpuddle.cloud",
    opts=pulumi.ResourceOptions(protect=True),
)

stackstorm = digitalocean.Droplet(
    "stackstorm",
    image="ubuntu-20-04-x64",
    name="stackstorm",
    region="nyc3",
    size="g-2vcpu-8gb",
    vpc_uuid="30f86d25-414e-434f-852d-993ed8d6815e",
    opts=pulumi.ResourceOptions(protect=True),
)
