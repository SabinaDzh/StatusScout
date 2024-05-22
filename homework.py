import logging
import os
import time
import sys
from http import HTTPStatus

import requests
from telebot import TeleBot
from telebot.apihelper import ApiException
from dotenv import load_dotenv

from exceptions import HomeworkVerdictNotFound

load_dotenv()


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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(funcName)s - '
    '%(lineno)d - %(levelname)s - %(message)s')
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
handler.setFormatter(formatter)


def check_tokens():
    """Проверяем доступность всех переменных окружения."""
    env_token = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    missing_tokens = [
        name_token for name_token, token in env_token.items()
        if token is None]
    if missing_tokens:
        text = f'Отсутствуют переменные окружения: {", ".join(missing_tokens)}'
        logger.critical(f'{text}. Работа программы завершена')
        raise AssertionError(text)


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение успешно отправлено: {message}')
    except ApiException as error:
        logger.error(
            f'Ошибка при отправке сообщения: {error}'
        )


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    from_date = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=from_date)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(
            f'Запрос к {ENDPOINT} с параметрами {timestamp} '
            f'провалился с ошибкой {error}')
    if response.status_code != HTTPStatus.OK:
        raise ValueError(f'Ошибка ответа API. Код: {response.status_code},'
                         f' причина: {response.reason}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие ожидаемым типам данных."""
    logger.info('Начало проверки запроса API')
    if not isinstance(response, dict):
        raise TypeError(f'Неверный тип ответа API {type(response)}')
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ homeworks в ответе API')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError(f'Неверный тип ответа API '
                        f'{type(response.get("homeworks"))}. Ожидается: list')
    if response.get('current_date') is None:
        raise KeyError('Отсутствует ключ current_date в ответе API')
    logger.info('Проверка успешно завершена')
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    logger.info('Начало проверки статуса работы')
    if 'homework_name' not in homework:
        raise KeyError(
            'Неверный статус домашней работы: нет ключа "homework_name"'
        )
    homework_name = homework['homework_name']
    if homework['status'] is not None:
        verdict = HOMEWORK_VERDICTS.get(homework['status'])
        if not verdict:
            raise HomeworkVerdictNotFound(f'Не найден статус домашней работы'
                                          f' {homework["status"]}')
    logger.info('Проверка успешно завершена')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
                last_message = message
            else:
                logging.debug('Статус домашнего задания не изменился')
            timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != last_message:
                send_message(bot, message)
                last_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
