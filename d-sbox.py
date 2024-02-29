from common import *

SymbolicCNFConstraintForSbox = SymbolicCNFConstraintForSbox43


tf = open(TIME_OUT, "a")
countSbox = InitialLowerBound
tick("total")
for round in range(SearchRoundStart, SearchRoundEnd):
    tick("round")
    matsuiRoundIndex, matsuiCount = matsui(round)
    while True:
        cnfbuilder(
            round,
            countSbox,
            matsuiRoundIndex,
            matsuiCount,
            SymbolicCNFConstraintForSbox,
            f"R{round}-A{countSbox}.cnf",
        )
        tick("sat")
        flag = satsolver(f"R{round}-A{countSbox}.cnf", f"R{round}-A{countSbox}.out")
        tick("sat")
        log(f"\tRound: {round}; Active: {countSbox:2}; {flag:1}; Cost: {cost('sat')}")
        countSbox += 1
        if flag:
            break
    DiffActiveSbox[round] = countSbox - 1
    tick("round")
    tf.write(f"Round: {round}; Active: {countSbox - 1}; Cost: {cost('round')}\n")
tick("total")


tf.write(f"Total Runtime: {cost('total')}\n\n")
tf.close()
log(DiffActiveSbox)
log(f"Total Runtime: {cost('total')}")
