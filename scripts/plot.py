import os

import matplotlib.pyplot as plt
import pandas as pd

# prepare csv for plot
solvers = [
    "cadical",
    "cryptominisat",
    "kissat",
    "glucose-syrup",
    "maplesat",
]

# plt.rcParams["font.sans-serif"] = ["simsun"]
plt.rcParams["font.sans-serif"] = ["Times New Roman"]
plt.rcParams["text.usetex"] = True

legend_fontsize = 50
ticks_fontsize = 40
label_fontsize = 40


# TODO: larger font, harden line
def merge_csv(filename):
    # check if file exist
    if os.path.isfile(filename):
        return pd.read_csv(filename)

    df = pd.DataFrame()
    dfs = []
    for solver in solvers:
        df_a = pd.read_csv(f"A-{solver}.csv")
        df_b = pd.read_csv(f"B-{solver}.csv")

        df_a.drop(columns=["M_s", "M_p", "M_l"], inplace=True)
        df_b.drop(columns=["M_s", "M_p", "M_l"], inplace=True)
        df_a.drop(columns=["round"], inplace=True)
        df_b.drop(columns=["round"], inplace=True)

        dfs.append(df_a)
        dfs.append(df_b)
    df = pd.concat(dfs, axis=1)
    df.to_csv(filename, index=False)
    return df


def plot_cmp_solvers(df, model):
    plt.cla()
    plt.clf()
    plt.subplot(1, 2, 1)
    for f_nr, host in enumerate(["A", "B"]):
        plt.subplot(1, 2, f_nr + 1)
        for sol_nr, solver in enumerate(solvers):
            sname = solver[:3].lower()
            entry = f"T_{{{sname}}}^{{{host},{model}}}"
            plt.plot(
                list(range(1, 29)),
                df[entry],
                marker="o",
                linewidth=15,
                label=f"${entry}$",
                linestyle=["-", ":", "--", "solid", "-."][sol_nr],
                color=["red", "blue", "orange", "green", "black"][sol_nr],
            )
            plt.xticks(fontsize=ticks_fontsize)
            plt.yticks(fontsize=ticks_fontsize)
            plt.legend(loc="best", fontsize=legend_fontsize)
            plt.xlabel("Round", fontsize=label_fontsize)
            plt.ylabel("Time", fontsize=label_fontsize)
    plt.show()
    plt.savefig(f"plot_cmp_solvers-{model}.png")


# https://www.zhihu.com/question/26627112
def plot_cmp_hosts(df, sname):
    plt.cla()
    plt.clf()

    plt.subplot(1, 3, 1)
    for f_nr, model in enumerate(["s", "l", "p"]):
        plt.subplot(1, 3, f_nr + 1)
        for h_nr, host in enumerate(["A", "B"]):
            entry = f"T_{{{sname}}}^{{{host},{model}}}"
            plt.bar(
                list(range(1, 29)),
                df[entry],
                label=f"${entry}$",
                color=["red", "blue"][h_nr],
            )
            # plt.bar_label(bar, labels=A_ratio, label_type="edge")
            plt.xticks(fontsize=ticks_fontsize)
            plt.yticks(fontsize=ticks_fontsize)
            plt.legend(loc="best", fontsize=legend_fontsize)
            plt.xlabel("Round", fontsize=label_fontsize)
            if f_nr == 0:
                plt.ylabel("Time", fontsize=label_fontsize)
        A_values = df[f"T_{{{sname}}}^{{A,{model}}}"]
        B_values = df[f"T_{{{sname}}}^{{B,{model}}}"]
        A_ratio = B_values / A_values
        _ = plt.twinx()
        # if f_nr == 2:
        #     ax.set_ylabel("Ratio", fontsize=label_fontsize)
        plt.plot(A_ratio, marker="*", color="black", linewidth=10, label="Ratio")
        plt.yticks(fontsize=ticks_fontsize)
        if f_nr == 2:
            plt.ylabel("Ratio", fontsize=label_fontsize)
        plt.legend(loc="best", fontsize=legend_fontsize)
        # for a, b in zip(list(range(1, 29)), A_ratio):
        #     pc = int(b * 100)
        #     print(a, b)
        #     plt.text(a, b, b, ha="center", va="bottom", fontsize=12)
        # plt.ylabel("Ratio", fontsize=30)
        # plt.legend(loc="best", fontsize=30)
        # plt.title(f"{solver} 求解器", size=30)
    plt.show()
    plt.savefig(f"plot_cmp_host-{sname}.png")
    plt.cla()
    plt.clf()


if __name__ == "__main__":
    df = merge_csv("all.csv")
    plt.show = lambda: None
    plt.figure(figsize=(45, 20))

    # compare solvers
    for model in ["s", "l", "p"]:
        plot_cmp_solvers(df, model)

    # compare hosts
    for solver in solvers:
        plot_cmp_hosts(df, solver[:3].lower())

    # same solvers, different models?
    # plot_cmp_models(df, "B")
    # plot_cmp_models(df, "B")

# df_a = df_a.rename(columns=lambda name: f"A-{name}")
# df_b = df_b.rename(columns=lambda name: f"B-{name}")
# df = pd.concat([df_a, df_b], axis=1)
# E_{cry}^{A,s}
# sname = solvers[:3].to_lower()
# new_columns = ["round", f"E_{{{sname}}}^{{{solver}}}", "E_{A,s}"]
# df = df.reindex(columns=new_columns)
