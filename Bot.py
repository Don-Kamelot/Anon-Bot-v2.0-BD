# Подключение библиотек
import vk_api  # ВК АПИ
import sqlite3 as sql  # База данных
from vk_api.longpoll import VkLongPoll, VkEventType  #Импорт лонгпула

check_anon = ''  # Переменная для поиска собеседника


def send_message(user_id, message):  # Отправка сообщений пользователю
    vk.method('messages.send', {'user_id': str(user_id), 'message': str(message), 'random_id': 0})


def anon_join():  # Фкункция входа в поиск собеседника
    connections = sql.connect("user.sqlite", check_same_thread=False)
    a = connections.cursor()
    a.execute("UPDATE user_info SET IN_CHAT = '%s' WHERE VK_ID = '%s'" % ('yes', int(event.user_id)))
    connections.commit()
    connections.close()
    send_message(event.user_id, 'Вы в поиске.')
    anon_search()


def anon_search():  # Функция поиска собеседника
    global check_anon

    # Проверяем переменную
    if check_anon == '':  # Если пустая
        check_anon = str(event.user_id)  # Присваемваем id пользователя
    else:  # Если в переменной есть id
        connections = sql.connect("user.sqlite", check_same_thread=False)
        a = connections.cursor()
        with_id = check_anon
        check_anon = ''  # Обнуляем переменную
        try:
            send_message(with_id, 'Собеседник найден!')
            a.execute("UPDATE user_info SET WITH_ID = '%s' "
                      "WHERE VK_ID = '%s'" % (int(event.user_id), int(with_id)))
            send_message(event.user_id, 'Собеседник найден!')
            a.execute("UPDATE user_info SET WITH_ID = '%s' "
                      "WHERE VK_ID = '%s'" % (int(with_id), int(event.user_id)))
        except vk_api.VkApiError:
            check_anon = str(event.user_id)
        connections.commit()
        connections.close()


def conversation():  # Если в чате/поиске
    connections = sql.connect("user.sqlite", check_same_thread=False)
    a = connections.cursor()
    a.execute("SELECT * FROM user_info WHERE VK_ID = '%s'" % (str(event.user_id)))
    results = a.fetchall()

    if ressponse_lower == 'выход': # Если написал "Выход"
        try:  # Пробуем
            send_message(results[0][1], 'Собеседник вышел из чата.') # Отправить сообщение собеседнику
            a.execute("UPDATE user_info SET WITH_ID = '%s' "
                      "WHERE VK_ID = '%s'" % (0, int(results[0][1])))  # Обновляем данные в базе данных
            a.execute("UPDATE user_info SET IN_CHAT = '%s' "
                      "WHERE VK_ID = '%s'" % ('no', int(results[0][1])))
        except vk_api.VkApiError:  # Если нет собеседника, либо он заблокировал бота
            pass  # Ничего не делаем
        send_message(event.user_id, 'Вы вышли из поиска/чата.')
        a.execute("UPDATE user_info SET WITH_ID = '%s' "
                  "WHERE VK_ID = '%s'" % (0, int(event.user_id)))
        a.execute("UPDATE user_info SET IN_CHAT = '%s' "
                  "WHERE VK_ID = '%s'" % ('no', int(event.user_id)))
    elif results[0][1] == 0:  # Если нет собеседника
        send_message(event.user_id, 'Вы в поиске!')
    else:  # Если есть собеседник
        try:
            send_message(results[0][1], 'Собеседник: ' + ressponse)  # Пересылаем сообщение собеседнику
        except vk_api.VkApiError:  # Если собеседник заблокировал бота
            send_message(event.user_id, 'Собеседник заблокировал бота.\n'
                                        'Если хотите начать другой диалог\n'
                                        'Напиишите: "Старт".')
            a.execute("UPDATE user_info SET WITH_ID = '%s' "
                      "WHERE VK_ID = '%s'" % (0, int(event.user_id)))
            a.execute("UPDATE user_info SET IN_CHAT = '%s' "
                      "WHERE VK_ID = '%s'" % ('no', int(event.user_id)))    

    connections.commit()
    connections.close()  # Закрываем базу данных


if __name__ == '__main__':  # Главный блок
    while True:  # Бесконечный цикл
        vk = vk_api.VkApi(token='ТУТ ТОКЕН')  # Сюда нужно вставить токен
        session_api = vk.get_api()  # Подключение к сессии
        longpoll = VkLongPoll(vk)  # Лонгпулл

        while True: # Ещё 1 бесконечный цикл
            for event in longpoll.listen():  # Прослушиваем лонгпул
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:  # Если пришло новое сообщение и оно для "меня"
                        ressponse = str(event.text)  # Присваиваем переменной сообщение пользователя
                        ressponse_lower = ressponse.lower()  # Делаем всю сообщение в нижнем регистре
                        cmd = ressponse_lower.split(' ')  # Разбиваем сообщение по пробелам
                        cmd.append('NOCMD')  # Дабовляем в конец NOCMD

                        connection = sql.connect("user.sqlite", check_same_thread=False)  # Подключение к базе данных
                        q = connection.cursor()  # Установка курсора
                        q.execute("SELECT * FROM user_info WHERE VK_ID = '%s'" % (str(event.user_id)))  # Ищем пользователя в базе данных
                        result = q.fetchall()  # Присваеваем результат переменной
                        if len(result) == 0:  # Если аккаунта нет
                            q.execute("INSERT INTO user_info (VK_ID) VALUES ('%s')" % (str(event.user_id)))  # Дабовляем нового пользователя
                        connection.commit()
                        connection.close()  # Закрываем базу данных

                        connection = sql.connect("user.sqlite", check_same_thread=False)
                        q = connection.cursor()
                        q.execute("SELECT * FROM user_info WHERE VK_ID = '%s'" % (str(event.user_id)))
                        result = q.fetchall()
                        connection.commit()
                        connection.close()

                        if result[0][2] == 'yes':  # Если в Чате
                            conversation()  # Заходим в функцию
                        elif cmd[0] == 'старт' and cmd[1] == 'NOCMD':  # Если прописал "старт"
                            anon_join()  # Заходим в функцию
                        else:  # Иначе
                            send_message(event.user_id, 'Введите: "Старт".')  # Пишем о том, что нужно прописать "Старт"
