import util
from bean import autoencoder,nn
import numpy as np
# 测试数据，x为输入，y为输出
x = np.array([[0,0,1,0,0],
            [0,1,1,0,1],
            [1,0,0,0,1],
            [1,1,1,0,0],
            [0,1,0,1,0],
            [0,1,1,1,1],
            [0,1,0,0,1],
            [0,1,1,0,1],
            [1,1,1,1,0],
            [0,0,0,1,0]])
y = np.array([[0],
            [1],
            [0],
            [1],
            [0],
            [1],
            [0],
            [1],
            [1],
            [0]])


nodes=[5,3,2]

ae = util.aebuilder(nodes)

ae = util.aetrain(ae, x, 6000)

nodescomplete = np.array([5,3,2,1])
aecomplete = nn(nodescomplete)

# 训练得到的权值，即原来的autoencoder网络中每一个autoencoder中的第一层到中间层的权值
for i in range(len(nodescomplete)-2):
    aecomplete.W[i] = ae.encoders[i].W[0]
# 开始进行神经网络训练，主要就是进行微调
aecomplete = util.nntrain(aecomplete, x, y, 3000)

print (aecomplete.values[3])