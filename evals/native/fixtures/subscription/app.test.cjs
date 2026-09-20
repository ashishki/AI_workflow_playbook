const assert = require('node:assert/strict');
const {validEmail} = require('./app');
assert.equal(validEmail('reader@example.com'), true);
assert.equal(validEmail('wrong'), false);
assert.equal(validEmail(''), false);
console.log('Email validation checks passed');
