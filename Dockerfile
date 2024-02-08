FROM python:3.9-slim
LABEL maintainer="Ramtin Bagheri <bagheri.ramtin@gmail.com>"

WORKDIR /app

COPY requirements.txt requirements.txt

ENV BUILD_DEPS="build-essential" \
    APP_DEPS="curl libpq-dev"

RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" | cat > /etc/apt/apt.conf.d/10no--check-valid-until
RUN apt-get update \
  && apt-get install -y ${BUILD_DEPS} ${APP_DEPS} cron --no-install-recommends \
  && pip install -r requirements.txt \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /usr/share/doc && rm -rf /usr/share/man \
  && apt-get purge -y --auto-remove ${BUILD_DEPS} \
  && apt-get clean

COPY crontab /etc/cron.d/crontab
#
## Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/crontab
#
## Apply cron job
#RUN crontab /etc/cron.d/crontab

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

## Run the command on container startup
RUN /usr/bin/crontab /etc/cron.d/crontab
CMD ["cron", "-f"]