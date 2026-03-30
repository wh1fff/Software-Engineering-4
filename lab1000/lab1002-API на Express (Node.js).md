# **Лабораторная работа 2. Часть 2: API на Express (Node.js)**

## **Тема:** Разработка REST API с использованием Express и Node.js

### **Цель работы:**
Практическое знакомство с созданием RESTful API на Node.js с использованием Express. Освоение middleware, валидации данных, работы с файловой системой и сравнение подходов разных фреймворков.

---

## **Задание: API для управления задачами (Task Manager)**

Разработайте REST API для управления задачами с использованием Express, Node.js и файловой системы для хранения данных.

### **1. Настройка проекта**

Откройте терминал в Ubuntu и выполните:

```bash
# Создание проекта
mkdir task-api
cd task-api

# Инициализация проекта Node.js
npm init -y

# Установка зависимостей
npm install express cors dotenv
npm install -D nodemon

# Установка дополнительных пакетов для валидации и утилит
npm install joi uuid express-rate-limit helmet

# Создание структуры проекта
mkdir src
mkdir src/middleware
mkdir src/routes
mkdir src/utils
touch src/app.js
touch src/server.js
touch src/routes/tasks.js
touch src/middleware/validation.js
touch src/middleware/errorHandler.js
touch src/utils/fileOperations.js
touch .env
touch .gitignore
```

**Файл: `.gitignore`**
```
node_modules/
.DS_Store
*.log
tasks.json
.env
```

**Файл: `package.json`** (обновите scripts секцию)
```json
{
  "name": "task-api",
  "version": "1.0.0",
  "description": "REST API для управления задачами",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "nodemon src/server.js",
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "dotenv": "^16.0.0",
    "joi": "^17.9.0",
    "uuid": "^9.0.0",
    "express-rate-limit": "^6.10.0",
    "helmet": "^7.0.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.0"
  }
}
```

### **2. Базовое API (70% предоставляется)**

**Файл: `src/utils/fileOperations.js`**

```javascript
const fs = require('fs').promises;
const path = require('path');

const DATA_FILE = path.join(__dirname, '../../tasks.json');

// Инициализация файла данных если его нет
const initializeDataFile = async () => {
  try {
    await fs.access(DATA_FILE);
  } catch {
    // Файл не существует, создаем с начальными данными
    const initialData = {
      tasks: [],
      categories: ['work', 'personal', 'shopping', 'health'],
      lastId: 0
    };
    await fs.writeFile(DATA_FILE, JSON.stringify(initialData, null, 2));
  }
};

// Чтение данных из файла
const readData = async () => {
  try {
    const data = await fs.readFile(DATA_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error reading data file:', error);
    throw new Error('Failed to read data');
  }
};

// Запись данных в файл
const writeData = async (data) => {
  try {
    await fs.writeFile(DATA_FILE, JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('Error writing data file:', error);
    throw new Error('Failed to write data');
  }
};

// Получение следующего ID
const getNextId = async () => {
  const data = await readData();
  data.lastId += 1;
  await writeData(data);
  return data.lastId;
};

// Экспортируем функции
module.exports = {
  initializeDataFile,
  readData,
  writeData,
  getNextId
};
```

**Файл: `src/middleware/validation.js`**

```javascript
const Joi = require('joi');

// Схема для создания задачи
const createTaskSchema = Joi.object({
  title: Joi.string()
    .min(3)
    .max(100)
    .required()
    .messages({
      'string.min': 'Название должно содержать минимум 3 символа',
      'string.max': 'Название не должно превышать 100 символов',
      'any.required': 'Название обязательно'
    }),
  
  description: Joi.string()
    .max(500)
    .allow('')
    .messages({
      'string.max': 'Описание не должно превышать 500 символов'
    }),
  
  category: Joi.string()
    .valid('work', 'personal', 'shopping', 'health')
    .default('personal')
    .messages({
      'any.only': 'Категория должна быть одной из: work, personal, shopping, health'
    }),
  
  priority: Joi.number()
    .integer()
    .min(1)
    .max(5)
    .default(3)
    .messages({
      'number.min': 'Приоритет должен быть от 1 до 5',
      'number.max': 'Приоритет должен быть от 1 до 5'
    }),
  
  dueDate: Joi.date()
    .greater('now')
    .messages({
      'date.greater': 'Дата выполнения должна быть в будущем'
    })
});

// Схема для обновления задачи
const updateTaskSchema = Joi.object({
  title: Joi.string()
    .min(3)
    .max(100),
  
  description: Joi.string()
    .max(500)
    .allow(''),
  
  category: Joi.string()
    .valid('work', 'personal', 'shopping', 'health'),
  
  priority: Joi.number()
    .integer()
    .min(1)
    .max(5),
  
  dueDate: Joi.date()
    .greater('now'),
  
  completed: Joi.boolean()
});

// Middleware для валидации создания задачи
const validateCreateTask = (req, res, next) => {
  const { error } = createTaskSchema.validate(req.body, { abortEarly: false });
  
  if (error) {
    return res.status(400).json({
      error: 'Validation Error',
      details: error.details.map(detail => ({
        field: detail.path[0],
        message: detail.message
      }))
    });
  }
  
  next();
};

// Middleware для валидации обновления задачи
const validateUpdateTask = (req, res, next) => {
  const { error } = updateTaskSchema.validate(req.body, { abortEarly: false });
  
  if (error) {
    return res.status(400).json({
      error: 'Validation Error',
      details: error.details.map(detail => ({
        field: detail.path[0],
        message: detail.message
      }))
    });
  }
  
  // Проверка, что хотя бы одно поле передано для обновления
  if (Object.keys(req.body).length === 0) {
    return res.status(400).json({
      error: 'Validation Error',
      message: 'Необходимо передать хотя бы одно поле для обновления'
    });
  }
  
  next();
};

// Middleware для валидации ID
const validateId = (req, res, next) => {
  const id = parseInt(req.params.id);
  
  if (isNaN(id) || id <= 0) {
    return res.status(400).json({
      error: 'Validation Error',
      message: 'ID должен быть положительным числом'
    });
  }
  
  req.params.id = id; // Преобразуем ID в число
  next();
};

module.exports = {
  validateCreateTask,
  validateUpdateTask,
  validateId
};
```

