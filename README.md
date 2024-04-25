## sat search for `PRESENT`

Use different SAT solvers as backend to speed up differenial/linear cryptanalysis of `PRESENT`.
* sat solvers
  * cadical  https://github.com/arminbiere/cadical
  * cryptominisat https://github.com/msoos/cryptominisat
  * kissat https://github.com/arminbiere/kissat
  * glucose https://github.com/audemard/glucose
* more candidates https://satcompetition.github.io/2023/downloads/satcomp23slides.pdf
* optimizer https://github.com/hgarrereyn/SBVA


## usage
basic
For benchmark relevant purpose, refer to makefile:

```
usage: main.py [-h] --solver SOLVER [--sbva] [-p] [-l] [-s S] [-e E]

options:
  -h, --help       show this help message and exit
  --solver SOLVER
  --sbva
  -p, --prob
  -l, --linear
  -s S
  -e E
```
