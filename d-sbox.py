import time

from common import *

FullRound = 32

SearchRoundStart = 1
SearchRoundEnd = 8
InitialLowerBound = 0

GroupConstraintChoice = 1

# Parameters for choice 1
GroupNumForChoice1 = 1

DiffActiveSbox = FullRound * [0]


def CountClausesInRoundFunction(Round):
    return 1 + Round * 16 * 43


def GenSequentialEncoding(x, u, main_var_num, cardinalitycons, w):
    n = main_var_num
    k = cardinalitycons
    if k > 0:
        w(f"-{x[0] + 1} {u[0][0] + 1} 0\n")
        for j in range(1, k):
            w(f"-{u[0][j] + 1} 0\n")
        for i in range(1, n - 1):
            w(f"-{x[i] + 1} {u[i][0] + 1} 0\n")
            w(f"-{u[i - 1][0] + 1} {u[i][0] + 1} 0\n")
            w(f"-{x[i] + 1} -{u[i - 1][k - 1] + 1} 0\n")
        for j in range(1, k):
            for i in range(1, n - 1):
                w(f"-{x[i] + 1} -{u[i - 1][j - 1] + 1} {u[i][j] + 1} 0\n")
                w(f"-{u[i - 1][j] + 1} {u[i][j] + 1} 0\n")
        w(f"-{x[n - 1] + 1} -{u[n - 2][k - 1] + 1} 0\n")
    if k == 0:
        for i in range(n):
            w(f"-{x[i] + 1} 0\n")


def GenMatsuiConstraint(x, u, n, k, l, r, m, w):
    if m > 0:
        if l == 0 and r < n - 1:
            for i in range(1, r + 1):
                w(f"-{x[i] + 1} -{u[i - 1][m - 1] + 1} 0\n")
        if l > 0 and r == n - 1:
            for i in range(k - m):
                w(f"{u[l - 1][i] + 1} -{u[r - 1][i + m] + 1} 0\n")
            for i in range(k - m + 1):
                w((f"{u[l - 1][i] + 1} -{x[r] + 1} -{u[r - 1][i + m - 1] + 1} 0\n"))
        if l > 0 and r < n - 1:
            for i in range(k - m):
                w(f"{u[l - 1][i] + 1} -{u[r][i + m] + 1} 0\n")
    if m == 0:
        for i in range(l, r + 1):
            w(f"-{x[i] + 1} 0\n")


