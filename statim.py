from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from emoji import emojize
from datetime import datetime
from connection import get_process_state

"""written by Shahzod on 9 Nov 2019"""

class RadioButton:

    def __init__(self):
        self.on = False
        self.icon = ':white_circle:'

    def change_state(self):
        self.on = not self.on
        self.icon = ':radio_button:' if self.on else ':white_circle:'


class Checkbox:

    def __init__(self):
        self.on = False
        self.icon = ':white_medium_square:'

    def change_state(self):
        self.on = not self.on
        self.icon = ':ballot_box_with_check:' if self.on else ':white_medium_square:'


class Options:

    def __init__(self, variants):
        self.ids = list(range(len(variants)))
        self.states = list()  # real objects
        self.buttons = list()  # InlineKeyboardButton objects with relationship to InlineKeyboardMarkup
        # self.max_len = max(len(x) for x in variants)
        # self.variants = [f'{x:<{self.max_len}}' for x in variants]
        # self.variants = [x.ljust(self.max_len) for x in variants]  # chapdan yozish uchun bo'sh joy bilan to'ldirish
        self.variants = variants


class InlineButton:

    def __init__(self, my_text, my_key, is_multiple):
        self.my_emoji = Checkbox() if is_multiple else RadioButton()
        self.my_text = my_text
        button_text = emojize(f'{self.my_emoji.icon} {self.my_text}')
        self.button = InlineKeyboardButton(text=button_text, callback_data=my_key)

    def change_button(self):
        self.my_emoji.change_state()
        self.button.text = emojize(f'{self.my_emoji.icon} {self.my_text}')


class Question:
    """Generates question object for interaction"""

    def __init__(self, quest_id, quest_text, options, isMultiple=False, columns=1):
        self.quest_id = quest_id
        self.quest_text = quest_text
        self.options = options
        self.isMultiple = isMultiple
        self.isChecked = False
        self.reply_markup = None
        self.columns = columns

    def reshape(self, options_list):
        reshaped, option_num = list(), 0
        len_options = len(options_list)
        while option_num < len_options:
            row, n = list(), 1
            while n <= self.columns:
                row.append(options_list[option_num][0])
                n += 1
                option_num += 1
                if option_num == len_options: break
            reshaped.append(row)
        return reshaped

    def create_quest(self):
        obj_options = self.options
        options_list = list()
        for i in obj_options.ids:
            key = f'{self.quest_id}-{i}'
            option_button = InlineButton(my_text=obj_options.variants[i], my_key=key,
                                         is_multiple=self.isMultiple)
            obj_options.states.append(option_button)
            options_list.append([option_button.button])
        if self.columns != 1:
            options_list = self.reshape(options_list)
        self.reply_markup = InlineKeyboardMarkup(options_list)
        # just creating a reference to the buttons of the Markup
        obj_options.buttons = self.reply_markup.inline_keyboard
        # return self.reply_markup


class Next:

    def __init__(self, callback_data, language):
        self.text = {'uzb': '<i>Кейинги саволга ўтиш:</i>',
                     'rus': '<i>Перейти к следующему вопросу:</i>'}[language]
        button_text = {'uzb': ' >> Кейингиси ',
                       'rus': ' >> Далее '}[language]
        inline_button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        self.reply_markup = InlineKeyboardMarkup([[inline_button]])


class Greeting:

    def __init__(self):
        self.text_uzb = ('<b>Хуш келибсиз! Инфляцион кутилмаларни аниқлаш бўйича СЎРОВНОМА.</b>\n'
                        'Илтимос тилни танланг!')
        self.text_rus = ('<b>Добро пожаловать! ВОПРОСНИК по определению инфляционных ожиданий.</b>\n'
                         'Пожалуйста выберите язык!')
        button1 = InlineKeyboardButton(text="Ўзбекча", callback_data="uzb")
        button2 = InlineKeyboardButton(text="Русский", callback_data="rus")
        self.reply_markup = InlineKeyboardMarkup([[button1, button2]])


