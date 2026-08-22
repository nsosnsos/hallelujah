#!/usr/bin/env python3
"""crypto utility"""

import base64
import os
import sys

op_en = ["en", "encrypt"]
op_de = ["de", "decrypt"]
CRYPT_EXT = ".cry"


def usage():
    """crypto usage"""
    print(f"Usage: {os.path.basename(__file__)} OPTION PASSWORD FILENAME")
    print("    OPTION: [en|encrypt] for encryption, [de|decrypt] for decryption.")
    print("    PASSWORD: password for cryption.")
    print("    FILENAME: filename for cryption.")
    print(f"Note: after encryption, FILENAME{CRYPT_EXT} would be generated.")
    print(f"      before decryption, FILENAME should be ended with [{CRYPT_EXT}].")


def get_code(pwd):
    """code generator"""
    i, sz = 0, len(pwd)
    while i < sz:
        yield pwd[i]
        i = (i + 1) % sz


def crypt(src, pwd, op):
    """crypto process"""
    if op in op_en:
        des = src + CRYPT_EXT
    else:
        if not src.endswith(CRYPT_EXT):
            usage()
            return
        des = src[: -(len(CRYPT_EXT))]
    with open(src, "rb") as src_fd:
        src_data = src_fd.read()
        if op in op_de:
            src_data = base64.b64decode(src_data)
        with open(des, "wb") as des_fd:
            des_data = []
            for data in src_data:
                target = 0
                code = ord(next(get_code(pwd)))
                for i in range(8):
                    src_bit = (data >> i) & 1
                    code_bit = (code >> i) & 1
                    des_bit = src_bit ^ code_bit
                    target |= des_bit << i
                des_data.append(target)
            if op in op_en:
                des_data = base64.b64encode(bytes(des_data))
            else:
                des_data = bytes(des_data)
            des_fd.write(des_data)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()
    else:
        option, passwd, filename = sys.argv[1:]
        if not os.path.exists(filename):
            usage()
        elif option in op_en or option in op_de:
            crypt(filename, passwd, option)
        else:
            usage()
