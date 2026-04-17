# **Отчет по лабораторной работе №4: Анализ безопасности веб-приложений (SAST, SCA, DAST)

## Сведения о студенте  
**Дата:** 2026-04-16
**Семестр:** 2 курс, 2 семестр  
**Группа:** Пин-б-о-24-1  
**Дисциплина:** Технологии программирования  
**Студент:** Куйбышев Александр Максимович

---

## Цель работы

**Часть 1:** Освоение инструментов статического анализа безопасности (SAST) на примере Bandit. Выявление и устранение уязвимостей в Python-приложении (SQL-инъекции, hardcoded secrets, command injection), а также применение безопасных практик разработки.

**Часть 2:** Освоение анализа зависимостей (SCA) и динамического тестирования (DAST). Выявление уязвимых библиотек с помощью npm audit, тестирование приложения через OWASP ZAP и устранение XSS-уязвимостей.

---

### Часть 1: Статический анализ (SAST) с Bandit

#### Структура проекта

```
lab4/sast/
  ├── app.py
  ├── users.db
  ├── .bandit
  └── bandit_report.html
```

#### Выполненные задачи

1. Настроено Python-окружение и установлен Bandit
2. Проведен анализ кода `bandit app.py`
3. Обнаружены уязвимости: SQL-инъекции, hardcoded API ключ, command injection
4. Реализованы исправления всех уязвимостей
5. Проведен повторный анализ

#### Ключевые фрагменты кода (Часть 1)

**Исправление SQL-инъекции (/user)**
```py
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```
Использование параметризованных запросов исключает выполнение вредоносного SQL-кода, так как данные передаются отдельно от запроса.

---

**Исправление SQL-инъекции (/search)**
```py
query = "SELECT * FROM users WHERE username LIKE ?"
cursor.execute(query, (f"%{username}%",))
```
Параметры экранируются драйвером SQLite, что предотвращает внедрение SQL.

---

**Удаление hardcoded секрета**
```py
API_KEY = os.environ.get('API_KEY')

if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
```
Секреты не должны храниться в коде, используются переменные окружения.

---

**Исправление Command Injection**
```py
ALLOWED_COMMANDS = ['echo', 'date', 'whoami']

cmd = request.args.get('cmd', '')
parts = cmd.split()

if parts[0] not in ALLOWED_COMMANDS:
    return jsonify({"error": "Command not allowed"}), 403

result = subprocess.check_output(parts)
```
Убрано `shell=True` и добавлен `allow-list` допустимых команд.

---

**Конфигурация Bandit (.bandit)**
```yaml
skips: ['B101']
severity: MEDIUM
```

---

#### Результаты выполнения (Часть 1)
- До исправлений: обнаружено несколько HIGH/MEDIUM уязвимостей
- После исправлений: критические уязвимости устранены
- SQL-инъекции больше не воспроизводятся
- Command injection заблокирован
- API-ключ не хранится в коде

---
### Часть 2: SCA + DAST + XSS защита

#### Структура проекта

```
lab4/sca/
  ├── app.js
  ├── package.json
  ├── views/
  │   └── index.ejs
  ├── comments.db
  ├── audit-report.json
  ├── zap_report.html
  └── security-check.sh
```

#### Выполненные задачи

1. Проведен анализ зависимостей (`npm audit`)
2. Обнаружены уязвимости в: express, axios (SSRF), ejs
3. Обновлены зависимости
4. Проведено сканирование OWASP ZAP
5. Обнаружены XSS-уязвимости
6. Реализована защита: экранирование, санитизация, CSP
7. Исправлены SQL-инъекции

#### Ключевые фрагменты кода (Часть 2)

**Исправление SQL-инъекции (/api/search)**
```js
db.all(`SELECT * FROM comments WHERE comment LIKE ?`, 
    [`%${search}%`], 
    (err, comments) => {
        res.json(comments);
    });
```
Используется параметризованный запрос вместо конкатенации.

---

**Allow-list для сортировки**
```js
const allowedSort = [
    'created_at DESC',
    'created_at ASC',
    'username ASC',
    'username DESC'
];

if (!allowedSort.includes(sortParam)) {
    return res.status(400).json({ error: 'Invalid sort parameter' });
}
```
Предотвращает SQL-инъекцию через ORDER BY.

---

**Санитизация входных данных**
```js
const sanitizeHtml = (input) => {
    return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
};
```

---

**Безопасный вывод вместо innerHTML**
```js
const div = document.createElement('div');
div.textContent = comment.comment;
container.appendChild(div);
```
`textContent` не интерпретирует HTML, защита от XSS

---

**Content Security Policy**
```js
app.use((req, res, next) => {
    res.setHeader(
        'Content-Security-Policy',
        "default-src 'self'; script-src 'self';"
    );
    next();
});
```

---

**Обновление зависимостей (package.json)**
```json
"express": "^4.21.0",
"axios": "^1.6.0"
```

---

## Результаты выполнения (Часть 2)

- npm audit выявил уязвимые пакеты
- после обновления количество уязвимостей уменьшилось
- XSS-атаки больше не выполняются
- OWASP ZAP показал снижение уровня риска
- SSRF через axios устранен

---

## Ответы на контрольные вопросы

### Часть 1 (SAST)

#### **Какие уязвимости обнаружил Bandit?**

**Ответ:**  
SQL Injection (строки с f-string запросами), Hardcoded secrets, Command Injection (subprocess + shell=True)

#### **Почему параметризованные запросы защищают?**

**Ответ:**  
Параметры передаются отдельно от SQL-запроса, интерпретатор не воспринимает их как часть SQL-кода.

#### **Разница между shell=True и split()**

**Ответ:**  
`shell=True` выполняет строку как команду (опасно), `split()` передает аргументы напрямую (без интерпретации shell)

#### **Какие уязвимости SAST не находит?**

**Ответ:**  
- логические ошибки
- runtime-уязвимости
- ошибки конфигурации
- XSS в браузере

### Часть 2 (SCA + DAST)

#### **Какие CVE обнаружены?**

**Ответ:**  
- axios < 0.19 — SSRF
- старые версии express — уязвимости middleware
- ejs — XSS

#### **Разница npm audit и snyk**

**Ответ:**  
`npm audit` - базовый анализ, `snyk` - более глубокий анализ + база CVE

#### **Как ZAP находит XSS?**

**Ответ:**  
отправляет payload'ы, анализирует ответы, проверяет выполнение скриптов

#### **Почему CSP эффективен?**

**Ответ:**  
Даже если XSS есть, браузер блокирует выполнение скриптов, не разрешённых политикой.

#### **Ограничения DAST**

**Ответ:**  
- не видит исходный код
- не находит все уязвимости
- зависит от покрытия тестами

---

## Итог

В ходе лабораторной работы были изучены и применены современные подходы к обеспечению безопасности веб-приложений. Проведен статический анализ кода, анализ зависимостей и динамическое тестирование. Выявленные уязвимости устранены с использованием параметризованных запросов, санитизации данных, политики CSP и обновления библиотек. Получены практические навыки работы с инструментами Bandit, npm audit и OWASP ZAP, а также понимание принципов защиты от SQL-инъекций, XSS и других атак.