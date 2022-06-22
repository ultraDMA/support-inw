# Приложение Support v0.1
________________________
Регистрация
-------------
Для регистрации нового пользователя отправьте на адрес 

- > `auth/users/ `

**POST**-запрос с телом:

- > `{
    "email": "email@example.com",
    "username": "example_user",
    "password": "example.password"
}`

В случае успеха **API** вернёт статус `201_CREATED` и информацию о пользователе в теле ответа

- > `{"id":19,"username":"example_user","email":"email@example.com","is_active":true,"tickets":[]}`

-------------
JWT - авторизация
-------------
Чтобы получить _**JWT Access и Refresh**_ токены, отправьте на адрес

- > `auth/jwt/create/`

`POST`-запрос, в теле которого:

- >`{
    "username": "example_user",
    "password": "example.password"
}`

Если пользователь с такой парой логин-пароля зарегистрирован, **API** вернёт ответ со статусом  `200_OK`,
в теле которого будет пара токенов: 

- >`{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9......f5POmlCc_y2NJMYL1mjS7x2xi_PI2GU-5bS1rbptgJ4",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.......zacMPvs3gCocXVic0MAon_-pghLXBTTc5iWb1ygMBlA"
}`
- Время жизни `access` токена - 10 минут, `refresh` - 7 дней

Далее, чтобы получать новую пару токенов, отправьте на адрес

- > `auth/jwt/refresh/`

`POST` запрос в теле которого присутствует актуальный `refresh` токен

- > `{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9......f5POmlCc_y2NJMYL1mjS7x2xi_PI2GU-5bS1rbptgJ4"
}`

В теле ответа вернётся новая пара `access-refresh` токенов

-------------

Добавление тикета
-------------

Пользователь отправляет `POST`-запрос на адрес `/api/ticket`  _JSON_-объект с ключом `"message"` в теле запроса

> `{"message": "Some message like FOO BAR BIZ"}`

В заголовке запроса так же должен быть _JWT_ `access` токен. Пользователю возвращается ответ `201_CREATED` с телом
>`{
    "id": 66,
    "from_user_id": 19,
    "from_user": "example_user",
    "message": "Some message like FOO BAR BIZ",
    "status": "u",
    "changed_status": null,
    "answers": [],
    "created_at": "2022-06-22T14:12:07.488396Z"
}`

Подробнее:
* `"id"`: Идентификатор тикета, по которому он доступен `GET`-запросом для пользователя в `api/ticket/<id>`
* `"from_user_id"`: Идентификатор пользователя, создавшего тикет `auth/users/<from_user_id>`
* `"from_user"`: Имя пользователя, создавшего тикет
* `"message"`: Сообщение
* `"status"`: Статус - _решённый: `c`, нерешённый: `u`, замороженный: `f`_. Статусы может менять только саппорт
* `"changed_status"`: Идентификатор саппорта, изменившего статус
* `"answers"`: Список со всеми ответами на выбранный тикет
* `"created_at"`: Время создания
------------------------------------

Ответ на тикет
---------------------
_Способ ответа для пользователя и для саппорта аналогичен._

Чтобы ответить на тикет, необходимо отправить `POST`-запрос на адрес `api/ticket/<id>/answer` где `id` - 
идентификатор требуемого тикета с телом вида

> `{"message": "answer message"}`

в ответе API вернёт 

> `{
    "id": 29,
    "message": "answer message"
}`

Где
* `id`: Идентификатор **ответа**. Доступен `GET`-запросом в `api/comment/<id>`. Доступ к ответу имеет только 
пользователь создавший тикет, а так же саппорт.

Пример ответа `api/comment/29`: 
>`{
    "id": 29,
    "from_user_id": 19,
    "from_user": "example_user",
    "to_ticket": "http://127.0.0.1:8000/api/ticket/66",
    "message": "answer message",
    "answered_at": "2022-06-22T14:32:51.334919Z"
}`

Вид _ответа_ аналогичен по строению _тикету_, за исключением поля `"to_ticket"` - 
оно показывает к какому _тикету_ относится данный _ответ_.

Когда на тикет отвечает **саппорт**, пользователю отправляется уведомление на email, указанный
при регистрации. Email имеет вид:

>Support has reply to yor ticket:
> 
> 	Some message like FOO BAR BIZ
> ------------------------------
> 
>Reply message:
> 
>	answer message
> _____________________________
>
>To check your ticket, press to link: http://localhost:8000/api/ticket/66

По мере создания ответов пользователем и саппортом, тикет накапливает ответы в поле `"answers"`
>`{
    "id": 66,
    "from_user_id": 19,
    "from_user": "example_user",
    "message": "Some message like FOO BAR BIZ",
    "status": "u",
    "changed_status": null,
    "answers": [
        "http://127.0.0.1:8000/api/comment/31",
        "http://127.0.0.1:8000/api/comment/30",
        "http://127.0.0.1:8000/api/comment/29",
        "http://127.0.0.1:8000/api/comment/28"
    ],
    "created_at": "2022-06-22T14:12:07.488396Z"
}`
-----------------------------------------------------
Статусы тикетов
------------------
Статусы тикетов может менять только саппорт. Для этого необходимо отправить `POST`-запрос на
>`api/ticket/<id>/set_status`

с ключом `"status"` в теле запроса, например

> `{"status": "c"}`

В ответ `API` вернёт ответ
>`{
    "status": "c",
    "changed_status": 1
}`

и тикет будет изменён соответствующим образом
>`{
    "id": 66,
    "from_user_id": 19,
    "from_user": "example_user",
    "message": "Some message like FOO BAR BIZ",
    "status": "c",
    "changed_status": 1,
    "answers": [
        "http://127.0.0.1:8000/api/comment/31",
        "http://127.0.0.1:8000/api/comment/30",
        "http://127.0.0.1:8000/api/comment/29",
        "http://127.0.0.1:8000/api/comment/28"
    ],
    "created_at": "2022-06-22T14:12:07.488396Z"
}`
-----------------------------------
Фильтрация тикетов
----------------------------
Саппорт видит все тикеты. Пользователю доступны только те, что создал он сам.
Точка входа для всех тикетов `api/ticket`. Точка входа для конкретного тикета `api/ticket/<id>`
Тикеты можно фильтровать по статусам: решённые, нерешённые, замороженные.
Для этого нужно отправить `GET`-запрос c параметром `api/ticket?status=<status>`,
где `<status>`: `c`, `u` или `f`. Например:
>`api/ticket?status=c`
----------------------------

Назначаем Саппорта
------------------
В текущей версии программы права саппорта назнаечает Администратор через админ-панель 
Django `admin/` установкой галочки `staff`

