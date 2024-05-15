from email import encoders  # Модули для формирования письма
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib  # Модуль для отправки почты
import time
import logger # Модуль для логирования


SMTP_server = 'smtp.yandex.ru'
SMTP_port = '465'
my_mail = 'my_email@yandex.ru'
my_password = 'my_password'

def send_email(adr, subject, body, file=None):  # body - текст письма, adr - адрес получателя, subject - тема письма, file - файл, который нужно прикрепить к письму


    while True: # бесконечный цикл для подключения к серверу почты на случай обрыва подключения
        try:
            smtpobj = smtplib.SMTP_SSL(SMTP_server, int(SMTP_port))
            smtpobj.login(my_mail, my_password)
            break
        except Exception:
            time.sleep(300)

    sender_email = my_mail
    password = my_password

    # Создание составного сообщения и установка заголовка
    message = MIMEMultipart()
    message["From"] = sender_email  # Отправитель письма
    message["To"] = adr  # Получатель письма
    message["Subject"] = subject  # Тема письма
    message["Cc"] = ''  # вторичные получатели письма, которым направляется копия. Они видят и знают о наличии друг друга.
    message["Bcc"] = ''  # скрытые получатели письма, чьи адреса не показываются другим получателям.


    # Внесение тела письма
    message.attach(MIMEText(body, "plain"))

    if file:
        filename = file  # В той же папке что и код

        # Открытие PDF файла в бинарном режиме
        with open(filename, "rb") as attachment:
            # Заголовок письма application/octet-stream
            # Почтовый клиент обычно может загрузить это автоматически в виде вложения
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Кодирование файла под ASCII символы для отправки по почте
        encoders.encode_base64(part)

        # Внесение заголовка в виде пара/ключ к части вложения
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )

        # Внесение вложения в сообщение и конвертация сообщения в строку
        message.attach(part)
    text = message.as_string()
    logger.debug(f'Отправляется письмо {adr}')
    logger.debug(f'Отправитель: {sender_email}')
    logger.debug(f'Адресат: {adr}')
    smtpobj.sendmail(sender_email, adr, text)

    logger.exception('Send_mail error: ')
    time.sleep(30)  # При множественной отправке чтобы избежать блока сервера