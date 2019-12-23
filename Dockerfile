FROM pypy:3

WORKDIR /usr/src/app

COPY ./app/ ./

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "pypy3" ]

CMD [ "bot.py" ]
