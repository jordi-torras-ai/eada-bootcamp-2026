# AutoWorth

AutoWorth is a car valuation and listings app that sits alongside the Ownly property portal in this repository. It uses the supplied car listings to estimate prices and lets sellers post cars and registered buyers contact them.

## Run locally

Requirements: Python 3. The app uses only Python's standard library.

```bash
cd autoworth
python3 autoworth_server.py
```

Open <http://127.0.0.1:8765>. The server creates `autoworth.sqlite3` in this folder for accounts, listings, and messages. SQLite files are ignored by Git.

## Included

- Interactive price estimate based on comparable cars in the supplied data.
- Seller and buyer accounts. Email format is checked, but email is not verified.
- Car listings with make/model, year, mileage, condition, fuel, transmission, price, location, description, and contact details.
- Buyer-to-seller messages and seller inbox.
- [Exploratory data analysis report](car_eda_report.html).

## Data notice

The estimator dataset is embedded in `car_valuation.html`, so publishing this repository also publishes the supplied listing rows. The original CSV is not included separately. Confirm that the data may be shared before distributing the public repository.

AutoWorth is a local prototype. It binds to `127.0.0.1`; accounts and messages are local to this machine. Passwords are stored as salted PBKDF2 hashes. Do not use real account passwords or sensitive personal information in a demo. The app does not send email or verify mailbox ownership.