class Notes:

    def __init__(self, language):
        self.survey = {'uzb': 'Инфляцион кутилмаларни аниқлаш бўйича СЎРОВНОМА',
                       'rus': 'ВОПРОСНИК по определению инфляционных ожиданий'}[language]
        self.privacy = {
            'uzb': 'Сўровда олинган натижаларнинг сир сақланиши кафолатланади ва улардан  фақат умумлаштирилган ҳолда фойдаланилади.',
            'rus': 'Полученные результаты носят конфиденциальный характер и будут использованы в обобщенном виде.'}[language]
        self.thanks = {'uzb': 'Сўровда иштирок этганингиз учун ташаккур! Сизнинг билдирган фикрингиз биз учун муҳим.',
                       'rus': 'Благодарим за участие в опросе! Ваше мнение для нас ценно.'}[language]
        self.announcement = {
            'uzb': 'Сўров натижалари бўйича маълумот чорак якуни бўйича Марказий банк сайтида чоп этилади ',
            'rus': 'По итогам квартала информация о результатах опроса будет опубликована на сайте Центрального банка '
            }[language]
        self.site = {'uzb': '<a href="http://www.cbu.uz/uzc/">(www.cbu.uz).</a>',
                     'rus': '<a href="http://www.cbu.uz/ru/">(www.cbu.uz).</a>'}[language]


class Commenting:

    def __init__(self, user_name, language):
        self.user_name = user_name
        self.text = {'uzb': '<i>Cўровнома бўйича фикр ва таклифларингизни қуйидаги орқали юборишингиз мумкин:</i>',
                     'rus': '<i>Ниже Вы можете присылать свои мнение и предложения по опросу:</i>'}[language]
        button_text = {'uzb': ' >> Фикр билдириш ',
                       'rus': ' >> Оставить отзыв'}[language]
        inline_button = InlineKeyboardButton(text=button_text, callback_data='comment')
        self.reply_markup = InlineKeyboardMarkup([[inline_button]])
        self.explaining = {'uzb': '<i>Илтимос, фикрингизни ёзинг ва "Telegram"нинг юбориш тугмачасини босинг</i>',
                           'rus': '<i>Пожалуйста, введите свой комментарий и нажмите кнопку отправить "Telegram"а</i>'}[language]
        self.thanks = {'uzb': '<b>Фикр билдирганингиз учун раҳмат!</b>',
                       'rus': '<b>Спасибо за отзыв!</b>'}[language]
        self.is_clicked = False
        self.start_time = None
        self.elapsed_time = None
        self.comment = None


class User:

    def __init__(self, user_name, quests, language):
        self.user_name = user_name
        self.quests = quests
        self.notes = Notes(language)
        self.survey_date = str(datetime.now().date())
        self.start_time = datetime.now()
        self.finish_time = None
        self.elapsed_time = None
        self.language = language
        self.results = None
        self.last_seen = datetime.now()

    def export_results(self):
        answers = list()
        for quest in self.quests.values():
            answer = [int(state.my_emoji.on) for state in quest.options.states]
            answers.append(answer)
        self.results = answers

    def seen(self):
        self.last_seen = datetime.now()

    def finish(self):
        self.finish_time = datetime.now()
        self.elapsed_time = str(self.finish_time - self.start_time)[:10]
        self.start_time = self.start_time.strftime("%H:%M:%S")
        self.finish_time = self.finish_time.strftime("%H:%M:%S")
        self.export_results()


class AdminButtons:

    def __init__(self):
        import_button = InlineKeyboardButton('Import questions', callback_data='import')
        export_button = InlineKeyboardButton('Export results', callback_data='export')
        start_button = InlineKeyboardButton('Start survey', callback_data='start')
        finish_button = InlineKeyboardButton('Finish survey', callback_data='stop')
        get_comments = InlineKeyboardButton('Show comments', callback_data='get_comments')
        self.text = '<b>What operation do you want to perform?</b>'
        self.reply_markup = InlineKeyboardMarkup([[import_button, export_button],
                                                  [start_button,  finish_button],
                                                  [get_comments]])
        self.is_import = False
        self.is_running = get_process_state()
        print('is_running', self.is_running, flush=True)
