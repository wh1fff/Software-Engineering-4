# **Лабораторная работа 13. Часть 2: Анализ зависимостей и OWASP Top 10**

## **Тема:** Выявление уязвимых зависимостей, динамическое тестирование веб-приложений и защита от XSS-атак.

### **Цель работы:**
Научиться использовать инструменты анализа зависимостей (SCA) для выявления уязвимых библиотек, ознакомиться с основами динамического тестирования безопасности (DAST) с помощью OWASP ZAP, а также освоить методы защиты от XSS-уязвимостей.

---

## **Задание: Анализ и защита веб-приложения с уязвимыми зависимостями**

Вам предоставлено веб-приложение на Node.js/Express, которое использует устаревшие библиотеки с известными уязвимостями и содержит XSS-уязвимости. Ваша задача — проанализировать зависимости, выявить уязвимости, протестировать приложение с помощью OWASP ZAP и внедрить защиту от XSS.

---

## **Часть 2A: Анализ зависимостей (SCA)**

### **1. Настройка проекта Node.js**

```bash
# Создание директории проекта
mkdir lab4-sca
cd lab4-sca

# Инициализация Node.js проекта
npm init -y

# Установка зависимостей (уязвимые версии — специально для лабораторной)
npm install express@4.16.0 ejs@2.6.1 body-parser@1.18.3
npm install axios@0.18.0 --save
npm install sqlite3@5.0.0

# Установка инструментов для анализа
npm install -g npm-audit
npm install -g snyk
```

### **2. Базовый код (70% предоставляется)**

**Файл: `app.js`**

