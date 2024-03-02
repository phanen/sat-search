import os
import re
import time
from subprocess import DEVNULL, Popen

FullRound = 32

SearchRoundStart = 1
SearchRoundEnd = 32
InitialLowerBound = 0

GroupConstraintChoice = 1

# Parameters for choice 1
GroupNumForChoice1 = 1

# DiffActiveSbox
DiffActiveSbox = FullRound * [0]


VERBOSE = 1
SATOUTPUT = 0
log = print if VERBOSE else lambda *_: None

TIME_OUT = "RunTimeSummarise.out"
MATSUI_OUT = "MatsuiCondition.out"


SOLVER = {
    "cadical": [os.path.expanduser("~/b/cadical/build/cadical"), "-q"],
    "cryptominisat": [os.path.expanduser("~/b/cryptominisat/build/cryptominisat5")],
    "kissat": [os.path.expanduser("~/b/kissat/build/kissat"), "-q"],
}


def solver_builder(solver_name):
    solver_cmd = SOLVER.get(solver_name)
    if solver_cmd == None:
        exit("no such solver")
    if not os.access(solver_cmd[0], os.X_OK):
        exit("not executable solver")

    def satsolver(ifilename, ofilename):
        # https://github.com/arminbiere/cadical/blob/e71bd58937e6513f71bd8c93d91578785c592721/src/cadical.hpp#L478
        with open(ofilename, "+w") as f:
            out = f if SATOUTPUT else DEVNULL
            child = Popen([*solver_cmd, ifilename], stdout=out, stderr=DEVNULL)
            child.wait()
            if child.returncode == 10:
                return True
            elif child.returncode == 20:
                return False
            exit("unkown solver error")

    return satsolver


def clause_counter(round, activeSbox, matsuiRoundIndex, matsuiCount):
    def CountClausesInRoundFunction(round):
        return 1 + round * 16 * 43

    def CountClausesInSequentialEncoding(n, k):
        """
        n: mainVarNum
        k: cardinalitycons
        """
        if k > 0:
            return 1 + (k - 1) + (n - 2) * 3 + (k - 1) * (n - 2) * 2 + 1
        else:
            return n

    def CountClausesForMatsuiStrategy(n, k, l, r, m):
        count = 0
        if m > 0:
            if (l == 0) and (r < n - 1):
                for _ in range(1, r + 1):
                    count += 1
            elif (l > 0) and (r == n - 1):
                for _ in range(0, k - m):
                    count += 1
                for _ in range(0, k - m + 1):
                    count += 1
            elif (l > 0) and (r < n - 1):
                for _ in range(0, k - m):
                    count += 1
        if m == 0:
            for _ in range(l, r + 1):
                count += 1
        return count

    count_clause = CountClausesInRoundFunction(round)
    mainVarNum = 16 * round
    cardinalityCons = activeSbox
    count_clause += CountClausesInSequentialEncoding(mainVarNum, cardinalityCons)
    for mc in range(matsuiCount):
        StartRound = matsuiRoundIndex[mc][0]
        EndRound = matsuiRoundIndex[mc][1]
        leftNode = 16 * StartRound
        rightNode = 16 * EndRound - 1
        partialCardinalityCons = (
            activeSbox - DiffActiveSbox[StartRound] - DiffActiveSbox[round - EndRound]
        )
        count_clause += CountClausesForMatsuiStrategy(
            mainVarNum, cardinalityCons, leftNode, rightNode, partialCardinalityCons
        )
    return count_clause


def GenSequentialEncoding(x, u, n, k):
    """
    x: mainVars
    u: var_u
    n: mainVarNum
    k: cardinalitycons
    """
    seq = []
    if k > 0:
        seq.append(f"-{x[0] + 1} {u[0][0] + 1} 0\n")
        for j in range(1, k):
            seq.append(f"-{u[0][j] + 1} 0\n")
        for i in range(1, n - 1):
            seq.append(f"-{x[i] + 1} {u[i][0] + 1} 0\n")
            seq.append(f"-{u[i - 1][0] + 1} {u[i][0] + 1} 0\n")
            seq.append(f"-{x[i] + 1} -{u[i - 1][k - 1] + 1} 0\n")
        for j in range(1, k):
            for i in range(1, n - 1):
                seq.append(f"-{x[i] + 1} -{u[i - 1][j - 1] + 1} {u[i][j] + 1} 0\n")
                seq.append(f"-{u[i - 1][j] + 1} {u[i][j] + 1} 0\n")
        seq.append(f"-{x[n - 1] + 1} -{u[n - 2][k - 1] + 1} 0\n")
    else:  # if k == 0:
        for i in range(n):
            seq.append(f"-{x[i] + 1} 0\n")
    return seq


