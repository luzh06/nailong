import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const url=new URL('../web/collision.mjs',import.meta.url);
test('walking uses solid collision geometry, rather than floor heights alone',()=>{
 assert.ok(fs.existsSync(url),'capsule collision controller is missing');
});
if(fs.existsSync(url)){
 const {WalkWorld}=await import(url.href);
 const nav={x0:-5,y0:-5,step:.25,nx:41,ny:41,heights:Array(41*41).fill(0)};
 const wall=(x,y0,y1,h=3)=>[x,0,-y0,x,h,-y0,x,h,-y1,x,0,-y0,x,h,-y1,x,0,-y1];
 test('a fast move cannot tunnel through a thin wall',()=>{
  const w=new WalkWorld(nav,new Float32Array(wall(0,-4,4)));
  const p=w.move({x:-2,y:0,height:0},4,0);
  assert.ok(p.x<=-.279,JSON.stringify(p));assert.ok(w.canStand(p.x,p.y));
 });
 test('diagonal movement slides along a wall without penetrating it',()=>{
  const w=new WalkWorld(nav,new Float32Array(wall(0,-4,4)));
  const p=w.move({x:-.35,y:-2,height:0},1,2);
  assert.ok(p.x<=-.279);assert.ok(p.y>-.2);assert.ok(w.canStand(p.x,p.y));
 });
 test('a real doorway remains passable while its wall stays solid',()=>{
  const w=new WalkWorld(nav,new Float32Array([...wall(0,-4,-.7),...wall(0,.7,4)]));
  assert.ok(w.move({x:-2,y:0,height:0},4,0).x>1.9);
  assert.ok(w.move({x:-2,y:2,height:0},4,0).x<-.279);
 });
 test('wall collision works from either side',()=>{
  const w=new WalkWorld(nav,new Float32Array(wall(0,-4,4)));
  assert.ok(w.move({x:2,y:0,height:0},-4,0).x>=.279);
 });
 test('missing ground and a tall ledge both stop movement',()=>{
  const n={...nav,heights:nav.heights.map((h,i)=>i%nav.nx>20?.7:h)};
  const w=new WalkWorld(n,new Float32Array());
  assert.ok(w.move({x:-2,y:0,height:0},4,0).x<.25);
  const v={...nav,heights:nav.heights.map((h,i)=>i%nav.nx>20?null:h)};
  assert.ok(new WalkWorld(v,new Float32Array()).move({x:-2,y:0,height:0},4,0).x<.25);
 });
 test('small stair risers can be climbed',()=>{
  const n={...nav,heights:nav.heights.map((h,i)=>Math.max(0,Math.floor((i%nav.nx)/2)-10)*.122)};
  const w=new WalkWorld(n,new Float32Array());
  assert.ok(w.move({x:-2,y:0,height:0},4,0).x>1.9);
 });
 test('spawn cannot stay embedded in a wall',()=>{
  const w=new WalkWorld(nav,new Float32Array(wall(0,-4,4)));
  const p=w.findSpawn(0,0);assert.ok(p);assert.ok(w.canStand(p.x,p.y));assert.ok(Math.abs(p.x)>=.279);
 });
 test('large coplanar geometry builds within a bounded memory budget',()=>{
  // The district contains large planar faces. An octree replicates these at
  // every subdivision; reversed duplicates made the real build exceed 4 GB.
  const t=performance.now();
  const triangles=new Float32Array(Array.from({length:200},()=>wall(0,-4,4)).flat());
  const w=new WalkWorld(nav,triangles);
  assert.ok(performance.now()-t<2000,'planar collision build exceeded 2 seconds');
  assert.ok(w.move({x:-2,y:0,height:0},4,0).x<-.279);
 });
 test('opposing contacts cannot cancel and make a narrow gap a valid spawn',()=>{
  const w=new WalkWorld(nav,new Float32Array([...wall(0,0,4),...wall(.4,0,4)]));
  assert.equal(w.canStand(.12,2),false);
  const p=w.findSpawn(.12,2);assert.ok(p);assert.ok(p.x<=-.279||p.x>=.679);
 });
}
