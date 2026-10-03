import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../public/index.html',import.meta.url),'utf8');
const script=html.slice(html.indexOf('let audioStarting=false;'),html.indexOf('$("stop").onclick='))+
 html.slice(html.indexOf('$("stop").onclick='),html.indexOf('\n',html.indexOf('$("stop").onclick=')));
function setup({unsupported=false,ctorFail=false,startFail=false}={}){
 const elements={mic:{},stop:{}};let stopped=0,asked=0,uploaded=0,instance;
 class Recorder{
  static isTypeSupported(){return !unsupported}
  constructor(){if(ctorFail)throw Error('constructor failed');instance=this;this.state='inactive'}
  start(){if(startFail)throw Error('start failed');this.state='recording'}
  stop(){this.state='inactive';this.onstop?.()}
 }
 const context={recorder:null,$:id=>elements[id],status:()=>{},File,
  navigator:{mediaDevices:{getUserMedia:async()=>{asked++;return {getTracks:()=>[{stop:()=>stopped++}]}}}},
  window:{MediaRecorder:Recorder},MediaRecorder:Recorder,upload:()=>uploaded++,setTimeout:()=>1,clearTimeout:()=>{}};
 vm.runInNewContext(script,context);
 return {elements,context,get stopped(){return stopped},get asked(){return asked},get uploaded(){return uploaded},get instance(){return instance}};
}
test('unsupported codec never opens microphone',async()=>{
 const f=setup({unsupported:true});await f.elements.mic.onclick();assert.equal(f.asked,0);assert.equal(f.uploaded,0);assert.equal(f.elements.mic.disabled,false);
});
test('constructor and start failure both release every microphone track',async()=>{
 for(const options of [{ctorFail:true},{startFail:true}]){const f=setup(options);await f.elements.mic.onclick();assert.equal(f.stopped,1);assert.equal(f.uploaded,0);assert.equal(f.elements.mic.disabled,false)}
});
test('concurrent clicks request only one audio stream and stopped audio uploads once',async()=>{
 const f=setup();await Promise.all([f.elements.mic.onclick(),f.elements.mic.onclick()]);assert.equal(f.asked,1);
 f.instance.ondataavailable({data:new Blob(['synthetic'])});f.elements.stop.onclick();f.elements.stop.onclick();assert.equal(f.uploaded,1);assert.equal(f.stopped,1);
});
test('recording error and oversized audio never upload partial private bytes',async()=>{
 for(const mode of ['error','oversize']){const f=setup();await f.elements.mic.onclick();
  if(mode==='error')f.instance.onerror();else f.instance.ondataavailable({data:{size:8*1024*1024+1}});
  assert.equal(f.uploaded,0);assert.ok(f.stopped>=1);assert.equal(f.elements.stop.disabled,true)}
});
