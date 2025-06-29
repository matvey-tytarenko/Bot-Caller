const express = require("express");
const app = express();
app.use(express.json()); // Обработка JSON

const Telegram = {
  api: process.env.TELEGRAM_TOKEN,
  chat: { id: process.env.TELEGRAM_CHAT_ID },
};

let latestMessage = null;
let reset = null; // Здесь будем хранить последнее сообщение

// Отправка сообщения telegram
async function sendToTelegram(user, message) {
  const text = `Серёга хочет в тубзик`;
  const url = `https://api.telegram.org/bot${Telegram.api}/sendMessage`;

  const payload = {
    chat_id: process.env.TELEGRAM_CHAT_ID,
    text: text,
    parse_mode: "HTML",
  };

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const json = await res.json();
    console.log(`Telegram response: ${json}`);
    
  } catch (error) {
    console.error(`Telegram Error: ${error}`);
  }
}

// POST-запрос от клиента (горячая клавиша или трей)
app.post("/api/call", async (req, res) => {
  const { user, message } = req.body;

  if (!user || !message) {
    return res.status(400).json({ error: "Missing user or message" });
  }

  latestMessage = { user, message, time: new Date().toISOString() };
  console.log("📩 Message received:", latestMessage);

  res.status(200).json({ status: "ok", received: latestMessage });

  await sendToTelegram(user, message);

  // Reset for 10 sec
  if (reset) clearTimeout(reset);
  reset = setTimeout(() => {
    latestMessage = null;
  }, 30 * 1000);
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
