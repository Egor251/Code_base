FROM python:3.9

ADD .env /server/
ADD requirements.txt /server/
ADD data_structure.py /server/
ADD email_sender.py /server/
ADD main.py /server/



WORKDIR /server/

RUN pip install -r requirements.txt