// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Wildcat Labs
// Allocate large compiler inputs on the heap; cwrap string arguments use stack space.
'use strict';
const fs = require('fs');
const compiler = require(process.argv[2]);
if (process.argv[3] === '--version') {
  process.stdout.write('Version: ' + compiler.cwrap('solidity_version', 'string', [])() + '\n');
} else if (process.argv[3] === '--standard-json') {
  const input = fs.readFileSync(0);
  if (input.length > 32 * 1024 * 1024) throw new Error('compiler-input-size');
  const pointer = compiler._malloc(input.length + 1);
  try {
    compiler.HEAPU8.set(input, pointer);
    compiler.HEAPU8[pointer + input.length] = 0;
    const result = compiler.cwrap('solidity_compile', 'string', ['number', 'number', 'number'])(pointer, 0, 0);
    process.stdout.write(result);
  } finally {
    compiler._free(pointer);
  }
} else {
  throw new Error('compiler-mode');
}