```javascript
const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const axios = require('axios');

const app = express();
const port = 3000;

// Настройка шаблонизатора EJS
app.set('view engine', 'ejs');
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Инициализация базы данных
const db = new sqlite3.Database('./comments.db');

db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    
    // Добавляем тестовые комментарии
    db.run(`INSERT OR IGNORE INTO comments (id, username, comment) VALUES 
        (1, 'admin', 'Добро пожаловать на сайт!'),
        (2, 'user1', 'Отличный ресурс'),
        (3, 'user2', 'Очень полезная информация')`);
});

// Глобальная переменная для API ключа (hardcoded)
const API_KEY = 'test-api-key-12345';

// Маршруты

// Главная страница с комментариями
app.get('/', (req, res) => {
    // ❌ УЯЗВИМЫЙ КОД: потенциальная SQL-инъекция
    // TODO: Исправить на параметризованный запрос
    db.all(`SELECT * FROM comments ORDER BY created_at DESC`, (err, comments) => {
        if (err) {
            res.status(500).send('Database error');
            return;
        }
        res.render('index', { comments: comments, error: null });
    });
});

// Страница добавления комментария
app.post('/comment', (req, res) => {
    const { username, comment } = req.body;
    
    // ❌ УЯЗВИМЫЙ КОД: XSS-уязвимость — данные сохраняются без экранирования
    // TODO: Добавить санитизацию перед сохранением
    db.run(`INSERT INTO comments (username, comment) VALUES (?, ?)`, 
        [username || 'Anonymous', comment], 
        function(err) {
            if (err) {
                res.status(500).send('Error saving comment');
                return;
            }
            res.redirect('/');
        });
});

// API для получения комментариев (JSON)
app.get('/api/comments', (req, res) => {
    // ❌ УЯЗВИМЫЙ КОД: SQL-инъекция в параметре sort
    const sort = req.query.sort || 'created_at DESC';
    
    // TODO: Исправить SQL-инъекцию — использовать allow-list
    db.all(`SELECT * FROM comments ORDER BY ${sort}`, (err, comments) => {
        if (err) {
            res.status(500).json({ error: 'Database error' });
            return;
        }
        res.json(comments);
    });
});

// API для поиска по комментариям
app.get('/api/search', (req, res) => {
    const search = req.query.q || '';
    
    // ❌ УЯЗВИМЫЙ КОД: SQL-инъекция
    // TODO: Исправить на параметризованный запрос
    db.all(`SELECT * FROM comments WHERE comment LIKE '%${search}%'`, (err, comments) => {
        if (err) {
            res.status(500).json({ error: 'Database error' });
            return;
        }
        res.json(comments);
    });
});

// Эндпоинт с hardcoded секретом
app.get('/api/config', (req, res) => {
    // TODO: Убрать hardcoded ключ, использовать переменные окружения
    res.json({ 
        api_key: API_KEY,
        environment: 'development',
        debug: true
    });
});

// Эндпоинт, использующий axios с уязвимой версией
app.get('/api/external', async (req, res) => {
    const url = req.query.url || 'https://api.example.com/data';
    
    try {
        // ❌ УЯЗВИМЫЙ КОД: axios до версии 0.19.0 уязвим к SSRF
        const response = await axios.get(url);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'External request failed' });
    }
});

app.listen(port, () => {
    console.log(`App listening at http://localhost:${port}`);
});
```

**Файл: `views/index.ejs`**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Comment Board</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .comment { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
        .username { font-weight: bold; color: #333; }
        .date { font-size: 0.8em; color: #666; }
        .error { color: red; }
        form { margin: 20px 0; }
        input, textarea { width: 300px; margin: 5px 0; }
        button { margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Comment Board</h1>
    
    <form action="/comment" method="POST">
        <div>
            <label>Username:</label><br>
            <input type="text" name="username" placeholder="Your name">
        </div>
        <div>
            <label>Comment:</label><br>
            <textarea name="comment" rows="4" cols="40" placeholder="Your comment"></textarea>
        </div>
        <button type="submit">Post Comment</button>
    </form>
    
    <h2>Comments</h2>
    
    <% if (error) { %>
        <div class="error"><%= error %></div>
    <% } %>
    
    <% comments.forEach(function(comment) { %>
        <div class="comment">
            <div class="username"><%= comment.username %></div>
            <div class="comment-text"><%= comment.comment %></div>
            <div class="date"><%= comment.created_at %></div>
        </div>
    <% }); %>
    
    <div id="api-data">
        <h3>API Data</h3>
        <button onclick="loadComments()">Load Comments via API</button>
        <div id="api-result"></div>
    </div>
    
    <script>
        // ❌ УЯЗВИМЫЙ КОД: функция, уязвимая к XSS через eval
        function loadComments() {
            fetch('/api/comments')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    data.forEach(comment => {
                        // TODO: Исправить — использовать textContent, не innerHTML
                        html += '<div>' + comment.comment + '</div>';
                    });
                    document.getElementById('api-result').innerHTML = html;
                });
        }
        
        // ❌ УЯЗВИМЫЙ КОД: eval с пользовательским вводом
        function executeCode() {
            const code = document.getElementById('user-code').value;
            // TODO: Убрать eval, использовать безопасные альтернативы
            eval(code);
        }
    </script>
</body>
</html>
```

**Файл: `package.json`**

```json
{
  "name": "lab4-sca",
  "version": "1.0.0",
  "description": "Vulnerable app for security testing",
  "main": "app.js",
  "scripts": {
    "start": "node app.js",
    "audit": "npm audit"
  },
  "dependencies": {
    "express": "4.16.0",
    "ejs": "2.6.1",
    "body-parser": "1.18.3",
    "axios": "0.18.0",
    "sqlite3": "5.0.0"
  }
}
```

### **3. Задания для самостоятельного выполнения (30% дописать)**

---

## **Задание A: Анализ зависимостей (SCA)**

#### **A1. Запуск npm audit**

```bash
# Запуск аудита зависимостей
npm audit

# Просмотр подробного отчета
npm audit --json > audit-report.json
```

**Вопросы для анализа (ответить в отчете):**
1. Какие уязвимости обнаружены в зависимостях? Укажите названия пакетов, версии и CVE-идентификаторы.
2. Какова серьезность (severity) каждой уязвимости?
3. Какие уязвимости можно исправить автоматически, а какие требуют ручного обновления?

#### **A2. Исправление уязвимых зависимостей**

```bash
# Автоматическое исправление уязвимостей (там, где возможно)
npm audit fix

# Для критических уязвимостей, требующих обновления мажорной версии
npm audit fix --force

# Обновление конкретных пакетов
npm install express@latest
npm install axios@latest
```

**Дополнительно:** Используйте Snyk для более глубокого анализа:

