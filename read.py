file_q = open('q.lst','r')
count = 0
templist=[]
id=0
write_file="voice"

for  i in file_q:
    count+=1
    templist.append(i)
    if count == 20000:
        id+=1
        output = open(write_file+str(id)+".lst",'w')
        for line in templist:
            output.write(line)
        templist=[]
        count=0
        output.close()

if len(templist)!=0:
    id+=1
    output = open(write_file + str(id)+".lst", 'w')
    for line in templist:
        output.write(line)
    output.close()