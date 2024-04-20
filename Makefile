clean:
	rm *.out *.cnf

fmt:
	flynt -ll 200 -tc *.py
	isort ./*.py
	black ./*.py

benchmark: cadical cryptominisat kissat glucose-syrup lingeling maplesat

cadical cryptominisat kissat glucose-syrup lingeling maplesat:
	python src/main.py -s $@
	# python src/main.py -s $@ -p
	# python src/main.py -s $@ -l
	# python src/main.py -s $@ -l -p
