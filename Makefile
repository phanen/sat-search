
# benchmark: benchmark-24
benchmark: benchmark-28
benchmark-8: cadical-8 cryptominisat-8 kissat-8 glucose-syrup-8 maplesat-8
benchmark-24: cadical-24 cryptominisat-24 kissat-24 glucose-syrup-24 maplesat-24
benchmark-28: cryptominisat-28 kissat-28 glucose-syrup-28 maplesat-28
	
# cadical cryptominisat kissat glucose-syrup lingeling maplesat treengeling glucose-simp
cadical-8 cryptominisat-8 kissat-8 glucose-syrup-8 maplesat-8:
	python src/main.py --solver $(subst -8,, $@) -s 1 -e 9 -p -l
	# python src/main.py --solver $(subst -8,, $@) -s 1 -e 9
	# python src/main.py --solver $(subst -8,, $@) -s 1 -e 9 -p

cadical-24 cryptominisat-24 kissat-24 glucose-syrup-24 maplesat-24:
	python src/main.py --solver $(subst -24,, $@) -s 1 -e 25
	python src/main.py --solver $(subst -24,, $@) -s 1 -e 25 -p
	python src/main.py --solver $(subst -24,, $@) -s 1 -e 25 -p -l

cadical-28 cryptominisat-28 kissat-28 glucose-syrup-28 maplesat-28:
	python src/main.py --solver $(subst -28,, $@) -s 1 -e 29
	python src/main.py --solver $(subst -28,, $@) -s 1 -e 29 -p
	python src/main.py --solver $(subst -28,, $@) -s 1 -e 29 -p -l

csv:
	@python scripts/gen_csv.py

tbl: cadical-tbl cryptominisat-tbl kissat-tbl glucose-syrup-tbl maplesat-tbl

A := 65
cadical-tbl cryptominisat-tbl kissat-tbl glucose-syrup-tbl maplesat-tbl: csv
	@printf "\subsection*{\x$(shell printf %x $A). $(subst -tbl,,$@) 模型测试数据}"
	@echo
	@cat A-$(subst -tbl,,$@).csv | rust-script scripts/gen_latex.rs -C "$(subst -tbl,,$@) 模型测试数据结果（平台 A）"
	@echo
	@cat B-$(subst -tbl,,$@).csv | rust-script scripts/gen_latex.rs -C "$(subst -tbl,,$@) 模型测试数据结果（平台 B）"
	$(eval A := $(shell echo $$(($(A) + 1))))

# @cat $(hostnamectl hostname)-$(subst -tbl,,$@).csv | rust-script scripts/gen_latex.rs

clean:
	rm *.out *.cnf

fmt:
	flynt -ll 200 -tc *.py
	isort ./*.py
	black ./*.py


