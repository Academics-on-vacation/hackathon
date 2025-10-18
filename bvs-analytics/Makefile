up:
	docker-compose down
	docker-compose build
	docker-compose --env-file .env up -d
	docker-compose logs -f

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose down
	docker-compose build --no-cache
	docker-compose --env-file .env up -d
	docker-compose logs -f

clear:
	docker-compose down --rmi all --volumes --remove-orphans
