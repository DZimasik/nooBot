# coder :- DZ
# -*- coding: utf-8 -*-

import datetime
import time
import config
import telebot
import random
from data import *
from telebot import types
from noolite_TX import *

bot = telebot.TeleBot(config.token)

def update_path(path):
    return '|'.join([str(random.randint(0, 999)), path.split('|')[-1]])

def backwards_path(path, backwards_steps):
    return update_path('/'.join(path.split('/')[:backwards_steps]))

def make_link(string):
    return ''.join(c for c in string if c not in '0123456789')

def show_keyboard(data=None, path=None, keys=None, mark_list=None, mark='', unmarked='', control=True, periphery=False, interpretation_by=None, service_buttons=None):
    buttons = list()
    perip_buttons = list()

    keyboard = types.InlineKeyboardMarkup(row_width=8)   

    if path:
        path = path.split(":")[0]
        if path.split("/")[-1] in keys: 
            path = path.split("/")
            path = "/".join(path[:-2])
    
    if keys:
        for key in keys:
            for table in data.keys():
                if data[table].get(key):
                    break

            if mark_list and key in mark_list: text=mark+data[table][key]["name"]
            else: text=unmarked+data[table][key]["name"]
            
            if table == "device":
                
                if interpretation_by == "position":
                    id_place = data[table][key]["ID_place"]
                    if id_place:
                        interpretation_name = data["place"][str(id_place)]["name"]
                        text = text+" ["+interpretation_name+"]"                    
                
                if control: control_button = types.InlineKeyboardButton(text=text, callback_data=path+"/dev/"+key)
                
                if data[table][key]["is_dimmable"] is True:
                    for to_mtrf_data in ['0', '28', '42', '56', '70', '84', '100', '128']:
                        perip_buttons.append(types.InlineKeyboardButton(text=">>", callback_data=path+"/dev/"+key+":6,1,"+to_mtrf_data))                
                elif data[table][key]["is_dimmable"] is False:
                    perip_buttons.append(types.InlineKeyboardButton(text="Выключить", callback_data=path+"/dev/"+key+":0,0,0"))
                    perip_buttons.append(types.InlineKeyboardButton(text="Включить", callback_data=path+"/dev/"+key+":2,0,0"))
                    
                if data[table][key]["serial"]:
                    pass
                
       
            elif table == "place":
                if control: control_button = types.InlineKeyboardButton(text=text, callback_data=path+"/pl/"+key)
                
            elif table == "preset":
                if control: control_button = types.InlineKeyboardButton(text=text, callback_data=path+"/pr/"+key)
            
            elif table == "owner":
                if control: control_button = types.InlineKeyboardButton(text=text, callback_data=path+"/ow/"+key) 
            
            elif table == "guest":
                if control: control_button = types.InlineKeyboardButton(text=text, callback_data=path+"/gu/"+key)
            
            elif table == "passer":
                if control: control_button = types.InlineKeyboardButton(text=text, callback_data=path+"/pa/"+key)        
                
            if control: buttons.append(control_button)
            if periphery and perip_buttons:
                buttons.append(perip_buttons.copy())
                perip_buttons.clear()
    
    if service_buttons: buttons.extend(service_buttons)     
   
    for button in buttons:
        if type(button) is list:
            keyboard.add(*button)
        else:
            keyboard.add(button)
    
    return keyboard    




@bot.message_handler(commands=['start'])
def start_bot(message):
   
    global data

    if not data["owner"]:
        form = database(name=message.from_user.first_name+" "+message.from_user.last_name, ID_user=message.from_user.id).user_struct
        free_ID = database.free_ID(data, "owner")
        data = database.new_row(data, "owner", form, free_ID)
        database.save(config.db_file, data)
        
    owner = database.view_rows(data, "owner", "id", message.from_user.id)
    guest = database.view_rows(data, "guest", "id", message.from_user.id)
    passer = database.view_rows(data, "passer", "id", message.from_user.id)
    
    main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    home = types.KeyboardButton(text="Дом \U0001F3E0")
    preset = types.KeyboardButton(text="Сценарии \U00002728")
    settings = types.KeyboardButton(text="Настройки \U00002699")
    subscribe = types.KeyboardButton(text="Подписаться \U00002705")
    
    if owner or guest:       
        if owner:
            main_keyboard.add(home, preset)
            main_keyboard.add(settings)
        elif guest:
            main_keyboard.add(home, preset)
        bot.send_message(message.from_user.id, text="Привет "+message.from_user.first_name+", я твой домашний бот, начнём работу!", reply_markup=main_keyboard)
    
    elif not passer:
        free_ID = database.free_ID(data, "passer")
        if free_ID is not None:
            main_keyboard.add(subscribe)
            bot.send_message(message.from_user.id, text="Отправте подписку для получения возможности управлять ботом", reply_markup=main_keyboard)
        else:
            bot.send_message(message.from_user.id, text="Простите, число подписчиков ограниченно")
    else:
        bot.send_message(message.from_user.id, text="Простите, но я не могу вас впустить, пока хозяин мне не разрешит")




