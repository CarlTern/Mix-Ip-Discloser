import sys
from pcapfile import savefile

def getParameters():
    try:
        nazirIp = sys.argv[1]
        mixIp = sys.argv[2]
        numberOfPartners = sys.argv[3]
        filePath = sys.argv[4]
        if (nazirIp is False or mixIp is False or numberOfPartners is False or filePath is False):
            print("Invalid parameters")
            print("Usage:", '"disclosureAttack srcIp mixIp n filepath"')
            print("For example:", '"python3 disclosureAttack.py 127.0.0.1 255.255.255.255 2 ./pcapFile.pcap"')
            exit()
        else:
            return {"nIp":nazirIp, "mixIp":mixIp, "nbr":numberOfPartners, "path": filePath}
    except:
        print("Invalid parameters")
        print("Usage:", '"disclosureAttack srcIp mixIp n filepath"')
        print("For example:", '"python3 disclosureAttack.py 127.0.0.1 255.255.255.255 2 ./pcapFile.pcap"')
        exit()

def getFile(filePath):
    try:
        testcap = open(filePath, "rb")
        capfile = savefile.load_savefile(testcap, layers=2, verbose=True)
        testcap.close()
        return capfile
    except:
        print("Invalid file path")
        exit()

def isDisjoint(setToBeCompared, sets):
    for s in sets:
        if(s == setToBeCompared and len(s) == len(setToBeCompared)): # We dont want to compare a set to itself. 
            continue
        if(len(setToBeCompared.intersection(s)) is not 0): # Intersection between the sets => not disjoint

            return False

    return True

def learningPhase(packets, nazirIp, batchSize):
    sets = []
    srcList = []
    dstList = []
    nazirSent = False
    for index in range(len(packets)):
        ip_src = packets[index].packet.payload.src.decode('UTF8')
        ip_dst = packets[index].packet.payload.dst.decode('UTF8')
        srcList.append(ip_src)
        dstList.append(ip_dst)
        if(len(srcList) == batchSize):
            if (nazirSent and isDisjoint(set(dstList), sets)): # if true => save set.
                print("Found disjoint set!")
                sets.append(set(dstList))   
                nazirSent = False
            elif(nazirSent and isDisjoint(set(dstList), sets) == False):  # else if nazir sent but not disjoint => nazirSent = false
                nazirSent = False
            else:
                for srcIp in srcList:
                    if (srcIp == nazirIp):
                        nazirSent = True
                        break
            dstList.clear()
            srcList.clear()
    print("Found sets:", len(sets))
    return sets

def getAllSets(packets, nazirIp, batchSize):
    sets = []
    srcList = []
    dstList = []
    nazirSent = False
    for index in range(len(packets)):
        ip_src = packets[index].packet.payload.src.decode('UTF8')
        ip_dst = packets[index].packet.payload.dst.decode('UTF8')
        srcList.append(ip_src)
        dstList.append(ip_dst)
        if(len(srcList) == batchSize):
            if (nazirSent):
                sets.append(set(dstList))   
                nazirSent = False
            else:
                for srcIp in srcList:
                    if (srcIp == nazirIp):
                        nazirSent = True
                        break
            dstList.clear()
            srcList.clear()

    return sets

def isNoIntersectOtherwise(finalSets, s):
    for finalSet in finalSets:
        if(len(finalSet.intersection(s)) is not 0):

            return False

    return True

def excludingPhase(disjointSets, numberOfPartners, allSets):
    for s in allSets:
        for index in range(len(disjointSets)):
            compareSets = list(disjointSets)
            compareSets.remove(disjointSets[index])
            if(s == disjointSets[index]):
                continue
            if(len(s.intersection(disjointSets[index])) is not 0 and isNoIntersectOtherwise(compareSets, s)):
                disjointSets[index] = s.intersection(disjointSets[index])
        
    return disjointSets

def getAnswer(disjointSets):
    sum = 0
    for s in disjointSets:
        ip = s.pop()
        splitIp = ip.split(".")
        for index in range(len(splitIp)):
            splitIp[index] = int(splitIp[index]).to_bytes(1, byteorder='big').hex()
        ipAsHex = "".join(splitIp)
        sum += int(ipAsHex, 16)
    return sum

def getBatchSize(packets, mixIp):
    size = 0
    entered = False
    for packet in packets:
        srcIp = packet.packet.payload.src.decode("UTF8")
        if(mixIp == srcIp): # Found the first packet mix sends
            entered = True
            size += 1
        elif(entered and srcIp is not mixIp): # That was all sendings from the mix. 
            break
        
    return size

if __name__ == "__main__":
    parameters = getParameters()
    nazirIp = parameters['nIp']
    mixIp = parameters['mixIp']
    numberOfPartners = parameters['nbr']
    capFile = getFile(parameters['path'])
    batchSize = getBatchSize(capFile.packets, mixIp)
    print("Batch size:", batchSize)
    disjointSets = learningPhase(list(capFile.packets), nazirIp, batchSize)
    resultingSets = excludingPhase(disjointSets, numberOfPartners, getAllSets(list(capFile.packets), nazirIp, batchSize))
    answer = getAnswer(resultingSets)
    print("Answer:", answer)
    