**Файл: `src/middleware/errorHandler.js`**

```javascript
// Middleware для обработки ошибок 404
const notFoundHandler = (req, res, next) => {
  const error = new Error(`Not Found - ${req.originalUrl}`);
  error.status = 404;
  next(error);
};

// Основной обработчик ошибок
const errorHandler = (err, req, res, next) => {
  const statusCode = err.status || 500;
  const message = err.message || 'Internal Server Error';
  
  // Логирование ошибки (в реальном приложении можно писать в файл)
  console.error(`[${new Date().toISOString()}] ${statusCode} - ${message}`);
  console.error(err.stack);
  
  res.status(statusCode).json({
    error: {
      message,
      status: statusCode,
      timestamp: new Date().toISOString(),
      path: req.originalUrl,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    }
  });
};

module.exports = {
  notFoundHandler,
  errorHandler
};
```

### **3. Задания для самостоятельного выполнения (30% дописать)**

#### **A. Реализуйте CRUD операции в роутере задач** (обязательно)

**Файл: `src/routes/tasks.js`**

```javascript
const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const { 
  validateCreateTask, 
  validateUpdateTask, 
  validateId 
} = require('../middleware/validation');
const { 
  initializeDataFile, 
  readData, 
  writeData, 
  getNextId 
} = require('../utils/fileOperations');

// Инициализация файла данных при запуске
initializeDataFile();

// GET /api/tasks - получение всех задач с фильтрацией
router.get('/', async (req, res, next) => {
  try {
    const { category, completed, priority, sortBy } = req.query;
    const data = await readData();
    
    let tasks = [...data.tasks];
    
    // TODO: Реализуйте фильтрацию по категории (если передан параметр category)
    
    // TODO: Реализуйте фильтрацию по статусу выполнения
    // completed может быть 'true' или 'false' (строкой)
    
    // TODO: Реализуйте фильтрацию по приоритету
    // priority - число от 1 до 5
    
    // TODO: Реализуйте сортировку
    // sortBy может быть: 'dueDate', 'priority', 'createdAt'
    // Для сортировки по убыванию: '-dueDate', '-priority'
    
    // TODO: Добавьте пагинацию
    // Используйте параметры page и limit из query
    
    res.json({
      success: true,
      count: tasks.length,
      data: tasks
    });
    
  } catch (error) {
    next(error);
  }
});

// GET /api/tasks/:id - получение задачи по ID
router.get('/:id', validateId, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const data = await readData();
    
    // TODO: Найдите задачу по ID в data.tasks
    // Если задача не найдена, верните 404
    
    res.json({
      success: true,
      data: task
    });
    
  } catch (error) {
    next(error);
  }
});

// POST /api/tasks - создание новой задачи
router.post('/', validateCreateTask, async (req, res, next) => {
  try {
    const { title, description, category, priority, dueDate } = req.body;
    const data = await readData();
    
    const newTask = {
      id: await getNextId(),
      uuid: uuidv4(),
      title,
      description: description || '',
      category: category || 'personal',
      priority: priority || 3,
      dueDate: dueDate || null,
      completed: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    // TODO: Добавьте новую задачу в массив data.tasks
    
    // TODO: Сохраните обновленные данные
    
    res.status(201).json({
      success: true,
      message: 'Задача успешно создана',
      data: newTask
    });
    
  } catch (error) {
    next(error);
  }
});

// PUT /api/tasks/:id - полное обновление задачи
router.put('/:id', validateId, validateUpdateTask, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const updates = req.body;
    const data = await readData();
    
    // TODO: Найдите задачу по ID
    // Если не найдена - 404
    
    // TODO: Обновите задачу (все переданные поля)
    // Не забудьте обновить updatedAt
    
    // TODO: Сохраните обновленные данные
    
    res.json({
      success: true,
      message: 'Задача успешно обновлена',
      data: updatedTask
    });
    
  } catch (error) {
    next(error);
  }
});

// PATCH /api/tasks/:id/complete - отметка задачи как выполненной
router.patch('/:id/complete', validateId, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const data = await readData();
    
    // TODO: Найдите задачу по ID
    // Если не найдена - 404
    
    // TODO: Обновите статус задачи на completed: true
    // Обновите updatedAt
    
    // TODO: Сохраните обновленные данные
    
    res.json({
      success: true,
      message: 'Задача отмечена как выполненная',
      data: task
    });
    
  } catch (error) {
    next(error);
  }
});

// DELETE /api/tasks/:id - удаление задачи
router.delete('/:id', validateId, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const data = await readData();
    
    // TODO: Найдите индекс задачи по ID
    // Если не найдена - 404
    
    // TODO: Удалите задачу из массива
    
    // TODO: Сохраните обновленные данные
    
    res.json({
      success: true,
      message: 'Задача успешно удалена'
    });
    
  } catch (error) {
    next(error);
  }
});
```

