const { GetInfo } = require('../Controller/Controller');

const router = require('express').Router();

router.post('/call', GetInfo);

module.exports = router;