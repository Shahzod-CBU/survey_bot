from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from statim import Options, Question, Greeting, User, Next, AdminButtons, Commenting
from connection import get_quests, write_results, import_questions, change_process_state
from connection import get_results, write_comments, get_comments, export_quests
from connection import get_finished_users, get_finished_comments, check_user
from copy import deepcopy
from emoji import emojize
from datetime import datetime
from io import StringIO
import pandas as pd
import os

"""written by Shahzod on 9 Nov 2019"""


bot_token = 'Secret_TOKEN'
PORT = int(os.environ.get('PORT', '443'))
# print('port num', PORT)

multiple = {'uzb': 'Бир нечта жавобни белгилаш мумкин',
            'rus': 'Можно указать несколько ответов'}
users = dict()
comments = dict()
admin_buttons = AdminButtons()
questions_bil = dict()  # bilingual
quest_arr = dict()
allowed_list = [12345678, 87654321]
# script_directory = os.path.dirname(os.path.abspath(__file__))
script_directory = '/tmp'
regret_text = ('<b>Юзага келган техник узулишлар учун узр сўраймиз.</b>\n'
               '/start командаси орқали сўровномани қайта тўлдиришингиз мумкин. '
               'Сизнинг фикрингиз <b>биз учун муҳим</b>!\n\n'
               '<b>Мы приносим свои извинения за технические прерывания.</b>\n'
               'Вы можете повторно заполнить опрос, используя команду /start. '
               'Ваше мнение <b>ценно для нас!</b>')


def update_quest(chat_id, quest_id, option_id):
    users[chat_id].seen()
    user_questions = users[chat_id].quests
    current_button = user_questions[quest_id].options

    # radio button logic
    if not user_questions[quest_id].isMultiple:
        for inline_button in current_button.states:
            if inline_button.my_emoji.on:
                inline_button.change_button()
                break

    current_button.states[option_id].change_button()
    return user_questions[quest_id].reply_markup


def start_survey():
    global quest_arr
    quest_arr = {'uzb': get_quests('uzb'),
                 'rus': get_quests('rus')}

    for language, quests in quest_arr.items():
        questions = dict()
        eslatma = f'\n<i>{multiple[language]}</i>'
        for current_quest in quests:
            quest_id = current_quest[0]
            options = Options(variants=[x.lstrip() for x in current_quest[2].split(';')])
            # options = Options(variants=[x for x in current_quest[2].split(';')])
            quest_text = f'<b>{current_quest[1]}</b>'
            if current_quest[3]:
                quest_text += eslatma
            my_quest = Question(quest_id=quest_id,
                                quest_text=quest_text,
                                options=options,
                                isMultiple=current_quest[3],
                                columns=current_quest[4])
            my_quest.create_quest()
            questions[quest_id] = my_quest
        questions_bil[language] = questions

    if not admin_buttons.is_running:
        admin_buttons.is_running = 1
        change_process_state(1)

    print('Started', flush=True)


def start(bot, update):
    chat_id = update.message.chat_id
    if admin_buttons.is_running:
        greeting = Greeting()
        bot.send_message(chat_id=chat_id, text=greeting.text_uzb, parse_mode="HTML")
        bot.send_message(chat_id=chat_id, text=greeting.text_rus,
                         reply_markup=greeting.reply_markup, parse_mode="HTML")
    else:
        text = emojize('<b>The survey has not been started yet! :sleeping:</b>', use_aliases=True)
        bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")


