сделал конец процесса, всё работает, раннеры подхватывают свои работы, ура

# Overall structure
![schema](my_schema.png)

src includes all the services:
### [videoanalysis](src\videoanalysis) (API)
* Provides [FastAPI swagger interface](http://localhost:8000/docs) 
to interact with the project
* **reads from databases** 
* **writes orchestrator commands to kafka**

to run
```shell
poetry run uvicorn videoanalysis.main:app --reload --host 0.0.0.0 --port 8000
```

### [orchestrator](src\orchestrator)
(currently)
* resends runner_command if heartbeats from a scenario stops, 
thus providing отказоустойчивость (забыл как это на англ)
* currently does not set the state of a scenario to inactive, so basically works all the time
* **reads from orchestrator_commands topic**
* **reads from heartbeat**
* **writes to ScenariosDB directly**
* **writes to runner_commands topic**
```shell
poetry run python src/orchestrator/main.py
```


### [runner](src\runner)
(currently)
* Completely mocks inference and just
writes random stuff to PredictionsDB without even 
having any video to sample frames from
* **reads from runner_commands topic**
* **writes to PredictionsDB directly**
* **writes heartbeats to heartbeat topic**
```shell
poetry run python src/runner/main.py
```
or 3 of them are initialized in Docker

## Current state
### topics:
* runner_commands
* orchestrator_commands
* heartbeat

### services:
* runners
* orchestrator
* api (3 working handlers)

### databases:
* ScenariosDB
* PredictionsDB

# Commands
### 0)
if u have internal network in docker, delete it. And pro-tip - use docker compose down -v to destroy volumes

### 1) Installing dependencies
```shell 
poetry install
```

---

### 2) Set up kafka, ScenarioDB, PredictionsDB
```shell 
docker compose up -d
```
You should also wait for approximately 20 seconds for kafka-init, 
predictions-init and scenarios-init to prepare the containers for 
proper use by the services

---

### 3) Set up API
```shell
poetry run uvicorn videoanalysis.main:app --reload --host 0.0.0.0 --port 8000
```

now you can go to http://localhost:8000/docs to use handlers

---

### 4) Set up Orchestrator
```shell
poetry run python src/orchestrator/main.py
```

---

[//]: # (### 5&#41; Set up Runner)

[//]: # (```shell)

[//]: # (poetry run python src/orchestrator/main.py)

[//]: # (```)

[//]: # (---)





## don't forget

[//]: # (* сейчас есть беда с тем, что если у нас каким-то хером раннеры пропустят сообщение )

[//]: # (о начале сценария, то оркестратор просто бесконечно будет ждать, пока его кто-то подберёт, )

[//]: # (и притом не думаю, что это обязательно произойдёт...)

[//]: # (* наверное стоит делать ретраи по сценарию, раз в минуту хотя бы. )

[//]: # (А то щас я ретраю, только если раннер сломался после того как обработал хоть один кадр. А вдруг он сразу сломается и притом у нас не будет )

[//]: # (обработан ни один кадр, а оркестратор будет думать, что сценарий просто в очереди)
* init_shutdown должен не выдавать бесконечную загрузку, если сценарий успел закончится
* outbox