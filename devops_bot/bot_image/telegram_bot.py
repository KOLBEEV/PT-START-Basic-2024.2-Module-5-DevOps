import psycopg2
import re
import os
import datetime
import logging

# logging.disable(logging.CRITICAL)

if logging.getLogger().isEnabledFor(logging.CRITICAL):
    logging.basicConfig(filename=f'log-telegram-bot-{os.path.basename(__file__)}-{datetime.datetime.now()}.txt',
                        level=logging.INFO,
                        format=' %(asctime)s - %(levelname)s - %(message)s'
                        )

logger = logging.getLogger(__name__)

import paramiko
from dotenv import load_dotenv
from pathlib import Path

from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.error import BadRequest


class DotDict(dict):
    """Позволяет обращаться к элементам словаря через точку."""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class TelegramBot:
    def __init__(self):
        logger.info(f'Start {self.__init__.__name__}')
        dotenv_path = Path('.env').resolve()
        load_dotenv(dotenv_path=dotenv_path)

        self.__tm_token = os.getenv('TM_TOKEN')
        logger.info('Get TM_TOKEN')

        self.__chat_id = os.getenv('CHAT_ID')
        logger.info('Get CHAT_ID')

        self.emails = None
        self.phones = None

        self.commands = DotDict(
                {
                        'start'             : DotDict(
                                {
                                        'command'    : 'start',
                                        'button'     : '/start',
                                        'state_point': None,
                                        'callback'   : self.command_Start,
                                        }
                                ),
                        'cancel'            : DotDict(
                                {
                                        'command'    : 'cancel',
                                        'button'     : '/cancel',
                                        'state_point': None,
                                        'callback'   : self.command_Cancel,
                                        }
                                ),
                        'help'              : DotDict(
                                {
                                        'command'    : 'help',
                                        'button'     : '/help',
                                        'state_point': None,
                                        'callback'   : self.command_Help,
                                        }
                                ),
                        'echo'              : DotDict(
                                {
                                        'command'    : 'echo',
                                        'button'     : '/echo',
                                        'state_point': None,
                                        'callback'   : self.command_Echo,
                                        }
                                ),

                        ### 1. Поиск информации в тексте и её вывод.
                        'findEmails'        : DotDict(
                                {
                                        'command'    : 'find_email',
                                        'button'     : '/find_email',
                                        'state_point': 'find_email',
                                        'callback'   : self.command_FindEmails,
                                        }
                                ),
                        'add_db_Emails'     : DotDict(
                                {
                                        'command'    : 'add_db_emails',
                                        'button'     : '/add_db_emails',
                                        'state_point': 'add_db_emails',
                                        'callback'   : self.command_Add_db_Emails,
                                        }
                                ),
                        'findPhoneNumbers'  : DotDict(
                                {
                                        'command'    : 'find_phone_number',
                                        'button'     : '/find_phone_number',
                                        'state_point': 'find_phone_number',
                                        'callback'   : self.command_FindPhoneNumbers,
                                        }
                                ),
                        'add_db_Phones'     : DotDict(
                                {
                                        'command'    : 'add_db_phones',
                                        'button'     : '/add_db_phones',
                                        'state_point': 'add_db_phones',
                                        'callback'   : self.command_Add_db_Phones,
                                        }
                                ),

                        ### 2. Проверка сложности пароля регулярным выражением.
                        'verifyPassword'    : DotDict(
                                {
                                        'command'    : 'verify_password',
                                        'button'     : '/verify_password',
                                        'state_point': 'verify_password',
                                        'callback'   : self.command_VerifyPassword,
                                        }
                                ),
                        ### 3. Мониторинг Linux-системы.

                        ## 3.1. Сбор информации о системе.

                        # 3.1.1. О релизе.
                        'getRelease'        : DotDict(
                                {
                                        'command'    : 'get_release',
                                        'button'     : '/get_release',
                                        'state_point': 'get_release',
                                        'callback'   : self.command_GetRelease,
                                        }
                                ),

                        # 3.1.2. Об архитектуры процессора, имени хоста системы и версии ядра.
                        'getUname'          : DotDict(
                                {
                                        'command'    : 'get_uname',
                                        'button'     : '/get_uname',
                                        'state_point': 'get_uname',
                                        'callback'   : self.command_GetUname,
                                        }
                                ),

                        # 3.1.3. О времени работы.
                        'getUptime'         : DotDict(
                                {
                                        'command'    : 'get_uptime',
                                        'button'     : '/get_uptime',
                                        'state_point': 'get_uptime',
                                        'callback'   : self.command_GetUptime,
                                        }
                                ),

                        ## 3.2. Сбор информации о состоянии файловой системы.
                        'getDF'             : DotDict(
                                {
                                        'command'    : 'get_df',
                                        'button'     : '/get_df',
                                        'state_point': 'get_df',
                                        'callback'   : self.command_GetDF,
                                        }
                                ),

                        ## 3.3. Сбор информации о состоянии оперативной памяти.
                        'getFree'           : DotDict(
                                {
                                        'command'    : 'get_free',
                                        'button'     : '/get_free',
                                        'state_point': 'get_free',
                                        'callback'   : self.command_GetFree,
                                        }
                                ),

                        ## 3.4. Сбор информации о производительности системы.
                        'getMpstat'         : DotDict(
                                {
                                        'command'    : 'get_mpstat',
                                        'button'     : '/get_mpstat',
                                        'state_point': 'get_mpstat',
                                        'callback'   : self.command_GetMpstat,
                                        }
                                ),

                        ## 3.5. Сбор информации о работающих в данной системе пользователях.
                        'getW'              : DotDict(
                                {
                                        'command'    : 'get_w',
                                        'button'     : '/get_w',
                                        'state_point': 'get_w',
                                        'callback'   : self.command_GetW,
                                        }
                                ),

                        ## 3.6. Сбор логов.

                        # 3.6.1. Последние 10 входов в систему.
                        'getAuths'          : DotDict(
                                {
                                        'command'    : 'get_auths',
                                        'button'     : '/get_auths',
                                        'state_point': 'get_auths',
                                        'callback'   : self.command_GetAuths,
                                        }
                                ),
                        # 3.6.2. Последние 5 критических событий.
                        'getCritical'       : DotDict(
                                {
                                        'command'    : 'get_critical',
                                        'button'     : '/get_critical',
                                        'state_point': 'get_critical',
                                        'callback'   : self.command_GetCritical,
                                        }
                                ),

                        ## 3.7 Сбор информации о запущенных процессах.
                        'getPS'             : DotDict(
                                {
                                        'command'    : 'get_ps',
                                        'button'     : '/get_ps',
                                        'state_point': 'get_ps',
                                        'callback'   : self.command_GetPS,
                                        }
                                ),

                        ## 3.8 Сбор информации об используемых портах.
                        'getSS'             : DotDict(
                                {
                                        'command'    : 'get_ss',
                                        'button'     : '/get_ss',
                                        'state_point': 'get_ss',
                                        'callback'   : self.command_GetSS,
                                        }
                                ),

                        ## 3.9 Сбор информации об установленных пакетах.
                        'getAptList'        : DotDict(
                                {
                                        'command'    : 'get_apt_list',
                                        'button'     : '/get_apt_list',
                                        'state_point': 'get_apt_list',
                                        'callback'   : self.command_GetAptList,
                                        }
                                ),
                        'getAllPackagesList': DotDict(
                                {
                                        'command'    : 'get_all_packages',
                                        'button'     : '/get_all_packages',
                                        'state_point': 'get_all_packages',
                                        'callback'   : self.command_GetAllPackagesList,
                                        }
                                ),
                        'getOnePackageInfo' : DotDict(
                                {
                                        'command'    : 'get_one_package',
                                        'button'     : '/get_one_package',
                                        'state_point': 'get_one_package',
                                        'callback'   : self.command_GetOnePackageInfo,
                                        }
                                ),
                        ## 3.10 Сбор информации о запущенных сервисах.
                        'getServices'       : DotDict(
                                {
                                        'command'    : 'get_services',
                                        'button'     : '/get_services',
                                        'state_point': 'get_services',
                                        'callback'   : self.command_GetServices,
                                        },
                                ),
                        ## 3.10 Сбор информации о запущенных сервисах.
                        'getReplLogs'       : DotDict(
                                {
                                        'command'    : 'get_repl_logs',
                                        'button'     : '/get_repl_logs',
                                        'state_point': 'get_repl_logs',
                                        'callback'   : self.command_GetReplLogs,
                                        },
                                ),
                        }
                )

        logger.info(f'Stop {self.__init__.__name__}')

    # Функция для создания кнопок основных запросов
    def keyboard_menu_main(self):
        logger.info(f'Start {self.keyboard_menu_main.__name__}')

        return ReplyKeyboardMarkup(
                [
                        [KeyboardButton(self.commands.start.button)],
                        [KeyboardButton(self.commands.help.button)],
                        [KeyboardButton(self.commands.findEmails.button)],
                        [KeyboardButton(self.commands.findPhoneNumbers.button)],
                        [KeyboardButton(self.commands.verifyPassword.button)],
                        [KeyboardButton(self.commands.getRelease.button)],
                        [KeyboardButton(self.commands.getUname.button)],
                        [KeyboardButton(self.commands.getUptime.button)],
                        [KeyboardButton(self.commands.getDF.button)],
                        [KeyboardButton(self.commands.getFree.button)],
                        [KeyboardButton(self.commands.getMpstat.button)],
                        [KeyboardButton(self.commands.getW.button)],
                        [KeyboardButton(self.commands.getAuths.button)],
                        [KeyboardButton(self.commands.getCritical.button)],
                        [KeyboardButton(self.commands.getPS.button)],
                        [KeyboardButton(self.commands.getSS.button)],
                        [KeyboardButton(self.commands.getAptList.button)],
                        [KeyboardButton(self.commands.getServices.button)],
                        [KeyboardButton(self.commands.getReplLogs.button)],
                        ], resize_keyboard=True
                )

    # Функция для создания кнопки отмены запроса
    def keyboard_menu_cancel(self):
        logger.info(f'Start {self.keyboard_menu_cancel.__name__}')
        return ReplyKeyboardMarkup(
                [
                        [KeyboardButton(self.commands.cancel.button)],
                        ], resize_keyboard=True
                )

    def keyboard_apt_packages(self):
        logger.info(f'Start {self.keyboard_apt_packages.__name__}')
        return ReplyKeyboardMarkup(
                [
                        [KeyboardButton(self.commands.getAllPackagesList.button)],
                        [KeyboardButton(self.commands.getOnePackageInfo.button)],
                        [KeyboardButton(self.commands.cancel.button)],
                        ], resize_keyboard=True
                )

    def keyboard_add_db_Emails(self):
        logger.info(f'Start {self.keyboard_add_db_Emails.__name__}')
        return ReplyKeyboardMarkup(
                [
                        [KeyboardButton(self.commands.add_db_Emails.button)],
                        [KeyboardButton(self.commands.cancel.button)],
                        ], resize_keyboard=True
                )

    def keyboard_add_db_Phones(self):
        logger.info(f'Start {self.keyboard_add_db_Phones.__name__}')
        return ReplyKeyboardMarkup(
                [
                        [KeyboardButton(self.commands.add_db_Phones.button)],
                        [KeyboardButton(self.commands.cancel.button)],
                        ], resize_keyboard=True
                )

    def command_Start(self, update: Update = None, context=None):
        logger.info(f'Start {self.command_Start.__name__}')
        if update:
            user = update.effective_user
            update.message.reply_text(
                    f'Привет, {user.full_name}!',
                    reply_markup=self.keyboard_menu_main()  # Отправляем клавиатуру с кнопками
                    )
        else:
            context.bot.send_message(
                    chat_id=self.__chat_id,
                    text="Бот запущен!",
                    reply_markup=self.keyboard_menu_main()
                    )
        logger.info(f'Stop {self.command_Start.__name__}')

    def command_Cancel(self, update: Update, context):
        logger.info(f'Start {self.command_Cancel.__name__}')
        update.message.reply_text('Запрос отменен.', reply_markup=self.keyboard_menu_main())
        logger.info(f'Stop {self.command_Cancel.__name__}')
        return ConversationHandler.END

    def command_Help(self, update: Update, context):
        logger.info(f'Start {self.command_Help.__name__}')
        text = (
                "В боте реализован функционал поиска необходимой информации и вывода её пользователю.\n"

                "1. Информация, которую бот умеет выделять из текста:\n"
                "а) Email-адреса.\n"
                "Команда: /find_email\n"
                "Найденные почтовые аккаунты могут быть добавлены в базу данных.\n"
                "б) Номера телефонов.\n"
                "Команда: /find_phone_number\n"
                "Найденные телефонные номера могут быть добавлены в базу данных.\n"

                "2. Проверка сложности пароля регулярным выражением.\n"
                "В боте реализован функционал проверки сложности пароль с использованием регулярного выражения.\n"
                "Команда: /verify_password\n"

                "3. Мониторинг Linux-системы\n"
                "Бот реализовывает функционал для мониторинга Linux системы.\n"
                "Для этого устанавливается SSH-подключение к удаленному серверу\n"
                "3.1 Сбор информации о системе:\n"
                "3.1.1 О релизе.\n"
                "Команда: /get_release\n"
                "3.1.2 Об архитектуры процессора, имени хоста системы и версии ядра.\n"
                "Команда: /get_uname\n"
                "3.1.3 О времени работы.\n"
                "Команда: /get_uptime\n"
                "3.2 Сбор информации о состоянии файловой системы.\n"
                "Команда: /get_df\n"
                "3.3 Сбор информации о состоянии оперативной памяти.\n"
                "Команда: /get_free\n"
                "3.4 Сбор информации о производительности системы.\n"
                "Команда: /get_mpstat\n"
                "3.5 Сбор информации о работающих в данной системе пользователях.\n"
                "Команда: /get_w\n"
                "3.6 Сбор логов\n"
                "3.6.1 Последние 10 входов в систему.\n"
                "Команда: /get_auths\n"
                "3.6.2 Последние 5 критических событий.\n"
                "Команда: /get_critical\n"
                "3.7 Сбор информации о запущенных процессах.\n"
                "Команда: /get_ps\n"
                "3.8 Сбор информации об используемых портах.\n"
                "Команда: /get_ss\n"
                "3.9 Сбор информации об установленных пакетах.\n"
                "Команда: /get_apt_list\n"
                "Вывод всех пакетов:\n"
                "команда: /get_apt_list, потом /get_all_packages\n"
                "Поиск информации о пакете, название которого будет запрошено у пользователя:\n"
                "команда: /get_apt_list, потом /get_one_package\n"
                "3.10 Сбор информации о запущенных сервисах.\n"
                "Команда: /get_services\n"
                "Сбор логов о репликации из /var/log/postgresql/ Master-сервера.\n"
                "Команда: /get_repl_logs\n"
        )
        update.message.reply_text(text, reply_markup=self.keyboard_menu_main())
        logger.info(f'Stop {self.command_Help.__name__}')

    def command_FindEmails(self, update: Update, context):
        """
        Бот вывод список найденных email-адресов
        """
        logger.info(f'Start {self.command_FindEmails.__name__}')
        update.message.reply_text('Введите текст для поиска email-адресов: ',
                                  reply_markup=self.keyboard_menu_cancel()
                                  # Кнопка для отмены поиска
                                  )
        logger.info(f'Stop {self.command_FindEmails.__name__}')
        return self.commands.findEmails.state_point

    def findEmails(self, update: Update, context):
        logger.info(f'Start {self.findEmails.__name__}')
        user_input = update.message.text  # Получаем текст, содержащий (или нет) email-адреса
        emailsRegex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}')  # формат email-адресов
        emailsList = emailsRegex.findall(user_input)  # Ищем номера телефонов
        if not emailsList:  # Обрабатываем случай, когда номеров телефонов нет
            update.message.reply_text('Email-адреса не найдены', reply_markup=self.keyboard_menu_cancel())
            return  # Завершаем выполнение функции
        self.emails = '\n'.join([f'{emailsList[i]}' for i in range(len(emailsList))])
        emails = '\n'.join([f'{i + 1}. {emailsList[i]}' for i in range(len(emailsList))])
        update.message.reply_text(emails, reply_markup=self.keyboard_add_db_Emails()
                                  )  # Отправляем сообщение пользователю
        logger.info(f'Stop {self.findEmails.__name__}')
        return ConversationHandler.END  # self.commands.add_db_Emails.state_point # Завершаем работу обработчика диалога

    def command_Add_db_Emails(self, update: Update, context):
        logger.info(f'Start {self.command_Add_db_Emails.__name__}')
        host = os.getenv('DB_HOST')
        logger.info('Get DB_HOST')
        port = os.getenv('DB_PORT')
        logger.info('Get DB_PORT')
        username = os.getenv('DB_USER')
        logger.info('Get DB_USER')
        password = os.getenv('DB_PASSWORD')
        logger.info('Get DB_PASSWORD')
        database = os.getenv('DB_DATABASE')
        logger.info('Get DB_DATABASE')
        connection = None
        try:
            connection = psycopg2.connect(user=username,
                                          password=password,
                                          host=host,
                                          port=port,
                                          database=database
                                          )

            cursor = connection.cursor()
            for mail in self.emails.split('\n'):
                # logger.info(f'will insert {mail}')
                cursor.execute(f"INSERT INTO Emails (mail) VALUES ('{mail}');")
            connection.commit()
            update.message.reply_text(
                    f'Данные успешно добавлены в БД',
                    reply_markup=self.keyboard_menu_main()  # Отправляем клавиатуру с кнопками
                    )
            logging.info("Команда успешно выполнена")
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Ошибка при работе с PostgreSQL: {error}")
        finally:
            if connection:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
        logger.info(f'Stop {self.command_Add_db_Emails.__name__}')
        return ConversationHandler.END

    def command_FindPhoneNumbers(self, update: Update, context):
        """
        Бот вывод список найденных номеров телефона
        """
        logger.info(f'Start {self.command_FindPhoneNumbers.__name__}')
        update.message.reply_text('Введите текст для поиска телефонных номеров: ',
                                  reply_markup=self.keyboard_menu_cancel()
                                  # Кнопка для отмены поиска
                                  )
        logger.info(f'Stop {self.command_FindPhoneNumbers.__name__}')
        return self.commands.findPhoneNumbers.state_point

    def findPhoneNumbers(self, update: Update, context):
        logger.info(f'Start {self.findPhoneNumbers.__name__}')
        user_input = update.message.text  # Получаем текст, содержащий (или нет) номера телефонов
        """
        Различные варианты записи номеров телефона.
        - 8XXXXXXXXXX,
        - 8(XXX)XXXXXXX,
        - 8 XXX XXX XX XX,
        - 8 (XXX) XXX XX XX,
        - 8-XXX-XXX-XX-XX.
        Также вместо ‘8’ на первом месте может быть ‘+7’.
        """
        phoneNumRegex = re.compile(r'(\+7|8)(\s?[(-]?\d{3}[)-]?\s?\d{3}-?\s?\d{2}-?\s?\d{2})')  # формат
        phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов
        if not phoneNumberList:  # Обрабатываем случай, когда номеров телефонов нет
            update.message.reply_text('Телефонные номера не найдены', reply_markup=self.keyboard_menu_cancel())
            return  # Завершаем выполнение функции
        self.phones = '\n'.join(
                [f'{phoneNumberList[i][0] + phoneNumberList[i][1]}' for i in range(len(phoneNumberList))]
                )
        phones = '\n'.join(
                [f'{i + 1}. {phoneNumberList[i][0] + phoneNumberList[i][1]}' for i in range(len(phoneNumberList))]
                )
        update.message.reply_text(phones, reply_markup=self.keyboard_add_db_Phones()
                                  )  # Отправляем сообщение пользователю
        logger.info(f'Stop {self.findPhoneNumbers.__name__}')
        return ConversationHandler.END  # Завершаем работу обработчика диалога

    def command_Add_db_Phones(self, update: Update, context):
        logger.info(f'Start {self.command_Add_db_Phones.__name__}')
        host = os.getenv('DB_HOST')
        logger.info('Get DB_HOST')
        port = os.getenv('DB_PORT')
        logger.info('Get DB_PORT')
        username = os.getenv('DB_USER')
        logger.info('Get DB_USER')
        password = os.getenv('DB_PASSWORD')
        logger.info('Get DB_PASSWORD')
        database = os.getenv('DB_DATABASE')
        logger.info('Get DB_DATABASE')
        connection = None
        try:
            connection = psycopg2.connect(user=username,
                                          password=password,
                                          host=host,
                                          port=port,
                                          database=database
                                          )

            cursor = connection.cursor()
            for phone in self.phones.split('\n'):
                # logger.info(f'will insert {phone}')
                cursor.execute(f"INSERT INTO Phones (phone) VALUES ('{phone}');")
            connection.commit()
            update.message.reply_text(
                    f'Данные успешно добавлены в БД',
                    reply_markup=self.keyboard_menu_main()  # Отправляем клавиатуру с кнопками
                    )
            logging.info("Команда успешно выполнена")
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Ошибка при работе с PostgreSQL: {error}")
        finally:
            if connection:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
        logger.info(f'Stop {self.command_Add_db_Phones.__name__}')
        return ConversationHandler.END

    def command_VerifyPassword(self, update: Update, context):
        """
        Бот выводит информацию о сложности пароля
        """
        logger.info(f'Start {self.command_VerifyPassword.__name__}')
        update.message.reply_text('Введите пароль для оценки сложности: ',
                                  reply_markup=self.keyboard_menu_cancel()
                                  # Кнопка для отмены поиска
                                  )
        logger.info(f'Stop {self.command_VerifyPassword.__name__}')
        return self.commands.verifyPassword.state_point

    def verifyPassword(self, update: Update, context):
        logger.info(f'Start {self.verifyPassword.__name__}')
        user_input = update.message.text  # Получаем текст, содержащий (или нет) номера телефонов

        """
        Требования к паролю:
        - Пароль должен содержать не менее восьми символов.
        - Пароль должен включать как минимум одну заглавную букву (A–Z).
        - Пароль должен включать хотя бы одну строчную букву (a–z).
        - Пароль должен включать хотя бы одну цифру (0–9).
        - Пароль должен включать хотя бы один специальный символ, такой как !@#$%^&*().
        """

        passwdRegex = re.compile(r'(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}')

        passwdList = passwdRegex.search(user_input)

        if not passwdList:  # Обрабатываем случай, когда совпадений нет
            update.message.reply_text('Пароль простой', reply_markup=self.keyboard_menu_cancel())
            return  # Завершаем выполнение функции

        update.message.reply_text('Пароль сложный', reply_markup=self.keyboard_menu_cancel()
                                  )  # Отправляем сообщение пользователю
        logger.info(f'Stop {self.verifyPassword.__name__}')
        return  # ConversationHandler.END  # Завершаем работу обработчика диалога

    def getHostInfo(self, host='RM_HOST', port='RM_PORT', username='RM_USER', password='RM_PASSWORD', command="uname"):
        logger.info(f"Start {self.getHostInfo.__name__}")
        host = os.getenv(host)
        logger.info('Get HOST')
        port = os.getenv(port)
        logger.info('Get PORT')
        username = os.getenv(username)
        logger.info('Get USER')
        password = os.getenv(password)
        logger.info('Get PASSWORD')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password, port=int(port))
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        logger.info(f"Stop {self.getHostInfo.__name__}")
        return data

    def general_TG_Output(self, update: Update, context, host_command=None, output_text=None):
        if host_command:
            logger.info(f'Start {self.general_TG_Output.__name__} && {host_command}')
        else:
            logger.info(f'Start {self.general_TG_Output.__name__} && {output_text[:100]}')
        data = self.getHostInfo(command=host_command) if host_command else output_text
        try:
            update.message.reply_text(data, reply_markup=self.keyboard_menu_main())
        except BadRequest as e:
            max_length = 4096
            parts = [data[i:i + max_length] for i in range(0, len(data), max_length)]
            for part in parts[:-1:]:
                update.message.reply_text(part)
            update.message.reply_text(parts[-1], reply_markup=self.keyboard_menu_main())
        if host_command:
            logger.info(f'Stop {self.general_TG_Output.__name__} && {host_command}')
        else:
            logger.info(f'Stop {self.general_TG_Output.__name__} && {output_text[:100]}')

    def command_GetRelease(self, update: Update, context):
        logger.info(f'Start {self.command_GetRelease.__name__}')
        self.general_TG_Output(update, context, "lsb_release -a")
        logger.info(f'Stop {self.command_GetRelease.__name__}')

    def command_GetUname(self, update: Update, context):
        logger.info(f'Start {self.command_GetUname.__name__}')
        self.general_TG_Output(update, context, "uname -nmr")
        logger.info(f'Stop {self.command_GetUname.__name__}')

    def command_GetUptime(self, update: Update, context):
        logger.info(f'Start {self.command_GetUptime.__name__}')
        self.general_TG_Output(update, context, "uptime")
        logger.info(f'Stop {self.command_GetUptime.__name__}')

    def command_GetDF(self, update: Update, context):
        logger.info(f'Start {self.command_GetDF.__name__}')
        self.general_TG_Output(update, context, "df -h")
        logger.info(f'Stop {self.command_GetDF.__name__}')

    def command_GetFree(self, update: Update, context):
        logger.info(f'Start {self.command_GetFree.__name__}')
        self.general_TG_Output(update, context, "free -h")
        logger.info(f'Stop {self.command_GetFree.__name__}')

    def command_GetMpstat(self, update: Update, context):
        logger.info(f'Start {self.command_GetMpstat.__name__}')
        self.general_TG_Output(update, context, "mpstat -P ALL 1 1")
        logger.info(f'Stop {self.command_GetMpstat.__name__}')

    def command_GetW(self, update: Update, context):
        logger.info(f'Start {self.command_GetW.__name__}')
        self.general_TG_Output(update, context, "w")
        logger.info(f'Stop {self.command_GetW.__name__}')

    def command_GetAuths(self, update: Update, context):
        logger.info(f'Start {self.command_GetAuths.__name__}')
        self.general_TG_Output(update, context, "last -n 10")
        logger.info(f'Stop {self.command_GetAuths.__name__}')

    def command_GetCritical(self, update: Update, context):
        logger.info(f'Start {self.command_GetCritical.__name__}')
        text = self.getHostInfo(command="journalctl -p crit -n 5 | grep -E '^[A-Za-z]{3} [0-9]{2}'")
        text = re.sub(r'nautilus', r'ptstart', text)
        self.general_TG_Output(update, context, None, text)
        logger.info(f'Stop {self.command_GetCritical.__name__}')

    def command_GetPS(self, update: Update, context):
        logger.info(f'Start {self.command_GetPS.__name__}')
        self.general_TG_Output(update, context, "ps aux")
        logger.info(f'Stop {self.command_GetPS.__name__}')

    def command_GetSS(self, update: Update, context):
        logger.info(f'Start {self.command_GetSS.__name__}')
        self.general_TG_Output(update, context, "ss -tuln")
        logger.info(f'Stop {self.command_GetSS.__name__}')

    def command_GetAptList(self, update: Update, context):
        logger.info(f'Start {self.command_GetAptList.__name__}')
        update.message.reply_text('Выберите опцию:', reply_markup=self.keyboard_apt_packages())
        logger.info(f'Stop {self.command_GetAptList.__name__}')
        return self.commands.getAptList.state_point

    # Команда для получения списка всех установленных пакетов
    def get_apt_list(self):
        logger.info(f'Start {self.get_apt_list.__name__}')
        text = self.getHostInfo(command="dpkg -l | cat")
        text = re.compile(r'ii\s\s([a-z:.0-9-]+)\s').findall(text)
        logger.info(f'Stop {self.get_apt_list.__name__}')
        return ', '.join(text)

    def command_GetAllPackagesList(self, update: Update, context):
        logger.info(f'Start {self.command_GetAllPackagesList.__name__}')
        self.general_TG_Output(update, context, None, self.get_apt_list())
        logger.info(f'Stop {self.command_GetAllPackagesList.__name__}')
        return ConversationHandler.END

    def command_GetOnePackageInfo(self, update: Update, context):
        logger.info(f'Start {self.command_GetOnePackageInfo.__name__}')
        update.message.reply_text('Введите название пакета:',
                                  reply_markup=self.keyboard_apt_packages()
                                  # Кнопка для отмены поиска
                                  )
        logger.info(f'Stop {self.command_GetOnePackageInfo.__name__}')
        return self.commands.getOnePackageInfo.state_point

    def getOnePackageInfo(self, update: Update, context):
        logger.info(f'Start {self.getOnePackageInfo.__name__}')
        self.general_TG_Output(update, context, f"dpkg -s {update.message.text}")
        logger.info(f'Stop {self.getOnePackageInfo.__name__}')
        return ConversationHandler.END

    def command_GetServices(self, update: Update, context):
        logger.info(f'Start {self.command_GetServices.__name__}')
        self.general_TG_Output(update, context, "systemctl list-units --type=service --state=running")
        logger.info(f'Stop {self.command_GetServices.__name__}')

    def command_GetReplLogs(self, update: Update, context):
        logger.info(f'Start {self.command_GetReplLogs.__name__}')
        command = "cat /var/log/postgresql/postgresql*.log"
        data = self.getHostInfo(host='DB_HOST', command=command).split('\n')

        date = datetime.datetime.now().strftime("%Y-%m-%d")
        main_info = set()

        for line in data:
            line = line.strip()
            try:
                groups = re.compile(fr'^({date})\s([0-9:.]+)(.*)').search(line).groups()
                info, line = list(groups[0:-1:1]), groups[-1]
                # logger.info(info)
                # logger.info(line)
                if re.compile(r'connection received').search(line):
                    # logger.info(info)
                    # logger.info(line)
                    host, port = re.compile(r'host=([0-9:.]+)\sport=([0-9]+)').search(line).groups()
                    if host and port:
                        info.append('received'.upper())
                        info.append(host)
                        info.append(port)
                        logger.info(info)
                elif re.compile(r'connection authenticated').search(line):
                    # logger.info(info)
                    # logger.info(line)
                    identity, method = re.compile(
                            r'identity="([0-9a-zA-Z_-]+)"\smethod=([0-9a-zA-Z_-]+)'
                            ).search(line).groups()
                    if identity and method:
                        info.append('authenticated'.upper())
                        info.append(identity)
                        info.append(method)
                        logger.info(info)
                elif re.compile(r'connection authorized').search(line):
                    # logger.info(info)
                    # logger.info(line)
                    user, application_name = re.compile(
                            r'user=([0-9a-zA-Z_-]+)\sapplication_name=([/0-9a-zA-Z_-]+)'
                            ).search(line).groups()
                    if user and application_name:
                        info.append('authorized'.upper())
                        info.append(user)
                        info.append(application_name)
                        logger.info(info)
                elif re.compile(r'received replication command').search(line):
                    # logger.info(info)
                    # logger.info(line)
                    command = re.compile(r'received replication command:\s(.*)').search(line).groups()[0]
                    if command:
                        info.append('command'.upper())
                        info.append(command)
                        logger.info(info)
                elif re.compile(r'disconnection').search(line):
                    # logger.info(info)
                    # logger.info(line)
                    time, user, host, port = re.compile(
                            r'time:\s([0-9:.]+)\suser=([0-9a-zA-Z_-]+)\s.*\shost=([0-9:.]+)\sport=([0-9]+)'
                            ).search(line).groups()
                    if time and user and host and port:
                        info.append('disconnection'.upper())
                        info.append(time)
                        info.append(user)
                        info.append(host)
                        info.append(port)
                        # logger.info(info)
                tpl = tuple(info)
                if len(tpl) > 2 and tpl not in main_info:
                    main_info.add(tpl)
            except AttributeError:
                continue

        main_info = list('\t'.join(tpl) for tpl in sorted(main_info, key=lambda tpl: (tpl[1], tpl[2])))
        # logger.info(main_info)
        self.general_TG_Output(update, context, None, '\n'.join(main_info))
        logger.info(f'Stop {self.command_GetReplLogs.__name__}')

    def command_Echo(self, update: Update, context):
        logger.info(f'Start {self.command_Echo.__name__}')
        update.message.reply_text(update.message.text, reply_markup=self.keyboard_menu_main())
        logger.info(f'Stop {self.command_Echo.__name__}')

    def main(self):
        logger.info(f'Start {self.main.__name__}')
        updater = Updater(self.__tm_token, use_context=True)
        # Получаем диспетчер для регистрации обработчиков
        dp = updater.dispatcher

        ## Регистрируем обработчики команд

        # Обработчик команды /start
        dp.add_handler(CommandHandler(self.commands.start.command, self.commands.start.callback))

        # Обработчик команды /help
        dp.add_handler(CommandHandler(self.commands.help.command, self.commands.help.callback))

        # Обработчик команды /findEmails
        dp.add_handler(ConversationHandler(
                entry_points=[CommandHandler(self.commands.findEmails.state_point,
                                             self.commands.findEmails.callback
                                             )],
                states={
                        self.commands.findEmails.state_point: [
                                MessageHandler(Filters.text & ~Filters.command, self.findEmails)],
                        },
                fallbacks=[CommandHandler(self.commands.cancel.command, self.commands.cancel.callback)]
                )
                )

        # Обработчик команды /add_db_Emails

        dp.add_handler(ConversationHandler(
                entry_points=[CommandHandler(self.commands.add_db_Emails.state_point,
                                             self.commands.add_db_Emails.callback
                                             )],
                states={
                        self.commands.add_db_Emails.state_point: [
                                MessageHandler(Filters.text & ~Filters.command, self.commands.add_db_Emails.callback)],
                        },
                fallbacks=[CommandHandler(self.commands.add_db_Emails.command,
                                          self.commands.add_db_Emails.callback
                                          ),
                           CommandHandler(self.commands.cancel.command, self.commands.cancel.callback)]
                )
                )

        # Обработчик команды /findPhoneNumbers
        dp.add_handler(ConversationHandler(
                entry_points=[CommandHandler(self.commands.findPhoneNumbers.state_point,
                                             self.commands.findPhoneNumbers.callback
                                             )],
                states={
                        self.commands.findPhoneNumbers.state_point: [
                                MessageHandler(Filters.text & ~Filters.command, self.findPhoneNumbers)],
                        },
                fallbacks=[CommandHandler(self.commands.cancel.command, self.commands.cancel.callback)]
                )
                )

        # Обработчик команды /add_db_Phones

        dp.add_handler(ConversationHandler(
                entry_points=[CommandHandler(self.commands.add_db_Phones.state_point,
                                             self.commands.add_db_Phones.callback
                                             )],
                states={
                        self.commands.add_db_Phones.state_point: [
                                MessageHandler(Filters.text & ~Filters.command, self.commands.add_db_Phones.callback)],
                        },
                fallbacks=[CommandHandler(self.commands.add_db_Phones.command,
                                          self.commands.add_db_Phones.callback
                                          ),
                           CommandHandler(self.commands.cancel.command, self.commands.cancel.callback)]
                )
                )

        # Обработчик команды /verifyPassword
        dp.add_handler(ConversationHandler(
                entry_points=[CommandHandler(self.commands.verifyPassword.state_point,
                                             self.commands.verifyPassword.callback
                                             )],
                states={
                        self.commands.verifyPassword.state_point: [
                                MessageHandler(Filters.text & ~Filters.command, self.verifyPassword)],
                        },
                fallbacks=[CommandHandler(self.commands.cancel.command, self.commands.cancel.callback)]
                )
                )

        # Обработчик команды /get_release
        dp.add_handler(CommandHandler(self.commands.getRelease.command, self.commands.getRelease.callback))

        # Обработчик команды /get_uname
        dp.add_handler(CommandHandler(self.commands.getUname.command, self.commands.getUname.callback))

        # Обработчик команды /get_uptime
        dp.add_handler(CommandHandler(self.commands.getUptime.command, self.commands.getUptime.callback))

        # Обработчик команды /get_df
        dp.add_handler(CommandHandler(self.commands.getDF.command, self.commands.getDF.callback))

        # Обработчик команды /get_free
        dp.add_handler(CommandHandler(self.commands.getFree.command, self.commands.getFree.callback))

        # Обработчик команды /get_mpstat
        dp.add_handler(CommandHandler(self.commands.getMpstat.command, self.commands.getMpstat.callback))

        # Обработчик команды /get_w
        dp.add_handler(CommandHandler(self.commands.getW.command, self.commands.getW.callback))

        # Обработчик команды /get_auths
        dp.add_handler(CommandHandler(self.commands.getAuths.command, self.commands.getAuths.callback))

        # Обработчик команды /get_critical
        dp.add_handler(CommandHandler(self.commands.getCritical.command, self.commands.getCritical.callback))

        # Обработчик команды /get_ps
        dp.add_handler(CommandHandler(self.commands.getPS.command, self.commands.getPS.callback))

        # Обработчик команды /get_SS
        dp.add_handler(CommandHandler(self.commands.getSS.command, self.commands.getSS.callback))

        # Обработчик команды /get_apt_list
        dp.add_handler(ConversationHandler(
                entry_points=[
                        CommandHandler(self.commands.getAptList.state_point,
                                       self.commands.getAptList.callback
                                       ),
                        ],
                states={
                        self.commands.getOnePackageInfo.state_point: [
                                MessageHandler(Filters.text & ~Filters.command, self.getOnePackageInfo)]
                        },
                fallbacks=[
                        CommandHandler(self.commands.getAllPackagesList.command,
                                       self.commands.getAllPackagesList.callback
                                       ),
                        CommandHandler(self.commands.getOnePackageInfo.command,
                                       self.commands.getOnePackageInfo.callback
                                       ),
                        CommandHandler(self.commands.cancel.command,
                                       self.commands.cancel.callback
                                       )]
                )
                )

        # Обработчик команды /get_services
        dp.add_handler(CommandHandler(self.commands.getServices.command, self.commands.getServices.callback))

        # Обработчик команды /get_rep_logs
        dp.add_handler(CommandHandler(self.commands.getReplLogs.command, self.commands.getReplLogs.callback))

        # Обработчик текстовых сообщений /echo
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.commands.echo.callback))

        # Запускаем бота
        updater.start_polling()

        # Отправляем кнопку /start автоматически при запуске бота
        self.command_Start(context=updater)

        # Останавливаем бота при нажатии Ctrl+C
        updater.idle()

        logger.info(f'Stop {self.main.__name__}')


if __name__ == '__main__':
    logger.info('Start Script')
    bot = TelegramBot()
    bot.main()
    logger.info('Stop Script')
