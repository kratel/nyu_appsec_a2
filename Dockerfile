FROM python:3.7
LABEL maintainer="santi.f.salas@gmail.com"

COPY requirements.txt /tmp
WORKDIR /tmp
RUN pip install --upgrade pip && \
	pip install -r requirements.txt

COPY app.py /opt/web/
COPY spell_check.out /opt/web/
COPY wordlist.txt /opt/web/
COPY spellcheckapp /opt/web/spellcheckapp

WORKDIR /opt/web

EXPOSE 5000

CMD flask run --host=0.0.0.0
