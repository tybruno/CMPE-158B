from struct import unpack, pack
for i in range(0,5):
    # data_packet = f"\x00\x03\x00\x01{section.decode('utf-8')}"
    words = "blah \n black "
    i += 1
    s = pack('!HH',3,i)
    print(s)
    print(s + words.encode('utf-8'))
    