# Ownly on DigitalOcean

Status: the deployment was removed on October 19, 2026, including the application database, service, Apache host, certificate, and GoDaddy DNS record. These instructions describe the former installation and can be used as a reference to deploy it again.

This deployment runs the existing Node HTTP server behind Apache at `https://ownly.torras.ai`, using the local SQLite adapter. It needs no Cloudflare account, npm install, frontend compilation, or Python runtime. The browser prediction model is already exported in the repository.

The installer targets the existing x86_64 Ubuntu droplet and its Apache setup. It installs a checksum-verified Node 24 LTS runtime under `/opt/ownly`, retrieves a specific GitHub commit, runs the model/API/HTTP tests, and starts a systemd service bound to `127.0.0.1:8850`. A separate Apache virtual host handles only `ownly.torras.ai`. Existing virtual hosts and their DNS records are left in place.

The public portal lets anyone browse and register. Existing account and participant checks still protect listings and messages. Registration does not verify email ownership. The original owner-private Sites deployment is a separate installation; its database is not copied to this server.

## First deployment without local SSH

Use the DigitalOcean browser Web Console as root. Review the scripts before running them. Substitute the full reviewed commit SHA:

```bash
curl -fsSL https://raw.githubusercontent.com/jordi-torras-ai/eada-bootcamp-2026/COMMIT/deploy/digitalocean/install.sh -o /root/ownly-install.sh
bash /root/ownly-install.sh COMMIT
```

In GoDaddy, add only an `A` record with name `ownly`, value `161.35.176.210`, and TTL 600 seconds. Once the HTTP readiness challenge is reachable, obtain HTTPS using the server's existing Let's Encrypt account:

```bash
bash /opt/ownly/current/deploy/digitalocean/enable-https.sh
```

This does not accept new ACME terms automatically. If Certbot requires a new account or updated terms, complete that account step separately before proceeding. Certificate renewal uses the server's existing Certbot timer and reloads Apache after renewal. Port 8850 remains loopback-only; Apache exposes the application over HTTPS and redirects ordinary HTTP requests to HTTPS.

## Persistent state and updates

SQLite, including cover-photo blobs, lives at `/var/lib/ownly/ownly.sqlite`, managed by systemd's `StateDirectory`. Code releases live at `/opt/ownly/releases/COMMIT`, with `/opt/ownly/current` pointing to the active release. Updating the code does not replace the database. The service uses an unprivileged dynamic user with a read-only filesystem outside its state directory and a 256 MiB memory limit.

Run the installer with a newer reviewed commit to deploy an update. It keeps previous releases. To roll back code, point `current` at the prior release and restart only `ownly`; review schema compatibility before rolling back after new migrations. Later schema changes must append migrations rather than edit applied SQL.

```bash
systemctl status ownly --no-pager
journalctl -u ownly --no-pager -n 30
curl -fsS https://ownly.torras.ai/healthz
```

Before changing the database, stop Ownly and copy the whole `/var/lib/ownly/` directory (including any SQLite WAL/SHM sidecars) to a private backup location, then restart it. Do not commit account, listing, session, or message records to GitHub.

`OWNLY_PUBLIC_ORIGIN` pins the expected HTTPS origin for session cookies and request checks. `OWNLY_TRUST_PROXY=1` accepts `X-Real-IP` only from the loopback connection; Apache overwrites that header with its observed client IP. This avoids treating every visitor as the same login-rate-limit identity.
