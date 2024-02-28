import time
from subprocess import Popen

from common import *

FullRound = 32

SearchRoundStart = 1
SearchRoundEnd = 7
InitialLowerBound = 0

GroupConstraintChoice = 1

# Parameters for choice 1
GroupNumForChoice1 = 1

LinearBiasBound = FullRound * [0]


def CountClausesInRoundFunction(Round, Bias, clause_num):
    return clause_num + 1 + Round * 16 * 51


def CountClausesInSequentialEncoding(main_var_num, cardinalitycons, clause_num):
    count = clause_num
    n = main_var_num
    k = cardinalitycons
    if k > 0:
        return count + 1 + (k - 1) + (n - 2) * 3 + (k - 1) * (n - 2) * 2 + 1
    if k == 0:
        return count + n


def CountClausesForMatsuiStrategy(n, k, left, right, m, clausenum):
    count = clausenum
    if m > 0:
        if (left == 0) and (right < n - 1):
            for i in range(1, right + 1):
                count += 1
        if (left > 0) and (right == n - 1):
            for i in range(0, k - m):
                count += 1
            for i in range(0, k - m + 1):
                count += 1
        if (left > 0) and (right < n - 1):
            for i in range(0, k - m):
                count += 1
    if m == 0:
        for i in range(left, right + 1):
            count += 1
    return count


def GenSequentialEncoding(x, u, main_var_num, cardinalitycons, fout):
    n = main_var_num
    k = cardinalitycons
    if k > 0:
        clauseseq = f"-{x[0] + 1} {u[0][0] + 1} 0\n"
        fout.write(clauseseq)
        for j in range(1, k):
            clauseseq = f"-{u[0][j] + 1} 0\n"
            fout.write(clauseseq)
        for i in range(1, n - 1):
            clauseseq = f"-{x[i] + 1} {u[i][0] + 1} 0\n"
            fout.write(clauseseq)
            clauseseq = f"-{u[i - 1][0] + 1} {u[i][0] + 1} 0\n"
            fout.write(clauseseq)
            clauseseq = f"-{x[i] + 1} -{u[i - 1][k - 1] + 1} 0\n"
            fout.write(clauseseq)
        for j in range(1, k):
            for i in range(1, n - 1):
                clauseseq = f"-{x[i] + 1} -{u[i - 1][j - 1] + 1} {u[i][j] + 1} 0\n"
                fout.write(clauseseq)
                clauseseq = f"-{u[i - 1][j] + 1} {u[i][j] + 1} 0\n"
                fout.write(clauseseq)
        clauseseq = f"-{x[n - 1] + 1} -{u[n - 2][k - 1] + 1} 0\n"
        fout.write(clauseseq)
    if k == 0:
        for i in range(n):
            clauseseq = f"-{x[i] + 1} 0\n"
            fout.write(clauseseq)


def GenMatsuiConstraint(x, u, n, k, left, right, m, fout):
    if m > 0:
        if (left == 0) and (right < n - 1):
            for i in range(1, right + 1):
                clauseseq = f"-{x[i] + 1} -{u[i - 1][m - 1] + 1} 0\n"
                fout.write(clauseseq)
        if (left > 0) and (right == n - 1):
            for i in range(0, k - m):
                clauseseq = f"{u[left - 1][i] + 1} -{u[right - 1][i + m] + 1} 0\n"
                fout.write(clauseseq)
            for i in range(0, k - m + 1):
                clauseseq = f"{u[left - 1][i] + 1} -{x[right] + 1} -{u[right - 1][i + m - 1] + 1} 0\n"
                fout.write(clauseseq)
        if (left > 0) and (right < n - 1):
            for i in range(0, k - m):
                clauseseq = f"{u[left - 1][i] + 1} -{u[right][i + m] + 1} 0\n"
                fout.write(clauseseq)
    if m == 0:
        for i in range(left, right + 1):
            clauseseq = f"-{x[i] + 1} 0\n"
            fout.write(clauseseq)


