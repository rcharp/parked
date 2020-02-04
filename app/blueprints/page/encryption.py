import os
from flask import current_app
from Crypto.Cipher import AES
import base64


def encrypt(string):
    key = current_app.config.get('CRYPTO_KEY')

    enc_secret = AES.new(key[:32])
    tag_string = (str(string) +
                  (AES.block_size - len(str(string)) % AES.block_size) * "\0")
    cipher_text = base64.b64encode(enc_secret.encrypt(tag_string))

    return str(cipher_text, 'utf-8', 'ignore')


def decrypt(string):
    key = current_app.config.get('CRYPTO_KEY')

    cipher_text = bytes(string, 'utf-8')
    dec_secret = AES.new(key[:32])
    raw_decrypted = dec_secret.decrypt(base64.b64decode(cipher_text))
    clear_val = raw_decrypted.decode().rstrip("\0")
    return clear_val
