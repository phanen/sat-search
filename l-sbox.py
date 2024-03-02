import time
from subprocess import Popen

# from common import *
from const import *

FullRound = 32

SearchRoundStart = 1
SearchRoundEnd = 32
InitialLowerBound = 0

GroupConstraintChoice = 1

# Parameters for choice 1
GroupNumForChoice1 = 1

LinearActiveSbox = FullRound * [0]


def Decision(Round, ActiveSbox, MatsuiRoundIndex, MatsuiCount, flag):
    TotalSbox = 16 * Round
    count_var_num = 0
    time_start = time.time()
    # Declare variables
    xin = []
    w = []
    xout = []
    for i in range(Round):
        xin.append([])
        w.append([])
        xout.append([])
        for j in range(64):
            xin[i].append(0)
        for j in range(16):
            w[i].append(0)
        for j in range(64):
            xout[i].append(0)
    # Allocate variables
    for i in range(Round):
        for j in range(64):
            xin[i][j] = count_var_num
            count_var_num += 1
        for j in range(16):
            w[i][j] = count_var_num
            count_var_num += 1
    for i in range(Round - 1):
        for j in range(64):
            xout[i][j] = xin[i + 1][j]
    for i in range(64):
        xout[Round - 1][i] = count_var_num
        count_var_num += 1
    auxiliary_var_u = []
    for i in range(TotalSbox - 1):
        auxiliary_var_u.append([])
        for j in range(ActiveSbox):
            auxiliary_var_u[i].append(count_var_num)
            count_var_num += 1
    # Count the number of clauses in the round function
    count_clause_num = 0
    count_clause_num = CountClausesInRoundFunction(Round, ActiveSbox, count_clause_num)
    # Count the number of clauses in the original sequential encoding
    Main_Var_Num = 16 * Round
    CardinalityCons = ActiveSbox
    count_clause_num = CountClausesInSequentialEncoding(
        Main_Var_Num, CardinalityCons, count_clause_num
    )
    # Count the number of clauses for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 16 * StartingRound
        RightNode = 16 * EndingRound - 1
        PartialCardinalityCons = (
            ActiveSbox
            - LinearActiveSbox[StartingRound]
            - LinearActiveSbox[Round - EndingRound]
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
    file = open(f"Problem-Round{Round}-Active{ActiveSbox}.cnf", "w")
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
        for i in range(64):
            y += [xout[r][P[i]]]
        for i in range(16):
            for j in range(39):
                X = list([])
                for k in range(4):
                    X += [xin[r][4 * i + k]]
                for k in range(4):
                    X += [y[4 * i + k]]
                X += [w[r][i]]
                clauseseq = ""
                for k in range(9):
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
            Main_Vars += [w[Round - 1 - r][i]]
    GenSequentialEncoding(
        Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, file
    )
    # Add constraints for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 16 * StartingRound
        RightNode = 16 * EndingRound - 1
        PartialCardinalityCons = (
            ActiveSbox
            - LinearActiveSbox[StartingRound]
            - LinearActiveSbox[Round - EndingRound]
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


# main function
CountSbox = InitialLowerBound
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
        flag = Decision(totalround, CountSbox, MatsuiRoundIndex, MatsuiCount, flag)
        CountSbox += 1
    LinearActiveSbox[totalround] = CountSbox - 1
    time_end = time.time()
    file = open("RunTimeSummarise.out", "a")
    resultseq = f"Round: {totalround}; Active S-box: {LinearActiveSbox[totalround]}; Runtime: {time_end - time_start}\n"
    file.write(resultseq)
    file.close()
print(str(LinearActiveSbox))
TotalTimeEnd = time.time()
print(f"Total Runtime: {TotalTimeEnd - TotalTimeStart}")
file = open("RunTimeSummarise.out", "a")
resultseq = f"Total Runtime: {TotalTimeEnd - TotalTimeStart}"
file.write(resultseq)
