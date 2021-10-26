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

    msg = "     "
    grip = []

    if len(data1) == 0:
        while True:
            print("Baglanti Koptu")
            time.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((socket.gethostname(), 5556))
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
    # print(grip)
    if '0' in grip:
        msg = msg + "Gripper Kapama     "
    elif '1' in grip:
        msg = msg + "Gripper Acma     "
    if '3' in grip:
        msg = msg + "Gripper Ac     "
    elif '4' in grip:
        msg = msg + "Gripper Kapa     "
    if '5' in grip:
        msg = msg + "Saat yonu cevir     "
    elif '7' in grip:
        msg = msg + "Saat yonu cevirme     "
    if '6' in grip:
        msg = msg + "Saat tersi cevir     "
    elif '8' in grip:
        msg = msg + "Saat tersi cevirme     "
    now = time.time()
    print(data1, "      ", grip, "     ", now - last)