def GenMatsuiConstraint(x, u, n, k, l, r, m):
    seq = []
    if m > 0:
        if l == 0 and r < n - 1:
            for i in range(1, r + 1):
                seq.append(f"-{x[i] + 1} -{u[i - 1][m - 1] + 1} 0\n")
        if l > 0 and r == n - 1:
            for i in range(k - m):
                seq.append(f"{u[l - 1][i] + 1} -{u[r - 1][i + m] + 1} 0\n")
            for i in range(k - m + 1):
                seq.append(
                    f"{u[l - 1][i] + 1} -{x[r] + 1} -{u[r - 1][i + m - 1] + 1} 0\n"
                )
        if l > 0 and r < n - 1:
            for i in range(k - m):
                seq.append(f"{u[l - 1][i] + 1} -{u[r][i + m] + 1} 0\n")
    else:  # if m == 0:
        for i in range(l, r + 1):
            seq.append(f"-{x[i] + 1} 0\n")
    return seq


def matsui(round):
    matsuiRoundIndex, matsuiCount = [], 0
    matsuiCount = 0
    # Generate Matsui condition under choice 1
    if GroupConstraintChoice == 1:
        for group in range(GroupNumForChoice1):
            for round in range(1, round - group + 1):
                matsuiRoundIndex.append([group, group + round])
                matsuiCount += 1
    # Printing Matsui conditions
    with open(MATSUI_OUT, "a") as file:
        resultseq = f"Round: {round}; Partial Constraint Num: {matsuiCount}\n"
        file.write(resultseq)
        file.write(f"{matsuiRoundIndex}\n")
        log(resultseq.strip("\n"))
        log(f"{matsuiRoundIndex}")
    return matsuiRoundIndex, matsuiCount


def cnfbuilder(
    round,
    activeSbox,
    matsuiRoundIndex,
    matsuiCount,
    SymbolicCNFConstraintForSbox,
    cnffile,
):
    xi = []
    w = []
    xo = []
    totalSbox = 16 * round
    count_var = 0
    var_u = []
    for i in range(round):
        xi.append(list(range(count_var, count_var + 64)))
        count_var += 64
        w.append(list(range(count_var, count_var + 16)))
        count_var += 16
    for i in range(round - 1):
        xo.append(xi[i + 1])
    xo.append(list(range(count_var, count_var + 64)))
    count_var += 64
    for i in range(totalSbox - 1):
        var_u.append(range(count_var, count_var + activeSbox))
        count_var += activeSbox

    # Add constraints to claim nonzero input difference
    seq = []
    for i in range(64):
        seq.append(f"{xi[0][i] + 1} ")
    seq.append(f"0\n")
    # Add constraints for the round function
    for r in range(round):
        y = [xo[r][P[i]] for i in range(64)]
        for i in range(16):
            for j in range(43):
                X = []
                for k in range(4):
                    X.append(xi[r][4 * i + k])
                for k in range(4):
                    X.append(y[4 * i + k])
                X.append(w[r][i])
                for k in range(len(SymbolicCNFConstraintForSbox[0])):
                    if SymbolicCNFConstraintForSbox[j][k] == 1:
                        seq.append(f"-{X[k] + 1} ")
                    if SymbolicCNFConstraintForSbox[j][k] == 0:
                        seq.append(f"{X[k] + 1} ")
                seq.append(f"0\n")

    # Add constraints for the original sequential encoding
    mainVars = []
    for r in range(round):
        for i in range(16):
            mainVars.append(w[round - 1 - r][i])
    mainVarNum = 16 * round
    cardinalityCons = activeSbox
    seq += GenSequentialEncoding(mainVars, var_u, mainVarNum, cardinalityCons)
    # Add constraints for Matsui's strategy
    for mc in range(matsuiCount):
        StartRound = matsuiRoundIndex[mc][0]
        EndRound = matsuiRoundIndex[mc][1]
        leftNode = 16 * StartRound
        rightNode = 16 * EndRound - 1
        partialCardinalityCons = (
            activeSbox - DiffActiveSbox[StartRound] - DiffActiveSbox[round - EndRound]
        )
        seq += GenMatsuiConstraint(
            mainVars,
            var_u,
            mainVarNum,
            cardinalityCons,
            leftNode,
            rightNode,
            partialCardinalityCons,
        )
    with open(cnffile, "w") as file:
        # count_clause = clause_counter(round, activeSbox, matsuiRoundIndex, matsuiCount)
        count_clause = "".join(seq).count("\n")
        file.write(f"p cnf {count_var} {count_clause}\n")
        file.write("".join(seq))


