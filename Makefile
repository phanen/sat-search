clean:
	rm *.out *.cnf

fmt:
	flynt -ll 200 -tc *.py
	isort ./*.py
	black ./*.py

benchmark: cadical cryptominisat kissat

cadical cryptominisat kissat:
	python main.py -s $@
	python main.py -s $@ -p
	python main.py -s $@ -l
	python main.py -s $@ -l -p
