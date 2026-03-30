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

initializeDataFile();

// GET /api/tasks/stats/summary — MUST be before /:id
router.get('/stats/summary', async (req, res, next) => {
  try {
    const data = await readData();
    const tasks = data.tasks;
    const now = new Date();

    const stats = {
      total: tasks.length,
      completed: 0,
      pending: 0,
      overdue: 0,
      byCategory: {},
      byPriority: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
    };

    for (const task of tasks) {
      if (task.completed) {
        stats.completed++;
      } else {
        stats.pending++;
        if (task.dueDate && new Date(task.dueDate) < now) {
          stats.overdue++;
        }
      }

      stats.byCategory[task.category] = (stats.byCategory[task.category] || 0) + 1;

      const p = task.priority;
      if (p >= 1 && p <= 5) {
        stats.byPriority[p]++;
      }
    }

    res.json({ success: true, data: stats });
  } catch (error) {
    next(error);
  }
});

// GET /api/tasks/search/text — MUST be before /:id
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

    const results = data.tasks.filter(task =>
      (task.title && task.title.toLowerCase().includes(searchTerm)) ||
      (task.description && task.description.toLowerCase().includes(searchTerm))
    );

    res.json({ success: true, count: results.length, data: results });
  } catch (error) {
    next(error);
  }
});

// GET /api/tasks — list with filtering, sorting, pagination
router.get('/', async (req, res, next) => {
  try {
    const { category, completed, priority, sortBy, page, limit } = req.query;
    const data = await readData();

    let tasks = [...data.tasks];

    if (category) {
      tasks = tasks.filter(t => t.category === category);
    }

    if (completed !== undefined) {
      const completedBool = completed === 'true';
      tasks = tasks.filter(t => t.completed === completedBool);
    }

    if (priority !== undefined) {
      const priorityNum = parseInt(priority);
      if (!isNaN(priorityNum)) {
        tasks = tasks.filter(t => t.priority === priorityNum);
      }
    }

    if (sortBy) {
      const descending = sortBy.startsWith('-');
      const field = descending ? sortBy.slice(1) : sortBy;

      tasks.sort((a, b) => {
        let valA = a[field];
        let valB = b[field];

        if (field === 'dueDate' || field === 'createdAt') {
          valA = valA ? new Date(valA).getTime() : 0;
          valB = valB ? new Date(valB).getTime() : 0;
        }

        if (valA < valB) return descending ? 1 : -1;
        if (valA > valB) return descending ? -1 : 1;
        return 0;
      });
    }

    const pageNum = parseInt(page) || 1;
    const limitNum = parseInt(limit) || 10;
    const startIndex = (pageNum - 1) * limitNum;
    const paginated = tasks.slice(startIndex, startIndex + limitNum);

    res.json({
      success: true,
      count: paginated.length,
      total: tasks.length,
      page: pageNum,
      totalPages: Math.ceil(tasks.length / limitNum),
      data: paginated
    });
  } catch (error) {
    next(error);
  }
});

// GET /api/tasks/:id
router.get('/:id', validateId, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const data = await readData();

    const task = data.tasks.find(t => t.id === taskId);
    if (!task) {
      return res.status(404).json({ success: false, error: `Задача с ID ${taskId} не найдена` });
    }

    res.json({ success: true, data: task });
  } catch (error) {
    next(error);
  }
});

// POST /api/tasks
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

    data.tasks.push(newTask);
    await writeData(data);

    res.status(201).json({ success: true, message: 'Задача успешно создана', data: newTask });
  } catch (error) {
    next(error);
  }
});

// PUT /api/tasks/:id
router.put('/:id', validateId, validateUpdateTask, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const updates = req.body;
    const data = await readData();

    const taskIndex = data.tasks.findIndex(t => t.id === taskId);
    if (taskIndex === -1) {
      return res.status(404).json({ success: false, error: `Задача с ID ${taskId} не найдена` });
    }

    const updatedTask = {
      ...data.tasks[taskIndex],
      ...updates,
      updatedAt: new Date().toISOString()
    };
    data.tasks[taskIndex] = updatedTask;
    await writeData(data);

    res.json({ success: true, message: 'Задача успешно обновлена', data: updatedTask });
  } catch (error) {
    next(error);
  }
});

// PATCH /api/tasks/:id/complete
router.patch('/:id/complete', validateId, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const data = await readData();

    const taskIndex = data.tasks.findIndex(t => t.id === taskId);
    if (taskIndex === -1) {
      return res.status(404).json({ success: false, error: `Задача с ID ${taskId} не найдена` });
    }

    data.tasks[taskIndex].completed = true;
    data.tasks[taskIndex].updatedAt = new Date().toISOString();
    await writeData(data);

    res.json({ success: true, message: 'Задача отмечена как выполненная', data: data.tasks[taskIndex] });
  } catch (error) {
    next(error);
  }
});

// DELETE /api/tasks/:id
router.delete('/:id', validateId, async (req, res, next) => {
  try {
    const taskId = req.params.id;
    const data = await readData();

    const taskIndex = data.tasks.findIndex(t => t.id === taskId);
    if (taskIndex === -1) {
      return res.status(404).json({ success: false, error: `Задача с ID ${taskId} не найдена` });
    }

    data.tasks.splice(taskIndex, 1);
    await writeData(data);

    res.json({ success: true, message: 'Задача успешно удалена' });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
