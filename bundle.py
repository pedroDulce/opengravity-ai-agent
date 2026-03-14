import certifi
import shutil

with open(certifi.where(), "rb") as base:
    base_cert = base.read()

with open("redsara.pem", "rb") as corp:
    corp_cert = corp.read()

with open("combined-ca.pem", "wb") as out:
    out.write(base_cert)
    out.write(b"\n")
    out.write(corp_cert)