@bot.message_handler(func=lambda message: True, content_types=['text'])
def main_keyboard_and_text(message):

    global data
    global callback
    global form

    owner = database.view_rows(data, "owner", "id", message.from_user.id)
    guest = database.view_rows(data, "guest", "id", message.from_user.id)
    passer = database.view_rows(data, "passer", "id", message.from_user.id)    
    
    if message.text == "Дом \U0001F3E0" and (owner or guest):
        keys = database.view_rows(data, "place")
        if keys:
            home = show_keyboard(data, update_path("view"), keys)
            bot.send_message(message.from_user.id, text="Комнаты", reply_markup=home)
        else:
            bot.send_message(message.from_user.id, text="Опаньки, похоже у вас ещё не добавлено ни одной комнаты. Для добавления комнат перейдите в раздел Настройки > Комнаты > Добавить комнату")
                
    elif message.text == "Сценарии \U00002728" and (owner or guest):
        keys = database.view_rows(data, "preset")
        if keys:
            preset = show_keyboard(data, update_path("view"), keys)
            bot.send_message(message.from_user.id, text="Сценарии", reply_markup=preset)
        else:
            bot.send_message(message.from_user.id, text="Хммм, похоже у вас ещё не настроены сценарии. Для настройки сценариев перейдите в раздел Настройки > Сценарии > Создать сценарий")
       
    elif message.text == "Настройки \U00002699" and owner:        
        place = types.InlineKeyboardButton(text="Комнаты", callback_data=update_path("pl_set"))
        device = types.InlineKeyboardButton(text="Устройства", callback_data=update_path("dev_set"))
        preset = types.InlineKeyboardButton(text="Сценарии", callback_data=update_path("pr_set"))
        users = types.InlineKeyboardButton(text="Пользователи", callback_data=update_path("us-s_set"))
        settings = show_keyboard(service_buttons=[place, device, preset, users])
        bot.send_message(message.from_user.id, "Настройки", reply_markup=settings)
        
    elif message.text == "Подписаться \U00002705" and not owner and not guest and not passer:
        free_ID = database.free_ID(data, "passer")
        if free_ID is not None:
            form[message.from_user.id] = database(name=message.from_user.first_name+" "+message.from_user.last_name, ID_user=message.from_user.id).user_struct
            data = database.new_row(data, "passer", form[message.from_user.id], free_ID)
            if database.save(config.db_file, data):
                remove_keyboard = types.ReplyKeyboardRemove()
                bot.send_message(message.from_user.id, text="Подписка отправлена, ожидайте ответа хозяина", reply_markup=remove_keyboard)                    
                for owner_id in data["owner"].keys():
                    bot.send_message(data["owner"][owner_id]["id"], text=message.from_user.first_name+" "+message.from_user.last_name+" хочет управлять вашим домом")
        else:
            bot.send_message(message.from_user.id, text="Простите, число подписчиков ограниченно")
            
    elif callback.get(message.from_user.id) and owner:
        
        call_data = callback[message.from_user.id]
        link = make_link(call_data.split('|')[-1])
        steps = call_data.split('|')[-1].split("/")    
            
        if link == "pl_set/add":
            free_ID = database.free_ID(data, "place")
            form[message.from_user.id] = database(name=message.text).other_struct
            data = database.new_row(data, "place", form[message.from_user.id], free_ID)
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[message.from_user.id], -1)) 
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[message.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            
            if database.save(config.db_file, data):            
                bot.send_message(message.from_user.id, text="Добавлена комната "+message.text, reply_markup=keyboard)
            
        elif link == "pl_set/corr/pl//rename":
            table = "place"
            place_id = steps[3]
            old_plase_name = data[table][place_id]["name"]
            new_place_name = message.text
            data[table][place_id]["name"] = new_place_name
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[message.from_user.id], -1)) 
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[message.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            
            if database.save(config.db_file, data):            
                bot.send_message(message.from_user.id, text="Комната "+old_plase_name+" переименована в "+new_place_name, reply_markup=keyboard)
        
        elif link == "dev_set/add/block":
            form[message.from_user.id]["name"] = message.text
            bind = types.InlineKeyboardButton(text="Привязать", callback_data=call_data+"/bind")
            cannel = types.InlineKeyboardButton(text="Отмена", callback_data=call_data+"/cannel")
            keyboard = show_keyboard(service_buttons=[bind, cannel])
            bot.send_message(message.from_user.id, text="Для привязки силового блока нажмите его сервисную кнопку, светодиод на блоке должен замигать. Далее передайте команду Привязать", reply_markup=keyboard)
        
        elif link == "dev_set/opt/dev//rename":
            table = "device"
            device_id = steps[3]
            old_device_name = data[table][device_id]["name"]
            new_device_name = message.text
            data[table][device_id]["name"] = new_device_name
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[message.from_user.id], -1)) 
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[message.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            
            if database.save(config.db_file, data):            
                bot.send_message(message.from_user.id, text="Устройство "+old_device_name+" переименовано в "+new_device_name, reply_markup=keyboard)
        
        elif link == "pr_set/add":
            form[message.from_user.id] = dict()
            form[message.from_user.id]["preset"] = database(name=message.text).other_struct
            form[message.from_user.id]["devices"] = dict()
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[message.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[message.from_user.id]+"/cannel")       
            keys = database.view_rows(data, "device")
            
            if keys:               
                keyboard = show_keyboard(data, callback[message.from_user.id], keys, interpretation_by="position", service_buttons=[back, cannel])
                bot.send_message(message.from_user.id, text="Выберите устройства, которое будут участвовать в сценарии "+message.text, reply_markup=keyboard)               
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.send_message(message.from_user.id, text="Похоже у вас нет привязанных устройств", reply_markup=keyboard)
                
        elif link == "pr_set/corr/pr//rename":
            table = "preset"
            preset_id = steps[3]
            old_preset_name = data[table][preset_id]["name"]
            new_preset_name = message.text
            data[table][preset_id]["name"] = new_preset_name
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[message.from_user.id], -1)) 
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[message.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            
            if database.save(config.db_file, data):            
                bot.send_message(message.from_user.id, text="Сценарий "+old_preset_name+" переименован в "+new_preset_name, reply_markup=keyboard)
         
    callback[message.from_user.id] = update_path("cannel")




@bot.callback_query_handler(func=lambda call: True)
def callback_from_buttons(call):

    global data
    global callback
    global form
    
    
    owner = database.view_rows(data, "owner", "id", call.from_user.id)
    guest = database.view_rows(data, "guest", "id", call.from_user.id)
    passer = database.view_rows(data, "passer", "id", call.from_user.id)    
    
    
    if owner or guest:
        print(str(datetime.datetime.now()), call.from_user.first_name, call.from_user.last_name, '>>', call.data)
        callback[call.from_user.id] = update_path(call.data)  
        link = make_link(callback[call.from_user.id].split('|')[-1])
        steps = callback[call.from_user.id].split('|')[-1].split("/")   

    if owner:
        if link == "pl_set":
            correct = types.InlineKeyboardButton(text="Редактировать комнату", callback_data=callback[call.from_user.id]+"/corr")
            add = types.InlineKeyboardButton(text="Добавить комнату", callback_data=callback[call.from_user.id]+"/add")
            keyboard = show_keyboard(service_buttons=[correct, add])        
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки комнат", reply_markup=keyboard)
                
        elif link == "pl_set/corr":
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keys = database.view_rows(data, "place")
            
            if keys:
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки комнат", reply_markup=keyboard)            
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Опаньки, похоже у вас ещё не добавлено ни одной комнаты. Для добавления комнат перейдите в раздел Настройки > Комнаты > Добавить комнату", reply_markup=keyboard)
                    
        elif link == "pl_set/corr/pl/":
            place_id = steps[3]
            place_name = data["place"][place_id]["name"]
            add_device = types.InlineKeyboardButton(text="Добавить устройства", callback_data=callback[call.from_user.id]+"/fill")
            del_device = types.InlineKeyboardButton(text="Убрать устройства", callback_data=callback[call.from_user.id]+"/empty")
            rename_place = types.InlineKeyboardButton(text="Переименовать комнату", callback_data=callback[call.from_user.id]+"/rename")       
            del_place = types.InlineKeyboardButton(text="Удалить комнату", callback_data=callback[call.from_user.id]+"/del")
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -2))         
            keyboard = show_keyboard(service_buttons=[add_device, del_device, rename_place, del_place, back, cannel]) 
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки комнаты "+place_name, reply_markup=keyboard)            
            
        elif link in ("pl_set/corr/pl//fill", "pl_set/corr/pl//fill/dev/"):
            place_id = steps[3]
            place_name = data["place"][place_id]["name"]        
            
            if link == "pl_set/corr/pl//fill": backwards_steps = -1
            elif link == "pl_set/corr/pl//fill/dev/": backwards_steps = -3

            save = types.InlineKeyboardButton(text="Сохранить \U0001F4BE", callback_data=callback[call.from_user.id]+"/save")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], backwards_steps))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")       
            keys = database.view_rows(data, "device", "ID_place", None)
            
            if keys: 
                if link == "pl_set/corr/pl//fill":
                    form[call.from_user.id] = list()
                elif link == "pl_set/corr/pl//fill/dev/":
                    device_id = steps[6]
                    if device_id in form[call.from_user.id]:
                        form[call.from_user.id].remove(device_id)
                    else:
                        form[call.from_user.id].append(device_id)

                if form[call.from_user.id]: buttons = [save, back, cannel]            
                else: buttons = [back, cannel]            
                
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, form[call.from_user.id], mark='\U00002714 ', service_buttons=buttons)
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Выберите устройства, которое хотите добавить в комнату "+place_name, reply_markup=keyboard)               
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Похоже свободных усторйств нет", reply_markup=keyboard)
                
        elif link == "pl_set/corr/pl//fill/dev//save":
            place_id = steps[3]
            place_name = data["place"][place_id]["name"]        
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -4))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            keys = form[call.from_user.id]
            
            if keys:
                device_names = list()
                for device_id in keys:
                    device_name = data["device"][device_id]["name"]
                    device_names.append(device_name)
                    data["device"][device_id]["ID_place"] = int(place_id)
                
                if database.save(config.db_file, data):
                    if len(device_names) == 1: text = "Устройство "+device_name+" добавлено в комнату "+place_name
                    else: text = "Устройства "+' и '.join([', '.join(device_names[:-1]), device_names[-1]])+" добавлены в комнату "+place_name  
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Вы ничего не добавили в комнату "+place_name, reply_markup=keyboard)
        
        elif link in ("pl_set/corr/pl//empty", "pl_set/corr/pl//empty/dev/"):
            place_id = steps[3]
            place_name = data["place"][place_id]["name"]
            
            if link == "pl_set/corr/pl//empty": backwards_steps = -1
            elif link == "pl_set/corr/pl//empty/dev/": backwards_steps = -3
        
            save = types.InlineKeyboardButton(text="Сохранить \U0001F4BE", callback_data=callback[call.from_user.id]+"/save")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], backwards_steps))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")            
            keys = database.view_rows(data, "device", "ID_place", int(place_id))
            
            if keys:              
                if link == "pl_set/corr/pl//empty":
                    form[call.from_user.id] = list() 
                elif link == "pl_set/corr/pl//empty/dev/":
                    device_id = steps[6]
                    if device_id in form[call.from_user.id]:
                        form[call.from_user.id].remove(device_id)
                    else:
                        form[call.from_user.id].append(device_id)             
                
                if form[call.from_user.id]: buttons = [save, back, cannel]            
                else: buttons = [back, cannel]
                
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, form[call.from_user.id], mark='\U00002714 ', service_buttons=buttons)  
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Выберите устройства, которое хотите убрать из комнаты "+place_name, reply_markup=keyboard)                       
            else: 
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Похоже комната "+place_name+" пуста", reply_markup=keyboard)
        
        elif link == "pl_set/corr/pl//empty/dev//save":
            place_id = steps[3]
            place_name = data["place"][place_id]["name"]        
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -4))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            keys = form[call.from_user.id]
            
            if keys:
                device_names = list() 
                for device_id in keys:
                    device_name = data["device"][device_id]["name"]
                    device_names.append(device_name)
                    data["device"][device_id]["ID_place"] = None 
                
                if database.save(config.db_file, data):
                    if len(device_names) == 1: text = "Устройство "+device_name+" убрано из комнаты "+place_name
                    else: text = "Устройства "+' и '.join([', '.join(device_names[:-1]), device_names[-1]])+" убраны из комнаты "+place_name  
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Вы ничего не убрали из комнаты "+place_name, reply_markup=keyboard)
        
        elif link == "pl_set/corr/pl//rename":
            place_id = steps[3]
            place_name = data["place"][place_id]["name"]            
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Введите новое название для комнаты "+place_name)
        
        elif link == "pl_set/corr/pl//del":
            place_id = steps[3]
            place_name = data["place"][place_id]["name"]
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -3))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            keys = database.view_rows(data, "device", "ID_place", int(place_id))
            
            for key in keys: data["device"][key]["ID_place"] = None
            data = database.del_row(data, "place", place_id)
            
            if database.save(config.db_file, data):
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Комната "+place_name+" удалена", reply_markup=keyboard)
        
        elif link == "pl_set/add":
            free_ID = database.free_ID(data, "place")
            
            if free_ID is not None:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Введите название комнаты")
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Простите, число добавляемых комнат ограничено")            
                callback[call.from_user.id] = update_path("cannel")
            
        elif link == "dev_set":
            set_dev = types.InlineKeyboardButton(text="Настроить устройство", callback_data=callback[call.from_user.id]+"/opt")
            add_dev = types.InlineKeyboardButton(text="Добавить устройство", callback_data=callback[call.from_user.id]+"/add")
            keyboard = show_keyboard(service_buttons=[set_dev, add_dev])        
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки устройств", reply_markup=keyboard)        
        
        elif link == "dev_set/opt":
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")           
            keys = database.view_rows(data, "device")
            
            if keys:
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, interpretation_by="position", service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Выберите устройство, которое нужно настроить", reply_markup=keyboard)               
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Устройства отсутствуют. Для добавления устройств перейдите в раздел Настройки > Устройства > Добавить устройство", reply_markup=keyboard)
        
        elif link == "dev_set/opt/dev/":
            device_id = steps[3]
            device_name = data["device"][device_id]["name"] 
            device_type = types.InlineKeyboardButton(text="Тип устройства", callback_data=callback[call.from_user.id]+"/type")
            rename = types.InlineKeyboardButton(text="Переименовать", callback_data=callback[call.from_user.id]+"/rename")
            del_device = types.InlineKeyboardButton(text="Удалить", callback_data=callback[call.from_user.id]+"/del")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -2))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[device_type, rename, del_device, back, cannel])        
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки устройства "+device_name, reply_markup=keyboard)
        
        elif link in ("dev_set/opt/dev//type", "dev_set/opt/dev//type/dimer", "dev_set/opt/dev//type/switch"):
            device_id = steps[3]
            
            if link == "dev_set/opt/dev//type": backwards_steps = -1
            elif link in ("dev_set/opt/dev//type/dimer", "dev_set/opt/dev//type/switch"): backwards_steps = -2
        
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], backwards_steps))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")                
            
            if data["device"].get(device_id):
                device_name = data["device"][device_id]["name"] 
                is_dimable = data["device"][device_id]["is_dimmable"]
                
                if link == "dev_set/opt/dev//type":
                    call_data = callback[call.from_user.id]
                    if is_dimable:
                        dimer_ok = u'\U00002714 '
                        switch_ok = ''
                    else:
                        dimer_ok = ''
                        switch_ok = u'\U00002714 '                        
                elif link in ("dev_set/opt/dev//type/dimer", "dev_set/opt/dev//type/switch"):
                    call_data = update_path('/'.join(steps[:-1]))
                    if steps[-1] == "dimer":
                        dimer_ok = u'\U00002714 '
                        switch_ok = ''
                    elif steps[-1] == "switch":
                        dimer_ok = ''
                        switch_ok = u'\U00002714 '                        
      
                dimer = types.InlineKeyboardButton(text=dimer_ok+"Димер", callback_data=call_data+"/dimer")
                switch = types.InlineKeyboardButton(text=switch_ok+"Выключатель", callback_data=call_data+"/switch")     
                save = types.InlineKeyboardButton(text="Сохранить \U0001F4BE", callback_data=callback[call.from_user.id]+"/save")
                
                if (is_dimable and steps[-1] == "switch") or (not is_dimable and steps[-1] == "dimer"):
                    keyboard = show_keyboard(service_buttons=[[dimer, switch], save, back, cannel]) 
                else:
                    keyboard = show_keyboard(service_buttons=[[dimer, switch], back, cannel])
                    
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Тип устройства "+device_name, reply_markup=keyboard)            
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Устройство было изменено до вас", reply_markup=keyboard)
        
        elif link in ("dev_set/opt/dev//type/dimer/save", "dev_set/opt/dev//type/switch/save"):
            device_id = steps[3]
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -3))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")            
            keyboard = show_keyboard(service_buttons=[back, cannel])
            
            if data["device"].get(device_id):
                device_name = data["device"][device_id]["name"]
                
                if steps[-2] == "dimer":
                    data["device"][device_id]["is_dimmable"] = True
                    text = "Устройство "+device_name+" настроено как димер"
                elif steps[-2] == "switch":
                    data["device"][device_id]["is_dimmable"] = False
                    text = "Устройство "+device_name+" настроено как выключатель"
                
                if database.save(config.db_file, data): 
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=keyboard) 
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Устройство было изменено до вас", reply_markup=keyboard)
        
        elif link == "dev_set/opt/dev//rename":
            device_id = steps[3]
            device_name = data["device"][device_id]["name"]            
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Введите новое название для устройства "+device_name)    
        
        elif link == "dev_set/opt/dev//del":
            device_id = steps[3]
            device_name = data["device"][device_id]["name"]  
            unbind = types.InlineKeyboardButton(text="Отвязать", callback_data=callback[call.from_user.id]+"/unbind")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[unbind, back, cannel]) 
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Прежде чем удалить устройство "+device_name+", его нужно отвязать.", reply_markup=keyboard)
        
        elif link == "dev_set/opt/dev//del/unbind":
            device_id = steps[3]
            CH = data["device"][device_id]["CH"]
            mtrf.tx_command(channel=CH, cmd=9, fmt=0, dat=0)
            following = types.InlineKeyboardButton(text="Далее \U000027A1", callback_data=callback[call.from_user.id]+"/fol")
            repeat = types.InlineKeyboardButton(text="Повторить отвязку \U0001F504", callback_data=callback[call.from_user.id])
            keyboard = show_keyboard(service_buttons=[following, repeat]) 
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Если светодиод на силовом блоке замигал чаще, подтвердите отвязку нажав на его сервисную кнопку. Если частота мигания светодиода не изменилась, повторите попытку отвязки.", reply_markup=keyboard)
        
        elif link == "dev_set/opt/dev//del/unbind/fol":
            device_id = steps[3]
            device_name = data["device"][device_id]["name"]  
            database.del_row(data, "device", device_id)
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -5))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])
            
            if database.save(config.db_file, data): 
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Устройство "+device_name+" отвязано и удалено.", reply_markup=keyboard)
        
        elif link == "dev_set/add":
            add_block = types.InlineKeyboardButton(text="Добавить силовой блок", callback_data=callback[call.from_user.id]+"/block") 
            #add_sensor = types.InlineKeyboardButton(text="Добавить датчик", callback_data=callback[call.from_user.id]+"/sensor")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[add_block, back, cannel])                  
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Добавить устройство", reply_markup=keyboard)
        
        elif link == "dev_set/add/block":
            free_ID = database.free_ID(data, "device")
            free_CH = database.free_CH(data, 0)
            free_CH_F = database.free_CH(data, 2)
            
            if (free_ID and free_CH and free_CH_F) is not None:
                form[call.from_user.id] = database(CH=free_CH, mode=0, is_dimmable=False).device_struct
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Введите название устройства")
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Простите, число добавляемых устройств ограничено")
                callback[call.from_user.id] = update_path("cannel")
                
        elif link == "dev_set/add/block/bind":
            CH = form[call.from_user.id]["CH"]
            mtrf.tx_command(channel=CH, cmd=15, fmt=0, dat=0)
            following = types.InlineKeyboardButton(text="Далее \U000027A1", callback_data=callback[call.from_user.id]+"/fol")
            repeat = types.InlineKeyboardButton(text="Повторить привязку \U0001F504", callback_data=callback[call.from_user.id])
            keyboard = show_keyboard(service_buttons=[following, repeat]) 
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Если светодиод на силовом блоке замигал чаще, подтвердите привязку нажав два раза на его сервисную кнопку. Если частота мигания светодиода не изменилась, повторите попытку привязки.", reply_markup=keyboard)        
        
        elif link == "dev_set/add/block/bind/fol":
            device_name = form[call.from_user.id]["name"]
            free_ID = database.free_ID(data, "device")
            database.new_row(data, "device", form[call.from_user.id], free_ID)
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -3))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            
            if database.save(config.db_file, data): 
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Добавлено новое устройство "+device_name+". Для перемещения устройства в какую-либо комнату перейдите в раздел Настройки > Комнаты > Редактировать комнату", reply_markup=keyboard)
        
        elif link == "pr_set":
            correct = types.InlineKeyboardButton(text="Редактировать сценарий", callback_data=callback[call.from_user.id]+"/corr")
            add = types.InlineKeyboardButton(text="Создать сценарий", callback_data=callback[call.from_user.id]+"/add")
            keyboard = show_keyboard(service_buttons=[correct, add])        
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки сценариев", reply_markup=keyboard)            
        
        elif link == "pr_set/corr":
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")             
            keys = database.view_rows(data, "preset")
            
            if keys:              
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Сценарии", reply_markup=keyboard)
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Хммм, похоже у вас ещё не настроены сценарии. Для настройки сценариев перейдите в раздел Настройки > Сценарии > Создать сценарий", reply_markup=keyboard)
        
        elif link == "pr_set/corr/pr/":
            preset_id = steps[3]
            preset_name = data["preset"][preset_id]["name"] 
            add_device = types.InlineKeyboardButton(text="Добавить устройства", callback_data=callback[call.from_user.id]+"/fill")
            del_device = types.InlineKeyboardButton(text="Убрать устройства", callback_data=callback[call.from_user.id]+"/empty")
            set_preset = types.InlineKeyboardButton(text="Настроить сценарий", callback_data=callback[call.from_user.id]+"/set")
            rename = types.InlineKeyboardButton(text="Переименовать", callback_data=callback[call.from_user.id]+"/rename")
            del_preset = types.InlineKeyboardButton(text="Удалить", callback_data=callback[call.from_user.id]+"/del")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -2))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[add_device, del_device, set_preset, rename, del_preset, back, cannel])        
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки сценария "+preset_name, reply_markup=keyboard)      
        
        elif link in ("pr_set/corr/pr//fill", "pr_set/corr/pr//fill/dev/"):
            preset_id = steps[3]
            preset_name = data["preset"][preset_id]["name"]
            
            if link == "pr_set/corr/pr//fill": backwards_steps = -1
            elif link == "pr_set/corr/pr//fill/dev/": backwards_steps = -3            
            
            following = types.InlineKeyboardButton(text="Далее \U000027A1", callback_data=callback[call.from_user.id]+"/fol")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], backwards_steps))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")            
            keys = database.view_rows(data, "device")
            fill_device_id = list()
            
            for key in keys:    # Check it!
                if not data["device"][key]["ID_preset"].get(preset_id):
                    fill_device_id.append(key)
            
            if fill_device_id is not None:
                if link == "pr_set/corr/pr//fill":
                    form[call.from_user.id] = dict()
                    form[call.from_user.id]["preset"] = data["preset"][preset_id]
                    form[call.from_user.id]["devices"] = dict()   
                elif link == "pr_set/corr/pr//fill/dev/":
                    device_id = steps[6]
                    if device_id in form[call.from_user.id]["devices"].keys():
                        del form[call.from_user.id]["devices"][device_id]
                    else:
                        form[call.from_user.id]["devices"][device_id] = None               
                
                if form[call.from_user.id]["devices"]: buttons = [following, back, cannel]            
                else: buttons = [back, cannel]                
                
                keyboard = show_keyboard(data, callback[call.from_user.id], fill_device_id, form[call.from_user.id]["devices"].keys(), mark='\U00002714 ' , interpretation_by="position", service_buttons=buttons)
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Выберите устройства, которое хотите добавить в сценарий "+preset_name, reply_markup=keyboard)               
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Свободных устройств нет. В сценарии "+preset_name+" участвуют все устройства.", reply_markup=keyboard)
        
        
        
        
        
        
        
        
        
        
        elif link == "pr_set/corr/pr//rename":
            preset_id = steps[3]
            preset_name = data["preset"][preset_id]["name"]            
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Введите новое название для сценария "+preset_name)            
        
        elif link == "pr_set/corr/pr//del":
            preset_id = steps[3]
            preset_name = data["preset"][preset_id]["name"]
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -3))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])            
            keys = database.view_rows(data, "device")
            
            for key in keys:
                if data["device"][key]["ID_preset"].get(preset_id):
                    del data["device"][key]["ID_preset"][preset_id]
            
            data = database.del_row(data, "preset", preset_id)
            if database.save(config.db_file, data):
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Сценарий "+preset_name+" удалён", reply_markup=keyboard)
          
          
          
          
            
        
        elif link == "pr_set/add":
            free_ID = database.free_ID(data, "preset")
            
            if free_ID is not None:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Введите название сценария")
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Простите, число добавляемых сценариев ограничено")            
                callback[call.from_user.id] = update_path("cannel")
        
        elif link == "pr_set/add/dev/":
            device_id = steps[3]
            preset_name = form[call.from_user.id]["preset"]["name"]

            following = types.InlineKeyboardButton(text="Далее \U000027A1", callback_data=callback[call.from_user.id]+"/fol")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -3))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")       
            keys = database.view_rows(data, "device")
            
            if keys:
                if device_id in form[call.from_user.id]["devices"].keys():
                    del form[call.from_user.id]["devices"][device_id]
                else:
                    form[call.from_user.id]["devices"][device_id] = None

                if form[call.from_user.id]["devices"]: buttons = [following, back, cannel]            
                else: buttons = [back, cannel]            
                
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, form[call.from_user.id]["devices"].keys(), mark='\U00002714 ', interpretation_by="position", service_buttons=buttons)
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Выберите устройства, которое будут участвовать в сценарии "+preset_name, reply_markup=keyboard)               
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Похоже у вас нет привязанных устройств", reply_markup=keyboard)

        elif link in ("pr_set/add/dev//fol", "pr_set/corr/pr//fill/dev//fol"):
            preset_name = form[call.from_user.id]["preset"]["name"]
            save = types.InlineKeyboardButton(text="Сохранить \U0001F4BE", callback_data=callback[call.from_user.id]+"/save")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")            
            keys = form[call.from_user.id]["devices"].keys()
            all_configured = list(filter(lambda device_id: form[call.from_user.id]["devices"][device_id] is not None, form[call.from_user.id]["devices"].keys()))
            
            if len(all_configured) == len(form[call.from_user.id]["devices"].keys()): buttons = [save, back, cannel]
            else: buttons = [back, cannel]
                    
            if keys:           
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, all_configured, mark='\U00002714 ', interpretation_by="position", service_buttons=buttons)
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройте устройства, которое будут участвовать в сценарии "+preset_name, reply_markup=keyboard)
            
        elif link in  ("pr_set/add/dev//fol/dev/", "pr_set/add/dev//fol/dev/:,,", "pr_set/corr/pr//fill/dev//fol/dev/", "pr_set/corr/pr//fill/dev//fol/dev/:,,"):
            device_id = steps[-1].split(":")[0] # Change to negative step in all links!!!
            keys = device_id
            dev = steps[-1].split(":")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -2))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")            

            if keys and link in ("pr_set/add/dev//fol/dev/:,,", "pr_set/corr/pr//fill/dev//fol/dev/:,,"):
                form[call.from_user.id]["devices"][device_id] = dev[1]
                if data["device"].get(dev[0]):
                    CH = data["device"][dev[0]]["CH"]
                    cmd = int(dev[1].split(',')[0])
                    fmt = int(dev[1].split(',')[1])
                    dat = int(dev[1].split(',')[2])      
                    mtrf.tx_command(channel=CH, cmd=cmd, fmt=fmt, dat=dat)            
            
            keyboard = show_keyboard(data, callback[call.from_user.id], [keys], control=False, periphery=True, service_buttons=[back, cannel])
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Выберите состояние устройства", reply_markup=keyboard)            
        
        elif link in ("pr_set/add/dev//fol/save", "pr_set/corr/pr//fill/dev//fol/save"):
            preset_name = form[call.from_user.id]["preset"]["name"]
            free_ID = database.free_ID(data, "preset")
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -5))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])
                 
            device_names = list()
            for key in form[call.from_user.id]["devices"].keys(): # Check it up to code!!!
                device_name = data["device"][key]["name"]
                device_names.append(device_name)

            if link == "pr_set/add/dev//fol/save" and free_ID is not None:
                if len(device_names) == 1: text = "Создан новый сценарий "+preset_name+" с устройством "+device_names[-1]
                else: text =  "Создан новый сценарий "+preset_name+" с устройствами "+' и '.join([', '.join(device_names[:-1]), device_names[-1]])
                
                for key in form[call.from_user.id]["devices"].keys():
                    data["device"][key]["ID_preset"][free_ID] = form[call.from_user.id]["devices"][key]
                data = database.new_row(data, "preset", form[call.from_user.id]["preset"], free_ID)
                if database.save(config.db_file, data): 
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
            
            elif link == "pr_set/corr/pr//fill/dev//fol/save":
                if len(device_names) == 1: text = "Устройство "+device_names[-1]+" добавлено в сценарий "+preset_name
                else: text =  "Устройства "+' и '.join([', '.join(device_names[:-1]), device_names[-1]])+" добавлены в сценарий "+preset_name               
                
                device_id = steps[-6]
                for key in form[call.from_user.id]["devices"].keys():
                    data["device"][key]["ID_preset"][device_id] = form[call.from_user.id]["devices"][key]                 
                if database.save(config.db_file, data): 
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
        
        elif link == "us-s_set":
            owners = types.InlineKeyboardButton(text="Хозяева", callback_data=callback[call.from_user.id]+"/ow-s")
            guests = types.InlineKeyboardButton(text="Гости", callback_data=callback[call.from_user.id]+"/gu-s")
            passers = types.InlineKeyboardButton(text="Подписчики", callback_data=callback[call.from_user.id]+"/pa-s")
            keyboard = show_keyboard(service_buttons=[owners, guests, passers])        
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Настройки пользователей", reply_markup=keyboard)        
        
        elif link in ("us-s_set/ow-s", "us-s_set/gu-s", "us-s_set/pa-s"):
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")           
            
            if link == "us-s_set/ow-s":
                keys = database.view_rows(data, "owner")
                keys.remove(database.view_rows(data, "owner", "id", call.from_user.id)[0])
                text = "Настройки хозяев"
                e_text = "Кроме Вас никаких хозяев нет"
            elif link == "us-s_set/gu-s":
                keys = database.view_rows(data, "guest")
                text = "Настройки гостей"
                e_text = "Гости отсутствуют"            
            elif link == "us-s_set/pa-s":
                keys = database.view_rows(data, "passer")
                text = "Настройки подписчиков"
                e_text = "Подписчики отсутствуют"            
            
            if keys:
                keyboard = show_keyboard(data, callback[call.from_user.id], keys, service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)               
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=e_text, reply_markup=keyboard)
        
        elif link in ("us-s_set/ow-s/ow/", "us-s_set/gu-s/gu/", "us-s_set/pa-s/pa/"):
            if steps[2] == "ow"
                table = "owner"
            elif steps[2] == "gu"
                table = "guest"
            elif steps[2] == "pa"
                table = "passer"    
            
            user_id = steps[3]
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -1))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")            
            
            if data[table].get(user_id):
                user_name = data[table][user_id]["name"]
                set_owner = types.InlineKeyboardButton(text="Сделать хозяином", callback_data=callback[call.from_user.id]+"/set_ow")
                set_guest = types.InlineKeyboardButton(text="Сделать гостем", callback_data=callback[call.from_user.id]+"/set_gu")
                del_user = types.InlineKeyboardButton(text="Удалить", callback_data=callback[call.from_user.id]+"/del")
                
                if table == "ow":
                    buttons = [set_guest, del_user, back, cannel]
                    text = "Настройки хозяина "+user_name
                elif table == "gu":
                    buttons = [set_owner, del_user, back, cannel]
                    text = "Настройки гостя "+user_name
                elif table == "pa":
                    buttons = [set_owner, set_guest, del_user, back, cannel]
                    text = "Настройки подписчика "+user_name
                
                keyboard = show_keyboard(service_buttons=buttons) 
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
            else:
                keyboard = show_keyboard(service_buttons=[back, cannel])
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Такого пользователя больше нет", reply_markup=keyboard)
        
        elif link in ("us-s_set/ow-s/ow//set_gu", "us-s_set/ow-s/ow//del",
                      "us-s_set/gu-s/gu//set_ow", "us-s_set/gu-s/gu//del",
                      "us-s_set/pa-s/pa//set_ow", "us-s_set/pa-s/pa//set_gu", "us-s_set/pa-s/pa//del"):
            
            table = "owner"
            user_id = steps[3]
            action = steps[4] 
            
            back = types.InlineKeyboardButton(text="Назад \U000021A9", callback_data=backwards_path(callback[call.from_user.id], -3))
            cannel = types.InlineKeyboardButton(text="Отмена \U0000274C", callback_data=callback[call.from_user.id]+"/cannel")
            keyboard = show_keyboard(service_buttons=[back, cannel])
        
            if data[table].get(user_id):
                form[call.from_user.id] = data[table][user_id]
                user_name = data[table][user_id]["name"]
                
                main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                home = types.KeyboardButton(text="Дом \U0001F3E0")
                preset = types.KeyboardButton(text="Сценарии \U00002728")
                settings = types.KeyboardButton(text="Настройки \U00002699")            
                remove_keyboard = types.ReplyKeyboardRemove()
                
                if action == "set_ow":
                    free_ID = database.free_ID(data, "owner")
                    if free_ID is not None:
                        data = database.del_row(data, table, user_id)
                        data = database.new_row(data, "owner", form[call.from_user.id], user_id)
                        main_keyboard.add(home, preset)
                        main_keyboard.add(settings)
                        if database.save(config.db_file, data):                            
                            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Пользователь "+user_name+" добавлен как хозяин", reply_markup=keyboard)
                            try: bot.send_message(form[call.from_user.id]["id"], text="Вы приглашены в дом, чувствуйте себя здесь хозяином " u'\U0001F609', reply_markup=main_keyboard)
                            except Exception: pass                      
                    else:
                        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Простите, число хозяев ограничено")
                
                if action == "set_gu":
                    free_ID = database.free_ID(data, "guest")
                    if free_ID is not None:
                        data = database.del_row(data, table, user_id)
                        data = database.new_row(data, "guest", form[call.from_user.id], user_id)
                        main_keyboard.add(home, preset)
                        if database.save(config.db_file, data):                        
                            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Пользователь "+user_name+" добавлен как гость", reply_markup=keyboard)
                            try: bot.send_message(form[call.from_user.id]["id"], text="Вы приглашены в дом, будте моим гостем " u'\U0001F609', reply_markup=main_keyboard)
                            except Exception: pass
                    else:
                        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Простите, число гостей ограничено")
                        
                if action == "del":
                    data = database.del_row(data, table, user_id)
                    if database.save(config.db_file, data):
                        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Пользователь "+user_name+" удалён", reply_markup=keyboard)
                        try: bot.send_message(form[call.from_user.id]["id"], text="Простите, но вам отказано в доступе к дому " u'\U00002639', reply_markup=remove_keyboard)
                        except Exception: pass
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Пользователь был изменён до вас", reply_markup=keyboard)        
        
        
        elif steps[-1] == "cannel":
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Отмена")
        
    
    if owner or guest: 
        if link in ("view/pl/", "view/pl//use/dev/", "view/pl//use/dev/:,,"):
            place_id = steps[2]
            
            if data["place"].get(place_id):
                place_name = data["place"][place_id]["name"]
                keys = database.view_rows(data, "device", "ID_place", int(place_id))        
                
                if keys:
                    if link == "view/pl/":
                        path = callback[call.from_user.id]+"/use"
                    elif link in ("view/pl//use/dev/", "view/pl//use/dev/:,,"):
                        path = callback[call.from_user.id]
                        dev = steps[5].split(":")
                        
                        if data["device"].get(dev[0]):
                            CH = data["device"][dev[0]]["CH"]
                            
                            if len(dev) == 1:
                                cmd = 4
                                fmt = 0
                                dat = 0
                            else:
                                cmd = int(dev[1].split(',')[0])
                                fmt = int(dev[1].split(',')[1])
                                dat = int(dev[1].split(',')[2])      
                            
                            mtrf.tx_command(channel=CH, cmd=cmd, fmt=fmt, dat=dat)                        
                            
                            #bot.answer_callback_query(call.id, show_alert=False, text=data["device"][dev[0]]["name"])    
                        
                    keyboard = show_keyboard(data, path, keys, periphery=True)
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Комната "+place_name, reply_markup=keyboard)                
                else:
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Комната "+place_name+" пуста")
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Такой комнаты больше нет")
        
        elif link == "view/pr/":
            preset_id = steps[2]
            pack = dict()
            
            if data["preset"].get(preset_id):
                keys = database.view_rows(data, "device")
                
                for key in keys:
                    if data["device"][key]["ID_preset"].get(preset_id):
                        pack[data["device"][key]["CH"]] = data["device"][key]["ID_preset"][preset_id]

                for CH in pack:
                    cmd = int(pack[CH].split(',')[0])
                    fmt = int(pack[CH].split(',')[1])
                    dat = int(pack[CH].split(',')[2])                    
                    mtrf.tx_command(channel=CH, cmd=cmd, fmt=fmt, dat=dat)
                    time.sleep(0.35)
                    
                preset = show_keyboard(data, update_path("view"), database.view_rows(data, "preset"))
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Сценарии", reply_markup=preset)
            else:
                bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Хммм, похоже у вас ещё не настроены сценарии. Для настройки сценариев перейдите в раздел Настройки > Сценарии > Создать сценарий")



if __name__ == '__main__':
    
    data = database.load(config.db_file)
    callback = dict()
    form = dict()

    while True:
        try: bot.polling(none_stop=True, interval=0)          
        except Exception as e:
            print(str(datetime.datetime.now()), ">>", e)
            time.sleep(5)
