import getopt, socket, sys, re, os

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:f:")
    except getopt.GetoptError as err:
        sys.exit("ERROR: WRONG ARGUMENTS")    
    for o, a in opts:
        if o == "-n":
            nameServer = a
            port = re.split(":", a)

        elif o == "-f":
            surl = a
            fsAndFiles = re.split("\/\/", a)[1]
            fs = re.split("\/", fsAndFiles)[0]
            DirAndFiles = re.split("\/", fsAndFiles, 1)[1]

            if "/" in DirAndFiles:
                DirAndFiles = "/" + DirAndFiles
                Files = DirAndFiles.rsplit("/", 1)[1]

            elif "*" in DirAndFiles:
                continue

            else:
                Files = re.split("\/", fsAndFiles)[1]

        else:
            sys.exit(2)

    #check is ip is valid
    try:
        socket.inet_aton(port[0])
        oktets = re.split("\.", port[0])
        if len(oktets) != 4:
            sys.exit("ERROR: INVALID IP ADDRESS")
    except socket.error:
        sys.exit("ERROR: INVALID IP ADDRESS")

    #check if port is valid
    if not 0 < int(port[1]) <= 65535:
        sys_exit("ERROR: INVALID PORT NUMBER")

    #UDP
    sUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    try:
        send_data = "WHEREIS " + fs
        sUDP.sendto(send_data.encode('utf-8'), (port[0], int(port[1])))

        data, address = sUDP.recvfrom(4096)
    except:
        sys.exit("UDP COMMUNICATION ERROR")


    serverAnswer = data.decode('utf-8')

    #4#error message recieved from the nameserver = exit
    if serverAnswer[0] == "E":
        sys.exit(serverAnswer)

    serverAnswer = re.split(" ", data.decode('utf-8'))
    ip = re.split(":", serverAnswer[1])[0]
    port = re.split(":", serverAnswer[1])[1]
    server_address = (ip, int(port))

    #TCP

    #to store data recieved from server here
    dataToWrite = []

    #"*"case
    if DirAndFiles == '*':
        message = 'GET index FSP/1.0\r\nHostname: '+fs+'\r\nAgent: xcicmi00\r\n\r\n'
        line = ''

        sTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sTCP.settimeout(30)
        sTCP.connect(server_address)
        sTCP.sendall(message.encode('utf-8'))

        #find out name of the files
        while True:
            data = sTCP.recv(1)
            if not data:
                break
            data = data.decode('utf-8')
            line += data
            firstLine = line.splitlines()[0]        #header
            fileNames = line.splitlines()[3:]       #name of the files

        for name in fileNames:
            if "/" in name:
                name = "/" + name

            sTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    #create socket
            #server_address = (ip, int(port))
            sTCP.connect(server_address)
            message = 'GET '+name+' FSP/1.0\r\nHostname: '+fs+'\r\nAgent: xcicmi00\r\n\r\n'
            sTCP.sendall(message.encode('utf-8'))

            #index gives all files on the server, if the file is in subfoler, it is in format: dir/file
            if "/" in name:
                name = name.rsplit("/", 1)[1]

            while True:
                data = sTCP.recv(1)
                if not data:
                    break
                dataToWrite.append(data)

            if dataToWrite[8] == b"N":
                sys.exit("ERROR: FILE NOT FOUND")

            #determine, when data section starts
            counterR = 0
            counterI = 1
            for i in dataToWrite:
                counterI += 1
                if i == b"\r":
                    counterR += 1
                if counterR == 3:
                    break

            lenHELP = ''
            counterL = 0
            for i in dataToWrite:
                counterL += 1
                i = i.decode('utf-8')
                lenHELP += i
                if counterL == counterI-4:
                    lenHELP = lenHELP.splitlines()[1]
                    length = re.split(":", lenHELP)[1]
                    length = int(length)
                    break


            if dataToWrite[8] == b"S":
                file = open(name, "wb")
                for j in dataToWrite[counterI:]:
                    file.write(j)
                file.close()

            if (os.stat(name).st_size != length):
                sys.exit("ERROR: FILE NOT LOADED SUCCESSFULLY")

            dataToWrite = []

        sys.exit(0)

    #just one file download
    message = 'GET '+DirAndFiles+' FSP/1.0\r\nHostname: '+fs+'\r\nAgent: xcicmi00\r\n\r\n'
    sTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sTCP.settimeout(30)
        sTCP.connect(server_address)
        sTCP.sendall(message.encode('utf-8'))

        while True:
            data = sTCP.recv(1)
            if not data:
                break
            dataToWrite.append(data)

    except:
        sys.exit("TCP COMMUNICATION ERROR")

    if dataToWrite[8] == b"N":
        sys.exit("ERROR: FILE NOT FOUND")

    #determine, when data section starts
    counterR = 0
    counterI = 1
    for i in dataToWrite:
        counterI += 1
        if i == b"\r":
            counterR += 1
        if counterR == 3:
            break

    lenHELP = ''
    counterL = 0
    for i in dataToWrite:
        counterL += 1
        i = i.decode('utf-8')
        lenHELP += i
        if counterL == counterI-4:
            lenHELP = lenHELP.splitlines()[1]
            length = re.split(":", lenHELP)[1]
            length = int(length)
            break


    if dataToWrite[8] == b"S":
        file = open(Files, "wb")
        for i in dataToWrite[counterI:]:
            file.write(i)
        file.close()

    if (os.stat(Files).st_size != length):
        sys.exit("ERROR: FILE NOT LOADED SUCCESSFULLY")


main()