#### **B. Реализуйте статистику по задачам** (обязательно)

В тот же файл `src/routes/tasks.js` добавьте:

```javascript
// GET /api/tasks/stats - статистика по задачам
router.get('/stats/summary', async (req, res, next) => {
  try {
    const data = await readData();
    const tasks = data.tasks;
    
    const stats = {
      total: 0,
      completed: 0,
      pending: 0,
      overdue: 0,
      byCategory: {},
      byPriority: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0
      }
    };
    
    // TODO: Реализуйте подсчет статистики:
    // 1. Общее количество задач
    // 2. Количество выполненных задач
    // 3. Количество невыполненных задач
    // 4. Количество просроченных задач (dueDate < сегодня и completed = false)
    // 5. Распределение задач по категориям
    // 6. Распределение задач по приоритетам
    
    res.json({
      success: true,
      data: stats
    });
    
  } catch (error) {
    next(error);
  }
});
```

#### **C. Реализуйте эндпоинт для поиска задач** (дополнительно)

```javascript
// GET /api/tasks/search - поиск задач
router.get('/search/text', async (req, res, next) => {
  try {
    const { q } = req.query;
    
    if (!q || q.trim().length < 2) {
      return res.status(400).json({
        success: false,
        error: 'Поисковый запрос должен содержать минимум 2 символа'
      });
    }
    
    const data = await readData();
    const searchTerm = q.toLowerCase().trim();
    
    // TODO: Реализуйте поиск задач
    // Искать в полях title и description
    // Поиск должен быть регистронезависимым
    // Верните задачи, содержащие поисковый запрос
    
    res.json({
      success: true,
      count: results.length,
      data: results
    });
    
  } catch (error) {
    next(error);
  }
});
```

### **4. Настройка основного приложения**

**Файл: `src/app.js`**

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const tasksRouter = require('./routes/tasks');
const { notFoundHandler, errorHandler } = require('./middleware/errorHandler');

const app = express();

// Безопасность
app.use(helmet());

// CORS
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 минут
  max: 100, // максимум 100 запросов с одного IP
  message: {
    error: 'Слишком много запросов. Попробуйте позже.'
  }
});
app.use('/api/', limiter);

// Парсинг JSON
app.use(express.json());

// Логирование запросов (простое)
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Routes
app.use('/api/tasks', tasksRouter);

// TODO: Добавьте корневой маршрут GET / который возвращает информацию об API
// Пример: { name: 'Task Manager API', version: '1.0.0', docs: '/api/tasks' }

// TODO: Добавьте маршрут для проверки здоровья GET /health
// Должен возвращать { status: 'healthy', timestamp: new Date().toISOString() }

// Обработка 404
app.use(notFoundHandler);

// Обработка ошибок
app.use(errorHandler);

module.exports = app;
```

**Файл: `src/server.js`**

```javascript
require('dotenv').config();
const app = require('./app');

const PORT = process.env.PORT || 3000;

// Запуск сервера
app.listen(PORT, () => {
  console.log(`🚀 Сервер запущен на порту ${PORT}`);
  console.log(`📚 Документация API доступна по адресу: http://localhost:${PORT}/api/tasks`);
  console.log(`🌐 Режим: ${process.env.NODE_ENV || 'development'}`);
});

