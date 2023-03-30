import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import RequestException

from exceptions import HTTPException

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='a'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствут обязательные переменные.')
        raise KeyError('Отсутствут обязательные переменные.')


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': (timestamp)}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except RequestException as error:
        raise ConnectionError(f'Ошибка при запросе к основному API: {error}'
                              ) from error

    if response.status_code != HTTPStatus.OK:
        code = response.status_code
        text = response.text
        details = f'Кода ответа: {code}, сообщение об ошибке: {text}'
        raise HTTPException(f'Ошибка ответа сервера. {details}')

    if response == '':
        raise TypeError('Полученные данные не содержат информации')
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API - не словарь.')

    if 'homeworks' not in response:
        raise KeyError('В ответе API нет ключа homeworks.')

    if 'current_date' not in response:
        raise KeyError('В ответе API нет ключа current_date.')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Значение ключа homeworks - не список.')

    homework = response['homeworks'][0]
    return homework


def parse_status(homework):
    """Извлечение статуса домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError('Ответ API - не словарь.')
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутствует')
    homework_name = homework['homework_name']

    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует')
    homework_status = homework['status']

    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(
            f'Неожиданный статус домашней работы: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def send_message(bot, message):
    """Отправка сообщения о статусе домашней работы."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение ушло')
    except telegram.error.TelegramError as error:
        logging.exception(f'Сообщение не отправлено: {error}.')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            bot.send_message(TELEGRAM_CHAT_ID, message)
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = response['current_date']


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.critical('Bot остановлен вручную.')
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        bot.send_message(TELEGRAM_CHAT_ID, 'Bot остановлен вручную.')
