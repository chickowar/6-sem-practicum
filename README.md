**working**
_API —(create scenario)—> Kafka —> Orchestrator —> DB —(check scenario)—> API_
**pipeline**

# Commands

### 1) Managing dependencies
```shell 
poetry install
```

---

### 2) Set up kafka, ScenarioDB
```shell 
docker compose up -d
```

---

### 3) Initialize scenarios table
```shell 
cd src
poetry run python  .\common\db\scenarios.py
```

---

### 4) Set up API
```shell
poetry run uvicorn videoanalysis.main:app --reload --host 0.0.0.0 --port 8000
```

now you can go to http://localhost:8000/docs to use handlers

---

### 5) Set up Orchestrator
after making at least one scenario using [swagger](http://localhost:8000/docs#/default/create_scenario_scenario__post) \
(*the topics aren't being created without that at the moment, I'll fix it later*)
```shell
poetry run python src/orchestrator/main.py
```

---

### 6) It works, hooray

---





## don't forget
* make scripts in docker compose to create topics with preferably a configurable amount of partitions
* **OR** do it using python (confluent_kafka) 

(I think first is better)