const http = require("http");
const app = require("./index");
require("dotenv").config();

// Server config
const server = http.createServer(app);
const PORT = process.env.PORT || 5000;

// Server listen
server.listen(PORT, (err) => {
  let status = false;

  if (err) {
    console.error(`Server Error: ${err}`);
    app.get("/", (req, res) => {
      res.status(400).json({
        "Server Status": `${status}`,
        "Error Message": `${err}`,
      });
    });
  } else {
    console.log(`Server has been started on: http://localhost:${PORT}`);
    status = true;
    app.get("/", (req, res) => {
      res.status(200).json({
        "Server Status": `${status}`,
        Message: `Server has been started successfully!`,
      });
    });
  }
});
