PYTHON ?= python3
OUTPUT ?= build/manual

.PHONY: all native cia check test
all: native

native:
	$(PYTHON) tools/build_native.py --output "$(OUTPUT)"

cia:
	$(PYTHON) tools/build_native.py --output "$(OUTPUT)" --cia $(if $(MAKEROM),--makerom "$(MAKEROM)")

check:
	$(PYTHON) tools/build_native.py --check

test:
	$(PYTHON) -m unittest discover -s tests -v
