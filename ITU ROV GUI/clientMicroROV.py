import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((socket.gethostname(), 5566))

while True:
    last = time.time()
    data = s.recv(4)
    # print("Data : " + str(data))
    data1 = (data.decode('utf-8'))
    # print("Decoded Data : " + data1 + "     " + str(len(data1)))

    grip = []

    if len(data1) == 0:
        while True:
            print("Baglanti Koptu")
            time.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((socket.gethostname(), 5566))
                print("Baglanti geri geldi")
                time.sleep(1)
                break
            except:
                pass
        continue
    else:
        for char in data1:
            grip.append(char)
        # grip.pop(0)
        # grip.pop(-1)
        now = time.time()
        print(data1, "      ", grip, "     ", now - last)


