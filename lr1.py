# Author: xhxhkxh at 22:33 2023/1/16
# A simple IR model
import torch
import matplotlib.pyplot as plt
from time import perf_counter as pcr
import gradio as gr
import xdlibs

xdlibs.showCUDAInformation()

ENABLE_FIGURE = True

# the final results into w(eights) as y = w0 * x + w1
w = torch.rand(2)

startTime = pcr()/1000
#print("Program starting at",pcr()/1000, 's')
#print("Initing Tensors at", pcr()/1000,'s')


# x = torch.Tensor([1.4,5,11,16,21])
# y = torch.Tensor([14.4,29.6,62,85.5,113.4])

x = torch.Tensor([-3,3])
y = torch.Tensor([-1,1])

# x = torch.Tensor([4, 5, 6])
# y = torch.Tensor([7, 4, 1])

# This function used to init tensor.


def initX(x):
    x0 = torch.ones(x.numpy().size)
    X = torch.stack((x, x0), dim=1)
    return X


def train(epoches=3, learningRate=0.001):

    for epoch in range(epoches):

        output = inputs.mv(w)
        loss = (output - target).pow(2).sum()

        loss.backward()     
        w.data -= w.grad * learningRate
        w.grad.zero_()
        if (ENABLE_FIGURE):
            if (epoch % 85 == 0):
                draw(output, loss, epoch)
        else:
            print("At epoch: %d, loss: %s, weights:%s" %
                  (epoch, round(loss.item(), 4), w.data))
    return w, loss


def draw(o, loss, epo):
    if (CUDA):
        o = o.cpu()
    plt.cla()
    plt.scatter(x.numpy(), y.numpy())
    plt.plot(x.numpy(), o.data.numpy(), 'r-', lw=5)
    plt.text(3.5, 0, 'loss=%s' % (loss.item()),
             fontdict={'size': 15, 'color': 'black'})
    plt.text(4, 7.5, "At epoch: %s" % epo)
    plt.pause(0.005)


#print('Tensors inited at',pcr()/1000,'s, time eslapped:',pcr()/1000 - startTime)


#print("Init target at",pcr()/1000)
X = initX(x)
#print("Target inited at", pcr()/1000,'\n',X,'\n',y,'\n',w,'\n')

# defines input & output
CUDA = torch.cuda.is_available()
if (CUDA):
    print("Enable GPU accelerate.")
    inputs = X.cuda()
    target = y.cuda()
    w = w.cuda()
    w.requires_grad = True
else:
    inputs = X
    target = y
    w = w
    w.requires_grad = True


def grStart(FIGURE):
    ENABLE_FIGURE = FIGURE
    if (ENABLE_FIGURE):
        print("Drawing figure is on")
    else:
        print("Figure drawing disabled, command-based output.")

    print("start training loop")

    w, loss = train(10000, 0.01)

    print("Complete, loss: %s, weights: %s" % (loss.item(), w.data))
    print("Probably two weights is: %s %s" % (w.data[0], w.data[1]))
    return loss.item(), w.data


grStart(True)