def grep(pattern, path):
    with open(path) as f:
        content = f.read()
    return re.match(pattern, content)


def gen_timer():
    timetable = {}

    def tick(name):
        t = time.time()
        if name in timetable:
            timetable[name].append(t)
        else:
            timetable[name] = [t]
        return t

    def cost(name):
        return timetable[name][1] - timetable[name][0]

    return tick, cost


tick, cost = gen_timer()

# fmt: off
P = [
    0, 16, 32, 48,
    1, 17, 33, 49,
    2, 18, 34, 50,
    3, 19, 35, 51,
    4, 20, 36, 52,
    5, 21, 37, 53,
    6, 22, 38, 54,
    7, 23, 39, 55,
    8, 24, 40, 56,
    9, 25, 41, 57,
    10, 26, 42, 58,
    11, 27, 43, 59,
    12, 28, 44, 60,
    13, 29, 45, 61,
    14, 30, 46, 62,
    15, 31, 47, 63,
 ]

SymbolicCNFConstraintForSbox55 = [  # Differential Probability PRESENT (55)
    [1, 9, 0, 0, 0, 1, 9, 0, 9, 9, 9],
    [1, 0, 1, 9, 0, 1, 1, 9, 9, 9, 9],
    [1, 1, 0, 9, 1, 1, 0, 9, 9, 9, 9],
    [1, 0, 9, 0, 9, 1, 0, 0, 9, 9, 9],
    [0, 9, 1, 1, 9, 1, 0, 1, 9, 9, 9],
    [9, 0, 1, 1, 9, 1, 1, 0, 1, 9, 9],
    [9, 1, 0, 1, 1, 9, 0, 0, 1, 9, 9],
    [9, 1, 0, 9, 0, 9, 0, 0, 0, 9, 9],
    [0, 9, 0, 9, 0, 0, 1, 0, 9, 9, 9],
    [9, 0, 1, 0, 1, 0, 9, 1, 9, 9, 9],
    [9, 0, 1, 0, 9, 1, 1, 1, 9, 9, 9],
    [9, 1, 0, 9, 9, 0, 9, 1, 0, 9, 9],
    [9, 1, 1, 0, 9, 9, 0, 9, 0, 9, 9],
    [9, 1, 9, 9, 1, 9, 0, 1, 0, 9, 9],
    [9, 1, 0, 1, 0, 9, 1, 0, 1, 9, 9],
    [0, 0, 9, 1, 0, 9, 0, 9, 0, 9, 9],
    [9, 0, 0, 9, 0, 9, 1, 0, 0, 9, 9],
    [9, 0, 1, 1, 1, 9, 0, 0, 1, 9, 9],
    [9, 1, 0, 0, 9, 0, 1, 1, 9, 9, 9],
    [9, 9, 9, 9, 0, 0, 0, 0, 9, 9, 1],
    [0, 0, 9, 9, 0, 0, 9, 0, 9, 9, 1],
    [9, 1, 0, 0, 1, 1, 9, 1, 9, 9, 9],
    [9, 0, 0, 9, 1, 9, 1, 9, 1, 9, 9],
    [0, 1, 9, 1, 0, 9, 1, 1, 9, 9, 9],
    [9, 1, 0, 9, 9, 1, 1, 9, 0, 9, 9],
    [0, 1, 1, 9, 9, 9, 9, 0, 0, 9, 9],
    [9, 1, 1, 9, 0, 9, 0, 9, 1, 9, 9],
    [0, 0, 1, 9, 1, 0, 0, 9, 9, 9, 9],
    [9, 9, 9, 0, 9, 0, 0, 9, 0, 9, 1],
    [0, 1, 1, 9, 9, 9, 9, 1, 1, 9, 9],
    [9, 0, 0, 0, 9, 1, 0, 9, 0, 9, 9],
    [1, 9, 1, 1, 0, 9, 1, 9, 9, 9, 9],
    [9, 9, 9, 1, 1, 0, 1, 9, 0, 9, 9],
    [1, 0, 0, 1, 9, 9, 9, 1, 9, 9, 9],
    [1, 1, 9, 1, 1, 9, 0, 9, 9, 9, 9],
    [9, 1, 1, 9, 1, 9, 1, 9, 1, 9, 9],
    [9, 9, 9, 1, 0, 1, 0, 1, 9, 9, 9],
    [9, 9, 9, 1, 1, 1, 1, 9, 1, 9, 9],
    [9, 0, 1, 9, 0, 9, 0, 0, 0, 9, 9],
    [9, 0, 0, 9, 1, 9, 0, 0, 0, 9, 9],
    [0, 9, 0, 9, 9, 0, 0, 0, 9, 1, 9],
    [9, 0, 1, 1, 9, 9, 9, 1, 0, 9, 9],
    [1, 9, 1, 0, 1, 9, 9, 9, 0, 9, 9],
    [1, 0, 0, 0, 9, 9, 9, 0, 9, 9, 9],
    [0, 0, 9, 9, 1, 9, 1, 9, 0, 9, 9],
    [9, 0, 1, 9, 1, 1, 9, 9, 0, 9, 9],
    [9, 9, 9, 0, 0, 9, 0, 9, 1, 9, 9],
    [0, 0, 0, 9, 9, 9, 9, 9, 1, 9, 9],
    [9, 9, 9, 1, 9, 9, 9, 9, 9, 9, 0],
    [9, 9, 9, 0, 0, 9, 1, 9, 0, 9, 9],
    [9, 1, 9, 0, 9, 9, 9, 0, 0, 9, 9],
    [9, 9, 9, 9, 9, 9, 9, 1, 9, 9, 0],
    [9, 9, 9, 9, 9, 9, 9, 9, 1, 9, 0],
    [9, 9, 9, 9, 9, 9, 9, 9, 9, 0, 1],
    [9, 0, 0, 9, 0, 9, 0, 9, 1, 9, 9],
]

