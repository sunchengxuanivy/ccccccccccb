fInput = open('Transcript/TranscriptList.txt', 'r')
samples = []
for szLine in fInput:
    samples.append(szLine.rstrip())
fInput.close()

for fileName in samples:
    fullPath = 'Transcript/' + fileName
    fTrans = open(fullPath, 'r')
    szOutput = ''
    szItem = ''
    for szTransLine in fTrans:
        szCol = szTransLine.split(',')
        if len(szCol) >= 3:
            szItem = szCol[2]
        szWord = szItem.split('\'')
        if len(szWord) >= 2:
            szOutput = szOutput + szWord[1]
        elif len(szWord) == 1:
            szOutput = szOutput + szWord[0]

    fTrans.close()
    fOut = open('TranscriptOut/' + fileName, 'w')
    fOut.write(szOutput)
    fOut.close()
    # print(szOutput)

fInput.close()
