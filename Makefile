lint:
	isort scripts server api_tests integration_tests
	black -l 80 scripts server api_tests integration_tests
	flake8 --config setup.cfg scripts server api_tests integration_tests
	mypy scripts server api_tests integration_tests

# CI test commands
ci-test:
	isort scripts server api_tests integration_tests
	black -l 80 scripts server api_tests integration_tests
	flake8 --config setup.cfg scripts server api_tests integration_tests
	mypy scripts server api_tests integration_tests
	#pytest --cov=solution tests/
	# use a separate docker-compose-ci-test file to
	API_RUN_LOCATION=test DEPLOY_ENV=local PRODUCT_PREFIX=uniframe docker-compose -f docker-compose-ci-test.yml up -d --build
	sleep 5  # wait 5 second so that docker containers in a stable status
	API_RUN_LOCATION=test docker-compose exec server /bin/bash -c 'pytest -vv api_tests'
	API_RUN_LOCATION=test docker-compose exec server /bin/bash -c 'behave integration_tests/ --capture-stderr'	
	docker-compose down --volume

# only run FastAPI server
api:
	uvicorn server.api.main:app --reload 	

# run local backend server in docker
# move the two commands into server docker container
#	# docker-compose exec db /bin/bash ./init-database.sh
#	# docker-compose exec server /bin/bash -c 'alembic upgrade head'
docker-backend:
	IMAGE_BUILD_DATE=2022-10-22-2-2 DEPLOY_ENV=dev PRODUCT_PREFIX=uniframe API_RUN_LOCATION=local docker-compose -f docker-compose.yml up -d --build server rq_worker_batch rq_worker_realtime 
	docker-compose logs -f
