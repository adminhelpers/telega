import telebot
from requests import get
from telebot import types
from pymongo import MongoClient
import time
import subprocess
from datetime import datetime, date, timedelta

global index_send
index_send = 0

cluster = MongoClient("mongodb+srv://dbrbase:YqxZgV1GL8s4CVxX@rodinadb.rhew3.mongodb.net/rodinaname?retryWrites=true&w=majority")
db = cluster["rodina"]
users = db["users"]

bot = telebot.TeleBot('5515463608:AAFmyO9G-3Sk9JtUJVmpwOuPdJxgPoopFrM')

@bot.message_handler(commands=['start']) # /start
def start_message(message):
    markup_inline = types.InlineKeyboardMarkup()
    item_one = types.InlineKeyboardButton(text='Погнали!', callback_data='go')

    markup_inline.add(item_one)
    bot.reply_to(message, '*Привет, гонщик* 😎\n\nЯ буду сообщать тебе о всех уличных гонках на улицах *Иркутска* или *Ангарска*, если ты этого захочешь.'
                  '\nЖми на кнопку "*Погнали*", что бы я отправлял тебе актуальную информацию о предстоящих заездах!', parse_mode= "Markdown", reply_markup=markup_inline)

@bot.message_handler(commands=['delete_user']) # Удаление юзера из базы данных
def delete_user_from_id(message):
    if message.from_user.id in [330435662, 532678880]:
        try: user_id = int(message.text.split(' ')[1])
        except: bot.reply_to(message, '*Для удаления участника из базы данных рассылки, опционально укажите его ID*\n\n_К примеру: /delete_user 1233457_', parse_mode= "Markdown")
        if users.count_documents({"city": 'Angarsk', "ids": user_id}) == 0:
            bot.reply_to(message, f'*Пользователя с указанным ID({user_id}) в списке не найдено*', parse_mode= "Markdown")
        else:
            tag = users.find_one({"city": 'Angarsk', "ids": user_id})["tag"]
            users.delete_one({"city": 'Angarsk', "ids": user_id})
            if users.count_documents({"ids": user_id, "type": "going_user"}) != 0:
                users.delete_one({"ids": user_id, "type": "going_user"})
            if users.count_documents({"type": "user_in_rise", "id": message.from_user.id}) != 0:
                users.delete_one({"type": "user_in_rise", "id": message.from_user.id})
            bot.reply_to(message, f'Пользователь {tag} __удалён__ из базы данных.', parse_mode= "Markdown")

@bot.message_handler(commands=['users']) # Список зареганых на рассылку
def get_users_on_reverse(message):
    if message.from_user.id in [330435662, 532678880]:
        answer = [f'\n[{i["ids"]}]: {i["user_name"]}' for i in users.find({"city": "Angarsk"})]
        if len(answer) == 0: bot.send_message(message.chat.id, f'*Список зарегистрированных на рассылку участников пуст*', parse_mode= "Markdown")
        else:
            str_i = ''.join(answer)
            bot.send_message(message.chat.id, f'*Список зарегистрированных на рассылку участников: {str_i}*', parse_mode= "Markdown")

@bot.message_handler(commands=['info']) # Информация о юзере
def get_user_info_by_id(message):
    if message.from_user.id in [330435662, 532678880]:
        text_info = []
        try: user_id = int(message.text.split(' ')[1])
        except: bot.reply_to(message, f'*Для просмотра информации о участнике, опционально укажите его* ID\n\n_К примеру: /info {message.from_user.id}_', parse_mode= "Markdown")
        if users.count_documents({"city": 'Angarsk', "ids": user_id}) == 0:
            bot.reply_to(message, f'*Пользователя с указанным ID({user_id}) в списке не найдено.*', parse_mode= "Markdown")
        else:
            user_inv = users.find_one({"city": 'Angarsk', "ids": user_id})
            text_info.append(f'Информация о пользователе *{user_inv["user_name"]}*({user_inv["tag"]}):\n\n*1.* Пользователь подписан на рассылку.\n')
            if users.count_documents({"ids": user_id, "type": "going_user"}) == 0:
                text_info.append('*2.* Зарегистрированных автомобилей *нет*.')
            else:
                text_info.append('*2.* Зарегистрированные автомоби:\n')
                auto_users = users.find_one({"ids": user_id, "type": "going_user"})["auto"]
                if auto_users[0] != 1:
                    text_info.append(f'  *›* {auto_users[0]}\n')
                if auto_users[1] != 1:
                    text_info.append(f'  *›* {auto_users[1]}\n')
                if auto_users[2] != 1:
                    text_info.append(f'  *›* {auto_users[2]}\n')
                if auto_users[3] != 1:
                    text_info.append(f'  *›* {auto_users[3]}\n')

            str_info = ''.join(text_info)
            bot.send_message(message.chat.id, str_info, parse_mode= "Markdown")

# Указать автомобиль(Марку)
def user_answer_auto(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, '*Вы успешно отменили регистрацию автомобиля.*', parse_mode= "Markdown")
    elif len(list(message.text)) < 5:
        bot.send_message(message.chat.id, '*Тебе нужно указать марку автомобиля полностью.* [_Пример: Tayota Mark II, 2001_]', parse_mode= "Markdown")
    else:
        global marka_auto
        marka_auto = message.text
        gos_number_auto = bot.send_message(message.chat.id, '*Супер, принял твоё сообщение!*\n'
                                          'Теперь укажи госурадственный номер автомобиля. [_Пример: В211АТ38_]', parse_mode= "Markdown")
        bot.register_next_step_handler(gos_number_auto, user_answer_number)

# Указать номер автомобиля
def user_answer_number(message):
    if message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, '*Вы успешно отменили регистрацию автомобиля.*', parse_mode= "Markdown")

    elif len(list(message.text)) < 8:
        bot.send_message(message.chat.id, '*Тебе нужно указать полный государственный номер.* [_Пример:_ В211АТ38]', parse_mode= "Markdown")
    else:
        global number_auto
        number_auto = message.text
        markup_inline = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Всё правильно', callback_data='next_step')
        item_reverse = types.InlineKeyboardButton(text='Повторить', callback_data='revregist')
        markup_inline.add(item_next, item_reverse)
        bot.send_message(message.chat.id, '*Отлично, получил твоё сообщение!*\n\n'
                                          'Теперь, самое время проверить данные:\n'
                                          f'*1.* Марка автомобиля: __{marka_auto}__'
                                          f'*2.* Государственный номер: __{number_auto}__\n\n'
                                          'Если все данные введены верно, нажимай на кнопку "*Всё правильно*"\n'
                                          'В случае, если ты хочешь заполнить данные сначала, нажми "*Повторить*"', parse_mode= "Markdown", reply_markup=markup_inline)

