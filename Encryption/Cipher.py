# Encryption variables
SHIFTING_KEY = 17
CHARS = list("7AqOcL>NM(Teplv$45IV-\nsmCQ:#yUB|.rbnG9?_2 PDFtigw&ZXH1)KJY,k3jxaSW6u£%Eod80z@h!fR")


# Handle encryption / decryption for messages sent between Client and Server
def cipher(message, encrypt):
    new_message = ""
    # Iterate over each character in the message
    for char in message:
        index = CHARS.index(char)
        # If it contains a character not found in CHARS, add it to new_message
        if not CHARS[index]:
            new_message += char
            continue
        if encrypt:
            # Increase the index by SHIFTING_KEY constant
            index += SHIFTING_KEY
            # If it goes out of range, loop it back to the start
            if index >= len(CHARS):
                index -= len(CHARS)
        else:
            # Decrease the index by SHIFTING_KEY constant
            index -= SHIFTING_KEY
            # If it goes out of range, loop it back to the end
            if index < 0:
                index += len(CHARS)
        new_message += CHARS[index]
    return new_message
