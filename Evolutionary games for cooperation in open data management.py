import networkx as nx
import numpy as np
import random

# 生成具有周期性边界的方格网络（row * col）   k = 4
def create_periodic_grid_graph_4(rows, cols):
    G = nx.Graph()
    for i in range(rows):
        for j in range(cols):
            G.add_node((i, j))
            # 添加右边的边
            G.add_edge((i, j), (i, (j + 1) % cols))
            # 添加下边的边
            G.add_edge((i, j), ((i + 1) % rows, j))
    return G

# 生成具有周期性边界的方格网络（row * col）   k = 4
def create_periodic_grid_graph_8(rows, cols):
    G = nx.Graph()
    for i in range(rows):
        for j in range(cols):
            G.add_node((i, j))
            # 添加四边的边
            G.add_edge((i, j), (i, (j + 1) % cols))  # 右边
            G.add_edge((i, j), (i, (j - 1) % cols))  # 左边
            G.add_edge((i, j), ((i + 1) % rows, j))  # 下边
            G.add_edge((i, j), ((i - 1) % rows, j))  # 上边
            # 添加对角线的边
            G.add_edge((i, j), ((i + 1) % rows, (j + 1) % cols))  # 右下
            G.add_edge((i, j), ((i + 1) % rows, (j - 1) % cols))  # 左下
            G.add_edge((i, j), ((i - 1) % rows, (j + 1) % cols))  # 右上
            G.add_edge((i, j), ((i - 1) % rows, (j - 1) % cols))  # 左上
    return G


def dict_values(lis, dic):   # 返回dic中以lis的key的value值
    result = []
    for i in lis:
        result.append(dic[i])
    return result

def payoff_cal(G, x, state, pom_0, pom_1, pom_2):
    Ux = 0
    for interaction in list(G.edges(x)):
        if interaction not in state:
            interaction = (interaction[1], interaction[0])
            if state[interaction] == 0:
                Ux += pom_0[strategy[x][t_update]][strategy[interaction[0]][t_update]]
            elif state[interaction] == 1:
                Ux += pom_1[strategy[x][t_update]][strategy[interaction[0]][t_update]]
            elif state[interaction] == 2:
                Ux += pom_2[strategy[x][t_update]][strategy[interaction[0]][t_update]]
        else:
            if state[interaction] == 0:
                Ux += pom_0[strategy[x][t_update]][strategy[interaction[1]][t_update]]
            elif state[interaction] == 1:
                Ux += pom_1[strategy[x][t_update]][strategy[interaction[1]][t_update]]
            elif state[interaction] == 2:
                Ux += pom_2[strategy[x][t_update]][strategy[interaction[1]][t_update]]
    return Ux


rows = 100
cols = 100
n = rows * cols
ETime = 10000
run_times = 50
b = 1.5
r = 0.4
pom_0 = [[1, -r], [b, 0]]  # PDG
pom_1 = [[1, 1 - r], [1 + r, 0]]  # SDG
pom_2 = [[1, -r], [r, 0]]  # SHG

lam_0 = 0.05  # PDG变为SDG的速率
lam_1 = 0.03  # SDG变为SHG的速率

mu_1_list = np.arange(0.005,0.1,0.01)   # SDG变为PDG的速率
mu_2_list = np.arange(0.005,0.1,0.01)   # SHG变为SDG的速率

K = 0.1  # 噪音因素

