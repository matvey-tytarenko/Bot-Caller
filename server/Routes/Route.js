const { GetInfo } = require('../Controller/Controller');

const router = require('express').Router();

// router.post('/call', GetInfo);
router.get('/call', (req, res) => {
    res.status(200).json(req.body);
})

module.exports = router;