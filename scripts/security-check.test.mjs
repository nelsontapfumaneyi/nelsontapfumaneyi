import test from 'node:test';
import assert from 'node:assert/strict';
import {inspect,sensitivePath} from './security-check.mjs';
test('detects credentials and links without returning their values',()=>{
 const examples=[
  ['github-token','gh'+'p_'+'A'.repeat(36)],
  ['private-key','-----BEGIN '+'OPENSSH PRIVATE KEY-----'],
  ['ai-api-key','sk-'+'proj-'+'A'.repeat(40)],
  ['session-link','https://claude.ai/'+'code/session_'+'A'.repeat(24)],
  ['signed-url','https://example.invalid/file?'+'X-Amz-Signature='+'a'.repeat(64)],
  ['session-cookie','sessionKey='+'A'.repeat(40)],
  ['credential-url',['postgresql:', '/', '/', 'user', ':', 'password', '@localhost/db'].join('')],
  ['bearer-token','Bearer '+'A'.repeat(32)],
  ['jwt','eyJ'+'a'.repeat(12)+'.eyJ'+'b'.repeat(12)+'.'+'c'.repeat(12)]
 ];
 for(const [rule,value] of examples) {
  const hits=inspect(value); assert.ok(hits.some(h=>h.rule===rule),rule);
  assert.ok(!JSON.stringify(hits).includes(value));
 }
});
test('public sources and empty Tableau password are allowed',()=>{
 assert.deepEqual(inspect("https://www.rbz.co.zw/index.php\npassword=''\ndbname=umfdop"),[]);
});
test('credential files blocked but sanitized examples allowed',()=>{
 for(const p of ['.env','x/.env.production','x/id_ed25519','cookies.json','recording.har']) assert.ok(sensitivePath(p),p);
 for(const p of ['.env.example','.env.sample','data/findings.csv']) assert.ok(!sensitivePath(p),p);
});
