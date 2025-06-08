FROM python

RUN useradd --create-home --shell /bin/bash python
USER python

COPY --chown=python requirements.txt /home/python/repo/
WORKDIR /home/python/repo/
RUN pip install --no-cache-dir --requirement './requirements.txt'

COPY --chown=python src/zen_quotes/main.py /home/python/repo/src/zen_quotes/
RUN mkdir /home/python/repo/output

CMD ["python", "./src/zen_quotes/main.py"]