@run_async
def icon_actions(bot, update):
    try:
        query = update.callback_query
        bot.answer_callback_query(query.id)
        chat_id = query.message.chat_id
        message_id = query.message.message_id

        def send_quest(user_questions_1, quest_1, from_next=False):
            next_question = user_questions_1[quest_1 + 1]
            if not from_next:
                bot.send_message(chat_id=chat_id, text=next_question.quest_text,
                                 reply_markup=next_question.reply_markup, parse_mode='HTML')
            else:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=next_question.quest_text,
                                      reply_markup=next_question.reply_markup, parse_mode='HTML')
            if next_question.isMultiple:
                next_question.isChecked = True
                next_button = Next(callback_data=f'n{quest_1 + 1}', language=users[chat_id].language)
                bot.send_message(chat_id=chat_id, text=next_button.text,
                                 reply_markup=next_button.reply_markup, parse_mode='HTML')

        if '-' in query.data:
            user = users[chat_id]
            user_questions = user.quests
            quest, answer = query.data.split('-')  # get ids of the question and the option
            quest, answer = int(quest), int(answer)
            reply_markup = update_quest(chat_id, quest, answer)
            bot.editMessageReplyMarkup(chat_id=chat_id, message_id=message_id,
                                       reply_markup=reply_markup, parse_mode='HTML')
            if not user_questions[quest].isChecked:
                user_questions[quest].isChecked = True
                if quest != len(user_questions):
                    send_quest(user_questions, quest)
                else:
                    text = f'<b>{user.notes.thanks}</b>\n{user.notes.announcement} {user.notes.site}'
                    bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                    user.finish()
                    write_results(chat_id, user)
                    del users[chat_id]
                    comments[chat_id] = comment = Commenting(user.user_name, user.language)
                    bot.send_message(chat_id=chat_id, text=comment.text,
                                     reply_markup=comment.reply_markup, parse_mode="HTML")
        elif query.data == "uzb" or query.data == "rus":
            names = query.from_user
            username = f'fn:{names.first_name}, ln:{names.last_name}, un:{names.username}'
            users[chat_id] = user = User(user_name=username,
                                         quests=deepcopy(questions_bil[query.data]),
                                         language=query.data)
            # text = f'<b>{user.notes.survey}</b>\n{user.notes.privacy}'
            # bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            question = user.quests[1]
            bot.send_message(chat_id=chat_id, text=question.quest_text,
                             reply_markup=question.reply_markup, parse_mode="HTML")
        elif query.data[0] == 'n':       # from next button
            user_questions = users[chat_id].quests
            quest = int(query.data.replace('n', ''))
            send_quest(user_questions, quest, True)
        elif query.data == 'comment':
            comment = comments[chat_id]
            comment.is_clicked = True
            comment.start_time = datetime.now()
            bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                  text=comment.explaining, parse_mode='HTML')
        elif query.data == 'import':
            admin_buttons.is_import = True
            bot.send_message(chat_id=chat_id, text='Please, send a file!')
        elif query.data == 'export':
            filename = get_results()
            data_file = os.path.join(script_directory, 'output.csv')
            # data_file = "/tmp/output.csv"
            bot.send_document(chat_id=chat_id, document=open(data_file, 'rb'), filename=filename)
        elif query.data == 'start':
            if admin_buttons.is_running:
                text = emojize('Overriding running survey... :thinking_face:', use_aliases=True)
                bot.send_message(chat_id=chat_id, text=text)
            start_survey()
            text = emojize('The survey has been started! :arrow_forward:', use_aliases=True)
            bot.send_message(chat_id=chat_id, text=text)
        elif query.data == 'stop':
            if not admin_buttons.is_running:
                text = emojize('<b>Firstly, start the survey!</b> :flushed:', use_aliases=True)
                bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            else:
                print('Finished', flush=True)
                admin_buttons.is_running = 0
                change_process_state(0)
                text = emojize('The survey has been finished! :lock:', use_aliases=True)
                bot.send_message(chat_id=chat_id, text=text)
                users.clear()
        elif query.data == 'get_comments':
            filename = get_comments()
            data_file = os.path.join(script_directory, 'comment.csv')
            bot.send_document(chat_id=chat_id, document=open(data_file, 'rb'), filename=filename)

    except KeyError as exc:
        key = exc.args[0]
        print('User trying reaccess:', key, flush=True)
        if not check_user(key):
            bot.send_message(chat_id=key, text=regret_text, parse_mode="HTML")
            print(f'Message sent to {key}', flush=True)
    except Exception as ex:
        print(ex, flush=True)


def admin(bot, update):
    chat_id = update.message.chat_id

    if chat_id in allowed_list:
        bot.send_message(chat_id=chat_id, text=admin_buttons.text,
                         reply_markup=admin_buttons.reply_markup, parse_mode="HTML")
    else:
        text = '<b>You cannot execute this command!</b>'
        bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")


def document_handler(bot, update):
    if admin_buttons.is_import:
        chat_id = update.message.chat_id
        file = bot.getFile(update.message.document.file_id)
        file_name = os.path.join(script_directory, 'questions.xlsx')
        file.download(file_name)
        # data = StringIO(str(file.download_as_bytearray(), 'utf-8'))
        # df1 = pd.read_csv(data, sep="\t", header=None)
        df1 = pd.read_excel(file_name, header=None, encoding='utf-8')
        df1.columns = ["test", "id", "quests", "options", "is_multiple", "num_columns", "language"]
        try:
            import_questions(df1)
            text = emojize(':heavy_check_mark: <b>Successfully got questions!</b>', use_aliases=True)
            bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            admin_buttons.is_import = False
        except Exception as ex:
            print('Error in getting questions', ex, flush=True)
            text = emojize('<b>:x:  Please, insert the file in an applicable format.</b>', use_aliases=True)
            bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")