```bash
# Установка Snyk
npm install -g snyk

# Аутентификация (требуется бесплатный аккаунт)
snyk auth

# Анализ проекта
snyk test

# Мониторинг зависимостей
snyk monitor
```

---

## **Задание B: Динамическое тестирование с OWASP ZAP**

#### **B1. Запуск OWASP ZAP**

```bash
# Запуск через Docker (рекомендуется)
docker pull owasp/zap2docker-stable

# Запуск в режиме пассивного сканирования
docker run -v $(pwd):/zap/wrk -t owasp/zap2docker-stable \
    zap-baseline.py -t http://host.docker.internal:3000 \
    -g gen.conf -r zap_report.html
```

**Альтернативный способ:** Скачать и установить ZAP с официального сайта, запустить в графическом режиме.

#### **B2. Ручное тестирование XSS-уязвимостей**

**Тестовые payload'ы для XSS:**

```bash
# Тест 1: Простой XSS
POST http://localhost:3000/comment
Content-Type: application/x-www-form-urlencoded

username=<script>alert('XSS')</script>&comment=Test

# Тест 2: XSS через атрибут
GET http://localhost:3000/search?q="><script>alert('XSS')</script>

# Тест 3: XSS через событие
GET http://localhost:3000/user?name=<img src=x onerror=alert('XSS')>

# Тест 4: XSS через eval
# Вставьте в поле ввода на странице:
# alert(document.cookie)
```

**Вопросы для отчета:**
1. Какие XSS-уязвимости были обнаружены?
2. Как OWASP ZAP идентифицирует уязвимости?
3. В чем разница между активным и пассивным сканированием?

---

## **Задание C: Исправление XSS-уязвимостей**

#### **C1. Исправление в шаблоне EJS**

EJS по умолчанию экранирует HTML при использовании `<%= %>`. Убедитесь, что везде используется правильный синтаксис:

```ejs
<!-- Безопасно: экранирует HTML -->
<div><%= comment.username %></div>
<div><%= comment.comment %></div>

<!-- Опасно: не экранирует HTML -->
<!-- <div><%- comment.comment %></div> -->
```

#### **C2. Исправление в JavaScript (client-side)**

```javascript
// Шаблон для исправления XSS в динамически создаваемом HTML
function loadCommentsSafe() {
    fetch('/api/comments')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('api-result');
            container.innerHTML = ''; // Очистка
            
            data.forEach(comment => {
                // Безопасный способ: создание элементов через DOM API
                const div = document.createElement('div');
                const text = document.createTextNode(comment.comment);
                div.appendChild(text);
                container.appendChild(div);
                
                // Альтернатива: использование textContent
                // div.textContent = comment.comment;
            });
        });
}

// TODO: Исправить функцию executeCode — удалить eval
function executeCodeSafe() {
    const code = document.getElementById('user-code').value;
    // Вариант 1: Запретить выполнение произвольного кода
    alert('Code execution is disabled for security reasons');
    
    // Вариант 2: Если необходимо — использовать безопасные альтернативы
    // Например, разбор JSON вместо eval
    try {
        const data = JSON.parse(code);
        console.log('Parsed data:', data);
    } catch (e) {
        console.log('Invalid JSON');
    }
}
```

#### **C3. Внедрение Content Security Policy (CSP)**

Добавьте CSP-заголовки в Express:

```javascript
// TODO: Добавить middleware для CSP
app.use((req, res, next) => {
    // Базовый CSP: запрет inline-скриптов, разрешение только из того же источника
    res.setHeader(
        'Content-Security-Policy',
        "default-src 'self'; script-src 'self'; style-src 'self';"
    );
    next();
});

// Для более гибкой настройки (с nonce):
const crypto = require('crypto');

app.use((req, res, next) => {
    const nonce = crypto.randomBytes(16).toString('base64');
    res.locals.nonce = nonce;
    res.setHeader(
        'Content-Security-Policy',
        `default-src 'self'; script-src 'self' 'nonce-${nonce}';`
    );
    next();
});
```

#### **C4. Санитизация данных перед сохранением**

