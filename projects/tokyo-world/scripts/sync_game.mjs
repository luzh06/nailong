// 把游戏层源码同步到完整运行包（output/tokyo-three/web），并删除过期的 .gz 旁路文件。
// 用法：node projects/tokyo-world/scripts/sync_game.mjs [运行包web目录]
import {cpSync,existsSync,rmSync,readdirSync,statSync,mkdirSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const src=join(dirname(fileURLToPath(import.meta.url)),'..','web');
const dst=process.argv[2]||'D:/project/chatgpt/ci/output/tokyo-three/web';
const items=['world.js','index.html','game','models/characters','vendor/SkeletonUtils.js'];
function walk(p,out=[]){if(statSync(p).isDirectory())for(const f of readdirSync(p))walk(join(p,f),out);else out.push(p);return out;}
let n=0;
for(const it of items){const s=join(src,it);if(!existsSync(s))continue;
 for(const f of walk(s)){const rel=f.slice(src.length+1),d=join(dst,rel);mkdirSync(dirname(d),{recursive:true});cpSync(f,d);if(existsSync(d+'.gz'))rmSync(d+'.gz');n++;}}
console.log(`synced ${n} files -> ${dst}`);
