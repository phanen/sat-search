clean:
	rm *.out *.cnf

fmt:
	flynt -ll 200 -tc *.py
	isort ./*.py
	black ./*.py

benchmark:
	hyperfine --warmup 5 'python d-sbox.py'
	hyperfine --warmup 5 'python d-prob.py'
	hyperfine --warmup 5 'python l-sbox.py'
	hyperfine --warmup 5 'python l-bias.py'