SymbolicCNFConstraintForSbox43 = [  # Differential PRESENT (43)
    [1, 0, 1, 9, 0, 1, 1, 9, 9],
    [9, 0, 0, 9, 1, 0, 1, 0, 9],
    [0, 9, 9, 1, 1, 1, 1, 0, 9],
    [9, 1, 0, 0, 9, 0, 1, 1, 9],
    [1, 0, 1, 9, 1, 1, 0, 0, 9],
    [1, 1, 0, 9, 0, 1, 1, 0, 9],
    [1, 1, 0, 9, 1, 1, 0, 9, 9],
    [0, 0, 1, 1, 1, 9, 0, 9, 9],
    [9, 1, 0, 1, 1, 1, 1, 9, 9],
    [9, 0, 1, 0, 1, 9, 1, 1, 9],
    [9, 1, 0, 0, 1, 1, 9, 1, 9],
    [0, 0, 0, 9, 1, 9, 1, 9, 9],
    [9, 0, 1, 0, 9, 0, 0, 1, 9],
    [9, 1, 0, 0, 0, 0, 9, 1, 9],
    [9, 1, 1, 0, 0, 9, 0, 9, 9],
    [9, 0, 1, 0, 9, 1, 1, 1, 9],
    [0, 0, 1, 9, 1, 0, 0, 9, 9],
    [9, 1, 1, 1, 1, 0, 1, 9, 9],
    [9, 0, 1, 1, 1, 1, 1, 9, 9],
    [0, 9, 0, 9, 9, 0, 0, 0, 1],
    [0, 1, 0, 9, 0, 0, 1, 9, 9],
    [0, 1, 1, 9, 0, 9, 0, 0, 9],
    [1, 1, 9, 0, 1, 9, 1, 1, 9],
    [0, 1, 0, 1, 9, 1, 1, 9, 9],
    [0, 1, 1, 9, 0, 9, 1, 1, 9],
    [9, 1, 1, 0, 1, 9, 1, 0, 9],
    [0, 1, 1, 9, 1, 9, 0, 1, 9],
    [9, 0, 0, 0, 1, 9, 9, 0, 9],
    [9, 9, 9, 9, 0, 0, 0, 0, 1],
    [9, 9, 9, 1, 0, 1, 0, 1, 9],
    [1, 9, 1, 1, 0, 9, 1, 9, 9],
    [0, 0, 9, 9, 0, 0, 9, 0, 1],
    [1, 0, 0, 1, 9, 9, 9, 1, 9],
    [1, 1, 9, 1, 1, 9, 0, 9, 9],
    [9, 0, 0, 9, 0, 9, 0, 1, 9],
    [9, 9, 9, 0, 0, 1, 0, 0, 9],
    [9, 1, 9, 9, 9, 9, 9, 9, 0],
    [0, 0, 0, 0, 9, 9, 9, 9, 1],
    [0, 0, 0, 1, 9, 9, 9, 0, 9],
    [9, 0, 0, 0, 9, 9, 1, 0, 9],
    [9, 9, 1, 9, 9, 9, 9, 9, 0],
    [9, 9, 9, 9, 9, 9, 9, 1, 0],
    [1, 9, 9, 9, 9, 9, 9, 9, 0],
]
# fmt:on
