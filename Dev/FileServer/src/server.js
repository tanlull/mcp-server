const express = require('express');
const fs = require('fs').promises;
const path = require('path');

const app = express();
app.use(express.json());

// Configuration
const PORT = 3000;
const BASE_PATH = process.env.BASE_PATH || process.env.HOME;

// Error handler middleware
const errorHandler = (err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: err.message || 'Internal Server Error',
    code: err.code
  });
};

// MCP Routes
app.post('/list', async (req, res, next) => {
  try {
    const dirPath = path.join(BASE_PATH, req.body.path || '');
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    
    const items = await Promise.all(entries.map(async (entry) => {
      const fullPath = path.join(dirPath, entry.name);
      const stats = await fs.stat(fullPath);
      
      return {
        name: entry.name,
        path: path.relative(BASE_PATH, fullPath),
        type: entry.isDirectory() ? 'directory' : 'file',
        size: stats.size,
        modified: stats.mtime,
        created: stats.birthtime
      };
    }));

    res.json({ items });
  } catch (err) {
    next(err);
  }
});

app.post('/read', async (req, res, next) => {
  try {
    const filePath = path.join(BASE_PATH, req.body.path);
    const content = await fs.readFile(filePath, 'utf-8');
    res.json({ content });
  } catch (err) {
    next(err);
  }
});

app.post('/write', async (req, res, next) => {
  try {
    const filePath = path.join(BASE_PATH, req.body.path);
    await fs.writeFile(filePath, req.body.content);
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

app.post('/create', async (req, res, next) => {
  try {
    const itemPath = path.join(BASE_PATH, req.body.path);
    
    if (req.body.type === 'directory') {
      await fs.mkdir(itemPath, { recursive: true });
    } else {
      await fs.writeFile(itemPath, '');
    }
    
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

app.post('/delete', async (req, res, next) => {
  try {
    const itemPath = path.join(BASE_PATH, req.body.path);
    const stats = await fs.stat(itemPath);
    
    if (stats.isDirectory()) {
      await fs.rmdir(itemPath, { recursive: true });
    } else {
      await fs.unlink(itemPath);
    }
    
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

app.post('/move', async (req, res, next) => {
  try {
    const sourcePath = path.join(BASE_PATH, req.body.source);
    const targetPath = path.join(BASE_PATH, req.body.target);
    
    await fs.rename(sourcePath, targetPath);
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

app.post('/copy', async (req, res, next) => {
  try {
    const sourcePath = path.join(BASE_PATH, req.body.source);
    const targetPath = path.join(BASE_PATH, req.body.target);
    
    const stats = await fs.stat(sourcePath);
    if (stats.isDirectory()) {
      // Recursive directory copy
      await fs.cp(sourcePath, targetPath, { recursive: true });
    } else {
      await fs.copyFile(sourcePath, targetPath);
    }
    
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

// Apply error handler
app.use(errorHandler);

// Start server
app.listen(PORT, () => {
  console.log(`MCP Server running at http://localhost:${PORT}`);
  console.log(`Base path: ${BASE_PATH}`);
});
