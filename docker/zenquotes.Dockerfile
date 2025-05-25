FROM python

RUN useradd --create-home --shell /bin/bash python
USER python
