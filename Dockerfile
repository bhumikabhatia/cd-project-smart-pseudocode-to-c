FROM python:3.9.5-slim-buster

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install astyle -y
ADD requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

ADD converterfunc.py ./app.py
ADD astyle ./astyle
COPY .streamlitconf /root/.streamlit

EXPOSE 80

CMD [ "opyrator", "launch-ui" ,"app:C_Code_Generator", "--port", "80" ]