// Обработка неожиданных ошибок
process.on('unhandledRejection', (err) => {
  console.error('Unhandled Rejection:', err);
  // В продакшене можно завершить процесс
  // process.exit(1);
});

process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err);
  // В продакшене можно завершить процесс
  // process.exit(1);
});
```

### **5. Запуск и тестирование API**

```bash
# Запуск в режиме разработки
npm run dev

# Запуск в production режиме
NODE_ENV=production npm start

# API будет доступно по адресу:
# http://localhost:3000/api/tasks
```

**Тестирование через curl:**
```bash
# Создать задачу
curl -X POST "http://localhost:3000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Купить продукты",
    "description": "Молоко, хлеб, яйца",
    "category": "shopping",
    "priority": 2,
    "dueDate": "2024-12-31"
  }'

# Получить все задачи
curl -X GET "http://localhost:3000/api/tasks"

# Отметить задачу как выполненную
curl -X PATCH "http://localhost:3000/api/tasks/1/complete"

# Получить статистику
curl -X GET "http://localhost:3000/api/tasks/stats/summary"
```

### **6. Что должно быть в отчёте:**

1. **Исходный код:**
   - Полный код файла `src/routes/tasks.js` с вашими дополнениями
   - Код корневых маршрутов из `src/app.js`

2. **Скриншоты:**
   - Успешное создание задачи (POST /api/tasks)
   - Работа фильтрации (GET /api/tasks?category=work)
   - Статистика задач (GET /api/tasks/stats/summary)
   - Обработка ошибок валидации

3. **Ответы на вопросы:**
   - Какие middleware вы использовали и для чего?
   - Как работает валидация с Joi в сравнении с Pydantic из части 1?
   - В чем преимущества файлового хранения данных для этого задания?
   - Как бы вы улучшили это API для production использования?

### **7. Критерии оценивания:**

#### **Обязательные требования (минимум для зачета):**
- ✅ **CRUD операции:** Реализованы все основные операции (GET, POST, PUT, DELETE, PATCH)
- ✅ **Валидация:** Корректная работа middleware валидации
- ✅ **Фильтрация и сортировка:** Работают параметры запроса для фильтрации задач
- ✅ **Статистика:** Реализован эндпоинт /stats/summary с подсчетом метрик
- ✅ **Обработка ошибок:** Корректные HTTP статус-коды и структурированные ошибки

#### **Дополнительные критерии (для повышения оценки):**
- ✨ **Поиск задач:** Реализован эндпоинт /search для полнотекстового поиска
- ✨ **Пагинация:** Реализована пагинация в GET /api/tasks
- ✨ **Тесты:** Написаны автоматические тесты для API
- ✨ **Безопасность:** Добавлены дополнительные middleware безопасности (helmet, rate limit)
- ✨ **Качество кода:** Чистый, модульный код с правильной обработкой асинхронных операций

#### **Неприемлемые ошибки:**
- ❌ Отсутствие обработки ошибок при операциях с файлами
- ❌ Возможность создать задачу с прошедшей датой выполнения
- ❌ Некорректная валидация входных данных
- ❌ Отсутствие проверки существования задачи при обновлении/удалении

### **8. Полезные команды для Ubuntu:**

```bash
# Проверка версии Node.js
node --version

# Проверка запущенных процессов на порту 3000
sudo lsof -i :3000

# Принудительное завершение процесса
sudo kill -9 $(sudo lsof -t -i:3000)

# Мониторинг логов в реальном времени
tail -f tasks.json

# Тестирование с HTTPie
http POST localhost:3000/api/tasks title="Новая задача" priority=1
```

### **9. Структура проекта:**

```
task-api/
├── src/
│   ├── app.js                 # Основное приложение Express
│   ├── server.js              # Точка входа сервера
│   ├── routes/
│   │   └── tasks.js           # Роутер задач
│   ├── middleware/
│   │   ├── validation.js      # Middleware валидации
│   │   └── errorHandler.js    # Обработчики ошибок
│   └── utils/
│       └── fileOperations.js  # Операции с файлами
├── tasks.json                 # Файл с данными (создастся автоматически)
├── package.json
├── .env
└── .gitignore
```

### **10. Советы по выполнению:**

1. **Работайте поэтапно:** Сначала реализуйте базовые CRUD операции, затем добавляйте фильтрацию и сортировку
2. **Тестируйте через curl или Postman:** Убедитесь, что все эндпоинты работают корректно
3. **Обрабатывайте асинхронность:** Не забывайте про async/await при работе с файлами
4. **Валидируйте входные данные:** Проверяйте все параметры запросов
5. **Следите за структурой ответов:** Все ответы должны иметь единый формат

**Примечание:** В задании предоставлено ~70% кода. Ваша задача — понять архитектуру Express и дописать недостающие ~30% функционала, обращая внимание на обработку ошибок и валидацию данных.

---