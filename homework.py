import logging
import os
import requests
import sys
import telegram
import time


from requests.exceptions import RequestException
from http import HTTPStatus
from dotenv import load_dotenv

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
    """Проверка доступности переменных окружения"""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствут обязательные переменные.')
        sys.exit()
    else:
        return True


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': (timestamp)}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except RequestException as error:
        raise ConnectionError(f'Ошибка при запросе к основному API: {error}'
                              ) from error

    if response.status_code != HTTPStatus.OK:
        raise ConnectionError(f'Сайт недоступен: {response.status_code}')

    response = response.json()
    return response


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

    homework = response['homeworks']
    return homework


def parse_status(homework):
    """Извлечение статуса домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError('Ответ API - не словарь.')
    if 'homework_name' not in homework:
        raise KeyError('Переменная homework_name отсутствует')
    homework_name = homework['homework_name']

    if 'status' not in homework:
        raise KeyError('Переменная status отсутствует')
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
    if not check_tokens():
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response['homeworks']:
                homework = response['homeworks'][0]
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
# У меня вопрос: я не нашла исключение, если ВДРУГ рухнул сервер,
# что бы тоже Бот успел отправить сообщение.
# Как это сделать?
