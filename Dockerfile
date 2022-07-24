FROM python:3.8-slim


ARG DEPLOY_ENV
ENV DEPLOY_ENV=${DEPLOY_ENV}
ARG PRODUCT_PREFIX
ENV PRODUCT_PREFIX=${PRODUCT_PREFIX}
ARG IMAGE_BUILD_DATE
ENV IMAGE_BUILD_DATE=${IMAGE_BUILD_DATE}

ENV API_RUN_LOCATION=local
ENV DOMAIN_NAME=localhost
ENV OAUTH2_GITHUB_CLIENT_ID=dummy1
ENV OAUTH2_GITHUB_CLIENT_SECRET=dummy2
ENV API_JWT_TOKEN_SECRET=Drmhze6EPcv0fN_81Bj-nADrmhze6EPcv0fN_81Bj-nA
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=nm
ENV K8S_REDIS_PASSWORD=abc

ENV NAME_MATCHING_HOME=/app

WORKDIR ${NAME_MATCHING_HOME}
COPY ./requirements.txt ${NAME_MATCHING_HOME}/requirements.txt

RUN apt-get update \
    && apt-get install gcc g++ libpq-dev -y \
    && apt install postgresql postgresql-contrib -y \
    && apt-get clean

RUN pip install -r ${NAME_MATCHING_HOME}/requirements.txt \
    && rm -rf /root/.cache/pip

COPY . ${NAME_MATCHING_HOME}/
RUN pip install -e ${NAME_MATCHING_HOME}/ 

