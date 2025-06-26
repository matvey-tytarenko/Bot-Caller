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

server.listen(PORT, (error) => {
  if (error) {
    console.error("❌ Server failed to start:", error);
  } else {
    console.log(`✅ Server is running on http://localhost:${PORT}`);
  }
});