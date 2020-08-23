#!/usr/bin/env python2.7
import sys
import binascii

# you can create this file by:
# 1. Start tibia, login to depot
# 2. Find the mana address: find <value>
#   * This will give you a large range
# 3. Use mana
# 4. Find the mana address again: find <new-value>
#   * This should give you the actual address, if not, repeat this step until
#     only one memory address matches.
# 5. In scanmem run the command: dump <mana-address-1000 hex> <1000-hex> /tmp/dump


def main(filepath):
    words = []
    with open(filepath, 'rb') as bf:
        eof = False
        while not eof:
            word = ""
            count = 0
            while count < 8:
                byte = bf.read(1)
                if byte == "" or byte is None:
                    eof = True
                    break
                else:
                    word += binascii.hexlify(byte)
                count += 1

            if word != "":
                words.append(word)

    for word in words:
        print(word)


if __name__ == "__main__":
    main(sys.argv[1])