def cnfbuilder(round, activeSbox, matsuiRoundIndex, matsuiCount, cnffile):
    totalSbox = 16 * round
    count_var = 0
    xin = [64 * [0] for _ in range(round)]
    w = [16 * [0] for _ in range(round)]
    xout = [64 * [0] for _ in range(round)]
    for i in range(round):
        for j in range(64):
            xin[i][j] = count_var
            count_var += 1
        for j in range(16):
            w[i][j] = count_var
            count_var += 1
    for i in range(round - 1):
        for j in range(64):
            xout[i][j] = xin[i + 1][j]
    for i in range(64):
        xout[round - 1][i] = count_var
        count_var += 1
    var_u = []
    for i in range(totalSbox - 1):
        var_u.append([])
        for j in range(activeSbox):
            var_u[i].append(count_var)
            count_var += 1

    count_clause = CountClausesInRoundFunction(round)
    mainVarNum = 16 * round
    cardinalityCons = activeSbox
    count_clause += CountClausesInSequentialEncoding(mainVarNum, cardinalityCons)
    for matsui_count in range(matsuiCount):
        StartingRound = matsuiRoundIndex[matsui_count][0]
        EndingRound = matsuiRoundIndex[matsui_count][1]
        leftNode = 16 * StartingRound
        rightNode = 16 * EndingRound - 1
        partialCardinalityCons = (
            activeSbox
            - DiffActiveSbox[StartingRound]
            - DiffActiveSbox[round - EndingRound]
        )
        count_clause += CountClausesForMatsuiStrategy(
            mainVarNum,
            cardinalityCons,
            leftNode,
            rightNode,
            partialCardinalityCons,
        )

    with open(cnffile, "w") as file:
        file.write(f"p cnf {count_var} {count_clause}\n")
        # Add constraints to claim nonzero input difference
        clauseseq = ""
        for i in range(64):
            clauseseq += f"{xin[0][i] + 1} "
        clauseseq += f"0\n"
        file.write(clauseseq)
        # Add constraints for the round function
        for r in range(round):
            y = []
            for i in range(64):
                y += [xout[r][P[i]]]
            for i in range(16):
                for j in range(43):
                    X = []
                    for k in range(4):
                        X += [xin[r][4 * i + k]]
                    for k in range(4):
                        X += [y[4 * i + k]]
                    X += [w[r][i]]
                    clauseseq = ""
                    for k in range(9):
                        if SymbolicCNFConstraintForSbox43[j][k] == 1:
                            clauseseq += f"-{X[k] + 1} "
                        if SymbolicCNFConstraintForSbox43[j][k] == 0:
                            clauseseq += f"{X[k] + 1} "
                    clauseseq += f"0\n"
                    file.write(clauseseq)
        # Add constraints for the original sequential encoding
        main_vars = []
        for r in range(round):
            for i in range(16):
                main_vars += [w[round - 1 - r][i]]
        GenSequentialEncoding(main_vars, var_u, mainVarNum, cardinalityCons, file.write)
        # Add constraints for Matsui's strategy
        for matsui_count in range(matsuiCount):
            StartingRound = matsuiRoundIndex[matsui_count][0]
            EndingRound = matsuiRoundIndex[matsui_count][1]
            leftNode = 16 * StartingRound
            rightNode = 16 * EndingRound - 1
            partialCardinalityCons = (
                activeSbox
                - DiffActiveSbox[StartingRound]
                - DiffActiveSbox[round - EndingRound]
            )
            GenMatsuiConstraint(
                main_vars,
                var_u,
                mainVarNum,
                cardinalityCons,
                leftNode,
                rightNode,
                partialCardinalityCons,
                file.write,
            )


# main function
countSbox = InitialLowerBound
TotalTimeStart = time.time()
for totalround in range(SearchRoundStart, SearchRoundEnd):
    time_start = time.time()
    matsuiRoundIndex = []
    matsuiCount = 0
    # Generate Matsui condition under choice 1
    if GroupConstraintChoice == 1:
        for group in range(GroupNumForChoice1):
            for round in range(1, totalround - group + 1):
                matsuiRoundIndex.append([])
                matsuiRoundIndex[matsuiCount].append(group)
                matsuiRoundIndex[matsuiCount].append(group + round)
                matsuiCount += 1
    # Printing Matsui conditions
    with open("MatsuiCondition.out", "a") as file:
        resultseq = f"Round: {totalround}; Partial Constraint Num: {matsuiCount}\n"
        file.write(resultseq)
        file.write(f"{matsuiRoundIndex}\n")
    flag = False
    while flag == False:
        cnfbuilder(
            round,
            countSbox,
            matsuiRoundIndex,
            matsuiCount,
            f"Round{round}-Active{countSbox}.cnf",
        )
        ts = time.time()
        flag = satsolver(
            f"Round{round}-Active{countSbox}.cnf",
            f"Round{round}-Active{countSbox}.out",
        )
        te = time.time()
        p(
            f"Round: {round}; Active: {countSbox:2}; {'Sat' if flag == True else 'UnSat':>5}; Cost: {ts - te}"
        )
        countSbox += 1
    DiffActiveSbox[totalround] = countSbox - 1
    time_end = time.time()
    with open(TIME_PATH, "a") as file:
        file.write(
            f"Round: {totalround}; Active S-box: {DiffActiveSbox[totalround]}; Runtime: {time_end - time_start}\n"
        )
TotalTimeEnd = time.time()

p(DiffActiveSbox)
p(f"Total Runtime: {TotalTimeEnd - TotalTimeStart}")
with open(TIME_PATH, "a") as file:
    file.write(f"Total Runtime: {TotalTimeEnd - TotalTimeStart}\n\n")