@bot.message_handler(commands=['help']) # /help
def help_command(message):
    markup_inline = types.InlineKeyboardMarkup()
    item_one = types.InlineKeyboardButton(text='Удалить', callback_data='delete_help')
    markup_inline.add(item_one)

    if message.from_user.id in [330435662, 532678880]:
        bot.send_message(message.chat.id, '_Команды бота:_'
                                          '\n*/start* — Начать общение с ботом'
                                          '\n*/mycar* — Список автомобилей в личной коллекции'
                                          '\n*/editcar* — Меню управленя коллекцией автомобилей'
                                          '\n\n_Команды администратора:_'
                                          '\n*Создать гонку* — Начать создавать гонку'
                                          '\n*/users* — Список зарегистрированных на рассылку пользователей'
                                          '\n*/info [id]* — Информация о юзере по ID можно найти в /users'
                                          '\n*/delete_rise* — Удалить гонку'
                                          '\n*/delete_user id* — Удалить пользователя из базы данных рассылки и гонок по ID'
                                          '\n*/rise_users* - Пользователи зарегистрированные в гонке', reply_markup=markup_inline, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, '_Команды бота:_'
                                          '\n*/start* — Начать общение с ботом'
                                          '\n*/mycar* — Список автомобилей в личной коллекции'
                                          '\n*/editcar* — Меню управленя коллекцией автомобилей', reply_markup=markup_inline, parse_mode="Markdown")

@bot.message_handler(commands=['delete_rise']) # Удаление гонки
def delete_rise_by_owner(message):
    if message.from_user.id in [330435662, 532678880]:
        if users.count_documents({"type": "rise"}) == 0:
            bot.send_message(message.chat.id, '*На данный момент нет ни одной активной гонки.*', parse_mode= "Markdown")
        else:
            info_rise = users.find_one({"type": "rise"})
            markup_inline = types.InlineKeyboardMarkup()
            item_yes = types.InlineKeyboardButton(text='Да', callback_data='accept_delete_rise')
            item_no = types.InlineKeyboardButton(text='Нет', callback_data='decline_delete_rise')
            markup_inline.add(item_yes, item_no)
            bot.send_message(message.chat.id, f'Вы действительно желаете удалить гонку на *{info_rise["time_date"]}* в *{info_rise["time_start"]}*?'
                             , parse_mode= "Markdown", reply_markup=markup_inline)

@bot.message_handler(commands=['mycar']) # /mycar
def get_car_user(message):
    text_info = []
    if users.count_documents({"ids": message.from_user.id, "type": "going_user"}) == 0:
        markup_inline = types.InlineKeyboardMarkup()
        item_add = types.InlineKeyboardButton(text='Добавить', callback_data='add_auto')
        markup_inline.add(item_add)
        add_auto = bot.send_message(message.chat.id, '*На данный момент, у Вас нет зарегистрированных автомобилей.*\n'
                                          'Для того что бы добавить автомобиль в свою коллекцию, нажмите на кнопку "*Добавить*"', parse_mode= "Markdown", reply_markup=markup_inline)
    else:
        text_info.append('*Автомобили из Вашей коллекции:*\n')
        auto_users = users.find_one({"ids": message.from_user.id, "type": "going_user"})["auto"]
        if auto_users[0] != 1:
            text_info.append(f'  *›* {auto_users[0]}\n')
        if auto_users[1] != 1:
            text_info.append(f'  *›* {auto_users[1]}\n')
        if auto_users[2] != 1:
            text_info.append(f'  *›* {auto_users[2]}\n')
        if auto_users[3] != 1:
            text_info.append(f'  *›* {auto_users[3]}\n')

        markup_inline = types.InlineKeyboardMarkup()
        item_add = types.InlineKeyboardButton(text='Добавить', callback_data='add_auto')
        item_edit = types.InlineKeyboardButton(text='Изменить', callback_data='edit_auto')
        item_delete = types.InlineKeyboardButton(text='Удалить', callback_data='delete_auto')
        if len(text_info) - 1 < 4:
            markup_inline.add(item_add, item_edit, item_delete)
        else:
            markup_inline.add(item_edit, item_delete)

        str_text = ''.join(text_info)
        bot.send_message(message.chat.id, str_text, parse_mode= "Markdown", reply_markup=markup_inline)

@bot.message_handler(commands=['editcar']) # Редактировать автомобили
def edit_car_user(message):
    if users.count_documents({"ids": message.from_user.id, "type": "going_user"}) == 0:
        markup_inline = types.InlineKeyboardMarkup()
        item_add = types.InlineKeyboardButton(text='Добавить', callback_data='add_auto')
        markup_inline.add(item_add)
        add_auto = bot.send_message(message.chat.id, '*На данный момент, у Вас нет зарегистрированных автомобилей.*\n'
                                          'Для того что бы добавить автомобиль в свою коллекцию, нажмите на кнопку "*Добавить*"', parse_mode= "Markdown", reply_markup=markup_inline)
    else:
        markup_inline = types.InlineKeyboardMarkup()
        item_add = types.InlineKeyboardButton(text='Добавить', callback_data='add_auto')
        item_edit = types.InlineKeyboardButton(text='Изменить', callback_data='edit_auto')
        item_delete = types.InlineKeyboardButton(text='Удалить', callback_data='delete_auto')

        text_info = []
        text_info.append('*Автомобили из Вашей коллекции:*\n')
        auto_users = users.find_one({"ids": message.from_user.id, "type": "going_user"})["auto"]
        if auto_users[0] != 1:
            text_info.append(f'  *›* {auto_users[0]}\n')
        if auto_users[1] != 1:
            text_info.append(f'  *›* {auto_users[1]}\n')
        if auto_users[2] != 1:
            text_info.append(f'  *›* {auto_users[2]}\n')
        if auto_users[3] != 1:
            text_info.append(f'  *›* {auto_users[3]}\n')

        if len(text_info) - 1 >= 4:
            text_info.append('\nНа данный момент, коллекция переполнена _(4/4)_\n**Доступные действия:**'
                          '\n*›* __Изменить__ автомобиль'
                          '\n*›* __Удалить__ автомобиль')
            str_text = ''.join(text_info)
            markup_inline.add(item_edit, item_delete)
            bot.send_message(message.chat.id, str_text, parse_mode= "Markdown", reply_markup=markup_inline)
        else:
            markup_inline.add(item_add, item_edit, item_delete)
            text_info.append('\nВам доступны следущие действия:'
                             '\n*›* __Добавить__ автомобиль'
                             '\n*›* __Изменить__ автомобиль'
                             '\n*›* __Удалить__ автомобиль')
            str_text = ''.join(text_info)
            bot.send_message(message.chat.id, str_text, parse_mode= "Markdown", reply_markup=markup_inline)

@bot.message_handler(commands=['rise_users']) # Список участников гонки
def get_rise_user_active(message):
    if message.from_user.id in [330435662, 532678880]:
        text_info = ['*Список участников гонки:*\n\n']
        for user in users.find({"type": "user_in_rise"}):
            text_info.append(f'_{user["tag"]} - {user["auto"]}_\n')

        str_text = ''.join(text_info)
        bot.send_message(message.chat.id, str_text, parse_mode= "Markdown")

@bot.message_handler(commands=['dbi']) # Список участников гонки
def delete_user_on_rise_by_id(message):
    if message.from_user.id in [330435662, 532678880]:
        if users.count_documents({"type": "user_in_rise", "tag": message.text.split(' ')[1]}) == 0:
            bot.send_message(message.chat.id, '_Такого пользователя нет._', parse_mode= "Markdown")
        else:
            users.delete_one({"type": "user_in_rise", "tag": message.text.split(' ')[1]})
            bot.send_message(message.chat.id, '_Пользователь удалён._', parse_mode= "Markdown")

