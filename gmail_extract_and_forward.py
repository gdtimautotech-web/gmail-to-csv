name: Gmail to CSV Forwarder

on:
  schedule:
    - cron: '5 * * * *'  # Ogni ora al minuto 5
  workflow_dispatch:  # permette anche di far partire manualmente

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
      # 1️⃣ Checkout del repository
      - name: Checkout repository
        uses: actions/checkout@v3

      # 2️⃣ Configura Python
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.13"

      # 3️⃣ Installa le dipendenze
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install py7zr pandas openpyxl

      # 4️⃣ Esegui lo script Python
      - name: Run Gmail extract and forward
        env:
          EMAIL: ${{ secrets.EMAIL }}
          APP_PASSWORD: ${{ secrets.APP_PASSWORD }}
          ZIP_PASSWORD: ${{ secrets.ZIP_PASSWORD }}
          SEND_TO: ${{ secrets.SEND_TO }}
          WORKDIR: "./workdir"
        run: |
          mkdir -p "$WORKDIR"
          python gmail_extract_and_forward.py