```javascript
// TODO: Добавить функцию санитизации
const sanitizeHtml = (input) => {
    if (!input) return '';
    // Базовая санитизация: замена опасных символов
    return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .replace(/\//g, '&#x2F;');
};

// Использование при сохранении комментария
app.post('/comment', (req, res) => {
    let { username, comment } = req.body;
    
    // Санитизация входных данных
    username = sanitizeHtml(username || 'Anonymous');
    comment = sanitizeHtml(comment || '');
    
    db.run(`INSERT INTO comments (username, comment) VALUES (?, ?)`, 
        [username, comment], 
        function(err) {
            // ...
        });
});
```

---

## **Задание D: Исправление SQL-инъекций в Node.js**

Исправьте уязвимые SQL-запросы, используя параметризованные запросы или библиотеки типа `sql-template-strings`.

```javascript
// TODO: Исправить /api/search
app.get('/api/search', (req, res) => {
    const search = req.query.q || '';
    
    // Параметризованный запрос
    db.all(`SELECT * FROM comments WHERE comment LIKE ?`, 
        [`%${search}%`], 
        (err, comments) => {
            if (err) {
                res.status(500).json({ error: 'Database error' });
                return;
            }
            res.json(comments);
        });
});

// TODO: Исправить /api/comments (allow-list для сортировки)
app.get('/api/comments', (req, res) => {
    const sortParam = req.query.sort || 'created_at DESC';
    
    // Allow-list разрешенных значений
    const allowedSort = [
        'created_at DESC',
        'created_at ASC',
        'username ASC',
        'username DESC'
    ];
    
    if (!allowedSort.includes(sortParam)) {
        return res.status(400).json({ error: 'Invalid sort parameter' });
    }
    
    db.all(`SELECT * FROM comments ORDER BY ${sortParam}`, (err, comments) => {
        // ...
    });
});
```

---

## **Задание E: Дополнительное задание — Автоматизация в CI/CD**

Создайте скрипт для автоматического запуска сканирования зависимостей и OWASP ZAP в CI/CD.

**Файл: `security-check.sh`**

```bash
#!/bin/bash
# TODO: Создать скрипт для автоматической проверки безопасности

echo "Running npm audit..."
npm audit --audit-level=moderate

if [ $? -ne 0 ]; then
    echo "❌ npm audit failed!"
    exit 1
fi

echo "Running OWASP ZAP baseline scan..."
docker run -v $(pwd):/zap/wrk -t owasp/zap2docker-stable \
    zap-baseline.py -t http://localhost:3000 \
    -r zap_report.html

echo "✅ Security checks completed"
```

**Файл: `.github/workflows/security.yml` (для GitHub Actions)**

```yaml
# TODO: Создать GitHub Actions workflow
name: Security Scan

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Еженедельно

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm audit --audit-level=high
      - run: npx snyk test
```

---

### **4. Запуск и проверка**

```bash
# Запуск приложения
npm start

# В другом терминале: тестирование уязвимостей

# Проверка XSS через curl
curl -X POST http://localhost:3000/comment \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=<script>alert('xss')</script>&comment=test"

# Проверка SQL-инъекции
curl "http://localhost:3000/api/search?q=' OR '1'='1"

# Проверка SSRF через axios
curl "http://localhost:3000/api/external?url=http://169.254.169.254/latest/meta-data/"

# Проверка уязвимостей зависимостей
npm audit

# Повторное сканирование ZAP
docker run -v $(pwd):/zap/wrk -t owasp/zap2docker-stable \
    zap-baseline.py -t http://host.docker.internal:3000 \
    -r zap_report_after.html
```

---

### **5. Что должно быть в отчёте:**

1. **Исходный код:**
   - Файл `app.js` с исправленными уязвимостями.
   - Файл `views/index.ejs` с исправленным шаблоном.
   - Файл `package.json` с обновленными версиями зависимостей.
   - Файл `security-check.sh` (если выполнено доп. задание).

2. **Скриншоты:**
   - Отчет `npm audit` до и после исправления зависимостей.
   - Отчет OWASP ZAP (zap_report.html) до исправлений.
   - Отчет OWASP ZAP после исправлений.
   - Доказательство успешного предотвращения XSS-атак (скриншот, что скрипт не выполняется).

