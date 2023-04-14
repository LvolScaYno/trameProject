import math

import numpy
import numpy as np
from matplotlib import pyplot, cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import matplotlib as mpl
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei'] # 用来正常显示中文标签（中文乱码问题）
# -----------------------------------------------------------------------------
# SOLVER
# -----------------------------------------------------------------------------
# ##variable declarations
mpl.use('TkAgg')
class Solver:
    def __init__(self):
        self.nx, self.ny = 51, 51
        self.fx, self.fy = 2, 2
        self.initX, self.initY = 2, 2
        self.nu = 0.01
        self.x_anchorLT, self.y_anchorLT = 0, 1
        self.x_anchorRB, self.y_anchorRB = 1, 0
        self.CFL = .0009
        self.nt = 1000
        # 辅助变量
        self.currentTimeStep = 0
        self.retData = []

    def __get_config(self):
        dx = self.fx / (self.nx - 1)
        dy = self.fy / (self.ny - 1)
        return self.nx, \
               self.ny, \
               self.nt, \
               dx, \
               dy, \
               self.CFL, \
               self.nu, \
               self.CFL * dx * dy / self.nu, \
               self.fx, \
               self.fy

    def initialize(self):
        nx, ny, nt, dx, dy, CFL, nu, dt, fx, fy = self.__get_config()
        self.u = numpy.ones((ny, nx))  # create a 1xn vector of 1's
        self.v = numpy.ones((ny, nx))
        self.un = numpy.ones((ny, nx))
        self.vn = numpy.ones((ny, nx))
        self.x = numpy.linspace(0, self.fx, nx)
        self.y = numpy.linspace(0, self.fy, ny)

        x_anchorLT = self.x_anchorLT
        y_anchorLT = self.y_anchorLT
        x_anchorRB = self.x_anchorRB
        y_anchorRB = self.y_anchorRB

        # #set hat function I.C. : u(.5<=x<=1 && .5<=y<=1 ) is 2
        self.u[int(y_anchorRB / dy): int(y_anchorLT / dy), int(x_anchorLT / dx):int(x_anchorRB / dx)] = self.initX
        # #set hat function I.C. : u(.5<=x<=1 && .5<=y<=1 ) is 2
        self.v[int(y_anchorRB / dy): int(y_anchorLT / dy), int(x_anchorLT / dx):int(x_anchorRB / dx)] = self.initY
        print(int(y_anchorRB / dy), int(y_anchorLT / dy))

    def get_current_data(self):
        return self.u, self.v, self.un, self.vn

    def get_solve_data(self):
        return self.retData

    def solve_next_step(self):
        nx, ny, nt, dx, dy, CFL, nu, dt, fx, fy = self.__get_config()

        if self.currentTimeStep == nt:
            print("solve complete")
            return True

        u, v, un, vn = self.u, self.v, self.un, self.vn
        # 返回数据
        retData = self.retData

        un = u.copy()
        vn = v.copy()

        u[1:-1, 1:-1] = (un[1:-1, 1:-1] -
                         dt / dx * un[1:-1, 1:-1] *
                         (un[1:-1, 1:-1] - un[1:-1, 0:-2]) -
                         dt / dy * vn[1:-1, 1:-1] *
                         (un[1:-1, 1:-1] - un[0:-2, 1:-1]) +
                         nu * dt / dx ** 2 *
                         (un[1:-1, 2:] - 2 * un[1:-1, 1:-1] + un[1:-1, 0:-2]) +
                         nu * dt / dy ** 2 *
                         (un[2:, 1:-1] - 2 * un[1:-1, 1:-1] + un[0:-2, 1:-1]))

        v[1:-1, 1:-1] = (vn[1:-1, 1:-1] -
                         dt / dx * un[1:-1, 1:-1] *
                         (vn[1:-1, 1:-1] - vn[1:-1, 0:-2]) -
                         dt / dy * vn[1:-1, 1:-1] *
                         (vn[1:-1, 1:-1] - vn[0:-2, 1:-1]) +
                         nu * dt / dx ** 2 *
                         (vn[1:-1, 2:] - 2 * vn[1:-1, 1:-1] + vn[1:-1, 0:-2]) +
                         nu * dt / dy ** 2 *
                         (vn[2:, 1:-1] - 2 * vn[1:-1, 1:-1] + vn[0:-2, 1:-1]))

        u[0, :] = 1
        u[-1, :] = 1
        u[:, 0] = 1
        u[:, -1] = 1

        v[0, :] = 1
        v[-1, :] = 1
        v[:, 0] = 1
        v[:, -1] = 1

        dataDict = dict()
        for i in range(nx):
            for j in range(ny):
                dataDict[(i * dx, j * dy)] = (u[i, j], v[i, j])

        retData.append(dataDict)
        self.u = u
        self.v = v
        self.un = un
        self.vn = vn

        print("迭代时间步：", self.currentTimeStep + 1)

        self.currentTimeStep = self.currentTimeStep + 1
        return False



if __name__ == '__main__':
    sv = Solver()
    sv.initialize()
    temp=np.zeros((sv.nt,2))
    result=np.zeros(sv.nt)
    fig,ax = plt.subplots()
    ax.set_xlim(0,1000)
    x,y=[],[]
    ax.set_xlim(0, 1000)
    ax.set_ylim(0,6)
    ax.set_title("ln(sum(square(cur-last)))")
    ax.set_xlabel("迭代步数")
    ax.set_ylabel("残差值")
    while sv.solve_next_step() is not True:
        plt.ion()
        plt.cla()
        temp[sv.currentTimeStep - 1][0] = np.sum(np.square(sv.u - sv.un))
        temp[sv.currentTimeStep - 1][1] = np.sum(np.square(sv.v - sv.vn))
        result[sv.currentTimeStep - 1] = math.sqrt(temp[sv.currentTimeStep - 1][0] * temp[sv.currentTimeStep - 1][0] + temp[sv.currentTimeStep - 1][1] * temp[sv.currentTimeStep - 1][1])
        result[sv.currentTimeStep - 1]=math.log(result[sv.currentTimeStep - 1]+1)*1000
        X = range(len(result))
        ax.plot(X[1:sv.currentTimeStep],result[1:sv.currentTimeStep])
        plt.show()
        plt.pause(0.001)
        plt.ioff()
    plt.show()


    # ani = FuncAnimation(fig, update, frames=np.arange(0,1000), interval=10, blit=False,
    #                     repeat=False)  # 创建动画效果
    # ani.save('./test.gif')
    # plt.show()  # 显示图片