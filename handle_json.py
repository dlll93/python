#!/usr/bin/env python
# encoding: utf-8

import json
f=open("new_wav.txt",'r')
end=[]
for file in f:
    image_key=file.split()[0]
    content=file.split()[1]
    input_="{\"image_key\":\""+image_key+"\",\"voice\":[{\"attrs\":{\"content\":\""+content+"\",\"is_valid\":\"yes\"}}]}"
    end.append(input_)
def store(end):
    fl=open('end.json', 'w')
    for i in end:
        fl.write(i)
        fl.write("\n")
    fl.close()
if __name__ == "__main__":

    store(end)