def comment_handler(bot, update):
    chat_id = update.message.chat_id
    try:
        comment = comments[chat_id]
        if comment.is_clicked:
            comment.comment = update.message.text.strip().replace('"', "")
            comment.elapsed_time = str(datetime.now() - comment.start_time)[:10]
            comment.is_clicked = False
            write_comments(chat_id, comment)
            bot.send_message(chat_id=chat_id, text=comment.thanks, parse_mode="HTML")
            del comments[chat_id]
    except KeyError as exc:
        key = exc.args[0]
        print('Commented user not found:', key, flush=True)
    except Exception as ex:
        print(ex, flush=True)


def num_users(bot, update):
    chat_id = update.message.chat_id

    if chat_id not in allowed_list:
        text = '<b>You cannot execute this command!</b>'
        bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        return

    actives, non_actives = 0, 0
    if users:           # non-empty
        hozir = datetime.now()
        for user in users.values():
            active_time = (hozir - user.last_seen).seconds / 60
            if active_time <= 20:
                actives += 1
            else:
                non_actives += 1

    text = ('<b>Number of current users:</b>\n'
            f'<b> - active: </b>{actives}\n'
            f'<b> - non-active: </b>{non_actives}')

    if comments:
        commenting = 0
        for comment in comments.values():
            if comment.is_clicked:
                commenting += 1
        if commenting:
            text += f'\n<b> - commenting: </b>{commenting}'

    try:
        text += (f'\n\nRecords: {get_finished_users()}\n'
                   f'Comments: {get_finished_comments()}')
    except:
        pass

    bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")


def export_questions(bot, update):
    chat_id = update.message.chat_id

    if chat_id in allowed_list:
        filename = export_quests()
        data_file = os.path.join(script_directory, 'questions_sql.csv')
        bot.send_document(chat_id=chat_id, document=open(data_file, 'rb'), filename=filename)


def tech_error(bot, update):
    chat_id = update.message.chat_id

    if chat_id in allowed_list:
        lost_users = []
        i = 0
        for user in lost_users:
            try:
                bot.send_message(chat_id=user, text=regret_text, parse_mode="HTML")
                i += 1
            except:
                continue
        print(f'{i} messages sent!', flush=True)


def time_up(bot, update):
    chat_id = update.message.chat_id

    if chat_id in allowed_list:
        restart_text = ('<b>Сизнинг фикрингиз биз учун муҳим</b>!\n'
                        'Илтимос, вақтингиз бўлганда сўровномани охирига етказиб қўйсангиз. '
                        'Саволларнинг умумий сони 11 та.\n\n'
                        '<b>Ваше мнение важно для нас!</b>\n'
                        'Пожалуйста, завершите опрос, когда у Вас будеть время. '
                        'Всего число вопросов 11.')
        i = 0
        hozir = datetime.now()
        non_actives = []
        for user_id, user_obj in users.items():
            if (hozir - user_obj.last_seen).seconds / 60 > 20:
                try:
                    bot.send_message(chat_id=user_id, text=restart_text, parse_mode="HTML")
                    non_actives.append(user_id)
                    i += 1
                except:
                    continue
        print(f'{i} messages sent!', flush=True)
        print(f'Non-active users: {non_actives}')


def main():
    updater = Updater(bot_token, workers=16)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('admin', admin))
    dp.add_handler(CommandHandler('users', num_users))
    dp.add_handler(CommandHandler('questions', export_questions))
    dp.add_handler(CommandHandler('resend', tech_error))
    dp.add_handler(CommandHandler('time_up', time_up))
    dp.add_handler(CallbackQueryHandler(icon_actions))
    dp.add_handler(MessageHandler(Filters.document, document_handler))
    dp.add_handler(MessageHandler(Filters.text, comment_handler))
    if admin_buttons.is_running:
        start_survey()
    print('Tayyor!', flush=True)
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=bot_token)
    updater.bot.set_webhook("https://surveybot1011.herokuapp.com/" + bot_token)
    # updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
