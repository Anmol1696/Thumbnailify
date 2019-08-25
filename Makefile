include .env

.PHONY: all worker server test-integration

worker:
	python3.7 -m worker.consume

server:
	python3.7 -m server.app

test-integration:
	pytest -vv -x --tb=auto

test-stress:
	python3.7 -m locust.main -f tests/stress/tests_post_stress.py
