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
    """ÐŸÐ¾Ð·Ð²Ð¾Ð»ÑÐµÑ‚ Ð¾Ð±Ñ€Ð°Ñ‰Ð°Ñ‚ÑŒÑÑ Ðº ÑÐ»ÐµÐ¼ÐµÐ½Ñ‚Ð°Ð¼ ÑÐ»Ð¾Ð²Ð°Ñ€Ñ Ñ‡ÐµÑ€ÐµÐ· Ñ‚Ð¾Ñ‡ÐºÑƒ."""
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

                        ### 1. ÐŸÐ¾Ð¸ÑÐº Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð² Ñ‚ÐµÐºÑÑ‚Ðµ Ð¸ ÐµÑ‘ Ð²Ñ‹Ð²Ð¾Ð´.
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

                        ### 2. ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° ÑÐ»Ð¾Ð¶Ð½Ð¾ÑÑ‚Ð¸ Ð¿Ð°Ñ€Ð¾Ð»Ñ Ñ€ÐµÐ³ÑƒÐ»ÑÑ€Ð½Ñ‹Ð¼ Ð²Ñ‹Ñ€Ð°Ð¶ÐµÐ½Ð¸ÐµÐ¼.
                        'verifyPassword'    : DotDict(
                                {
                                        'command'    : 'verify_password',
                                        'button'     : '/verify_password',
                                        'state_point': 'verify_password',
                                        'callback'   : self.command_VerifyPassword,
                                        }
                                ),
                        ### 3. ÐœÐ¾Ð½Ð¸Ñ‚Ð¾Ñ€Ð¸Ð½Ð³ Linux-ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹.

                        ## 3.1. Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ ÑÐ¸ÑÑ‚ÐµÐ¼Ðµ.

                        # 3.1.1. Ðž Ñ€ÐµÐ»Ð¸Ð·Ðµ.
                        'getRelease'        : DotDict(
                                {
                                        'command'    : 'get_release',
                                        'button'     : '/get_release',
                                        'state_point': 'get_release',
                                        'callback'   : self.command_GetRelease,
                                        }
                                ),

                        # 3.1.2. ÐžÐ± Ð°Ñ€Ñ…Ð¸Ñ‚ÐµÐºÑ‚ÑƒÑ€Ñ‹ Ð¿Ñ€Ð¾Ñ†ÐµÑÑÐ¾Ñ€Ð°, Ð¸Ð¼ÐµÐ½Ð¸ Ñ…Ð¾ÑÑ‚Ð° ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹ Ð¸ Ð²ÐµÑ€ÑÐ¸Ð¸ ÑÐ´Ñ€Ð°.
                        'getUname'          : DotDict(
                                {
                                        'command'    : 'get_uname',
                                        'button'     : '/get_uname',
                                        'state_point': 'get_uname',
                                        'callback'   : self.command_GetUname,
                                        }
                                ),

                        # 3.1.3. Ðž Ð²Ñ€ÐµÐ¼ÐµÐ½Ð¸ Ñ€Ð°Ð±Ð¾Ñ‚Ñ‹.
                        'getUptime'         : DotDict(
                                {
                                        'command'    : 'get_uptime',
                                        'button'     : '/get_uptime',
                                        'state_point': 'get_uptime',
                                        'callback'   : self.command_GetUptime,
                                        }
                                ),

                        ## 3.2. Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ ÑÐ¾ÑÑ‚Ð¾ÑÐ½Ð¸Ð¸ Ñ„Ð°Ð¹Ð»Ð¾Ð²Ð¾Ð¹ ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹.
                        'getDF'             : DotDict(
                                {
                                        'command'    : 'get_df',
                                        'button'     : '/get_df',
                                        'state_point': 'get_df',
                                        'callback'   : self.command_GetDF,
                                        }
                                ),

                        ## 3.3. Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ ÑÐ¾ÑÑ‚Ð¾ÑÐ½Ð¸Ð¸ Ð¾Ð¿ÐµÑ€Ð°Ñ‚Ð¸Ð²Ð½Ð¾Ð¹ Ð¿Ð°Ð¼ÑÑ‚Ð¸.
                        'getFree'           : DotDict(
                                {
                                        'command'    : 'get_free',
                                        'button'     : '/get_free',
                                        'state_point': 'get_free',
                                        'callback'   : self.command_GetFree,
                                        }
                                ),

                        ## 3.4. Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ð¿Ñ€Ð¾Ð¸Ð·Ð²Ð¾Ð´Ð¸Ñ‚ÐµÐ»ÑŒÐ½Ð¾ÑÑ‚Ð¸ ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹.
                        'getMpstat'         : DotDict(
                                {
                                        'command'    : 'get_mpstat',
                                        'button'     : '/get_mpstat',
                                        'state_point': 'get_mpstat',
                                        'callback'   : self.command_GetMpstat,
                                        }
                                ),

                        ## 3.5. Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ñ€Ð°Ð±Ð¾Ñ‚Ð°ÑŽÑ‰Ð¸Ñ… Ð² Ð´Ð°Ð½Ð½Ð¾Ð¹ ÑÐ¸ÑÑ‚ÐµÐ¼Ðµ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑÑ….
                        'getW'              : DotDict(
                                {
                                        'command'    : 'get_w',
                                        'button'     : '/get_w',
                                        'state_point': 'get_w',
                                        'callback'   : self.command_GetW,
                                        }
                                ),

                        ## 3.6. Ð¡Ð±Ð¾Ñ€ Ð»Ð¾Ð³Ð¾Ð².

                        # 3.6.1. ÐŸÐ¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ 10 Ð²Ñ…Ð¾Ð´Ð¾Ð² Ð² ÑÐ¸ÑÑ‚ÐµÐ¼Ñƒ.
                        'getAuths'          : DotDict(
                                {
                                        'command'    : 'get_auths',
                                        'button'     : '/get_auths',
                                        'state_point': 'get_auths',
                                        'callback'   : self.command_GetAuths,
                                        }
                                ),
                        # 3.6.2. ÐŸÐ¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ 5 ÐºÑ€Ð¸Ñ‚Ð¸Ñ‡ÐµÑÐºÐ¸Ñ… ÑÐ¾Ð±Ñ‹Ñ‚Ð¸Ð¹.
                        'getCritical'       : DotDict(
                                {
                                        'command'    : 'get_critical',
                                        'button'     : '/get_critical',
                                        'state_point': 'get_critical',
                                        'callback'   : self.command_GetCritical,
                                        }
                                ),

                        ## 3.7 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ð·Ð°Ð¿ÑƒÑ‰ÐµÐ½Ð½Ñ‹Ñ… Ð¿Ñ€Ð¾Ñ†ÐµÑÑÐ°Ñ….
                        'getPS'             : DotDict(
                                {
                                        'command'    : 'get_ps',
                                        'button'     : '/get_ps',
                                        'state_point': 'get_ps',
                                        'callback'   : self.command_GetPS,
                                        }
                                ),

                        ## 3.8 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾Ð± Ð¸ÑÐ¿Ð¾Ð»ÑŒÐ·ÑƒÐµÐ¼Ñ‹Ñ… Ð¿Ð¾Ñ€Ñ‚Ð°Ñ….
                        'getSS'             : DotDict(
                                {
                                        'command'    : 'get_ss',
                                        'button'     : '/get_ss',
                                        'state_point': 'get_ss',
                                        'callback'   : self.command_GetSS,
                                        }
                                ),

                        ## 3.9 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾Ð± ÑƒÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½Ð½Ñ‹Ñ… Ð¿Ð°ÐºÐµÑ‚Ð°Ñ….
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
                        ## 3.10 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ð·Ð°Ð¿ÑƒÑ‰ÐµÐ½Ð½Ñ‹Ñ… ÑÐµÑ€Ð²Ð¸ÑÐ°Ñ….
                        'getServices'       : DotDict(
                                {
                                        'command'    : 'get_services',
                                        'button'     : '/get_services',
                                        'state_point': 'get_services',
                                        'callback'   : self.command_GetServices,
                                        },
                                ),
                        ## Ð¡Ð±Ð¾Ñ€ Ð»Ð¾Ð³Ð¾Ð² Ð¾ Ñ€ÐµÐ¿Ð»Ð¸ÐºÐ°Ñ†Ð¸Ð¸ Ð¸Ð· /var/log/postgresql/ Master-ÑÐµÑ€Ð²ÐµÑ€Ð°..
                        'getReplLogs'       : DotDict(
                                {
                                        'command'    : 'get_repl_logs',
                                        'button'     : '/get_repl_logs',
                                        'state_point': 'get_repl_logs',
                                        'callback'   : self.command_GetReplLogs,
                                        },
                                ),
                        'getEmails'       : DotDict(
                                {
                                        'command'    : 'get_emails',
                                        'button'     : '/get_emails',
                                        'state_point': 'get_emails',
                                        'callback'   : self.command_GetEmails,
                                        },
                                ),
                        'getPhones'       : DotDict(
                                {
                                        'command'    : 'get_phones',
                                        'button'     : '/get_phones',
                                        'state_point': 'get_phones',
                                        'callback'   : self.command_GetPhones,
                                        },
                                ),
                        }
                )

        logger.info(f'Stop {self.__init__.__name__}')

    # Ð¤ÑƒÐ½ÐºÑ†Ð¸Ñ Ð´Ð»Ñ ÑÐ¾Ð·Ð´Ð°Ð½Ð¸Ñ ÐºÐ½Ð¾Ð¿Ð¾Ðº Ð¾ÑÐ½Ð¾Ð²Ð½Ñ‹Ñ… Ð·Ð°Ð¿Ñ€Ð¾ÑÐ¾Ð²
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
                        [KeyboardButton(self.commands.getEmails.button)],
                        [KeyboardButton(self.commands.getPhones.button)],
                        ], resize_keyboard=True
                )

    # Ð¤ÑƒÐ½ÐºÑ†Ð¸Ñ Ð´Ð»Ñ ÑÐ¾Ð·Ð´Ð°Ð½Ð¸Ñ ÐºÐ½Ð¾Ð¿ÐºÐ¸ Ð¾Ñ‚Ð¼ÐµÐ½Ñ‹ Ð·Ð°Ð¿Ñ€Ð¾ÑÐ°
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
                    f'ÐŸÑ€Ð¸Ð²ÐµÑ‚, {user.full_name}!',
                    reply_markup=self.keyboard_menu_main()  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÐºÐ»Ð°Ð²Ð¸Ð°Ñ‚ÑƒÑ€Ñƒ Ñ ÐºÐ½Ð¾Ð¿ÐºÐ°Ð¼Ð¸
                    )
        else:
            context.bot.send_message(
                    chat_id=self.__chat_id,
                    text="Ð‘Ð¾Ñ‚ Ð·Ð°Ð¿ÑƒÑ‰ÐµÐ½!",
                    reply_markup=self.keyboard_menu_main()
                    )
        logger.info(f'Stop {self.command_Start.__name__}')

    def command_Cancel(self, update: Update, context):
        logger.info(f'Start {self.command_Cancel.__name__}')
        update.message.reply_text('Ð—Ð°Ð¿Ñ€Ð¾Ñ Ð¾Ñ‚Ð¼ÐµÐ½ÐµÐ½.', reply_markup=self.keyboard_menu_main())
        logger.info(f'Stop {self.command_Cancel.__name__}')
        return ConversationHandler.END

    def command_Help(self, update: Update, context):
        logger.info(f'Start {self.command_Help.__name__}')
        text = (
                "Ð’ Ð±Ð¾Ñ‚Ðµ Ñ€ÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°Ð½ Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¾Ð½Ð°Ð» Ð¿Ð¾Ð¸ÑÐºÐ° Ð½ÐµÐ¾Ð±Ñ…Ð¾Ð´Ð¸Ð¼Ð¾Ð¹ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¸ Ð²Ñ‹Ð²Ð¾Ð´Ð° ÐµÑ‘ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑŽ.\n"

                "1. Ð˜Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ñ, ÐºÐ¾Ñ‚Ð¾Ñ€ÑƒÑŽ Ð±Ð¾Ñ‚ ÑƒÐ¼ÐµÐµÑ‚ Ð²Ñ‹Ð´ÐµÐ»ÑÑ‚ÑŒ Ð¸Ð· Ñ‚ÐµÐºÑÑ‚Ð°:\n"
                "Ð°) Email-Ð°Ð´Ñ€ÐµÑÐ°.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /find_email\n"
                "ÐÐ°Ð¹Ð´ÐµÐ½Ð½Ñ‹Ðµ Ð¿Ð¾Ñ‡Ñ‚Ð¾Ð²Ñ‹Ðµ Ð°ÐºÐºÐ°ÑƒÐ½Ñ‚Ñ‹ Ð¼Ð¾Ð³ÑƒÑ‚ Ð±Ñ‹Ñ‚ÑŒ Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ñ‹ Ð² Ð±Ð°Ð·Ñƒ Ð´Ð°Ð½Ð½Ñ‹Ñ….\n"
                "Ð±) ÐÐ¾Ð¼ÐµÑ€Ð° Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð¾Ð².\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /find_phone_number\n"
                "ÐÐ°Ð¹Ð´ÐµÐ½Ð½Ñ‹Ðµ Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð½Ñ‹Ðµ Ð½Ð¾Ð¼ÐµÑ€Ð° Ð¼Ð¾Ð³ÑƒÑ‚ Ð±Ñ‹Ñ‚ÑŒ Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ñ‹ Ð² Ð±Ð°Ð·Ñƒ Ð´Ð°Ð½Ð½Ñ‹Ñ….\n"

                "2. ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° ÑÐ»Ð¾Ð¶Ð½Ð¾ÑÑ‚Ð¸ Ð¿Ð°Ñ€Ð¾Ð»Ñ Ñ€ÐµÐ³ÑƒÐ»ÑÑ€Ð½Ñ‹Ð¼ Ð²Ñ‹Ñ€Ð°Ð¶ÐµÐ½Ð¸ÐµÐ¼.\n"
                "Ð’ Ð±Ð¾Ñ‚Ðµ Ñ€ÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°Ð½ Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¾Ð½Ð°Ð» Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ¸ ÑÐ»Ð¾Ð¶Ð½Ð¾ÑÑ‚Ð¸ Ð¿Ð°Ñ€Ð¾Ð»ÑŒ Ñ Ð¸ÑÐ¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ð½Ð¸ÐµÐ¼ Ñ€ÐµÐ³ÑƒÐ»ÑÑ€Ð½Ð¾Ð³Ð¾ Ð²Ñ‹Ñ€Ð°Ð¶ÐµÐ½Ð¸Ñ.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /verify_password\n"

                "3. ÐœÐ¾Ð½Ð¸Ñ‚Ð¾Ñ€Ð¸Ð½Ð³ Linux-ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹\n"
                "Ð‘Ð¾Ñ‚ Ñ€ÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ñ‹Ð²Ð°ÐµÑ‚ Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¾Ð½Ð°Ð» Ð´Ð»Ñ Ð¼Ð¾Ð½Ð¸Ñ‚Ð¾Ñ€Ð¸Ð½Ð³Ð° Linux ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹.\n"
                "Ð”Ð»Ñ ÑÑ‚Ð¾Ð³Ð¾ ÑƒÑÑ‚Ð°Ð½Ð°Ð²Ð»Ð¸Ð²Ð°ÐµÑ‚ÑÑ SSH-Ð¿Ð¾Ð´ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ðµ Ðº ÑƒÐ´Ð°Ð»ÐµÐ½Ð½Ð¾Ð¼Ñƒ ÑÐµÑ€Ð²ÐµÑ€Ñƒ\n"
                "3.1 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ ÑÐ¸ÑÑ‚ÐµÐ¼Ðµ:\n"
                "3.1.1 Ðž Ñ€ÐµÐ»Ð¸Ð·Ðµ.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_release\n"
                "3.1.2 ÐžÐ± Ð°Ñ€Ñ…Ð¸Ñ‚ÐµÐºÑ‚ÑƒÑ€Ñ‹ Ð¿Ñ€Ð¾Ñ†ÐµÑÑÐ¾Ñ€Ð°, Ð¸Ð¼ÐµÐ½Ð¸ Ñ…Ð¾ÑÑ‚Ð° ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹ Ð¸ Ð²ÐµÑ€ÑÐ¸Ð¸ ÑÐ´Ñ€Ð°.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_uname\n"
                "3.1.3 Ðž Ð²Ñ€ÐµÐ¼ÐµÐ½Ð¸ Ñ€Ð°Ð±Ð¾Ñ‚Ñ‹.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_uptime\n"
                "3.2 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ ÑÐ¾ÑÑ‚Ð¾ÑÐ½Ð¸Ð¸ Ñ„Ð°Ð¹Ð»Ð¾Ð²Ð¾Ð¹ ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_df\n"
                "3.3 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ ÑÐ¾ÑÑ‚Ð¾ÑÐ½Ð¸Ð¸ Ð¾Ð¿ÐµÑ€Ð°Ñ‚Ð¸Ð²Ð½Ð¾Ð¹ Ð¿Ð°Ð¼ÑÑ‚Ð¸.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_free\n"
                "3.4 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ð¿Ñ€Ð¾Ð¸Ð·Ð²Ð¾Ð´Ð¸Ñ‚ÐµÐ»ÑŒÐ½Ð¾ÑÑ‚Ð¸ ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_mpstat\n"
                "3.5 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ñ€Ð°Ð±Ð¾Ñ‚Ð°ÑŽÑ‰Ð¸Ñ… Ð² Ð´Ð°Ð½Ð½Ð¾Ð¹ ÑÐ¸ÑÑ‚ÐµÐ¼Ðµ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑÑ….\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_w\n"
                "3.6 Ð¡Ð±Ð¾Ñ€ Ð»Ð¾Ð³Ð¾Ð²\n"
                "3.6.1 ÐŸÐ¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ 10 Ð²Ñ…Ð¾Ð´Ð¾Ð² Ð² ÑÐ¸ÑÑ‚ÐµÐ¼Ñƒ.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_auths\n"
                "3.6.2 ÐŸÐ¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ 5 ÐºÑ€Ð¸Ñ‚Ð¸Ñ‡ÐµÑÐºÐ¸Ñ… ÑÐ¾Ð±Ñ‹Ñ‚Ð¸Ð¹.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_critical\n"
                "3.7 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ð·Ð°Ð¿ÑƒÑ‰ÐµÐ½Ð½Ñ‹Ñ… Ð¿Ñ€Ð¾Ñ†ÐµÑÑÐ°Ñ….\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_ps\n"
                "3.8 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾Ð± Ð¸ÑÐ¿Ð¾Ð»ÑŒÐ·ÑƒÐµÐ¼Ñ‹Ñ… Ð¿Ð¾Ñ€Ñ‚Ð°Ñ….\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_ss\n"
                "3.9 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾Ð± ÑƒÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½Ð½Ñ‹Ñ… Ð¿Ð°ÐºÐµÑ‚Ð°Ñ….\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_apt_list\n"
                "Ð’Ñ‹Ð²Ð¾Ð´ Ð²ÑÐµÑ… Ð¿Ð°ÐºÐµÑ‚Ð¾Ð²:\n"
                "ÐºÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_apt_list, Ð¿Ð¾Ñ‚Ð¾Ð¼ /get_all_packages\n"
                "ÐŸÐ¾Ð¸ÑÐº Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ð¿Ð°ÐºÐµÑ‚Ðµ, Ð½Ð°Ð·Ð²Ð°Ð½Ð¸Ðµ ÐºÐ¾Ñ‚Ð¾Ñ€Ð¾Ð³Ð¾ Ð±ÑƒÐ´ÐµÑ‚ Ð·Ð°Ð¿Ñ€Ð¾ÑˆÐµÐ½Ð¾ Ñƒ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»Ñ:\n"
                "ÐºÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_apt_list, Ð¿Ð¾Ñ‚Ð¾Ð¼ /get_one_package\n"
                "3.10 Ð¡Ð±Ð¾Ñ€ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸ Ð¾ Ð·Ð°Ð¿ÑƒÑ‰ÐµÐ½Ð½Ñ‹Ñ… ÑÐµÑ€Ð²Ð¸ÑÐ°Ñ….\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_services\n"
                "Ð¡Ð±Ð¾Ñ€ Ð»Ð¾Ð³Ð¾Ð² Ð¾ Ñ€ÐµÐ¿Ð»Ð¸ÐºÐ°Ñ†Ð¸Ð¸ Ð¸Ð· /var/log/postgresql/ Master-ÑÐµÑ€Ð²ÐµÑ€Ð°.\n"
                "ÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /get_repl_logs\n"
        )
        update.message.reply_text(text, reply_markup=self.keyboard_menu_main())
        logger.info(f'Stop {self.command_Help.__name__}')

    def command_FindEmails(self, update: Update, context):
        """
        Ð‘Ð¾Ñ‚ Ð²Ñ‹Ð²Ð¾Ð´ ÑÐ¿Ð¸ÑÐ¾Ðº Ð½Ð°Ð¹Ð´ÐµÐ½Ð½Ñ‹Ñ… email-Ð°Ð´Ñ€ÐµÑÐ¾Ð²
        """
        logger.info(f'Start {self.command_FindEmails.__name__}')
        update.message.reply_text('Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ñ‚ÐµÐºÑÑ‚ Ð´Ð»Ñ Ð¿Ð¾Ð¸ÑÐºÐ° email-Ð°Ð´Ñ€ÐµÑÐ¾Ð²: ',
                                  reply_markup=self.keyboard_menu_cancel()
                                  # ÐšÐ½Ð¾Ð¿ÐºÐ° Ð´Ð»Ñ Ð¾Ñ‚Ð¼ÐµÐ½Ñ‹ Ð¿Ð¾Ð¸ÑÐºÐ°
                                  )
        logger.info(f'Stop {self.command_FindEmails.__name__}')
        return self.commands.findEmails.state_point

    def findEmails(self, update: Update, context):
        logger.info(f'Start {self.findEmails.__name__}')
        user_input = update.message.text  # ÐŸÐ¾Ð»ÑƒÑ‡Ð°ÐµÐ¼ Ñ‚ÐµÐºÑÑ‚, ÑÐ¾Ð´ÐµÑ€Ð¶Ð°Ñ‰Ð¸Ð¹ (Ð¸Ð»Ð¸ Ð½ÐµÑ‚) email-Ð°Ð´Ñ€ÐµÑÐ°
        emailsRegex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}')  # Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚ email-Ð°Ð´Ñ€ÐµÑÐ¾Ð²
        emailsList = emailsRegex.findall(user_input)  # Ð˜Ñ‰ÐµÐ¼ Ð½Ð¾Ð¼ÐµÑ€Ð° Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð¾Ð²
        if not emailsList:  # ÐžÐ±Ñ€Ð°Ð±Ð°Ñ‚Ñ‹Ð²Ð°ÐµÐ¼ ÑÐ»ÑƒÑ‡Ð°Ð¹, ÐºÐ¾Ð³Ð´Ð° Ð½Ð¾Ð¼ÐµÑ€Ð¾Ð² Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð¾Ð² Ð½ÐµÑ‚
            update.message.reply_text('Email-Ð°Ð´Ñ€ÐµÑÐ° Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½Ñ‹', reply_markup=self.keyboard_menu_cancel())
            return  # Ð—Ð°Ð²ÐµÑ€ÑˆÐ°ÐµÐ¼ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð¸Ðµ Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¸
        self.emails = '\n'.join([f'{emailsList[i]}' for i in range(len(emailsList))])
        emails = '\n'.join([f'{i + 1}. {emailsList[i]}' for i in range(len(emailsList))])
        update.message.reply_text(emails, reply_markup=self.keyboard_add_db_Emails()
                                  )  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÑÐ¾Ð¾Ð±Ñ‰ÐµÐ½Ð¸Ðµ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑŽ
        logger.info(f'Stop {self.findEmails.__name__}')
        return ConversationHandler.END  # self.commands.add_db_Emails.state_point # Ð—Ð°Ð²ÐµÑ€ÑˆÐ°ÐµÐ¼ Ñ€Ð°Ð±Ð¾Ñ‚Ñƒ Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸ÐºÐ° Ð´Ð¸Ð°Ð»Ð¾Ð³Ð°

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
                    f'Ð”Ð°Ð½Ð½Ñ‹Ðµ ÑƒÑÐ¿ÐµÑˆÐ½Ð¾ Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ñ‹ Ð² Ð‘Ð”',
                    reply_markup=self.keyboard_menu_main()  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÐºÐ»Ð°Ð²Ð¸Ð°Ñ‚ÑƒÑ€Ñƒ Ñ ÐºÐ½Ð¾Ð¿ÐºÐ°Ð¼Ð¸
                    )
            logging.info("ÐšÐ¾Ð¼Ð°Ð½Ð´Ð° ÑƒÑÐ¿ÐµÑˆÐ½Ð¾ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð°")
        except (Exception, psycopg2.Error) as error:
            logging.error(f"ÐžÑˆÐ¸Ð±ÐºÐ° Ð¿Ñ€Ð¸ Ñ€Ð°Ð±Ð¾Ñ‚Ðµ Ñ PostgreSQL: {error}")
        finally:
            if connection:
                cursor.close()
                connection.close()
                logging.info("Ð¡Ð¾ÐµÐ´Ð¸Ð½ÐµÐ½Ð¸Ðµ Ñ PostgreSQL Ð·Ð°ÐºÑ€Ñ‹Ñ‚Ð¾")
        logger.info(f'Stop {self.command_Add_db_Emails.__name__}')
        return ConversationHandler.END

    def command_FindPhoneNumbers(self, update: Update, context):
        """
        Ð‘Ð¾Ñ‚ Ð²Ñ‹Ð²Ð¾Ð´ ÑÐ¿Ð¸ÑÐ¾Ðº Ð½Ð°Ð¹Ð´ÐµÐ½Ð½Ñ‹Ñ… Ð½Ð¾Ð¼ÐµÑ€Ð¾Ð² Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð°
        """
        logger.info(f'Start {self.command_FindPhoneNumbers.__name__}')
        update.message.reply_text('Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ñ‚ÐµÐºÑÑ‚ Ð´Ð»Ñ Ð¿Ð¾Ð¸ÑÐºÐ° Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð½Ñ‹Ñ… Ð½Ð¾Ð¼ÐµÑ€Ð¾Ð²: ',
                                  reply_markup=self.keyboard_menu_cancel()
                                  # ÐšÐ½Ð¾Ð¿ÐºÐ° Ð´Ð»Ñ Ð¾Ñ‚Ð¼ÐµÐ½Ñ‹ Ð¿Ð¾Ð¸ÑÐºÐ°
                                  )
        logger.info(f'Stop {self.command_FindPhoneNumbers.__name__}')
        return self.commands.findPhoneNumbers.state_point

    def findPhoneNumbers(self, update: Update, context):
        logger.info(f'Start {self.findPhoneNumbers.__name__}')
        user_input = update.message.text  # ÐŸÐ¾Ð»ÑƒÑ‡Ð°ÐµÐ¼ Ñ‚ÐµÐºÑÑ‚, ÑÐ¾Ð´ÐµÑ€Ð¶Ð°Ñ‰Ð¸Ð¹ (Ð¸Ð»Ð¸ Ð½ÐµÑ‚) Ð½Ð¾Ð¼ÐµÑ€Ð° Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð¾Ð²
        """
        Ð Ð°Ð·Ð»Ð¸Ñ‡Ð½Ñ‹Ðµ Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ñ‹ Ð·Ð°Ð¿Ð¸ÑÐ¸ Ð½Ð¾Ð¼ÐµÑ€Ð¾Ð² Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð°.
        - 8XXXXXXXXXX,
        - 8(XXX)XXXXXXX,
        - 8 XXX XXX XX XX,
        - 8 (XXX) XXX XX XX,
        - 8-XXX-XXX-XX-XX.
        Ð¢Ð°ÐºÐ¶Ðµ Ð²Ð¼ÐµÑÑ‚Ð¾ â€˜8â€™ Ð½Ð° Ð¿ÐµÑ€Ð²Ð¾Ð¼ Ð¼ÐµÑÑ‚Ðµ Ð¼Ð¾Ð¶ÐµÑ‚ Ð±Ñ‹Ñ‚ÑŒ â€˜+7â€™.
        """
        phoneNumRegex = re.compile(r'(\+7|8)(\s?[(-]?\d{3}[)-]?\s?\d{3}-?\s?\d{2}-?\s?\d{2})')  # Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚
        phoneNumberList = phoneNumRegex.findall(user_input)  # Ð˜Ñ‰ÐµÐ¼ Ð½Ð¾Ð¼ÐµÑ€Ð° Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð¾Ð²
        if not phoneNumberList:  # ÐžÐ±Ñ€Ð°Ð±Ð°Ñ‚Ñ‹Ð²Ð°ÐµÐ¼ ÑÐ»ÑƒÑ‡Ð°Ð¹, ÐºÐ¾Ð³Ð´Ð° Ð½Ð¾Ð¼ÐµÑ€Ð¾Ð² Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð¾Ð² Ð½ÐµÑ‚
            update.message.reply_text('Ð¢ÐµÐ»ÐµÑ„Ð¾Ð½Ð½Ñ‹Ðµ Ð½Ð¾Ð¼ÐµÑ€Ð° Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½Ñ‹', reply_markup=self.keyboard_menu_cancel())
            return  # Ð—Ð°Ð²ÐµÑ€ÑˆÐ°ÐµÐ¼ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð¸Ðµ Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¸
        self.phones = '\n'.join(
                [f'{phoneNumberList[i][0] + phoneNumberList[i][1]}' for i in range(len(phoneNumberList))]
                )
        phones = '\n'.join(
                [f'{i + 1}. {phoneNumberList[i][0] + phoneNumberList[i][1]}' for i in range(len(phoneNumberList))]
                )
        update.message.reply_text(phones, reply_markup=self.keyboard_add_db_Phones()
                                  )  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÑÐ¾Ð¾Ð±Ñ‰ÐµÐ½Ð¸Ðµ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑŽ
        logger.info(f'Stop {self.findPhoneNumbers.__name__}')
        return ConversationHandler.END  # Ð—Ð°Ð²ÐµÑ€ÑˆÐ°ÐµÐ¼ Ñ€Ð°Ð±Ð¾Ñ‚Ñƒ Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸ÐºÐ° Ð´Ð¸Ð°Ð»Ð¾Ð³Ð°

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
                    f'Ð”Ð°Ð½Ð½Ñ‹Ðµ ÑƒÑÐ¿ÐµÑˆÐ½Ð¾ Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ñ‹ Ð² Ð‘Ð”',
                    reply_markup=self.keyboard_menu_main()  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÐºÐ»Ð°Ð²Ð¸Ð°Ñ‚ÑƒÑ€Ñƒ Ñ ÐºÐ½Ð¾Ð¿ÐºÐ°Ð¼Ð¸
                    )
            logging.info("ÐšÐ¾Ð¼Ð°Ð½Ð´Ð° ÑƒÑÐ¿ÐµÑˆÐ½Ð¾ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð°")
        except (Exception, psycopg2.Error) as error:
            logging.error(f"ÐžÑˆÐ¸Ð±ÐºÐ° Ð¿Ñ€Ð¸ Ñ€Ð°Ð±Ð¾Ñ‚Ðµ Ñ PostgreSQL: {error}")
        finally:
            if connection:
                cursor.close()
                connection.close()
                logging.info("Ð¡Ð¾ÐµÐ´Ð¸Ð½ÐµÐ½Ð¸Ðµ Ñ PostgreSQL Ð·Ð°ÐºÑ€Ñ‹Ñ‚Ð¾")
        logger.info(f'Stop {self.command_Add_db_Phones.__name__}')
        return ConversationHandler.END
    
    def command_GetEmails(self, update: Update, context):
        logger.info(f'Start {self.command_GetEmails.__name__}')
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
        connection, data = None, 'test'
        try:
            connection = psycopg2.connect(user=username,
                                          password=password,
                                          host=host,
                                          port=port,
                                          database=database
                                          )

            cursor = connection.cursor()
            cursor.execute("SELECT * FROM Emails;")
            data = cursor.fetchall()
            #for row in data:
                #print(row)  
            connection.commit()
            #emails = re.findall(r'"([^"]+)"', data)
            #data = '\n'.join([lst[0] for lst in data])
            update.message.reply_text(
                    data,
                    reply_markup=self.keyboard_menu_main()  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÐºÐ»Ð°Ð²Ð¸Ð°Ñ‚ÑƒÑ€Ñƒ Ñ ÐºÐ½Ð¾Ð¿ÐºÐ°Ð¼Ð¸
                    )
            logging.info("ÐšÐ¾Ð¼Ð°Ð½Ð´Ð° ÑƒÑÐ¿ÐµÑˆÐ½Ð¾ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð°")
        except (Exception, psycopg2.Error) as error:
            logging.error(f"ÐžÑˆÐ¸Ð±ÐºÐ° Ð¿Ñ€Ð¸ Ñ€Ð°Ð±Ð¾Ñ‚Ðµ Ñ PostgreSQL: {error}")
        finally:
            if connection:
                cursor.close()
                connection.close()
                logging.info("Ð¡Ð¾ÐµÐ´Ð¸Ð½ÐµÐ½Ð¸Ðµ Ñ PostgreSQL Ð·Ð°ÐºÑ€Ñ‹Ñ‚Ð¾")
        logger.info(f'Stop {self.command_GetEmails.__name__}')
        return ConversationHandler.END
        
    def command_GetPhones(self, update: Update, context):
        logger.info(f'Start {self.command_GetPhones.__name__}')
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
        connection, data = None, 'test'
        try:
            connection = psycopg2.connect(user=username,
                                          password=password,
                                          host=host,
                                          port=port,
                                          database=database
                                          )

            cursor = connection.cursor()
            cursor.execute("SELECT * FROM Phones;")
            data = cursor.fetchall()
            #for row in data:
                #print(row)  
            connection.commit()
            #data = '\n'.join([lst[0] for lst in data])
            #phones = re.findall(r'"([^"]+)"', input_string)
            update.message.reply_text(
                    data,
                    reply_markup=self.keyboard_menu_main()  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÐºÐ»Ð°Ð²Ð¸Ð°Ñ‚ÑƒÑ€Ñƒ Ñ ÐºÐ½Ð¾Ð¿ÐºÐ°Ð¼Ð¸
                    )
            logging.info("ÐšÐ¾Ð¼Ð°Ð½Ð´Ð° ÑƒÑÐ¿ÐµÑˆÐ½Ð¾ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð°")
        except (Exception, psycopg2.Error) as error:
            logging.error(f"ÐžÑˆÐ¸Ð±ÐºÐ° Ð¿Ñ€Ð¸ Ñ€Ð°Ð±Ð¾Ñ‚Ðµ Ñ PostgreSQL: {error}")
        finally:
            if connection:
                cursor.close()
                connection.close()
                logging.info("Ð¡Ð¾ÐµÐ´Ð¸Ð½ÐµÐ½Ð¸Ðµ Ñ PostgreSQL Ð·Ð°ÐºÑ€Ñ‹Ñ‚Ð¾")
        logger.info(f'Stop {self.command_GetPhones.__name__}')
        return ConversationHandler.END


    def command_VerifyPassword(self, update: Update, context):
        """
        Ð‘Ð¾Ñ‚ Ð²Ñ‹Ð²Ð¾Ð´Ð¸Ñ‚ Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸ÑŽ Ð¾ ÑÐ»Ð¾Ð¶Ð½Ð¾ÑÑ‚Ð¸ Ð¿Ð°Ñ€Ð¾Ð»Ñ
        """
        logger.info(f'Start {self.command_VerifyPassword.__name__}')
        update.message.reply_text('Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ð¿Ð°Ñ€Ð¾Ð»ÑŒ Ð´Ð»Ñ Ð¾Ñ†ÐµÐ½ÐºÐ¸ ÑÐ»Ð¾Ð¶Ð½Ð¾ÑÑ‚Ð¸: ',
                                  reply_markup=self.keyboard_menu_cancel()
                                  # ÐšÐ½Ð¾Ð¿ÐºÐ° Ð´Ð»Ñ Ð¾Ñ‚Ð¼ÐµÐ½Ñ‹ Ð¿Ð¾Ð¸ÑÐºÐ°
                                  )
        logger.info(f'Stop {self.command_VerifyPassword.__name__}')
        return self.commands.verifyPassword.state_point

    def verifyPassword(self, update: Update, context):
        logger.info(f'Start {self.verifyPassword.__name__}')
        user_input = update.message.text  # ÐŸÐ¾Ð»ÑƒÑ‡Ð°ÐµÐ¼ Ñ‚ÐµÐºÑÑ‚, ÑÐ¾Ð´ÐµÑ€Ð¶Ð°Ñ‰Ð¸Ð¹ (Ð¸Ð»Ð¸ Ð½ÐµÑ‚) Ð½Ð¾Ð¼ÐµÑ€Ð° Ñ‚ÐµÐ»ÐµÑ„Ð¾Ð½Ð¾Ð²

        """
        Ð¢Ñ€ÐµÐ±Ð¾Ð²Ð°Ð½Ð¸Ñ Ðº Ð¿Ð°Ñ€Ð¾Ð»ÑŽ:
        - ÐŸÐ°Ñ€Ð¾Ð»ÑŒ Ð´Ð¾Ð»Ð¶ÐµÐ½ ÑÐ¾Ð´ÐµÑ€Ð¶Ð°Ñ‚ÑŒ Ð½Ðµ Ð¼ÐµÐ½ÐµÐµ Ð²Ð¾ÑÑŒÐ¼Ð¸ ÑÐ¸Ð¼Ð²Ð¾Ð»Ð¾Ð².
        - ÐŸÐ°Ñ€Ð¾Ð»ÑŒ Ð´Ð¾Ð»Ð¶ÐµÐ½ Ð²ÐºÐ»ÑŽÑ‡Ð°Ñ‚ÑŒ ÐºÐ°Ðº Ð¼Ð¸Ð½Ð¸Ð¼ÑƒÐ¼ Ð¾Ð´Ð½Ñƒ Ð·Ð°Ð³Ð»Ð°Ð²Ð½ÑƒÑŽ Ð±ÑƒÐºÐ²Ñƒ (Aâ€“Z).
        - ÐŸÐ°Ñ€Ð¾Ð»ÑŒ Ð´Ð¾Ð»Ð¶ÐµÐ½ Ð²ÐºÐ»ÑŽÑ‡Ð°Ñ‚ÑŒ Ñ…Ð¾Ñ‚Ñ Ð±Ñ‹ Ð¾Ð´Ð½Ñƒ ÑÑ‚Ñ€Ð¾Ñ‡Ð½ÑƒÑŽ Ð±ÑƒÐºÐ²Ñƒ (aâ€“z).
        - ÐŸÐ°Ñ€Ð¾Ð»ÑŒ Ð´Ð¾Ð»Ð¶ÐµÐ½ Ð²ÐºÐ»ÑŽÑ‡Ð°Ñ‚ÑŒ Ñ…Ð¾Ñ‚Ñ Ð±Ñ‹ Ð¾Ð´Ð½Ñƒ Ñ†Ð¸Ñ„Ñ€Ñƒ (0â€“9).
        - ÐŸÐ°Ñ€Ð¾Ð»ÑŒ Ð´Ð¾Ð»Ð¶ÐµÐ½ Ð²ÐºÐ»ÑŽÑ‡Ð°Ñ‚ÑŒ Ñ…Ð¾Ñ‚Ñ Ð±Ñ‹ Ð¾Ð´Ð¸Ð½ ÑÐ¿ÐµÑ†Ð¸Ð°Ð»ÑŒÐ½Ñ‹Ð¹ ÑÐ¸Ð¼Ð²Ð¾Ð», Ñ‚Ð°ÐºÐ¾Ð¹ ÐºÐ°Ðº !@#$%^&*().
        """

        passwdRegex = re.compile(r'(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&()])[A-Za-z\d@$!%*#?&()]{8,}')

        passwdList = passwdRegex.search(user_input)

        if not passwdList:  # ÐžÐ±Ñ€Ð°Ð±Ð°Ñ‚Ñ‹Ð²Ð°ÐµÐ¼ ÑÐ»ÑƒÑ‡Ð°Ð¹, ÐºÐ¾Ð³Ð´Ð° ÑÐ¾Ð²Ð¿Ð°Ð´ÐµÐ½Ð¸Ð¹ Ð½ÐµÑ‚
            update.message.reply_text('ÐŸÐ°Ñ€Ð¾Ð»ÑŒ Ð¿Ñ€Ð¾ÑÑ‚Ð¾Ð¹', reply_markup=self.keyboard_menu_cancel())
            return  # Ð—Ð°Ð²ÐµÑ€ÑˆÐ°ÐµÐ¼ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð¸Ðµ Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¸

        update.message.reply_text('ÐŸÐ°Ñ€Ð¾Ð»ÑŒ ÑÐ»Ð¾Ð¶Ð½Ñ‹Ð¹', reply_markup=self.keyboard_menu_cancel()
                                  )  # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÑÐ¾Ð¾Ð±Ñ‰ÐµÐ½Ð¸Ðµ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑŽ
        logger.info(f'Stop {self.verifyPassword.__name__}')
        return  # ConversationHandler.END  # Ð—Ð°Ð²ÐµÑ€ÑˆÐ°ÐµÐ¼ Ñ€Ð°Ð±Ð¾Ñ‚Ñƒ Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸ÐºÐ° Ð´Ð¸Ð°Ð»Ð¾Ð³Ð°

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
        update.message.reply_text('Ð’Ñ‹Ð±ÐµÑ€Ð¸Ñ‚Ðµ Ð¾Ð¿Ñ†Ð¸ÑŽ:', reply_markup=self.keyboard_apt_packages())
        logger.info(f'Stop {self.command_GetAptList.__name__}')
        return self.commands.getAptList.state_point

    # ÐšÐ¾Ð¼Ð°Ð½Ð´Ð° Ð´Ð»Ñ Ð¿Ð¾Ð»ÑƒÑ‡ÐµÐ½Ð¸Ñ ÑÐ¿Ð¸ÑÐºÐ° Ð²ÑÐµÑ… ÑƒÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½Ð½Ñ‹Ñ… Ð¿Ð°ÐºÐµÑ‚Ð¾Ð²
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
        update.message.reply_text('Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ð½Ð°Ð·Ð²Ð°Ð½Ð¸Ðµ Ð¿Ð°ÐºÐµÑ‚Ð°:',
                                  reply_markup=self.keyboard_apt_packages()
                                  # ÐšÐ½Ð¾Ð¿ÐºÐ° Ð´Ð»Ñ Ð¾Ñ‚Ð¼ÐµÐ½Ñ‹ Ð¿Ð¾Ð¸ÑÐºÐ°
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
        # ÐŸÐ¾Ð»ÑƒÑ‡Ð°ÐµÐ¼ Ð´Ð¸ÑÐ¿ÐµÑ‚Ñ‡ÐµÑ€ Ð´Ð»Ñ Ñ€ÐµÐ³Ð¸ÑÑ‚Ñ€Ð°Ñ†Ð¸Ð¸ Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸ÐºÐ¾Ð²
        dp = updater.dispatcher

        ## Ð ÐµÐ³Ð¸ÑÑ‚Ñ€Ð¸Ñ€ÑƒÐµÐ¼ Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸ÐºÐ¸ ÐºÐ¾Ð¼Ð°Ð½Ð´

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /start
        dp.add_handler(CommandHandler(self.commands.start.command, self.commands.start.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /help
        dp.add_handler(CommandHandler(self.commands.help.command, self.commands.help.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /findEmails
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

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /add_db_Emails

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
        
        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_emails
        dp.add_handler(CommandHandler(self.commands.getEmails.command, self.commands.getEmails.callback))
        
        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_phones
        dp.add_handler(CommandHandler(self.commands.getPhones.command, self.commands.getPhones.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /findPhoneNumbers
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

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /add_db_Phones

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

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /verifyPassword
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

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_release
        dp.add_handler(CommandHandler(self.commands.getRelease.command, self.commands.getRelease.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_uname
        dp.add_handler(CommandHandler(self.commands.getUname.command, self.commands.getUname.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_uptime
        dp.add_handler(CommandHandler(self.commands.getUptime.command, self.commands.getUptime.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_df
        dp.add_handler(CommandHandler(self.commands.getDF.command, self.commands.getDF.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_free
        dp.add_handler(CommandHandler(self.commands.getFree.command, self.commands.getFree.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_mpstat
        dp.add_handler(CommandHandler(self.commands.getMpstat.command, self.commands.getMpstat.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_w
        dp.add_handler(CommandHandler(self.commands.getW.command, self.commands.getW.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_auths
        dp.add_handler(CommandHandler(self.commands.getAuths.command, self.commands.getAuths.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_critical
        dp.add_handler(CommandHandler(self.commands.getCritical.command, self.commands.getCritical.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_ps
        dp.add_handler(CommandHandler(self.commands.getPS.command, self.commands.getPS.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_SS
        dp.add_handler(CommandHandler(self.commands.getSS.command, self.commands.getSS.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_apt_list
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

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_services
        dp.add_handler(CommandHandler(self.commands.getServices.command, self.commands.getServices.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹ /get_rep_logs
        dp.add_handler(CommandHandler(self.commands.getReplLogs.command, self.commands.getReplLogs.callback))

        # ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚Ñ‡Ð¸Ðº Ñ‚ÐµÐºÑÑ‚Ð¾Ð²Ñ‹Ñ… ÑÐ¾Ð¾Ð±Ñ‰ÐµÐ½Ð¸Ð¹ /echo
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.commands.echo.callback))

        # Ð—Ð°Ð¿ÑƒÑÐºÐ°ÐµÐ¼ Ð±Ð¾Ñ‚Ð°
        updater.start_polling()

        # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÐºÐ½Ð¾Ð¿ÐºÑƒ /start Ð°Ð²Ñ‚Ð¾Ð¼Ð°Ñ‚Ð¸Ñ‡ÐµÑÐºÐ¸ Ð¿Ñ€Ð¸ Ð·Ð°Ð¿ÑƒÑÐºÐµ Ð±Ð¾Ñ‚Ð°
        self.command_Start(context=updater)

        # ÐžÑÑ‚Ð°Ð½Ð°Ð²Ð»Ð¸Ð²Ð°ÐµÐ¼ Ð±Ð¾Ñ‚Ð° Ð¿Ñ€Ð¸ Ð½Ð°Ð¶Ð°Ñ‚Ð¸Ð¸ Ctrl+C
        updater.idle()

        logger.info(f'Stop {self.main.__name__}')


if __name__ == '__main__':
    logger.info('Start Script')
    bot = TelegramBot()
    bot.main()
    logger.info('Stop Script')
