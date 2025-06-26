const http = require("http");
const app = require("./index");
require("dotenv").config();

const PORT = process.env.PORT || 5000;
let serverStatus = false;

// 📌 Роутинг до запуска сервера
function router(status, port) {
  app.get("/", (req, res) => {
    res.json({
      "Server Status": status,
      "Server Connection": "successfully",
    });
  });
}

router(serverStatus, PORT);

// 🔌 Запуск сервера
const server = http.createServer(app);

server.listen(PORT, (err) => {
  if (err) {
    console.error("❌ Server Error:", err);
  } else {
    serverStatus = true;
    console.log(`✅ Server started at: http://localhost:${PORT}`);
  }
});
