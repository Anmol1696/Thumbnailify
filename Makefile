include .env

.PHONY: all deploy worker server test-integration test-stress

all:
	docker-compose up

deploy:
	docker-compose up --scale worker=2

worker:
	python3.7 -m worker.consume

server:
	python3.7 -m server.app

test-integration:
	pytest -vv -x --tb=auto

test-stress:
	python3.7 -m locust.main -f tests/stress/tests_post_stress.py