@bot.callback_query_handler(func=lambda call: True) # Ответы на инлайны
def answer(call):
    global index_send
    # Удаление /help
    if call.data == 'delete_help': bot.delete_message(call.message.chat.id, call.message.id)

    # Регистрация на рассылку
    if call.data == 'go':
        if users.count_documents({"city": 'Angarsk', "ids": call.from_user.id}) == 0:
            users.insert_one({"city": 'Angarsk', "ids": call.from_user.id,
                              'user_name': f'{call.from_user.first_name} {call.from_user.last_name}',
                              "tag": f'@{call.from_user.username}',
                              "type": "Рассылка",
                              "chat_id": call.message.chat.id})

            markup_inline = types.InlineKeyboardMarkup()
            markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item_one = types.InlineKeyboardButton(text='Пропустить регистрацию', callback_data='register')
            markup_inline.add(item_one)
            item_go = types.KeyboardButton('Зарегистрироваться!')
            markup_reply.add(item_go)
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, '*Записал тебя в базу данных участников!*\n'
                                                   'Ты можешь зарегистрировать себя сейчас, для того что бы не тратить на это время в дальнейшем\n'
                                                   'Для прохождения регистриции жми на кнопку "*Регистрация*"\n\n'
                                                   'Так же, список всех команд ты сможешь найти тут - */help*', parse_mode= "Markdown", reply_markup=markup_reply)

        else:
            msg = bot.send_message(call.message.chat.id, 'Дружище, я всё понимаю, страсть к гонкам, но ты уже записан в базу!')
            time.sleep(10)
            bot.delete_message(call.message.chat.id, msg.id)

    # Повторная регистрация авто
    if call.data == 'revregist':
        bot.delete_message(call.message.chat.id, call.message.id)
        auto_mark = bot.send_message(call.message.chat.id, '*Ну давай пройдём регистрацию заново, коли тебе так угодно.*\n\n'
                                     'Тебе необходимо указать следущие данные, будь внимательнее:\n'
                                     '*1.* Марку автомобиля [_Пример: Toyota Mark II, 2001_]\n'
                                     '*2.* Государственный номер автомобиля [_Пример: В211АТ38_]\n\n'
                                     'Давай начнём с марки, напиши на каком автомобиле ты хочешь участвовать.\n\n'
                                     'Для того что бы отменить действие, введи слово "*Отмена*"', parse_mode= "Markdown")
        bot.register_next_step_handler(auto_mark, user_answer_auto)

    # Пропуск регистрации
    if call.data == 'register':
        bot.delete_message(call.message.chat.id, call.message.id)
        bot.send_message(call.message.chat.id, '*Ну... Хорошо, зарегистрируешься потом*\n'
                                               '*Тебе остаётся ждать информационной рассылки!*\n'
                                               '*До скорого!*', parse_mode= "Markdown")

    # Удаление/изменение автомобиля
    if call.data in ['delete_auto', 'edit_auto']:
        markup_inline = types.InlineKeyboardMarkup()
        text_info = []
        text_info.append('*Автомобили из Вашей коллекции:*\n')
        auto_users = users.find_one({"ids": call.from_user.id, "type": "going_user"})["auto"]
        if auto_users[0] != 1:
            if call.data.split('_')[0] == 'delete':
                item_one = types.InlineKeyboardButton(text= f'{auto_users[0]}', callback_data='del_auto_one')
            elif call.data.split('_')[0] == 'edit':
                item_one = types.InlineKeyboardButton(text= f'{auto_users[0]}', callback_data='edit_auto_one')
            markup_inline.add(item_one)
            text_info.append(f'  *›* {auto_users[0]}\n')
        if auto_users[1] != 1:
            if call.data.split('_')[0] == 'delete':
                item_two = types.InlineKeyboardButton(text= f'{auto_users[1]}', callback_data='del_auto_two')
            elif call.data.split('_')[0] == 'edit':
                item_two = types.InlineKeyboardButton(text= f'{auto_users[1]}', callback_data='edit_auto_two')
            markup_inline.add(item_two)
            text_info.append(f'  *›* {auto_users[1]}\n')
        if auto_users[2] != 1:
            if call.data.split('_')[0] == 'delete':
                item_three = types.InlineKeyboardButton(text= f'{auto_users[2]}', callback_data='del_auto_three')
            elif call.data.split('_')[0] == 'edit':
                item_three = types.InlineKeyboardButton(text=f'{auto_users[2]}', callback_data='edit_auto_three')
            markup_inline.add(item_three)
            text_info.append(f'  *›* {auto_users[2]}\n')
        if auto_users[3] != 1:
            if call.data.split('_')[0] == 'delete':
                item_four = types.InlineKeyboardButton(text= f'{auto_users[3]}', callback_data='del_auto_four')
            elif call.data.split('_')[0] == 'edit':
                item_four = types.InlineKeyboardButton(text=f'{auto_users[3]}', callback_data='edit_auto_four')
            markup_inline.add(item_four)
            text_info.append(f'  *›* {auto_users[3]}\n')

        if call.data.split('_')[0] == 'delete':
            text_info.append('\n*Какой автомобиль Вы хотите удалить?*')
        elif call.data.split('_')[0] == 'edit':
            text_info.append('\n*Какой автомобиль Вы хотите изменить?*')
        str_text = ''.join(text_info)
        bot.delete_message(call.message.chat.id, call.message.id)
        bot.send_message(call.message.chat.id, str_text, parse_mode= "Markdown", reply_markup=markup_inline)

    # Удаление автомобиля по index
    if call.data in ['del_auto_one', 'del_auto_two', 'del_auto_three', 'del_auto_four']:
        index = {"one": 0, "two": 1, "three": 2, "four": 3}
        number_index = call.data.split('_')[2]

        auto_users = users.find_one({"ids": call.from_user.id, "type": "going_user"})["auto"]
        autoname = auto_users[index[number_index]]
        auto_users.remove(auto_users[index[number_index]])
        auto_users.insert(index[number_index], 1)
        users.update_one({"ids": call.from_user.id, "type": "going_user"}, {"$set": {"auto": auto_users}})
        bot.delete_message(call.message.chat.id, call.message.id)
        bot.send_message(call.message.chat.id, f'*Вы успешно удалили из своей коллекции автомобиль:* _{autoname}_')

        text_info = []
        text_info.append('*Актуальные автомобили из Вашей коллекции:*\n')
        auto_users = users.find_one({"ids": call.from_user.id, "type": "going_user"})["auto"]
        if auto_users[0] != 1:
            text_info.append(f'  *›* {auto_users[0]}\n')
        if auto_users[1] != 1:
            text_info.append(f'  *›* {auto_users[1]}\n')
        if auto_users[2] != 1:
            text_info.append(f'  *›* {auto_users[2]}\n')
        if auto_users[3] != 1:
            text_info.append(f'  *›* {auto_users[3]}\n')

        str_text = ''.join(text_info)
        bot.send_message(call.message.chat.id, str_text, parse_mode= "Markdown")

    # Изменение автомобиля по index
    if call.data in ['edit_auto_one', 'edit_auto_two', 'edit_auto_three', 'edit_auto_four']:
        index = {"one": 0, "two": 1, "three": 2, "four": 3}
        number_index = call.data.split('_')[2]

        auto_users = users.find_one({"ids": call.from_user.id, "type": "going_user"})["auto"]
        autoname = auto_users[index[number_index]]
        auto_users.remove(auto_users[index[number_index]])
        auto_users.insert(index[number_index], 1)
        users.update_one({"ids": call.from_user.id, "type": "going_user"}, {"$set": {"auto": auto_users}})
        bot.delete_message(call.message.chat.id, call.message.id)
        auto_mark = bot.send_message(call.message.chat.id, f'*Так-с, как хочешь, меняем автомобиль* _{autoname}_!\n\n'
                                                           'Укажите параметры нового автомобиля:\n'
                                                           '*1.* Марку автомобиля [_Пример: Toyota Mark II, 2001_]\n'
                                                           '*2.* Государственный номер автомобиля [_Пример: В211АТ38_]\n\n'
                                                           '*Давай начнём с марки, напиши на каком автомобиле ты хочешь участвовать.*\n\n'
                                                           'Для того что бы отменить действие, введи слово "*Отмена*"', parse_mode= "Markdown")
        bot.register_next_step_handler(auto_mark, user_answer_auto)

    # Регистрация автомобиля
    if call.data == 'add_auto':
        bot.delete_message(call.message.chat.id, call.message.id)
        auto_mark = bot.send_message(call.message.chat.id, '*Так-с, ну давай попробуем зарегистрировать тебя!*\n\n'
                                                      'Для того, что бы ты смог принять участие в гонке, тебе необходимо указать следущие данные:\n'
                                                      '*1.* Марку автомобиля [_Пример: Toyota Mark II, 2001_]\n'
                                                      '*2.* Государственный номер автомобиля [_Пример: В211АТ38_]\n\n'
                                                      '*Давай начнём с марки, напиши на каком автомобиле ты хочешь участвовать.*\n\n'
                                                      'Для того что бы отменить действие, введи слово "*Отмена*"', parse_mode= "Markdown")
        bot.register_next_step_handler(auto_mark, user_answer_auto)

    # Одобрение гонки
    if call.data == 'accept_rise':
        bot.send_message(call.message.chat.id, '*Данные гонки сохранены.*', parse_mode= "Markdown")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        #532678880
        markup_inline = types.InlineKeyboardMarkup()
        item_one = types.InlineKeyboardButton(text='Принять участие', callback_data='in_rise_accept')
        markup_inline.add(item_one)
        text_info = []
        info_rise = users.find_one({"type": "rise", "owner": call.from_user.id})
        text_info.append('*Эй, водила! У меня для тебя отличная новость!*\nНамечается новая гонка.\n\n'f'   *›* Дата: *{info_rise["time_date"]}*\n'
                         f'   *›* Время: *{info_rise["time_start"]}*\n')
        if info_rise["timeout"] != 0: text_info.append(f'   *›* Максимальное время за которое нужно проехать трек: *{info_rise["timeout"]}*\n')
        if info_rise["dice"] != 0: text_info.append(f'   *›* Взнос с каждого участника: *{info_rise["dice"]}*\n')
        text_info.append('\nДля того что бы принять участие в гонке, нажмите "*Принять участие*"')
        str_text = ''.join(text_info)
        for user in users.find({"type": "Рассылка"}):
            bot.send_message(user["chat_id"], str_text, parse_mode= "Markdown", reply_markup=markup_inline)

    # Отмена гонки
    if call.data == 'delete_rise':
        users.update_one({"type": "rise", "owner": call.from_user.id}, {"$set": {"dice": 0}})
        users.delete_one({"type": "rise", "owner": call.from_user.id})
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        bot.send_message(call.message.chat.id, '*Окей, гонка успешно удалена!*', parse_mode= "Markdown")

    # Согласие на участие в гонке
    if call.data == 'in_rise_accept':
        if users.count_documents({"type": "rise"}) == 0:
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, '*Данная гонка уже неактуальна.*', parse_mode= "Markdown")

        elif users.find_one({"type": "rise"})["active"] == 0:
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, '*Регистрация на данную гонку закрыта*', parse_mode= "Markdown")

        if users.count_documents({"ids": call.from_user.id, "type": "going_user"}) == 0:
            markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item_go = types.KeyboardButton('Зарегистрироваться!')
            markup_reply.add(item_go)
            bot.send_message(call.message.chat.id, '*Для того, что бы принять участие в гонке, Вам необходимо зарегистрировать хотя бы одну машину.*', parse_mode= "Markdown", reply_markup=markup_reply)

        if users.count_documents({"type": "user_in_rice", "id": call.from_user.id}) != 0:
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, '*Вы уже зарегистрированы в этой гонке.*')
        else:
            text_info = []
            text_info.append('*Для того, что бы принять участие, выбирите автомобиль на котором будете принимать участие.*\n\n'
                             '*Автомобили из Вашей коллекции:*\n')
            auto_users = users.find_one({"ids": call.from_user.id, "type": "going_user"})["auto"]
            markup_inline = types.InlineKeyboardMarkup()
            if auto_users[0] != 1:
                item_one = types.InlineKeyboardButton(text=f'{auto_users[0]}', callback_data='rise_auto_select_one')
                markup_inline.add(item_one)
                text_info.append(f'  *›* {auto_users[0]}\n')
            if auto_users[1] != 1:
                item_two = types.InlineKeyboardButton(text=f'{auto_users[1]}', callback_data='rise_auto_select_two')
                markup_inline.add(item_two)
                text_info.append(f'  *›* {auto_users[1]}\n')
            if auto_users[2] != 1:
                item_three = types.InlineKeyboardButton(text=f'{auto_users[2]}', callback_data='rise_auto_select_three')
                markup_inline.add(item_three)
                text_info.append(f'  *›* {auto_users[2]}\n')
            if auto_users[3] != 1:
                item_four = types.InlineKeyboardButton(text=f'{auto_users[3]}', callback_data='rise_auto_select_four')
                markup_inline.add(item_four)
                text_info.append(f'  *›* {auto_users[3]}\n')

            str_text = ''.join(text_info)
            bot.send_message(call.message.chat.id, str_text, parse_mode= "Markdown", reply_markup=markup_inline)

    # Подтверждение участия
    if call.data == 'user_in_rice':
        if users.count_documents({"type": "user_in_rise", "id": call.from_user.id}) == 0:
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, '*Данная функция не актуальна для Вас, так как Вы не успели подтвердить своё участие в этой гонке.*', parse_mode= "Markdown")
        else:
            users.update_one({"type": "user_in_rise", "id": call.from_user.id}, {"$set": {"accept": 1}})
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, '*Принято, до встречи на финише!*', parse_mode= "Markdown")

    # Выбор автомобиля для гонки по index
    if call.data in ['rise_auto_select_one', 'rise_auto_select_two', 'rise_auto_select_three', 'rise_auto_select_four']:
        index = {"one": 0, "two": 1, "three": 2, "four": 3}
        number_index = call.data.split('_')[3]

        text_info = []
        auto_users = users.find_one({"ids": call.from_user.id, "type": "going_user"})["auto"]
        autoname = auto_users[index[number_index]]
        bot.delete_message(call.message.chat.id, call.message.id)
        user_info = users.find_one({"type": "Рассылка", "ids": call.from_user.id})
        users.insert_one({"type": "user_in_rise", "id": call.from_user.id, "auto": autoname,
                          "user_name": user_info["user_name"], "tag": user_info["tag"],
                          "accept": 0})
        text_info.append(f'*Для гонки выбран автомобиль:* _{autoname}_\n')

        datetim = list(f'{time.strftime("%H")}:{time.strftime("%M")}')
        if datetim[0] == "0": datetim.remove("0")
        datetimec = ''.join(datetim)
        time_start = users.find_one({"type": "rise"})["time_start"]
        lender = str(timedelta(hours=int(time_start.split(':')[0]), minutes=int(time_start.split(':')[1])) -
                     timedelta(hours=int(datetimec.split(':')[0]), minutes=int(datetimec.split(':')[1])))

        dateday = f'{time.strftime("%d")}.{time.strftime("%m")}.20{time.strftime("%y")}'
        if dateday == users.find_one({"type": "rise"})["time_date"]:
            if int(lender.split(':')[1]) > 59:
                text_info.append('*Точка старта будет отправлена Вам за час до начала гонки.*')
                str_text = ''.join(text_info)
                bot.send_message(call.message.chat.id, str_text, parse_mode= "Markdown")
            else:
                text_info.append(f'*До старта гонки остаётся {lender.split(":")[1]} минут.*\n*Локация старта:*')
                str_text = ''.join(text_info)
                bot.send_message(call.message.chat.id, str_text, parse_mode= "Markdown")
                time_rise = users.find_one({"type": "rise"})
                bot.send_location(call.from_user.id, time_rise["start_position_latitude"], time_rise["start_position_longitude"])
        else:
            text_info.append('*Точка старта будет отправлена Вам за час до начала гонки.*')
            str_text = ''.join(text_info)
            bot.send_message(call.message.chat.id, str_text, parse_mode= "Markdown")

    # Подтверждение удаления гонки
    if call.data == 'accept_delete_rise':
        users.delete_one({"type": "rise"})
        bot.delete_message(call.message.chat.id, call.message.id)
        for i in users.find({"type": "user_in_rise"}):
            users.delete_one({"_id": i["_id"]})
        index_send = 0
        bot.send_message(call.message.chat.id, '*Вы успешно отменили гонку.*', parse_mode= "Markdown", reply_markup=types.ReplyKeyboardRemove())

    # Отмена удаления гонки
    if call.data == 'decline_delete_rise': bot.delete_message(call.message.chat.id, call.message.id)

    # Запись автомобиля в базу
    if call.data == 'next_step':
        if users.count_documents({"ids": call.from_user.id, "type": "going_user"}) == 0:
            users.insert_one({"ids": call.from_user.id, "type": "going_user", "auto": [f"{marka_auto} | [ {number_auto} ]", 1, 1, 1]})
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, '*Поздравляю тебя с успешным прохождением регистрации!*\n'
                                                   f'Теперь в базе данных зарегистрирован твой автомобиль *{marka_auto}* с государственным номером *{number_auto}*\n\n'
                                                   f'*До встречи!*', parse_mode= "Markdown")
        else:
            auto_users = users.find_one({"ids": call.from_user.id, "type": "going_user"})["auto"]
            for i in auto_users:
                if i == 1:
                    index = auto_users.index(i)
                    auto_users.remove(auto_users[index])
                    auto_users.insert(index, f"{marka_auto} | [ {number_auto} ]")
                    users.update_one({"ids": call.from_user.id, "type": "going_user"}, {"$set": {"auto": auto_users}})
                    bot.delete_message(call.message.chat.id, call.message.id)
                    bot.send_message(call.message.chat.id, '*Супер!*\n'
                                                           f'Теперь в твою коллекцию добавлен автомобиль *{marka_auto}* с государственным номером *{number_auto}*\n\n'
                                                           f'*До встречи!*', parse_mode= "Markdown")
                    break

