const http = require("http");
const app = require("./index");
require("dotenv").config();

const PORT = process.env.PORT || 5000;
let serverStatus = false;

// 📌 Роутинг до запуска сервера
app.get("/", (req, res) => {
  if (serverStatus) {
    res.status(200).json({
      "Server Status": serverStatus,
      Message: "Server has been started successfully!",
    });
  } else {
    res.status(500).json({
      "Server Status": serverStatus,
      Message: "Server not started properly.",
    });
  }
});

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
