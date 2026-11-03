import * as T from 'three';

// Screen-space RenderTexture: contents retain their world perspective inside the mask.
// The same inner scene can then blend to the full viewport, like MeshPortalMaterial.
export function makePortalMaterial(texture,resolution){
 return new T.ShaderMaterial({uniforms:{map:{value:texture},resolution:{value:resolution}},vertexShader:`void main(){gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,fragmentShader:`uniform sampler2D map;uniform vec2 resolution;void main(){gl_FragColor=texture2D(map,gl_FragCoord.xy/resolution);#include <tonemapping_fragment>\n#include <colorspace_fragment>}`.replace(';#include',';\n#include')});
}
export function makeComposite(world,resolution){
 const scene=new T.Scene(),camera=new T.OrthographicCamera(-1,1,1,-1,0,1);
 const material=new T.ShaderMaterial({depthTest:false,depthWrite:false,uniforms:{world:{value:world},inner:{value:world},resolution:{value:resolution},blend:{value:0}},vertexShader:`varying vec2 uvScreen;void main(){uvScreen=uv;gl_Position=vec4(position.xy,0.,1.);}`,fragmentShader:`
 varying vec2 uvScreen;uniform sampler2D world;uniform sampler2D inner;uniform vec2 resolution;uniform float blend;
 void main(){
   vec2 d=vec2(12.0)/resolution*blend;
   vec4 blurred=vec4(0.);
   for(int x=-2;x<=2;x++){for(int y=-2;y<=2;y++){blurred+=texture2D(world,clamp(uvScreen+vec2(float(x),float(y))*d,vec2(0.),vec2(1.)))/25.;}}
   vec4 inside=texture2D(inner,uvScreen);
   gl_FragColor=mix(blurred,inside,0.9*smoothstep(0.15,1.0,blend));
   gl_FragColor.a*=1.0-0.94*smoothstep(0.35,1.0,blend);
   #include <tonemapping_fragment>
   #include <colorspace_fragment>
 }`});
 scene.add(new T.Mesh(new T.PlaneGeometry(2,2),material));return{scene,camera,material};
}
