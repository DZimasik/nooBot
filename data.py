# -*- coding: utf-8 -*-

import datetime
import json
import config


class database:
    
    def __init__(self, name=None, mode=None, CH=None, serial=None, state=None, ID_place=None, ID_preset=None, ID_user=None, is_dimmable=False):
        self.data = {"device":dict(), "place":dict(), "preset":dict(), "owner":dict(), "guest":dict(), "passer":dict()}
        self.device_struct = {"name":name, "mode":mode, "CH":CH, "serial":serial, "state":state, "is_dimmable":is_dimmable, "ID_place":ID_place, "ID_preset":dict()}
        self.user_struct = {"name":name, "id":ID_user}
        self.other_struct = {"name":name}        
    
    def new_row(data, table, form, free_ID): 
        data[table][free_ID] = form
        return data
    
    def del_row(data, table, key):
        del data[table][key]
        return data
    
    def view_rows(data, table, column=None, val=None):
        if column:
            rows = list()
            for keys in data[table].keys():
                if data[table][keys][column] == val:
                    rows.append(int(keys))
            rows = sorted(rows)             
        else:
            rows = sorted([int(keys) for keys in data[table].keys()])        
        rows = [str(keys) for keys in rows]
        return rows
    
    def free_ID(data, table):
        limit = {"device":90, "place":90, "preset":90, "owner":20, "guest":90, "passer":5}
        keys = list()
        free_ID = 0

        for pr_key in data.keys():
            for sec_key in data[pr_key].keys():
                keys.append(sec_key)
        while str(free_ID) in keys:
            free_ID+=1
        if (table in limit.keys()) and (len(data[table]) >= limit[table]):
            return None
        else:
            return str(free_ID)
    
    def free_CH(data, mode):
        free_CH = 0
        CH = list()
        for key in data["device"].keys():
            if data["device"][key]["mode"] == mode:
                CH.append(data["device"][key]["CH"])          
        while free_CH in CH:
            free_CH+=1
        if free_CH > 63:
            free_CH = None
        return free_CH        

    def save(file_name, data):
        try: 
            with open(file_name, 'w') as config_file:
                json.dump(data, config_file, sort_keys=True, indent=3, ensure_ascii=False)
                print(str(datetime.datetime.now()), ">> Save database")
                return True
        except Exception:
            print(str(datetime.datetime.now()), ">> ERROR!!! when save database file")
      
            
    def load(file_name):
        try: 
            with open(file_name, 'r') as config_file:
                print(str(datetime.datetime.now()), ">> Load database")
                return json.load(config_file)
        except Exception:
            print(str(datetime.datetime.now()), ">> ERROR!!! database file not found")    
            return database().data 
    