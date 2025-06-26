const express = require("express");
const app = express();
app.use(express.json()); // Обработка JSON

let latestMessage = null;
let reset = null; // Здесь будем хранить последнее сообщение

// POST-запрос от клиента (горячая клавиша или трей)
app.post("/api/call", (req, res) => {
  const { user, message } = req.body;

  if (!user || !message) {
    return res.status(400).json({ error: "Missing user or message" });
  }

  latestMessage = { user, message, time: new Date().toISOString() };
  console.log("📩 Message received:", latestMessage);

  res.status(200).json({ status: "ok", received: latestMessage });

  // Reset for 10 sec
  if (reset) clearTimeout(reset);
  reset = setTimeout(() => {
    latestMessage = null;
  }, 5 * 60 * 1000);
});

// GET-запрос на /
app.get("/", (req, res) => {
  if (latestMessage) {
    res.status(200).json({
      "Server Status": true,
      "Last Caller": latestMessage.user,
      Message: latestMessage.message,
      Time: latestMessage.time,
    });
  } else {
    res.status(200).json({
      "Server Status": true,
      Message: "No messages yet.",
    });
  }
});

// Экспорт serverless-функции для Vercel
module.exports = app;
