all: test lint

lint:
	pylint resilience
	pylint --disable="missing-module-docstring" \
		   --disable="missing-class-docstring" \
		   --disable="missing-function-docstring" \
		   tests

test:
	mypy resilience tests
	python -m pytest --cov-report=html --cov-report=term --cov=resilience tests -v