# Место старта(Геолокация)
def dot_starter(message):
    if message.content_type != 'location':
        msg_dot_start = bot.send_message(message.chat.id, '*Ты должен отправить мне геолокацию через вложения.*', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_dot_start, dot_starter)
    else:
        users.insert_one({"type": "rise", "owner": message.from_user.id, "time_start": 1, "dice": 1, "timeout": 1, "time_date": 1,
                          "start_position_latitude": message.json["location"]["latitude"],
                          "start_position_longitude": message.json["location"]["longitude"],
                          "end_position_latitude": 1, "end_position_longitude": 1, "active": 1})
        msg_dot_finish = bot.send_message(message.chat.id, '*Супер!*\nЛокация для старта была успешно установлена!\n\n'
                                          '*Теперь отправь мне геопозицию финиша.*', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_dot_finish, dot_finisher)

# Место финиша (Геолокация)
def dot_finisher(message):
    if message.content_type != 'location':
        msg_dot_finish = bot.send_message(message.chat.id, '*Ты должен отправить мне геолокацию через вложения.*', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_dot_finish, dot_finisher)
    else:
        users.update_one({"type": "rise", "owner": message.from_user.id},
                         {"$set": {"end_position_latitude": message.json["location"]["latitude"],
                                   "end_position_longitude": message.json["location"]["longitude"]}})
        msg_date = bot.send_message(message.chat.id, '*Супер!*\nЛокация для финиша была успешно установлена!\n\n'
                                                           'Теперь отправь дату проведения гонки [_День, месяц и год, формат: дд.мм.гггг_].'
                                                           '\n_Пример: 25.07.2022_', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_date, date_start_rise)

