const readline = require('readline');
const mdToAdf = require('md-to-adf');

let input = '';
const rl = readline.createInterface({ input: process.stdin, terminal: false });

rl.on('line', (line) => {
  input += line + '\n';
});

rl.on('close', () => {
  try {
    const adf = mdToAdf(input);
    console.log(JSON.stringify(adf, null, 2));
  } catch (err) {
    console.error('❌ Conversion error:', err);
    process.exit(1);
  }
});