for runer in range(run_times):
    # G = nx.barabasi_albert_graph(n, 3)  # 无标度网络
    G = nx.watts_strogatz_graph(n, 4, 0.15)  # 小世界网络

    result = {}
    for mu_1 in mu_1_list:
        result_mu_1 = {}
        for mu_2 in mu_2_list:
            print("\r" + "mu_1={:.3f},mu_2={:.3f},run:{:.2f}/{:.2f}".format(mu_1, mu_2, runer,run_times), end='')

            f_c = []
            state = {}  # 边状态字典 (PDG为0，SDG为1, SHG为2)   G0: PDG     G1: SDG      G2: SHG
            strategy = {}  # 玩家策略字典
            next_change = {}  # 边状态改变时间
            next_changer_flag = {}  # 玩家在进行SDG时决定改变为PDG或SHG的标记
            fun_f = lambda x: (len(x) - sum(list(map(lambda x: x[-1], list(x.values()))))) / len(x)  # 根据策略字典计算合作者比例

            # 初始化
            for i in G.nodes:
                strategy[i] = [0 <= random.uniform(0, 1) < 0.5]  # True为Defector,False为Cooperator
            f_c.append(fun_f(strategy))

            num_g0 = 0
            num_g1 = 0
            num_g2 = 0

            for i in G.edges:
                next_change[i] = 0
                state[i] = random.choice([0, 1, 2])  # 初始是个体随机进行G0, G1, G2
                if state[i] == 0:
                    next_change[i] += random.expovariate(lam_0)  # 边下一次变为进行G1的时间
                    num_g0 += 1  # 进行G0个数加1
                if state[i] == 1:
                    g2_time = random.expovariate(lam_1)  # 变为G2的时间
                    g0_time = random.expovariate(mu_1)  # 变为G0的时间
                    if g0_time > g2_time:  # 边变为G2
                        next_change[i] += g2_time  # 节点下一次变为进行G2的时间
                        next_changer_flag[i] = 'g2'
                    else:
                        next_change[i] += g0_time  # 节点下一次变为进行G0的时间
                        next_changer_flag[i] = 'g0'
                    num_g1 += 1  # 进行G1个数加1
                if state[i] == 2:
                    next_change[i] += random.expovariate(mu_2)  # 边下一次变为进行G1的时间
                    num_g2 += 1  # 进行G0个数加1

            tnow = 0
            t_update = 0  # 玩家在整数时间更新策略
            g0_list = [num_g0]  # G0个数
            g1_list = [num_g1]  # G1个数
            g2_list = [num_g2]  # G2个数
            flag = 0
            cmd = 0  # 从cmd后开始统计进行各个博弈的个数

            while tnow < ETime:
                #print("\r" + "mu_1={:.3f},mu_2={:.3f},fc={:.3f},t:{:.2f}/{:.2f}".format(mu_1,mu_2,f_c[-1], tnow, ETime), end='')

                if f_c[-1] == 1 or f_c[-1] == 0:
                    break

                while t_update < tnow:  # 玩家在整数时间同步更新策略（开始博弈）
                    Payoff = {}
                    # 更新每个玩家的策略
                    for x in G.nodes:
                        x_nei = list(G.neighbors(x))
                        y = random.choice(x_nei)  # 随机选出一个邻居节点
                        s_change = strategy[y][t_update]
                        if s_change == strategy[x][t_update]:  # x与y的策略一样
                            strategy[x].append(strategy[x][t_update])
                        else:  # x与y的策略不一样，需计算玩家的收益
                            if x not in Payoff:
                                Payoff[x] = payoff_cal(G, x, state, pom_0, pom_1, pom_2)
                            if y not in Payoff:
                                Payoff[y] = payoff_cal(G, y, state, pom_0, pom_1, pom_2)

                            ran = 1 / (1 + np.exp((Payoff[x] - Payoff[y]) / K))
                            if 0 <= random.uniform(0, 1) < ran:
                                strategy[x].append(strategy[y][t_update])
                            else:
                                strategy[x].append(strategy[x][t_update])
                    t_update += 1
                    f_c.append(fun_f(strategy))
                    g0_list.append(num_g0)
                    g1_list.append(num_g1)
                    g2_list.append(num_g2)
                # 边状态转移
                changer = min(next_change.items(), key=lambda x: x[1])[0]  # 找出下一个改变状态的边
                tnow = next_change[changer]
                if state[changer] == 1:  # 边当前在进行G1，即将改变状态
                    if next_changer_flag[changer] == 'g2':  # 边变为G2
                        state[changer] = 2
                        next_change[changer] += random.expovariate(mu_2)  # 边下一次变为进行G1的时间
                        num_g2 += 1  # 进行G2个数加1
                        num_g1 -= 1  # 进行G1个数减1
                    elif next_changer_flag[changer] == 'g0':  # 边变为G0
                        state[changer] = 0
                        next_change[changer] += random.expovariate(lam_0)  # 边下一次变为进行G1的时间
                        num_g0 += 1  # 进行G0个数加1
                        num_g1 -= 1  # 进行G1个数减1
                    else:
                        print('error!')
                elif state[changer] == 0:  # 边当前在进行G0，即将改变状态
                    state[changer] = 1  # 边只能变为G1
                    g2_time = random.expovariate(lam_1)  # 变为G2的时间
                    g0_time = random.expovariate(mu_1)  # 变为G0的时间
                    if g0_time > g2_time:  # 边变为G2
                        next_change[changer] += g2_time  # 边下一次变为进行G2的时间
                        next_changer_flag[changer] = 'g2'
                    else:
                        next_change[changer] += g0_time  # 边下一次变为进行G0的时间
                        next_changer_flag[changer] = 'g0'
                    num_g1 += 1  # 进行G1个数加1
                    num_g0 -= 1  # 进行G0个数减1
                elif state[changer] == 2:  # 边当前在进行G2，即将改变状态
                    state[changer] = 1  # 边只能变为G1
                    g2_time = random.expovariate(lam_1)  # 变为G2的时间
                    g0_time = random.expovariate(mu_1)  # 变为G0的时间
                    if g0_time > g2_time:  # 边变为G2
                        next_change[changer] += g2_time  # 边下一次变为进行G2的时间
                        next_changer_flag[changer] = 'g2'
                    else:
                        next_change[changer] += g0_time  # 边下一次变为进行G0的时间
                        next_changer_flag[changer] = 'g0'
                    num_g1 += 1  # 进行G1个数加1
                    num_g2 -= 1  # 进行G2个数减1
            result_mu_1['mu_2: {:.3f}'.format(mu_2)] = f_c
        result['mu_1: {:.3f}'.format(mu_1)] = result_mu_1