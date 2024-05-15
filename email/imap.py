import imaplib
import logging
import email
from email.header import decode_header
import base64
import time

my_email = 'email@yandex.ru'
my_password = '123'


def get_imap():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s:%(message)s', filename='emails.log')
    logger = logging.getLogger(__name__)
    logger.debug('Старт функции get_imap')

    def parse_mail(id):
        result, data = mail.fetch(id, "(RFC822)")   # Получаем тело письма (RFC822) для данного ID

        output_message = []

        message = email.message_from_bytes(data[0][1])

        # If the message is multipart, it basically has multiple emails inside
        # so you must extract each "submail" separately.
        '''if message.is_multipart():
            print('Multipart types:')
            for part in message.walk():
                print(f'- {part.get_content_type()}')
            multipart_payload = message.get_payload()
            #for sub_message in multipart_payload:
                # The actual text/HTML email contents, or attachment data
                #print(f'Payload\n{sub_message.get_payload()}')
        else:  # Not a multipart message, payload is simple string
            print(f'Payload\n{message.get_payload()}')'''
        # You could also use `message.iter_attachments()` to get attachments only

        for string in message.get_payload():  # Чтение содержимого
            print(str(base64.b64decode(string.get_payload()), 'utf-8'))
            output_message.append(str(base64.b64decode(string.get_payload()), 'utf-8'))

        text = message["subject"]

        message_from = []
        try:
            message_from = message["from"].split()
            if len(message_from) > 1:
                sender = message["from"].split()[1][1:-1]   # Выковыриваем адрес отправителя
            else:
                sender = message["from"].split()[0]
        except IndexError:
            sender = 'yandex'
        print(f'message_from = {message_from}')
        print(f'sender = {sender}')
        try:
            subject = decode_header(str(text))
            logger.exception('decode_header: ')
        except Exception:
            try:
                subject = str(base64.b64decode(text[10:-2]), 'utf-8')   # ЗАПОМНИТЬ СТРОКУ!! ДЕКОДИРОВАНИЕ ЗАГОЛОВКОВ ПИСЬМА!
            except Exception:
                subject = text.replace('\r', '')
                subject = subject.replace('\n', '')
                subject = subject.replace('=?UTF-8?B?', '')
                subject = subject.replace('?=', '')
                subject = subject.replace(' ', '')
                subject = str(base64.b64decode(subject), 'utf-8')

        try:
            subject = subject[0][0].decode(subject[0][1])
        except TypeError:
            subject = subject[0][0].decode('utf-8')

        return subject, sender, output_message, id_list

    while True:
        try:
            mail = imaplib.IMAP4_SSL('imap.yandex.ru')
            mail.login(my_email, my_password)
            mail.list()  # Выводит список папок в почтовом ящике.
            mail.select("inbox")  # Подключаемся к папке "входящие".
            logger.debug('Успешное подключение к почтовому ящику')
            break
        except Exception:
            logger.warning('Не удалось подключиться к почтовому ящику')
            time.sleep(300)

    result, message = mail.search(None, 'UNSEEN')

    ids = message[0]  # Получаем строку номеров писем
    id_list = ids.split()  # Разделяем ID писем

    for id in id_list:
        result = parse_mail(id)
        print(result)



