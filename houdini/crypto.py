from hashlib import md5
from secrets import token_hex


class Crypto:

    @staticmethod
    def hash(undigested):
        if type(undigested) == str:
            undigested = undigested.encode('utf-8')
        elif type(undigested) == int:
            undigested = str(undigested).encode('utf-8')
        return md5(undigested).hexdigest()

    @staticmethod
    def generate_random_key():
        return token_hex(8)

    @staticmethod
    def encrypt_password(password, digest=True):
        if digest:
            password = Crypto.hash(password)

        swapped_hash = password[16:32] + password[0:16]
        return swapped_hash

    @staticmethod
    def get_login_hash(password, rndk):
        key = Crypto.encrypt_password(password, False)
        key += rndk
        key += 'Y(02.>\'H}t":E1'

        login_hash = Crypto.encrypt_password(key)

        return login_hash
