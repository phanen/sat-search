
benchmark: benchmark-24
benchmark-8: cadical-8 cryptominisat-8 kissat-8 glucose-syrup-8 maplesat-8
benchmark-24: cadical-24 cryptominisat-24 kissat-24 glucose-syrup-24 maplesat-24
	
# cadical cryptominisat kissat glucose-syrup lingeling maplesat treengeling glucose-simp

cadical-8 cryptominisat-8 kissat-8 glucose-syrup-8 maplesat-8:
	python src/main.py --solver $(subst -8,, $@) -s 1 -e 9 -p -l
	# python src/main.py --solver $(subst -8,, $@) -s 1 -e 9
	# python src/main.py --solver $(subst -8,, $@) -s 1 -e 9 -p

cadical-24 cryptominisat-24 kissat-24 glucose-syrup-24 maplesat-24:
	python src/main.py --solver $(subst -24,, $@) -s 1 -e 25
	python src/main.py --solver $(subst -24,, $@) -s 1 -e 25 -p
	python src/main.py --solver $(subst -24,, $@) -s 1 -e 25 -p -l

clean:
	rm *.out *.cnf

fmt:
	flynt -ll 200 -tc *.py
	isort ./*.py
	black ./*.py

