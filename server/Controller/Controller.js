const fs = require("fs");
const path = require("path");

module.exports.GetInfo = (req, res) => {
  const filePath = path.join(__dirname, "..", "json", "message.json");

  try {
    const json = fs.readFileSync(filePath, "utf-8");
    const data = JSON.parse(json);
    console.log(data);
    res.json(data);
  } catch (error) {
    console.error("❌ JSON Read Error:", error.message);
    res.status(500).json({ error: "File not found or invalid JSON" });
  }
};