# Дата старта
def date_start_rise(message):
    if len([i for i in list(message.text) if i == '.']) <= 1:
        msg_dot_finish = bot.send_message(message.chat.id, '*Ты должен отправить мне дату формата:* дд.мм.гг\n'
                                          '_Пример: 25.07.2022_', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_dot_finish, date_start_rise)
    else:
        users.update_one({"type": "rise", "owner": message.from_user.id}, {"$set": {"time_date": message.text}})
        msg_time = bot.send_message(message.chat.id, '*Отлично! Дата проведения гонки установлена!*\n\n'
                                                     'Теперь, тебе нужно указать время проведения гонки [чч.мм]\n_Пример: 22:00_', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_time, time_rise_start)

#Время старта
def time_rise_start(message):
    if len([i for i in list(message.text) if i == ':']) < 1:
        msg_time = bot.send_message(message.chat.id, '*Ты должен отправить мне время формата:* чч.мм\n'
                                          '_Пример: 20:00_', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_time, time_rise_start)
    else:
        users.update_one({"type": "rise", "owner": message.from_user.id}, {"$set": {"time_start": message.text}})
        msg_timeout = bot.send_message(message.chat.id, '*Отлично! Время проведения гонки установлена!*\n\n'
                                                     'Теперь, тебе нужно указать максимально допустимое время для прохождения трассы.[кол-во минут]\n'
                                                     '_Пример: 30_\n\n'
                                                     '*В случае, если этот параметр не имеет необходимости, укажи:* 0')
        bot.register_next_step_handler(msg_timeout, rise_timeout)

