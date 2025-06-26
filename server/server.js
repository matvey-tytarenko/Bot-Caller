const app = require('./index')

module.exports = (req, res) => {
  if(req.url === "/") {
    res.status(200).json({
      "Server Status": true,
      "Message": "Server has been started successfully!",
    })
  } else {
    app(req, res);
  }
}