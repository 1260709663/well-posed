# 本地检查入口。Windows 下若无 make，直接用 python 跑 scripts/validate_skill.py
PY ?= python

.PHONY: check validate pycompile template clean

check: validate pycompile template ## 全部检查（提交前跑这个）
	@echo "==> check 完成"

validate: ## 校验 SKILL.md 是否符合 Agent Skills 规范
	$(PY) scripts/validate_skill.py .

pycompile: ## 语法检查所有脚本
	$(PY) -m py_compile scripts/prep.py scripts/build_pdf.py scripts/validate_skill.py
	@echo "==> py_compile 通过"

template: ## 编译模板，确认 LaTeX 工具链可用
	@mkdir -p build
	$(PY) scripts/build_pdf.py assets/template.tex --out build/template.pdf

clean: ## 清理构建产物
	rm -rf build scripts/__pycache__
