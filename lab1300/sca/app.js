const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const axios = require('axios');
const crypto = require('crypto');

const app = express();
const port = 3000;

app.set('view engine', 'ejs');
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// CSP защита
app.use((req, res, next) => {
    const nonce = crypto.randomBytes(16).toString('base64');
    res.locals.nonce = nonce;
    res.setHeader(
        'Content-Security-Policy',
        `default-src 'self'; script-src 'self' 'nonce-${nonce}';`
    );
    next();
});

// БД
const db = new sqlite3.Database('./comments.db', (err) => {
    if (err) {
        console.error("DB error:", err.message);
    } else {
        console.log("Connected to SQLite DB");
    }
});

db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
});

// Санитизация
const sanitizeHtml = (input) => {
    if (!input) return '';
    return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
};

// Главная
app.get('/', (req, res) => {
    db.all(`SELECT * FROM comments ORDER BY created_at DESC`, (err, comments) => {
        if (err) {
            res.status(500).send('Database error');
            return;
        }
        res.render('index', { comments: comments, error: null });
    });
});

// Добавление комментария
app.post('/comment', (req, res) => {
    let { username, comment } = req.body;

    username = sanitizeHtml(username || 'Anonymous');
    comment = sanitizeHtml(comment || '');

    db.run(`INSERT INTO comments (username, comment) VALUES (?, ?)`,
        [username, comment],
        function(err) {
            if (err) {
                res.status(500).send('Error');
                return;
            }
            res.redirect('/');
        });
});

// API комментариев (allow-list)
app.get('/api/comments', (req, res) => {
    const sortParam = req.query.sort || 'created_at DESC';

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
        if (err) {
            res.status(500).json({ error: 'Database error' });
            return;
        }
        res.json(comments);
    });
});

// Поиск
app.get('/api/search', (req, res) => {
    const search = req.query.q || '';

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

// Безопасный внешний запрос
app.get('/api/external', async (req, res) => {
    const url = req.query.url;

    if (!url || !url.startsWith('https://')) {
        return res.status(400).json({ error: 'Invalid URL' });
    }

    try {
        const response = await axios.get(url);
        res.json(response.data);
    } catch {
        res.status(500).json({ error: 'Request failed' });
    }
});

app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});