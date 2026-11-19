// Runs web/words.js in a fresh context and ranks the questions in a JSON file, for test_topic_search_emergency.py.
// Usage: node topic_search_emergency.mjs <words.js> <cases.json>
// Prints one ranked list per question: [[guide id, choice id or null, score], ...], best first.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const [, , wordsFile, casesFile] = process.argv;
const ctx = vm.createContext({});
vm.runInContext(readFileSync(wordsFile, 'utf8'), ctx, { filename: 'words.js' });
const W = ctx.SearchWords;
const cases = JSON.parse(readFileSync(casesFile, 'utf8'));
const stop = new Set(cases.stop || []);

// rankTopics is the function web/app.js calls from topicMatches(), so this is the app's own guide search.
process.stdout.write(JSON.stringify(
  cases.questions.map(q => W.rankTopics(q, cases.topics, stop).map(o => [o.t.id, o.c ? o.c.id : null, o.s])),
));
