import shutil

shutil.copyfile("ExtraDict/idf_big.txt", "ExtraDict/IDF_Out.txt")

fAddIDF = open("ExtraDict/IDF_V3.txt", 'r')
fOutIDF = open("ExtraDict/IDF_Out.txt", 'a')

fOutIDF.write("\n")
for line in fAddIDF:
    fOutIDF.write(line)
fAddIDF.close()
fOutIDF.close()