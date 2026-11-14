// Targeted disclosure guard, not a replacement for provider secret scanning.
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
export const rules = [
 ['private-key', /-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----/],
 ['github-token', /\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b/],
 ['ai-api-key', /\bsk-(?:ant-[A-Za-z0-9_-]{20,}|proj-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{32,})\b/],
 ['aws-access-key', /\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/],
 ['session-link', /https?:\/\/(?:claude\.ai\/(?:code\/session_|chat\/)|chatgpt\.com\/(?:c\/|share\/)|chat\.openai\.com\/(?:c\/|share\/))[A-Za-z0-9_-]+/i],
 ['credential-url', /[a-z][a-z0-9+.-]*:\/\/[^/\s:@]+:[^/\s@]+@/i],
 ['signed-url', /[?&](?:X-Amz-Signature|X-Goog-Signature|access_token|refresh_token|api_key|token|sig)=[A-Za-z0-9%_+./=-]{12,}/i],
 ['bearer-token', /\bBearer\s+[A-Za-z0-9._~+/-]{20,}/i],
 ['jwt', /\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/],
 ['session-cookie', /\b(?:sessionKey|session_token|sessionid|__Secure-next-auth\.session-token)\s*[:=]\s*["']?[A-Za-z0-9._~-]{20,}/i]
];
export function inspect(text) {
 const hits = [];
 for (const [i, line] of text.split(/\r?\n/).entries())
   for (const [rule, pattern] of rules) if (pattern.test(line)) hits.push({line:i+1, rule});
 return hits;
}
export function sensitivePath(path) {
 const name = path.split('/').pop();
 return (/^\.env(?:\.|$)/i.test(name) && !/\.example$|\.sample$|\.template$/i.test(name))
   || /^(?:id_rsa|id_ed25519|id_ecdsa|cookies\.txt|cookies\.json|storageState\.json|auth\.json|\.netrc|\.pgpass)$/i.test(name)
   || /\.(?:p12|pfx|har)$/i.test(name);
}
function git(args) { return execFileSync('git', args, {maxBuffer:64*1024*1024}); }
export function scan({since, all=false}={}) {
 if (since && !/^[a-f0-9]{40}$/i.test(since)) throw new Error('Expected a full commit SHA');
 const revisions = git(['rev-list', ...(all ? ['--all'] : [since ? since+'..HEAD' : 'HEAD'])]).toString().trim().split('\n').filter(Boolean);
 const trees = new Set(['HEAD', ...revisions]);
 const seen = new Set(); const findings = [];
 for (const rev of trees) {
   for (const entry of git(['ls-tree','-rz',rev]).toString().split('\0').filter(Boolean)) {
     const tab = entry.indexOf('\t'); const path = entry.slice(tab+1);
     const [mode,type,sha] = entry.slice(0,tab).split(' ');
     if (type !== 'blob') continue;
     const key = sha+':'+path;
     if (seen.has(key)) continue; seen.add(key);
     if (sensitivePath(path)) findings.push({location:path,rule:'sensitive-file',revision:rev});
     const bytes = git(['cat-file','blob',sha]);
     if (bytes.includes(0)) continue; // Binary artifacts need separate inspection.
     for (const hit of inspect(bytes.toString('utf8'))) findings.push({location:path,revision:rev,...hit});
   }
 }
 for (const rev of revisions)
   for (const hit of inspect(git(['show','-s','--format=%B',rev]).toString()))
     findings.push({location:'commit-message',revision:rev,...hit});
 return {findings, objects:seen.size, commits:revisions.length};
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
 try {
   const i=process.argv.indexOf('--since');
   if (i>=0 && !process.argv[i+1]) throw new Error('--since requires a SHA');
   const result=scan({since:i>=0?process.argv[i+1]:undefined,all:process.argv.includes('--all')});
   // Never print matched values, source lines, or full URLs.
   for (const f of result.findings) console.log(JSON.stringify(f));
   console.log(JSON.stringify({objects:result.objects,commits:result.commits,findings:result.findings.length}));
   process.exitCode=result.findings.length?1:0;
 } catch { console.error('Security scan could not complete; inspect repository access and revision arguments.'); process.exitCode=2; }
}
