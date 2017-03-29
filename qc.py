f = open("D:/ali_data/label/q1.txt","r",encoding= 'utf-8')
line = f.readlines()
f.close()
a=set()
for item in line:
    lst=item.split()
    a.add(lst[1])
print(a)

with open('D:/ali_data/label/test.txt', 'w',encoding = 'utf-8') as z:
    z.write(str(a))
    z.close()