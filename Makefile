
PYTHON ?= python3

help:
	@echo "skills-kit: короткие команды"
	@echo ""
	@echo "  make check        check.py + lang_check.py + check_examples.py"
	@echo "  make routing-eval routing-эвалы: floor rank-1 100"
	@echo "  make drift        сверка с локальной библиотекой навыков"
	@echo "  make versions     изменённый навык обязан поднять version"
	@echo "  make test         тесты валидатора, поиска, роутинга, упаковки и установки"
	@echo "  make hooks        локальный git-хук: git config core.hooksPath .githooks"
	@echo "  make find Q=…     поиск навыка по фразе"
	@echo "  make packs        цели установки и группы навыков"
	@echo "  make verify TARGET=claude  проверка установки: навык виден в хосте"
	@echo "  make install-dry  install.sh --target all --dry-run"
	@echo "  make pack         dist/ плоской раскладкой: skills/<имя>/SKILL.md"
	@echo "  make release      dist/ + релизный zip (версия из plugin.json)"

check:
	@./scripts/check.py
	@./scripts/lang_check.py
	@./scripts/check_examples.py

test:
	@$(PYTHON) ./scripts/test_check.py
	@if [ -f ./scripts/test_install.py ]; then \
		$(PYTHON) ./scripts/test_install.py; \
	else \
		echo "scripts/test_install.py нет — пропущено"; \
	fi
	@if [ -f ./scripts/test_routing_eval.py ]; then \
		$(PYTHON) ./scripts/test_routing_eval.py; \
	else \
		echo "scripts/test_routing_eval.py нет — пропущено"; \
	fi
	@if [ -f ./scripts/test_find_skill.py ]; then \
		$(PYTHON) ./scripts/test_find_skill.py; \
	else \
		echo "scripts/test_find_skill.py нет — пропущено"; \
	fi
	@if [ -f ./scripts/test_verify_install.py ]; then \
		$(PYTHON) ./scripts/test_verify_install.py; \
	else \
		echo "scripts/test_verify_install.py нет — пропущено"; \
	fi
	@if [ -f ./scripts/test_check_examples.py ]; then \
		$(PYTHON) ./scripts/test_check_examples.py; \
	else \
		echo "scripts/test_check_examples.py нет — пропущено"; \
	fi
	@if [ -f ./scripts/test_check_versions.py ]; then \
		$(PYTHON) ./scripts/test_check_versions.py; \
	else \
		echo "scripts/test_check_versions.py нет — пропущено"; \
	fi
	@if [ -f ./scripts/test_check_drift.py ]; then \
		$(PYTHON) ./scripts/test_check_drift.py; \
	else \
		echo "scripts/test_check_drift.py нет — пропущено"; \
	fi
	@if [ -f ./scripts/test_packaging.py ]; then \
		$(PYTHON) ./scripts/test_packaging.py; \
	else \
		echo "scripts/test_packaging.py нет — пропущено"; \
	fi

routing-eval:
	@$(PYTHON) ./scripts/routing_eval.py --min-rank1 100

drift:
	@$(PYTHON) ./scripts/check_drift.py $(if $(LIBRARY),--library "$(LIBRARY)")

versions:
	@$(PYTHON) ./scripts/check_versions.py --base $(or $(BASE),origin/master)

find:
	@if [ -z "$(Q)" ]; then echo 'укажи фразу: make find Q="готово, можно коммитить?"'; exit 2; fi
	@$(PYTHON) ./scripts/find_skill.py "$(Q)"

packs:
	@./scripts/install.sh --target list

verify:
	@if [ -z "$(TARGET)" ]; then echo 'укажи цель: make verify TARGET=claude'; exit 2; fi
	@$(PYTHON) ./scripts/verify_install.py --target "$(TARGET)"

hooks:
	@chmod +x .githooks/pre-commit
	@git config core.hooksPath .githooks
	@echo "хук установлен: git config core.hooksPath .githooks"

install-dry:
	@./scripts/install.sh --target all --dry-run

pack:
	@$(PYTHON) ./scripts/pack.py --clean

release:
	@$(PYTHON) ./scripts/pack.py --release

.PHONY: help check test routing-eval drift versions hooks find packs verify install-dry pack release
