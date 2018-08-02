test:
	black --check .
	py.test --cov=powerplan