3. **Ответы на вопросы:**
   - Какие CVE были обнаружены в зависимостях? Каковы их последствия?
   - В чем разница между `npm audit` и `snyk test`?
   - Как OWASP ZAP обнаруживает XSS-уязвимости? Объясните механизм.
   - Почему CSP (Content Security Policy) эффективен против XSS, даже если разработчик забыл экранировать вывод?
   - Какие ограничения есть у DAST-инструментов по сравнению с SAST?

---

### **6. Критерии оценивания:**

#### **Обязательные требования (минимум для зачета):**
- **Анализ зависимостей:** Запущен `npm audit`, выявлены уязвимые пакеты, предоставлен отчет.
- **Обновление зависимостей:** Уязвимые пакеты обновлены до безопасных версий (или обосновано, почему обновление невозможно).
- **XSS-уязвимости исправлены:** Шаблон EJS использует безопасное экранирование, client-side код не использует `innerHTML` с недоверенными данными.
- **SQL-инъекции исправлены:** Параметризованные запросы или allow-list для динамической сортировки.
- **OWASP ZAP запущен:** Предоставлен отчет сканирования.

#### **Дополнительные критерии (для повышения оценки):**
- **Внедрение CSP:** Добавлены заголовки Content Security Policy.
- **Санитизация:** Добавлена функция санитизации перед сохранением в БД.
- **Автоматизация:** Создан CI/CD workflow для автоматического сканирования.
- **Устранение SSRF:** Исправлен эндпоинт `/api/external` с добавлением валидации URL.

#### **Неприемлемые ошибки:**
- Оставлены XSS-уязвимости (пользовательский ввод выводится без экранирования).
- Оставлены SQL-инъекции.
- Hardcoded секреты в коде.

---

### **7. Полезные команды для Ubuntu:**

```bash
# Работа с npm audit
npm audit          # Показать отчет
npm audit fix      # Автоматическое исправление
npm audit fix --force  # Форсированное обновление (может сломать код)

# Работа с Snyk
snyk test          # Анализ проекта
snyk monitor       # Отправить отчет в Snyk dashboard
snyk wizard        # Интерактивное исправление

# Работа с OWASP ZAP через Docker
# Базовое сканирование
docker run -v $(pwd):/zap/wrk -t owasp/zap2docker-stable \
    zap-baseline.py -t http://localhost:3000 -r report.html

# Полное активное сканирование
docker run -v $(pwd):/zap/wrk -t owasp/zap2docker-stable \
    zap-full-scan.py -t http://localhost:3000 -r full_report.html

# API-сканирование (для OpenAPI/Swagger)
docker run -v $(pwd):/zap/wrk -t owasp/zap2docker-stable \
    zap-api-scan.py -t http://localhost:3000/swagger.json -r api_report.html

# Проверка XSS с помощью curl
curl -v "http://localhost:3000/?search=<script>alert(1)</script>"

# Проверка CSP заголовков
curl -I http://localhost:3000 | grep -i "content-security-policy"
```

---

### **8. Структура проекта:**

```
lab4-sca/
├── app.js
├── package.json
├── package-lock.json
├── views/
│   └── index.ejs
├── comments.db (создается автоматически)
├── security-check.sh (опционально)
├── .github/
│   └── workflows/
│       └── security.yml (опционально)
├── zap_report.html (создается при сканировании)
├── zap_report_after.html
└── audit-report.json
```

---

### **9. Советы по выполнению:**

1. **Запускайте ZAP в режиме пассивного сканирования сначала**, чтобы понять, какие уязвимости существуют без активного воздействия.
2. **Используйте `npm outdated`**, чтобы увидеть все устаревшие пакеты перед обновлением.
3. **Тестируйте XSS вручную** с помощью консоли разработчика браузера — это помогает понять, как именно уязвимость эксплуатируется.
4. **CSP лучше внедрять постепенно**, начиная с режима `Content-Security-Policy-Report-Only`, чтобы отследить нарушения без блокировки функционала.
5. **Не удаляйте функционал, исправляйте его** — цель лабораторной работы не в удалении эндпоинтов, а в понимании, как их защитить.

**Примечание:** В задании предоставлено ~70% кода. Ваша задача — понять логику работы, выявить уязвимости с помощью SCA и DAST-инструментов и дописать недостающие ~30% безопасных решений.