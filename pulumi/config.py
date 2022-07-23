import os
import time

DEFAULT_REGION = "nyc3"
DEFAULT_IMAGE = "ubuntu-20-04-x64"

TLD = "analogpuddle.cloud"
WEB_CNAME_TARGET = "mamercad.github.io."

SSH_PUBKEY_NAME = "mamercad@gmail.com"
SSH_PUBKEY = "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAirA5p3ABC+MQqE1bJkA83SHUkVBoiuaZyYRMB7up+6NW/9bSxMp36o2eFu+jFYh6O5K74Kp6yDPl+FUCXkpdmRHiEmKp6ET5+1LYc93CgWp1kieTDUVoM3e5IOmBvJrwFn/ot3ghQciO7jM34/r6j6LpDTVEXxtC0tT4SL+gXWhoWe9/McS0ElDkw0Eq7khyws6TXbSzIxNghtW+WzEFW+DYHVXRsTqhOI3AcQW4uQ8FLd5/qEvDRBZxsleTU1LUNNq99nuWpwvpRBwyAYWKkvDDz8bKj98ciqvjFShF3IUPGxrKVhgzKEN5GORTeZgQG+qQrv0AiIYyXsF+EFkOEQ== mamercad@gmail.com"

GITHUB_SSH_PUBKEY_NAME = "mamercad+github@gmail.com"
GITHUB_SSH_PUBKEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOwluiL+lFzPBfsDhlkAVC5rvr5Um6tPLQv1aVgUnZil mamercad+github@gmail.com"

LETSENCRYPT_EMAIL = "mamercad@gmail.com"

TAILSCALE_AUTH_KEY = os.getenv("TAILSCALE_AUTH_KEY")
DO_API_TOKEN = os.getenv("DO_API_TOKEN")

ST2_AUTH_USERNAME = os.getenv("ST2_AUTH_USERNAME")
ST2_AUTH_PASSWORD = os.getenv("ST2_AUTH_PASSWORD")

EPOCH_TIME = int(time.time())
