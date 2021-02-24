# О проекте

Данное приложение позволяет управлять бризером (пока один) Tion 3S (да, пока
только одна модель) через MQTT. Уже через MQTT мы можем подключить бризер к
Homeassistant либо другим системам умного дома.

Для настройки не нужен HACS, установка которого та ещё головная боль. С другой
стороны от вас требуется понимание того, что вы делаете.

Приложение очень простое, написано менее чем за вечер, и основное время ушло на
войну с докером и синезубом.

Используется библиотека [tion_python](https://github.com/TionAPI/tion_python).
Огромное спасибо автору за разбор протокола.

# Установка.

Само приложение легковесное, просто подключается к homeassistant, установленному
в контейнере или же через core установку. При этом рекомендуется использовать
внешний mqtt брокер.

Запуск через docker-compose

В примере ниже предполагается, что mosquitto настроен в том же docker-compose
файле. [Инструкция по настройке mosquitto описана здесь](todo)

```
version: 3
services:
  ...
  tion2mqtt: # Имя фактически может быть любым
    container_name: tion2mqtt
    image: shaggyone/tion2mqtt
    restart: unless-stopped
    network_mode: host # Можно использовать и bridge, тогда
    privileged: true   # Вроде как нужен для доступа к bluetooth
    environment: # Все настройки живут тут
      - TION_MODEL=S3 # S3 либо Lite
      - TION_MAC=AA:BB:CC:DD:EE:FF # Mac адрес бризера. Как получить см. ниже.
      - MOSQUITTO_URL=mqtt://<mqtt_user>:<mqtt_password>@<mqtt_host>:<mqtt_port>
    depends_on:
      - mosquitto
```

Примечания по конфигу:
1. в данном примере mqtt_host будет 127.0.0.1, т.к. a. mosquitto настроен в том
   же файле. b. используется `network_mode: host`.
2. Мак-адрес бризера:
    1. мак адрес можно посмотреть в приложении Tion Remote. Для этого
       заходите в управление самим бризером, нажимаете на "шестерёнку", там будет
       Мак адрес разделённый дефисами. Для tion2mqtt дефисы нужно заменить на
       двоеточие.
    2. Можно получить mac бризера из `bluetoothctl`. См. раздел сопряжение

# Сопряжение бризера
В `tion2mqtt` нет функции сопряжения. Предполагается, что вы выполнили
сопряжение для host системы. Это сделано сознательно, проще использовать
готовые утилиты, чем сразу пытаться повторить функциональность уже реализованную
в них. В прочем, я не исключаю того, что в будущем в `tion2mqtt` появится
функция сопряжения.

```
=> bluetoothctl
...
> scan on
...
# включаем режим сопряжения на бризере. Ждём когда в списке появится

pair AA:BB:CC:DD:EE:FF
# Да-да, вот он MAC адрес, который нужно добавить в конфиг.

connect AA:BB:CC:DD:EE:FF
# Убедимся, что сопряжение и правда прошло и работает

disconnect AA:BB:CC:DD:EE:FF
# Бризер не поддерживает подключение нескольких управляющих устройств
# одновременно так что освобождаем его.
```

# Подключение к homeassistant
В `configuration.yaml` добавляем строки.

```
switch:
  - platform: mqtt
    name: "Tion 3S State"
    unique_id: 'tion.0xaabbccddeeff.state'

    state_topic: tion/0xaabbccddeeff/state
    availability_topic: tion/0xaabbccddeeff/online
    command_topic: tion/0xaabbccddeeff/set/state
    qos: 1

    state_on: 'on'
    state_off: 'off'
    payload_on: 'on'
    payload_off: 'off'
    payload_available: 'online'
    payload_not_available: 'offline'

    retain: false

number:
  - platform: mqtt
    name: "Tion 3S Heater Temp"
    unique_id: 'tion.0xaabbccddeeff.heater_temp'

    state_topic: tion/0xaabbccddeeff/heater_temp
    availability_topic: tion/0xaabbccddeeff/online
    command_topic: tion/0xaabbccddeeff/set/heater_temp
    qos: 1

    payload_available: 'online'
    payload_not_available: 'offline'

    retain: false

  - platform: mqtt
    name: "Tion 3S Fan Speed"
    unique_id: 'tion.0xaabbccddeeff.fan_speed'

    state_topic: tion/0xaabbccddeeff/fan_speed
    availability_topic: tion/0xaabbccddeeff/online
    command_topic: tion/0xaabbccddeeff/set/fan_speed
    qos: 1

    payload_available: 'online'
    payload_not_available: 'offline'

    retain: false
```

Перезапускаем `homeassistant`. В результате `Настройки` -> `Объекты` получим
элементы для включения/выключения, установки температуры приточного воздуха и
управления скоростью вентилятора.

Обратите внимание на `0xaabbccddeeff` это MAC адрес без разделителей, в нижнем
регистре и с 0x в начале.

MQTT топики используемые приложением:
* `tion/0x<MAC бризера>` все переменные состояния бризера разом
* `tion/0x<MAC бризера>/<переменная>`     конкретная переменная состояния
* `tion/0x<MAC бризера>/set/<переменная>` установка состояния конкретной
  переменной. Список переменных, которые можно изменять:
    * `state` -- `on` или `off`. Включить/выключить бризер.
    * `heater` -- `on` или `off`. Включить/выключить подогрев приточного воздуха.
    * `sound` -- `on` или `off`. Включить/выключить писк при каждом событии.
    * `mode` -- `on` или `off`.
    * `heater_temp` -- температура до которой бризер должен подогревать воздух
    * `fan_speed` -- скорость вентилятора. 1..6


# Проблемы
Ну да они есть, куда без них...

Самая большая это то, что я пока не победил автоматическую сборку образа на
dockerhub. Так что пока нужно запускать сборку образа на малинке, как то так:
```
git clone https://github.com/shaggyone/tion2mqtt.git
cd tion2mqtt
docker build --tag shaggyone/tion2mqtt .
```

# TODO
* настроить сборку образом докера для разных платформ.
* сделать регулярный опрос состояния бризера (сейчас делается на старте и в
  момент управления)
* сделать отслеживание `online`/`offline` сейчас `tion2mqtt` всегда сообщает,
  будто бризер online.
* сделать образ на базе alpine версии (я смог победить сборку для x86, но для
  raspberry-pi получал странные ошибки).
* сделать поддержку Tion Lite (должно быть довольно просто)
* сделать возможность подключения нескольких бризеров одновременно.
* портировать логику приложения на ESP32. Смысл в том, что BLE плохо ловит
  сигнал на расстоянии. Из другой комнаты управлять бризером не факт что
  получится, а размещать хаб homeassistant специально рядом с бризером -- так
  себе идея. Зато мы можем рядом с каждым бризером разместить плату ценой 400р.
  + блок питания, плата будет общаться с MQTT через wifi.
* ещё можно перевести этот README на английский. Мне правда интересно, для кого,
  в каких ещё странах кроме СНГ люди готовы жечь электричество ради догрева
  приточного воздуха до приемлемой темперауры.