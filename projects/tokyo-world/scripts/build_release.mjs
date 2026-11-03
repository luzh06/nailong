// 生成可分发的《此间》体验包：从完整运行包复制网页与资源（去掉服务器专用的 .gz 旁路文件和开发文档），
// 加入免安装启动器与说明，并打成 zip。
// 用法：node projects/tokyo-world/scripts/build_release.mjs [运行包目录] [输出目录]
import {cpSync,existsSync,mkdirSync,readFileSync,writeFileSync,readdirSync,statSync,rmSync} from 'node:fs';
import {join,dirname,relative,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const here=dirname(fileURLToPath(import.meta.url));
const args=process.argv.slice(2).filter(a=>!a.startsWith('--'));
const runtime=args[0]||'D:/project/chatgpt/ci/output/tokyo-three';
const outRoot=args[1]||'D:/project/chatgpt/ci/output/cijian-release';
const NAME='此间_三日归途';
const dest=join(outRoot,NAME);
const KEEP_DIRS=['web','assets','bake','licenses'];
const SKIP=f=>f.endsWith('.gz');

if(existsSync(dest))rmSync(dest,{recursive:true});
mkdirSync(dest,{recursive:true});
let files=0,bytes=0;
function copyTree(src,dst){for(const name of readdirSync(src)){const s=join(src,name),d=join(dst,name);
 if(statSync(s).isDirectory()){mkdirSync(d,{recursive:true});copyTree(s,d);continue;}
 if(SKIP(name))continue;cpSync(s,d);files++;bytes+=statSync(s).size;}}
for(const dir of KEEP_DIRS){mkdirSync(join(dest,dir),{recursive:true});copyTree(join(runtime,dir),join(dest,dir));}
cpSync(join(runtime,'index.html'),join(dest,'index.html'));

// 启动器：PowerShell 5.1 需要带 BOM 的 UTF-8；批处理用 CRLF
const rel=join(here,'..','release');
const text=f=>readFileSync(join(rel,f),'utf8').replace(/\r?\n/g,'\r\n');
writeFileSync(join(dest,'serve.ps1'),'\ufeff'+text('serve.ps1'));
writeFileSync(join(dest,'开始体验.cmd'),text('开始体验.cmd'));
writeFileSync(join(dest,'README_请先读我.txt'),'\ufeff'+text('README_请先读我.txt'));

// GitHub Pages：关闭 Jekyll 处理，原样发布所有文件
writeFileSync(join(dest,'.nojekyll'),'');

// 自检：入口与游戏层文件都在
for(const need of ['web/index.html','web/world.js','web/game/main.mjs','web/models/characters/rin.glb','web/data/bk.glb'])
 if(!existsSync(join(dest,need)))throw new Error('缺少 '+need);
console.log(`release: ${files} files, ${(bytes/1048576).toFixed(1)} MB -> ${dest}`);

if(!process.argv.includes('--no-zip')){
 const zip=join(outRoot,NAME+'.zip');if(existsSync(zip))rmSync(zip);
 // Windows 自带 tar（bsdtar）可写 zip，文件名为 UTF-8
 execFileSync('C:/Windows/System32/tar.exe',['-a','-c','-f',zip,'-C',outRoot,NAME],{stdio:'inherit'});
 console.log(`zip: ${(statSync(zip).size/1048576).toFixed(1)} MB -> ${zip}`);
}
