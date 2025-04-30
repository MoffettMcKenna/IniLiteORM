# just the shell command to execute all unit tests in Docker
docker run --rm -it --name runUnitTests --mount type=bind,source="$(pwd)",target=/app unit_tests