# Максимальный интервал
def rise_timeout(message):
    try: msg = int(message.text)
    except:
        msg_timeout = bot.send_message(message.chat.id, '*Ты должен отправить мне число*\n_Пример: 30_')
        bot.register_next_step_handler(msg_timeout, rise_timeout)
    else:
        if int(message.text) == 0:
            users.update_one({"type": "rise", "owner": message.from_user.id}, {"$set": {"timeout": 'Отсутствует'}})
            msg_dice = bot.send_message(message.chat.id, '*Параметр максимально допустимого времени на прохождение трассы отменён.*\n\n'
                                                         'Теперь, тебе нужно указать сумму взноса с каждого участника. *[сумма]*\n_Пример: 1000 рублей_\n\n'
                                                         '*В случае, если этот параметр не имеет необходимости, укажи:* 0', parse_mode= "Markdown")
        else:
            users.update_one({"type": "rise", "owner": message.from_user.id}, {"$set": {"timeout": int(message.text)}})
            msg_dice = bot.send_message(message.chat.id, '*Параметр максимально допустимого времени на прохождение трассы установлен.*\n\n'
                                                         'Теперь, тебе нужно указать сумму взноса с каждого участника. *[сумма]*\n_Пример: 1000 рублей_\n\n'
                                                         '*В случае, если этот параметр не имеет необходимости, укажи:* 0', parse_mode= "Markdown")
        bot.register_next_step_handler(msg_dice, rise_dice_on_ex)

# Взнос и вывод
def rise_dice_on_ex(message):
    text_info = []
    if message.text == "0":
        users.update_one({"type": "rise", "owner": message.from_user.id}, {"$set": {"dice": 'Отсутствует'}})
        text_info.append('*Хорошо. Участники не будут вносить взнос за участие в гонке.*\n\n')
    else:
        users.update_one({"type": "rise", "owner": message.from_user.id}, {"$set": {"dice": message.text}})
        text_info.append('*Супер! Сумма первоначального взноса для участников установлена!*\n\n')

    info_rise = users.find_one({"type": "rise", "owner": message.from_user.id})
    text_info.append('*сталось проверить, все ли данные заполнены верно:*\n'
                     f'   *›* Дата проведения гонки: _{info_rise["time_date"]}_\n'
                     f'   *›* Время проведения гонки: _{info_rise["time_start"]}_\n'
                     f'   *›* Максимальное время за которое нужно проехать трек: _{info_rise["timeout"]} минут_\n'
                     f'   *›* Взнос с каждого участника: _{info_rise["dice"]}_')
    str_text = ''.join(text_info)
    bot.send_message(message.chat.id, str_text, parse_mode= "Markdown")
    bot.send_message(message.chat.id, '*Место старта:*', parse_mode= "Markdown")
    bot.send_location(message.chat.id, info_rise["start_position_latitude"], info_rise["start_position_longitude"])
    bot.send_message(message.chat.id, '*Место финиша:*', parse_mode= "Markdown")
    bot.send_location(message.chat.id, info_rise["end_position_latitude"], info_rise["end_position_longitude"])
    markup_inline = types.InlineKeyboardMarkup()
    item_yes = types.InlineKeyboardButton(text='Всё верно', callback_data='accept_rise')
    item_no = types.InlineKeyboardButton(text='Отмена', callback_data='delete_rise')
    markup_inline.add(item_yes, item_no)
    bot.send_message(message.chat.id, '*Всё ли заполнено верно?*', parse_mode= "Markdown", reply_markup=markup_inline)

def on_ready():
    print('██████╗░░█████╗░████████╗  ░█████╗░░█████╗░████████╗██╗██╗░░░██╗░█████╗░████████╗███████╗██████╗░\n'
          '██╔══██╗██╔══██╗╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝██║██║░░░██║██╔══██╗╚══██╔══╝██╔════╝██╔══██╗\n'
          '██████╦╝██║░░██║░░░██║░░░  ███████║██║░░╚═╝░░░██║░░░██║╚██╗░██╔╝███████║░░░██║░░░█████╗░░██║░░██║\n'
          '██╔══██╗██║░░██║░░░██║░░░  ██╔══██║██║░░██╗░░░██║░░░██║░╚████╔╝░██╔══██║░░░██║░░░██╔══╝░░██║░░██║\n'
          '██████╦╝╚█████╔╝░░░██║░░░  ██║░░██║╚█████╔╝░░░██║░░░██║░░╚██╔╝░░██║░░██║░░░██║░░░███████╗██████╔╝\n'
          '╚═════╝░░╚════╝░░░░╚═╝░░░  ╚═╝░░╚═╝░╚════╝░░░░╚═╝░░░╚═╝░░░╚═╝░░░╚═╝░░╚═╝░░░╚═╝░░░╚══════╝╚═════╝░')
    bot.send_message(-792645565, 'active bro')

