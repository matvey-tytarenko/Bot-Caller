const express = require('express');
const cors = require('cors');
const router = require('./Routes/Route')

const app = express();

// Middlewares
app.use(express.json());
app.use(cors());
app.use('/api', router)

// Export
module.exports = app;