import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {WalkWorld} from '../web/collision.mjs';
const root=new URL('../web/',import.meta.url);
const nav=JSON.parse(fs.readFileSync(new URL('navigation.json',root)));
const bin=fs.readFileSync(new URL('collision.bin',root));
const start=performance.now();
const world=new WalkWorld(nav,new Float32Array(bin.buffer,bin.byteOffset,bin.byteLength/4));
console.log(JSON.stringify({collisionBuildMs:performance.now()-start,rssMB:process.memoryUsage().rss/1048576}));
test('delivered district collision builds in less than 2 seconds',()=>assert.ok(performance.now()-start<2000));
test('parking and temple have physical ground at the former 30 cm seam',()=>{
 assert.ok(world.ground(42,-9.5)>.9,'the buried generic background plane cannot bridge the visible gap');
});
test('the visible baked junction road is used instead of the buried background plane',()=>{
 assert.ok(world.ground(0,-25.5)>-.1);
});
test('the cleared former house has no hidden siding collision',()=>{
 const p=world.findSpawn(-2.8,-24.5,.1);assert.ok(p);
 const next=world.move(p,-.8,0);assert.ok(next.x<-3.5,JSON.stringify(next));
});
test('the restored retained corner remains a visible solid building',()=>{
 const p=world.findSpawn(-2.5,-20.5,.1);assert.ok(p);
 const next=world.move(p,-1.5,0);assert.ok(next.x>-3.1,JSON.stringify(next));
});
test('the real 36-step staircase is traversable in both directions',()=>{
 for(const step of [.016,.025,.03,.045,.05,.055,.06]){
  let p=world.findSpawn(1,15);assert.ok(p);const count=Math.round(15/step);
  for(let i=0;i<count;i++)p=world.move(p,0,-step);
  assert.ok(p.y<.15,JSON.stringify({step,...p}));
  for(let i=0;i<count;i++)p=world.move(p,0,step);
  assert.ok(p.y>14.85,JSON.stringify({step,...p}));
 }
});
test('Kaminarimon central opening can be walked through and back',()=>{
 let p=world.findSpawn(41.5,-9.5);assert.ok(p);
 for(let i=0;i<210;i++)p=world.move(p,.05,0);
 assert.ok(p.x>51.5,JSON.stringify(p));
 for(let i=0;i<210;i++)p=world.move(p,-.05,0);
 assert.ok(p.x<41.6,JSON.stringify(p));
});
test('Hozomon central opening can be walked through and back',()=>{
 let p=world.findSpawn(68.5,-9.5);assert.ok(p);
 for(let i=0;i<280;i++)p=world.move(p,.05,0);
 assert.ok(p.x>82,JSON.stringify(p));
 for(let i=0;i<280;i++)p=world.move(p,-.05,0);
 assert.ok(p.x<68.6,JSON.stringify(p));
});
