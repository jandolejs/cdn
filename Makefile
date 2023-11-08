.DEFAULT_GOAL := start

start:
	docker compose up -d

build:
	docker compose build --no-cache && docker compose up -d --force-recreate
