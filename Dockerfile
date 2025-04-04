FROM alpine

ARG PY=python3

# set some pathing variable so the user can change as needed
ENV APP=/app

COPY ./requirements.txt /tmp/requirements.txt

# configure python
RUN apk add --no-cache python3 py3-pip
RUN $PY -m venv /venv
RUN source /venv/bin/activate && $PY -m pip install -r /tmp/requirements.txt

# add the source directory to the python path
ENV PYTHONPATH=$APP/src:$APP/test

WORKDIR $APP/test

# run the tests
ENTRYPOINT ["/venv/bin/python"]
CMD ["-m", "pytest", "--html=$APP/report.html"]

