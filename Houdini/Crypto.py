import hashlib
from random import choice
from string import ascii_letters, digits


class Crypto:

    @staticmethod
    def hash(string):
        if isinstance(string, int):
            string = str(string)

        return hashlib.md5(string.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_random_key():
        character_selection = ascii_letters + digits

        return "".join(choice(character_selection) for _ in range(16))

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
        key += "Y(02.>'H}t\":E1"

        login_hash = Crypto.encrypt_password(key)

        return login_hash
