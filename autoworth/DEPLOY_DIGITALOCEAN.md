# Deploy AutoWorth on a DigitalOcean Droplet

This setup uses Docker Compose, a persistent Docker volume for SQLite, and Caddy for HTTPS. It does not require SSH. Use the Droplet's **Console** in the DigitalOcean control panel. The Droplet needs a public IPv4 address and Docker Compose v2.

## Before starting

The AutoWorth files in this folder must be committed and pushed to the public GitHub repository. The deployment commands below expect them at `autoworth/` on the repository's `main` branch. The source folder currently contains the app files and Docker configuration; a deployment cannot fetch unpushed local changes.

Check the Droplet's existing services before using this Compose stack: Caddy needs ports 80 and 443. Do not start a second web proxy on those ports if another site already uses them; configure that existing proxy to forward `autoworth.si` to port 8765 instead.

## Deploy from the browser console

Open the Droplet in DigitalOcean, choose **Console**, then run:

```sh
sudo apt-get update
sudo apt-get install -y git docker.io docker-compose-v2
sudo systemctl enable --now docker
git clone --depth 1 --branch main https://github.com/jordi-torras-ai/eada-bootcamp-2026.git
cd eada-bootcamp-2026/autoworth
sudo docker compose up -d --build
```

If that repository is already cloned on the Droplet, update it with `git pull` from its repository directory and repeat the final two commands.

The SQLite database is kept in the `autoworth_data` Docker volume and survives container rebuilds. Keep a separate backup of that volume once real users have registered.

## Point GoDaddy DNS to the Droplet

In GoDaddy's DNS manager for `autoworth.si`, add or update an **A** record:

| Type | Name | Value | TTL |
| --- | --- | --- | --- |
| A | `autoworth` | the Droplet's public IPv4 address | Default |

Remove conflicting A or CNAME records for the `autoworth` host. Keep other records, including MX records, intact. DNS can take time to propagate. Once it resolves to the Droplet and ports 80/443 are reachable, Caddy requests and renews the HTTPS certificate automatically.

Check the service in the Droplet console with `sudo docker compose ps` and view startup logs with `sudo docker compose logs --tail=100`.

## Important data note

The database persists on the Droplet, but the estimator's source rows are embedded in `car_valuation.html`. If those rows are not licensed for public sharing, replace them with approved data before making the site public. This prototype also has no email verification, password reset, rate limiting, or moderation tools; don't collect real user passwords until those production safeguards are in place.
