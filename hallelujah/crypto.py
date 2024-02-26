#!/usr/bin/env python3
# -*- coding:utf-8 -*-
 
 
import os
import sys
import base64
 
 
op_en = ['en', 'encrypt']
op_de = ['de', 'decrypt']
crypt_ext = '.cry'
 
 
def usage():
    print(f'Usage: {os.path.basename(__file__)} OPTION PASSWORD FILENAME')
    print(f'    OPTION: [en|encrypt] for encryption, [de|decrypt] for decryption.')
    print(f'    PASSWORD: password for cryption.')
    print(f'    FILENAME: filename for cryption.')
    print(f'Note: after encryption, FILENAME{crypt_ext} would be generated.')
    print(f'      before decryption, FILENAME should be ended with [{crypt_ext}].')
 
def get_code(pwd):
    i, sz = 0, len(pwd)
    while i < sz:
        yield pwd[i]
        i = (i + 1) % sz
 
def crypt(src, pwd, op):
    if op in op_en:
        des = src + crypt_ext
    else:
        if not src.endswith(crypt_ext):
            usage()
            return
        des = src[:-(len(crypt_ext))]
    with open(src, 'rb') as src_fd:
        src_data = src_fd.read()
        if op in op_de:
            src_data = base64.b64decode(src_data)
        with open(des, 'wb') as des_fd:
            des_data = []
            for data in src_data:
                target = 0
                code = ord(next(get_code(pwd)))
                for i in range(8):
                    src_bit = (data >> i) & 1
                    code_bit = (code >> i) & 1
                    des_bit = src_bit ^ code_bit
                    target |= (des_bit << i)
                des_data.append(target)
            if op in op_en:
                des_data = base64.b64encode(bytes(des_data))
            else:
                des_data = bytes(des_data)
            des_fd.write(des_data)
 
 
if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage()
    else:
        op, pwd, filename = sys.argv[1:]
        if not os.path.exists(filename):
            usage()
        elif op in op_en or op in op_de:
            crypt(filename, pwd, op)
        else:
            usage()
 
