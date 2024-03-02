import os
from subprocess import DEVNULL, PIPE, Popen

from const import *
from utils import *

GroupConstraintChoice = 1
GroupNumForChoice1 = 1  # Parameters for choice 1

FullRound = 32
# DiffActiveSbox = FullRound * [0]
# DifferentialProbabilityBound = FullRound * [0]
Result = FullRound * [0]


VERBOSE = 1
SATOUTPUT = 1
log = print if VERBOSE else lambda *_: None

MATSUI = "MatsuiCondition.out"


SOLVER = {
    "cadical": [os.path.expanduser("~/b/cadical/build/cadical"), "-q"],
    "cryptominisat": [os.path.expanduser("~/b/cryptominisat/build/cryptominisat5")],
    "kissat": [os.path.expanduser("~/b/kissat/build/kissat"), "-q"],
}

SBVA = os.path.expanduser("~/b/SBVA/sbva")


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
            print("unkown solver error")
            exit(child.returncode)

    return satsolver


def reduce_by_sbva(filename):
    out, _ = Popen([SBVA, "-i", filename], stdout=PIPE).communicate()
    with open(filename, "wb") as f:
        f.write(out)


def clause_counter(round, activeSbox, matsuiRoundIndex, matsuiCount, box):

    def CountClausesInRoundFunction(round):
        return 1 + round * 16 * len(box)

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
            activeSbox - Result[StartRound] - Result[round - EndRound]
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
    with open(MATSUI, "a") as file:
        resultseq = f"Round: {round}; Partial Constraint Num: {matsuiCount}\n"
        file.write(resultseq)
        file.write(f"{matsuiRoundIndex}\n")
        log(resultseq.strip("\n"))
        log(f"{matsuiRoundIndex}")
    return matsuiRoundIndex, matsuiCount


def cnfbuilder_diff_sbox(
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
            for j in range(len(SymbolicCNFConstraintForSbox)):
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
        startRound = matsuiRoundIndex[mc][0]
        endRound = matsuiRoundIndex[mc][1]
        leftNode = 16 * startRound
        rightNode = 16 * endRound - 1
        partialCardinalityCons = (
            activeSbox - Result[startRound] - Result[round - endRound]
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
    with open(cnffile, "w") as f:
        # count_clause = clause_counter(round, activeSbox, matsuiRoundIndex, matsuiCount)
        count_clause = "".join(seq).count("\n")
        f.write(f"p cnf {count_var} {count_clause}\n")
        f.write("".join(seq))


def cnfbuilder_diff_prob(
    round,
    probability,
    matsuiRoundIndex,
    matsuiCount,
    SymbolicCNFConstraintForSbox,
    cnffile,
):
    xi = []  # 64
    p = []  # 16
    q = []
    m = []
    xo = []
    totalProb = 16 * round * 3
    count_var = 0
    var_u = []
    for i in range(round):
        xi.append(list(range(count_var, count_var + 64)))
        count_var += 64
        p.append(list(range(count_var, count_var + 16)))
        count_var += 16
        q.append(list(range(count_var, count_var + 16)))
        count_var += 16
        m.append(list(range(count_var, count_var + 16)))
        count_var += 16
    for i in range(round - 1):
        xo.append(xi[i + 1])
    xo.append(list(range(count_var, count_var + 64)))
    count_var += 64
    for i in range(totalProb - 1):
        var_u.append(range(count_var, count_var + probability))
        count_var += probability

    # Add constraints to claim nonzero input difference
    seq = []
    for i in range(64):
        seq.append(f"{xi[0][i] + 1} ")
    seq.append(f"0\n")
    # Add constraints for the round function
    for r in range(round):
        y = [xo[r][P[i]] for i in range(64)]
        for i in range(16):
            for j in range(len(SymbolicCNFConstraintForSbox)):
                X = []
                for k in range(4):
                    X.append(xi[r][4 * i + k])
                for k in range(4):
                    X.append(y[4 * i + k])
                X.append(p[r][i])
                X.append(q[r][i])
                X.append(m[r][i])
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
            mainVars.append(p[round - 1 - r][i])
            mainVars.append(q[round - 1 - r][i])
            mainVars.append(m[round - 1 - r][i])
    mainVarNum = 16 * round * 3
    cardinalityCons = probability
    seq += GenSequentialEncoding(mainVars, var_u, mainVarNum, cardinalityCons)
    # Add constraints for Matsui's strategy
    for mc in range(matsuiCount):
        startround = matsuiRoundIndex[mc][0]
        endround = matsuiRoundIndex[mc][1]
        leftNode = 16 * startround * 3
        rightNode = 16 * endround * 3 - 1
        partialCardinalityCons = (
            probability - Result[startround] - Result[round - endround]
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
    with open(cnffile, "w") as f:
        # count_clause = clause_counter(round, activeSbox, matsuiRoundIndex, matsuiCount)
        count_clause = "".join(seq).count("\n")
        f.write(f"p cnf {count_var} {count_clause}\n")
        f.write("".join(seq))


cnfbuilder_linear_sbox = cnfbuilder_diff_sbox


def cnfbuilder_linear_bias(
    round,
    probability,
    matsuiRoundIndex,
    matsuiCount,
    SymbolicCNFConstraintForSbox,
    cnffile,
):
    xi = []  # 64
    p = []  # 16
    q = []
    xo = []
    totalProb = 16 * round * 3
    count_var = 0
    var_u = []
    for i in range(round):
        xi.append(list(range(count_var, count_var + 64)))
        count_var += 64
        p.append(list(range(count_var, count_var + 16)))
        count_var += 16
        q.append(list(range(count_var, count_var + 16)))
        count_var += 16
    for i in range(round - 1):
        xo.append(xi[i + 1])
    xo.append(list(range(count_var, count_var + 64)))
    count_var += 64
    for i in range(totalProb - 1):
        var_u.append(range(count_var, count_var + probability))
        count_var += probability

    # Add constraints to claim nonzero input difference
    seq = []
    for i in range(64):
        seq.append(f"{xi[0][i] + 1} ")
    seq.append(f"0\n")
    # Add constraints for the round function
    for r in range(round):
        y = [xo[r][P[i]] for i in range(64)]
        for i in range(16):
            for j in range(len(SymbolicCNFConstraintForSbox)):
                X = []
                for k in range(4):
                    X.append(xi[r][4 * i + k])
                for k in range(4):
                    X.append(y[4 * i + k])
                X.append(p[r][i])
                X.append(q[r][i])
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
            mainVars.append(p[round - 1 - r][i])
            mainVars.append(q[round - 1 - r][i])
    mainVarNum = 16 * round * 2
    cardinalityCons = probability
    seq += GenSequentialEncoding(mainVars, var_u, mainVarNum, cardinalityCons)
    # Add constraints for Matsui's strategy
    for mc in range(matsuiCount):
        startround = matsuiRoundIndex[mc][0]
        endround = matsuiRoundIndex[mc][1]
        leftNode = 16 * startround * 2
        rightNode = 16 * endround * 2 - 1
        partialCardinalityCons = (
            probability - Result[startround] - Result[round - endround]
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
    with open(cnffile, "w") as f:
        # count_clause = clause_counter(round, activeSbox, matsuiRoundIndex, matsuiCount)
        count_clause = "".join(seq).count("\n")
        f.write(f"p cnf {count_var} {count_clause}\n")
        f.write("".join(seq))