@bot.message_handler(content_types=['text']) # Обработчик сообщения
def send_text(message):
    global index_send
    if message.text.lower() == 'привет': bot.send_message(message.chat.id, 'Приветик)')

    if message.text.lower() == 'зарегистрироваться!':
        if users.count_documents({"ids": message.from_user.id, "type": "going_user"}) != 0:
            bot.send_message(message.chat.id, '*Хм.. Вы уже есть в моей базе данных!*\n*Для регистрации автомобиля используйте /editcar*', parse_mode= "Markdown")
        else:
            auto_mark = bot.send_message(message.chat.id, '*Так-с, ну давай попробуем зарегистрировать тебя!*\n\n'
                                              'Для того, что бы ты смог принять участие в гонке, тебе необходимо указать следущие данные:\n'
                                              '*1.* Марку автомобиля [_Пример: Toyota Mark II, 2001_]\n'
                                              '*2.* Государственный номер автомобиля [_Пример: В211АТ38_]\n\n'
                                              'Давай начнём с марки, напиши на каком автомобиле ты хочешь участвовать.\n\n'
                                              'Для того что бы отменить действие, введи "*Отмена*"', parse_mode= "Markdown", reply_markup = types.ReplyKeyboardRemove())
            bot.register_next_step_handler(auto_mark, user_answer_auto)

    if message.text == 'Создать гонку':
        if message.from_user.id in [330435662, 532678880]:
            if users.count_documents({"type": "rise"}) != 0:
                bot.send_message(message.chat.id, '*На данный момент уже создана гонка.*\n'
                                                  '*Для того что бы удалить её, используйте /delete_rise*', parse_mode= "Markdown")
            else:
                msg_start = bot.send_message(message.chat.id, 'Ты находишься в меню создания гонки!'
                                                  '\nДля того, что бы всё получилось, тебе нужно указать следущие параметры:\n\n'
                                                  '   *›* Место начала гонки *[Geo-Location]*\n'
                                                  '   *›* Место финиша гонки *[Geo-Location]*\n'
                                                  '   *›* Дата проведения гонки *[дд.мм.гггг]*\n'
                                                  '   *›* Время проведения гонки *[минуты]*\n'
                                                  '   *›* Максимальное время за которое нужно проехать трек *[чч.мм]* | Если требуется\n'
                                                  '   *›* Взнос с каждого участника *[Сумма]* | Если требуется', parse_mode= "Markdown")
                msg_dot_start = bot.send_message(message.chat.id,
                                                 '*Для начала, давай разберёмся с местом старта\nПоставь метку на карте и отправь мне геолокацию.*', parse_mode= "Markdown")
                bot.register_next_step_handler(msg_dot_start, dot_starter)

    if message.text == 'AAA^@!HJCGABISJDI@&!LKA:SKD<AW':
        bot.send_message(message.chat.id, '*Принял запрос, проверяю время*', parse_mode= "Markdown")
        if users.count_documents({"type": "rise"}) != 0 and users.find_one({"type": "rise"})["time_start"] != 1:
            time_rise = users.find_one({"type": "rise"})
            datetim = list(f'{time.strftime("%H")}:{time.strftime("%M")}')
            if datetim[0] == "0": datetim.remove("0")
            datetimec = ''.join(datetim)
            datetime = users.find_one({"type": "rise"})["time_start"]
            dateday = f'{time.strftime("%d")}.{time.strftime("%m")}.20{time.strftime("%y")}'

            time_start = time_rise["time_start"]

            time_give_location_x = str(timedelta(hours=int(time_start.split(':')[0]), minutes=int(time_start.split(':')[1])) - timedelta(minutes=5))
            time_give_location = f'{time_give_location_x.split(":")[0]}:{time_give_location_x.split(":")[1]}'

            time_start_five_x = str(timedelta(hours=int(time_start.split(':')[0]), minutes=int(time_start.split(':')[1])) - timedelta(minutes=30))
            time_start_five = f'{time_start_five_x.split(":")[0]}:{time_start_five_x.split(":")[1]}'

            accept_time_start_X = str(timedelta(hours=int(time_start.split(':')[0]), minutes=int(time_start.split(':')[1])) + timedelta(minutes=5))
            accept_time_start = f'{accept_time_start_X.split(":")[0]}:{accept_time_start_X.split(":")[1]}'

            end_rice_x = str(timedelta(hours=int(time_start.split(':')[0]), minutes=int(time_start.split(':')[1])) + timedelta(minutes=20))
            end_rice = f'{end_rice_x.split(":")[0]}:{end_rice_x.split(":")[1]}'

            time_finish = 0

            if dateday == time_rise["time_date"]:

                lender = str(timedelta(hours=int(time_start.split(':')[0]), minutes=int(time_start.split(':')[1])) -
                             timedelta(hours=int(datetimec.split(':')[0]), minutes=int(datetimec.split(':')[1])))

                if lender.split(':')[1] == '59' or int(lender.split(':')[1]) < 59:
                    if index_send < 1:
                        for user in users.find({"type": "user_in_rise"}):
                            index_send = 1
                            bot.send_message(user["id"], f"*Внимание, гонка начнётся через {lender.split(':')[1]} минут!*\n*Локация старта:*", parse_mode= "Markdown")
                            bot.send_location(user["id"], time_rise["start_position_latitude"], time_rise["start_position_longitude"])

                if datetimec == time_give_location:
                    if index_send < 2:
                        index_send = 2
                        if len([i["tag"] for i in users.find({"type": "user_in_rise"})]) < 1:
                            for user in users.find({"type": "user_in_rise"}):
                                bot.send_message(user["id"], f"*Внимание, гонка на {time_rise['time_date']}({time_rise['time_start']}) отменена из за нехватки участников.*\n"
                                                                  f"*К сожалению, мы не можем проводить гонки, если количество участников меньше 4-х*\n\n"
                                                                  f"*До встречи на новых гонках!*", parse_mode= "Markdown")
                                bot.send_message(-1001618170960,
                                                 f"*Внимание, гонка на {time_rise['time_date']}({time_rise['time_start']}) отменена из за нехватки участников.*", parse_mode= "Markdown")
                                index_send = 0
                                users.delete_one({"type": "rise"})
                        else:
                            for user in users.find({"type": "user_in_rise"}):
                                markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                                item_finish = types.KeyboardButton('🏁 На финише')
                                item_dtp = types.KeyboardButton('Ⓜ Попал в ДТП')
                                item_teh = types.KeyboardButton('❗ Техническая проблема')
                                markup_reply.add(item_finish, item_dtp)
                                markup_reply.add(item_teh)
                                bot.send_message(user["id"], f"*Внимание, гонка начнётся через 5 минут!*\n"
                                                             f"После объявления старта, тебе будет необходимо нажать на кнопку '*Еду*' в течении *5-ти минут*, для того, что бы подтвердить своё участие.\n"
                                                             f"\n*До встречи на финише.*\n\n*Кстати, локация финиша:*", parse_mode= "Markdown")
                                bot.send_location(user["id"], time_rise["end_position_latitude"], time_rise["end_position_longitude"])
                                bot.send_message(user["id"], '*Тебе доступны 3 кнопки на клавиатуре, сейчас расскажу про каждую.*\n\n'
                                                             '🏁 *На финише* - Эту кнопку ты должен нажать после того, как финишировал на указанной локации.\n'
                                                             'Ⓜ *Попал в ДТП* - В случае, если ты попал в ДТП, нужно сообщить нам об этом, нажав на эту кнопку\n'
                                                             '❗ *Техническая проблема* - Если у твоего автомобиля появилась проблема технического характера, жми на эту кнопку!',
                                                 parse_mode= "Markdown", reply_markup=markup_reply)

                elif datetimec == time_start:
                    if index_send < 3:
                        for user in users.find({"type": "user_in_rise"}):
                            index_send = 3
                            markup_inline = types.InlineKeyboardMarkup()
                            item_one = types.InlineKeyboardButton(text='Еду',
                                                                  callback_data='user_in_rice')
                            markup_inline.add(item_one)
                            bot.send_message(user["id"], f"ПОГНАЛИИИИИИИИИ!!!!!!!!!!!!!!!!!!!!!\n\n"
                                                         f"Для того что бы подтвердить своё участие, нажмите кнопку 'Еду'", reply_markup=markup_inline)

                elif datetimec == accept_time_start:
                    if index_send < 4:
                        index_send = 4
                        for user in users.find({"type": "user_in_rise"}):
                            if user["accept"] == 0:
                                users.delete_one({"type": "user_in_rice", "_id": user["_id"]})
                                bot.send_message(user["id"], 'К сожалению, вы не успели подтвердить своё участие в гонке и были исключены.\n\n'
                                                             'До встречи на следующем заезде!', reply_markup = types.ReplyKeyboardRemove())

                elif time_rise["timeout"] != "Отсутствует":
                    time_finish_x = str(timedelta(hours=int(time_rise["time_start"].split(':')[0]), minutes=int(time_rise["time_start"].split(':')[1]))
                                        + timedelta(minutes=int(time_rise["timeout"])))
                    time_finish = f'{time_finish_x.split(":")[0]}:{time_finish_x.split(":")[1]}'
                    if datetimec == time_finish:
                        for user in users.find({"type": "user_in_rise"}):
                            if user["accept"] == 1:
                                bot.send_message(user["id"], 'Гонка была успешно завершена по истечению максимального времени её прохождения.\n'
                                                             'К сожалению, ты не успел преодолеть весь её участок и финишировать.\n\nДо встречи!.',
                                                             reply_markup=types.ReplyKeyboardRemove())
                            else:
                                bot.send_message(user["id"], 'Гонка была успешно завершена по истечению максимального времени её прохождения.\n'
                                                             'Мы очень рады, что Вы успели её преодолеть.\n\nДо встречи!.',
                                                             reply_markup=types.ReplyKeyboardRemove())
                            users.delete_one({"type": "user_in_rise", "_id": user["_id"]})
                        users.delete_one({"type": "rise"})
                        bot.send_message(-1001618170960, 'Гонка была успешно завершена по истечению максимального времени её прохождения.')
                        index_send = 0

                elif datetimec == end_rice:
                    for user in users.find({"type": "user_in_rise"}):
                        bot.send_message(user["id"],'Гонка была успешно завершена.\nДо встречи!', reply_markup=types.ReplyKeyboardRemove())
                        users.delete_one({"type": "user_in_rise", "_id": user["_id"]})
                    users.delete_one({"type": "rise"})
                    bot.send_message(-1001618170960, 'Гонка была успешно завершена.')
                    index_send = 0

                if lender.split(':')[1] == '30' or int(lender.split(':')[1]) < 30: users.update_one({"type": "rise"}, {
                    "$set": {"active": 0}})

    if message.text == '🏁 На финише':
        if users.count_documents({"type": "rise"}) == 0 or users.find_one({"type": "user_in_rise", "id": message.from_user.id})["accept"] == 0:
            bot.send_message(message.chat.id, '*Ошибка вызова №4*\n\nВозможные причины возникновения ошибки:\n *- В данный момент не проводится гонок.*'
                                              '\n *- Вы не подтвердили своё участие в гонке.*\n *- Вами была нажата кнопка "ДТП" или "Тех.Неполадка"*')
        else:
            # "finish_time": 0, "time_rice_going": 0
            datetim = list(f'{time.strftime("%H")}:{time.strftime("%M")}')
            if datetim[0] == "0": datetim.remove("0")
            datetimec = ''.join(datetim)
            time_start = users.find_one({"type": "rise"})["time_start"]
            time_finish_x = str(timedelta(hours=int(datetimec.split(':')[0]), minutes=int(datetimec.split(':')[1])) - timedelta(hours=int(time_start.split(':')[0]), minutes=int(time_start.split(':')[1])))
            time_finish = f'{time_finish_x.split(":")[0]}:{time_finish_x.split(":")[1]}'

            users.update_one({"type": "user_in_rise", "id": message.from_user.id}, {"$set": {"accept": 0}})
            users.insert_one({"type": "results", "id": message.from_user.id, "start_time": time_start, "finish_time": datetimec, "time_rice_going": time_finish})
            bot.send_message(message.chat.id, f'*Супер!*\n*Время прибытия на финиш:* __{datetimec}__\n\n'
                                              f'*Данная гонка пройдена тобой за {time_finish} минут.*\n\n*До встречи!*',
                             parse_mode= "Markdown", reply_markup=types.ReplyKeyboardRemove())

    if message.text == 'Ⓜ Попал в ДТП':
        if users.count_documents({"type": "rise"}) == 0 or users.find_one({"type": "user_in_rise", "id": message.from_user.id})["accept"] == 0:
            bot.send_message(message.chat.id, '*Ошибка вызова №4*\n\nВозможные причины возникновения ошибки:\n *- В данный момент не проводится гонок.*'
                                              '\n *- Вы не подтвердили своё участие в гонке.*\n *- Вами ранее была нажата кнопка "ДТП" или "Тех.Неполадка"*', parse_mode= "Markdown")
        else:
            bot.send_message(message.chat.id, '*Благодарим Вас за то, что сообщили нам данную информацию.*\n'
                                              '*Я перенаправил её в чат организаторов.*\n\n'
                                              '*Ваше участие в данной гонке завершено.*', parse_mode= "Markdown", reply_markup=types.ReplyKeyboardRemove())
            user = users.find_one({"type": "user_in_rise", "id": message.from_user.id})
            users.update_one({"type": "user_in_rise", "id": message.from_user.id}, {"$set": {"accept": 0}})
            bot.send_message(-1001618170960, f'*Внимание!*\n*Участником {user["tag"]} была нажата кнопка "Попал в ДТП".*', parse_mode= "Markdown")

    if message.text == '❗ Техническая проблема':
        if users.count_documents({"type": "rise"}) == 0 or users.find_one({"type": "user_in_rise", "id": message.from_user.id})["accept"] == 0:
            bot.send_message(message.chat.id, '*Ошибка вызова №4*\n\nВозможные причины возникновения ошибки:\n *- В данный момент не проводится гонок.*'
                                              '\n *- Вы не подтвердили своё участие в гонке.*\n *- Вами ранее была нажата кнопка "ДТП" или "Тех.Неполадка"*', parse_mode= "Markdown")
        else:
            bot.send_message(message.chat.id, '*Благодарим Вас за то, что сообщили нам данную информацию.*\n'
                                              '*Я перенаправил её в чат организаторов.*\n\n'
                                              '*Ваше участие в данной гонке завершено.*', parse_mode= "Markdown", reply_markup=types.ReplyKeyboardRemove())
            user = users.find_one({"type": "user_in_rise", "id": message.from_user.id})
            users.update_one({"type": "user_in_rise", "id": message.from_user.id}, {"$set": {"accept": 0}})
            bot.send_message(-1001618170960, f'*Внимание!*\n*Участником {user["tag"]} была нажата кнопка "Техническая проблема".*', parse_mode= "Markdown")

    if message.text == 'test':
        markup_inline = types.InlineKeyboardMarkup()
        item_yes = types.InlineKeyboardButton(text='Всё верно', callback_data='accept_rise')
        item_no = types.InlineKeyboardButton(text='Отмена', callback_data='delete_rise')
        markup_inline.add(item_yes, item_no)
        bot.send_message(message.chat.id, '*test*'
                                          '\n*/test testtesttesttesttesttesttest tes ttesttesttesttesttest*'
                                          '\n_/test testtesttebstte sttestte sttesttesttes ttesttesttesttesttest_'
                                          '\n_/test testtesttestt es ttest t e sttest testtesttesttesttesttesttest_'
                                          '\n_/test testtesttestt est testtesttestt e sttesttest testtesttesttest_'
                                          '\n_/test testtesttesttesttesttesttesttesttest sttesttesttesttesttest_'
                                          '\n_/test testtesttestte sttest testtesttesttesttesttesttesttesttest_'
                                          '\n_/test testtesttesttesttes  ttesttestt esttesttestt esttesttesttest_'
                                          '\n_/test testtesttesttes testtesttes ttesttesttesttesttesttesttest_'
                                          '\n_/test testtesttesttestte sttesttes  ttes ttes ttes ttesttesttesttest_'
                                          '\n_/test testtesttesttesttesttesttesttesttest testtesttesttesttest_', reply_markup=markup_inline, parse_mode="Markdown")
    else:
        if message.chat.id == bot.user.id:
            bot.send_message(message.chat.id, '*Извини, но я не понимаю чего ты от меня хочешь.*\n*Список моих команд ты можешь увидеть в команле /help*', parse_mode= "Markdown")

if __name__ == '__main__':
    on_ready()
    bot.polling(none_stop=True, interval=0)