def Decision(Round, Bias, MatsuiRoundIndex, MatsuiCount, flag):
    TotalBias = 16 * Round * 2
    count_var_num = 0
    time_start = time.time()
    # Declare variables
    xin = []
    p = []
    q = []
    xout = []
    for i in range(Round):
        xin.append([])
        p.append([])
        q.append([])
        xout.append([])
        for j in range(64):
            xin[i].append(0)
        for j in range(16):
            p[i].append(0)
            q[i].append(0)
        for j in range(64):
            xout[i].append(0)
    # Allocate variables
    for i in range(Round):
        for j in range(64):
            xin[i][j] = count_var_num
            count_var_num += 1
        for j in range(16):
            p[i][j] = count_var_num
            count_var_num += 1
        for j in range(16):
            q[i][j] = count_var_num
            count_var_num += 1
    for i in range(Round - 1):
        for j in range(64):
            xout[i][j] = xin[i + 1][j]
    for i in range(64):
        xout[Round - 1][i] = count_var_num
        count_var_num += 1
    auxiliary_var_u = []
    for i in range(TotalBias - 1):
        auxiliary_var_u.append([])
        for j in range(Bias):
            auxiliary_var_u[i].append(count_var_num)
            count_var_num += 1
    # Count the number of clauses in the round function
    count_clause_num = 0
    count_clause_num = CountClausesInRoundFunction(Round, Bias, count_clause_num)
    # Count the number of clauses in the original sequential encoding
    Main_Var_Num = 16 * Round * 2
    CardinalityCons = Bias
    count_clause_num = CountClausesInSequentialEncoding(
        Main_Var_Num, CardinalityCons, count_clause_num
    )
    # Count the number of clauses for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 16 * StartingRound * 2
        RightNode = 16 * EndingRound * 2 - 1
        PartialCardinalityCons = (
            Bias - LinearBiasBound[StartingRound] - LinearBiasBound[Round - EndingRound]
        )
        count_clause_num = CountClausesForMatsuiStrategy(
            Main_Var_Num,
            CardinalityCons,
            LeftNode,
            RightNode,
            PartialCardinalityCons,
            count_clause_num,
        )
    # Open file
    file = open(f"Problem-Round{Round}-Bias{Bias}.cnf", "w")
    file.write(f"p cnf {count_var_num} {count_clause_num}\n")
    # Add constraints to claim nonzero input difference
    clauseseq = ""
    for i in range(64):
        clauseseq += f"{xin[0][i] + 1} "
    clauseseq += f"0\n"
    file.write(clauseseq)
    # Add constraints for the round function
    for r in range(Round):
        y = list([])
        P = [
            0,
            16,
            32,
            48,
            1,
            17,
            33,
            49,
            2,
            18,
            34,
            50,
            3,
            19,
            35,
            51,
            4,
            20,
            36,
            52,
            5,
            21,
            37,
            53,
            6,
            22,
            38,
            54,
            7,
            23,
            39,
            55,
            8,
            24,
            40,
            56,
            9,
            25,
            41,
            57,
            10,
            26,
            42,
            58,
            11,
            27,
            43,
            59,
            12,
            28,
            44,
            60,
            13,
            29,
            45,
            61,
            14,
            30,
            46,
            62,
            15,
            31,
            47,
            63,
        ]
        SymbolicCNFConstraintForSbox = [  # Linear Bias PRESENT (51)
            [0, 9, 1, 0, 0, 9, 0, 9, 0, 9],
            [9, 0, 9, 1, 0, 0, 9, 0, 0, 9],
            [1, 1, 0, 1, 1, 9, 9, 9, 0, 9],
            [0, 1, 1, 9, 9, 0, 9, 0, 9, 9],
            [9, 1, 1, 9, 1, 9, 1, 9, 1, 9],
            [1, 0, 1, 9, 1, 9, 1, 0, 0, 9],
            [9, 1, 1, 9, 1, 9, 1, 1, 9, 9],
            [9, 1, 1, 9, 9, 0, 0, 0, 0, 9],
            [0, 1, 1, 9, 9, 1, 9, 1, 9, 9],
            [0, 9, 1, 1, 1, 9, 0, 0, 0, 9],
            [0, 1, 9, 1, 0, 9, 1, 0, 0, 9],
            [9, 0, 9, 9, 0, 0, 1, 1, 0, 9],
            [9, 9, 9, 9, 9, 9, 9, 1, 9, 0],
            [9, 0, 0, 9, 0, 9, 0, 9, 1, 9],
            [0, 0, 1, 1, 9, 9, 9, 1, 0, 9],
            [9, 1, 9, 1, 9, 1, 9, 1, 0, 9],
            [1, 9, 9, 9, 0, 9, 1, 1, 0, 9],
            [1, 9, 1, 9, 1, 1, 9, 9, 0, 9],
            [1, 1, 9, 0, 9, 9, 1, 0, 0, 9],
            [9, 9, 0, 9, 0, 1, 9, 0, 0, 9],
            [0, 0, 9, 9, 1, 1, 9, 0, 0, 9],
            [9, 0, 9, 0, 0, 1, 9, 9, 0, 9],
            [9, 0, 1, 9, 0, 1, 0, 9, 0, 9],
            [9, 1, 0, 9, 1, 1, 1, 9, 0, 9],
            [0, 9, 9, 0, 1, 1, 1, 9, 0, 9],
            [1, 9, 9, 9, 1, 9, 0, 1, 0, 9],
            [9, 9, 0, 9, 0, 0, 1, 1, 0, 9],
            [9, 9, 9, 1, 1, 0, 1, 1, 9, 9],
            [1, 0, 0, 0, 9, 0, 9, 9, 0, 9],
            [0, 9, 0, 9, 9, 0, 0, 1, 0, 9],
            [9, 9, 0, 1, 9, 0, 0, 0, 0, 9],
            [9, 0, 1, 0, 9, 0, 0, 9, 0, 9],
            [9, 9, 1, 1, 0, 0, 9, 0, 0, 9],
            [9, 1, 9, 0, 0, 0, 0, 9, 9, 9],
            [9, 9, 0, 0, 9, 1, 0, 9, 0, 9],
            [0, 9, 9, 0, 9, 0, 9, 0, 0, 1],
            [0, 0, 0, 9, 9, 0, 9, 9, 9, 1],
            [9, 9, 9, 9, 1, 9, 9, 9, 9, 0],
            [0, 9, 9, 9, 0, 0, 0, 9, 9, 1],
            [1, 9, 9, 1, 9, 1, 9, 9, 0, 9],
            [9, 9, 9, 9, 9, 1, 9, 9, 9, 0],
            [9, 9, 9, 9, 9, 9, 9, 9, 1, 0],
            [9, 9, 9, 9, 9, 9, 1, 9, 9, 0],
            [9, 1, 1, 9, 0, 9, 0, 9, 1, 9],
            [9, 0, 0, 9, 1, 9, 1, 9, 1, 9],
            [0, 9, 9, 9, 1, 1, 0, 9, 1, 9],
            [1, 1, 0, 9, 9, 0, 9, 9, 1, 9],
            [1, 0, 1, 9, 9, 0, 9, 9, 1, 9],
            [0, 9, 9, 9, 0, 1, 1, 9, 1, 9],
            [0, 1, 1, 9, 9, 9, 9, 9, 1, 9],
            [9, 9, 9, 9, 1, 0, 1, 9, 1, 9],
        ]
        for i in range(64):
            y += [xout[r][P[i]]]
        for i in range(16):
            X = list([])
            for j in range(4):
                X += [xin[r][4 * i + j]]
            for j in range(4):
                X += [y[4 * i + j]]
            X += [p[r][i]]
            X += [q[r][i]]
            for j in range(51):
                clauseseq = ""
                for k in range(10):
                    if SymbolicCNFConstraintForSbox[j][k] == 1:
                        clauseseq += f"-{X[k] + 1} "
                    if SymbolicCNFConstraintForSbox[j][k] == 0:
                        clauseseq += f"{X[k] + 1} "
                clauseseq += f"0\n"
                file.write(clauseseq)
    # Add constraints for the original sequential encoding
    Main_Vars = list([])
    for r in range(Round):
        for i in range(16):
            Main_Vars += [p[Round - 1 - r][i]]
            Main_Vars += [q[Round - 1 - r][i]]
    GenSequentialEncoding(
        Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, file
    )
    # Add constraints for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 16 * StartingRound * 2
        RightNode = 16 * EndingRound * 2 - 1
        PartialCardinalityCons = (
            Bias - LinearBiasBound[StartingRound] - LinearBiasBound[Round - EndingRound]
        )
        GenMatsuiConstraint(
            Main_Vars,
            auxiliary_var_u,
            Main_Var_Num,
            CardinalityCons,
            LeftNode,
            RightNode,
            PartialCardinalityCons,
            file,
        )
    file.close()
    # Call solver cadical
    order = f"~/Install/cadical/build/cadical Problem-Round{Round}-Bias{Bias}.cnf > Round{Round}-Bias{Bias}-solution.out"
    Popen(order, shell=True).wait()
    # Extracting results
    order = f"sed -n '/s SATISFIABLE/p' Round{Round}-Bias{Bias}-solution.out > SatSolution.out"
    Popen(order, shell=True).wait()
    order = f"sed -n '/s UNSATISFIABLE/p' Round{Round}-Bias{Bias}-solution.out > UnsatSolution.out"
    Popen(order, shell=True).wait()
    satsol = open("SatSolution.out")
    unsatsol = open("UnsatSolution.out")
    satresult = satsol.readlines()
    unsatresult = unsatsol.readlines()
    satsol.close()
    unsatsol.close()
    if (len(satresult) == 0) and (len(unsatresult) > 0):
        flag = False
    if (len(satresult) > 0) and (len(unsatresult) == 0):
        flag = True
    order = "rm SatSolution.out"
    Popen(order, shell=True).wait()
    order = "rm UnsatSolution.out"
    Popen(order, shell=True).wait()
    # Removing cnf file
    order = f"rm Problem-Round{Round}-Bias{Bias}.cnf"
    Popen(order, shell=True).wait()
    time_end = time.time()
    # Printing solutions
    if flag == True:
        print(f"Round:{Round}; Bias: {Bias}; Sat; TotalCost: {time_end - time_start}")
    else:
        print(f"Round:{Round}; Bias: {Bias}; Unsat; TotalCost: {time_end - time_start}")
    return flag


