const app = require("./index");

module.exports = (req, res) => {
  if (req.url === "/") {
    res.status(200).json({
      "Server Status": true,
      Message: "Serverless function is working!",
    });
  } else {
    app(req, res); // передаём в Express всё остальное
  }
};
