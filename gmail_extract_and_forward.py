#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import imaplib
import email
import py7zr
import os
import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- CONFIGURAZIONE tramite GitHub Secrets ---
EMAIL = os.environ.get("EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
WORKDIR = "/tmp/workdir"  # cartella temporanea su runner
ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")
CHECK_LAST = 5
SEND_TO = os.environ.get("SEND_TO", EMAIL)  # default a se stesso

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- FUNZIONI ---
def pulisci_cartella(path):
    if os.path.exists(path):
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))
    else:
        os.makedirs(path)

def estrai_zip(file_path, dest_folder, password):
    with py7zr.SevenZipFile(file_path, mode='r', password=password) as archive:
        archive.extractall(path=dest_folder)

def invia_email(to_address, files):
    msg = EmailMessage()
    msg['From'] = EMAIL
    msg['To'] = to_address
    msg['Subject'] = f"CSV estratti - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    msg.set_content("In allegato i CSV estratti dal 7z.")

    for f in files:
        with open(os.path.join(WORKDIR, f), 'rb') as fp:
            data = fp.read()
        msg.add_attachment(data, maintype='text', subtype='csv', filename=f)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

# --- SCRIPT PRINCIPALE ---
def main():
    logging.info("Pulizia cartella di lavoro...")
    pulisci_cartella(WORKDIR)

    logging.info("Connessione a Gmail...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, APP_PASSWORD)
    mail.select("inbox")

    typ, msgs = mail.search(None, "ALL")
    msgs = msgs[0].split()[::-1]

    allegato_7z = None

    for m in msgs[:CHECK_LAST]:
        typ, data = mail.fetch(m, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        logging.info(f"Controllando mail: {msg.get('subject')}")
        for part in msg.walk():
            if part.get_filename() and "LEAD 119" in part.get_filename() and part.get_filename().endswith(".7z"):
                allegato_7z = os.path.join(WORKDIR, part.get_filename())
                with open(allegato_7z, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                logging.info(f"Allegato 7z salvato: {part.get_filename()}")
                break
        if allegato_7z:
            break

    if not allegato_7z:
        logging.error("Allegato 7z non trovato nelle ultime 5 mail")
        return

    logging.info("Estrazione allegato 7z...")
    estrai_zip(allegato_7z, WORKDIR, ZIP_PASSWORD)

    csv_files = [f for f in os.listdir(WORKDIR) if f.endswith(".csv")]
    if not csv_files:
        logging.error("Nessun CSV estratto")
        return

    logging.info(f"Invio CSV a {SEND_TO}...")
    invia_email(SEND_TO, csv_files)
    logging.info("Operazione completata.")

if __name__ == "__main__":
    main()