# main function
CountBias = InitialLowerBound
TotalTimeStart = time.time()
for totalround in range(SearchRoundStart, SearchRoundEnd):
    flag = False
    time_start = time.time()
    MatsuiRoundIndex = []
    MatsuiCount = 0
    # Generate Matsui condition under choice 1
    if GroupConstraintChoice == 1:
        for group in range(0, GroupNumForChoice1):
            for round in range(1, totalround - group + 1):
                MatsuiRoundIndex.append([])
                MatsuiRoundIndex[MatsuiCount].append(group)
                MatsuiRoundIndex[MatsuiCount].append(group + round)
                MatsuiCount += 1
    # Printing Matsui conditions
    file = open("MatsuiCondition.out", "a")
    resultseq = f"Round: {totalround}; Partial Constraint Num: {MatsuiCount}\n"
    file.write(resultseq)
    file.write(f"{MatsuiRoundIndex}\n")
    file.close()
    while flag == False:
        flag = Decision(totalround, CountBias, MatsuiRoundIndex, MatsuiCount, flag)
        CountBias += 1
    LinearBiasBound[totalround] = CountBias - 1
    time_end = time.time()
    file = open("RunTimeSummarise.out", "a")
    resultseq = f"Round: {totalround}; Linear Biase: {LinearBiasBound[totalround]}; Runtime: {time_end - time_start}\n"
    file.write(resultseq)
    file.close()
print(str(LinearBiasBound))
TotalTimeEnd = time.time()
print(f"Total Runtime: {TotalTimeEnd - TotalTimeStart}")
file = open("RunTimeSummarise.out", "a")
resultseq = f"Total Runtime: {TotalTimeEnd - TotalTimeStart}"
file.write(resultseq)
