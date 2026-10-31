const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('main/apps/home/phone_setup.html','utf8');
const algorithm=html.slice(html.indexOf('function portraitLocalContrast('),html.indexOf('async function imageFile('));
const save=html.slice(html.indexOf('async function save(){'),html.indexOf("$('save').onclick="));
assert.match(html,/<legend>頭像顯示方式<\/legend>/);
assert.match(html,/id="portraitPresetFlat"[^>]*><span>單色/);
assert.ok(html.indexOf('id="portraitPresetFlat"')<html.indexOf('id="photoTools"'),'modes must be available without uploading a new photo');
const elements=new Map(),requests=[];
const $=id=>{if(!elements.has(id))elements.set(id,{value:'',checked:false,disabled:false,getContext(){return {createImageData:()=>({data:new Uint8ClampedArray(96*138*4)}),putImageData(){}}}});return elements.get(id)};
let stored=new Uint8Array(14280);stored.set([80,67,51,56,4,0,0,0]);
for(let i=1;i<256;i++)stored[8+i*4+3]=255;
stored.set([0,0,255,255],12);stored[1032]=1;
const original=new Uint8Array(stored);let readFailure=false,gate=null,failUpload=false;
const context=vm.createContext({$,PORTRAIT:{w:96,h:138},portrait:null,storedPortrait:null,portraitLoaded:false,portraitDirty:false,portraitPreset:4,portraitPreparedCache:null,portraitPalette:[0,1,2,255],portraitSubjectPalette:[30,90,170,255],window:{__T:42},AbortController,setTimeout,clearTimeout,TextEncoder,
 say(id,text){$(id).textContent=text},imageLoading:0,cardBusy:false,verified:false,hasSaved:true,cards:[],step(){},renderCards(){},pendingMuseConfig:()=>false,saveCards:async()=>{},bytes:s=>Buffer.byteLength(s||''),selectedCityProfile:()=>({city:'',region:'',radio_city:'',lat:'',lon:''}),
 fetch:async url=>{requests.push({method:'GET',url});if(gate)await gate;if(readFailure)throw Error('offline');return {ok:true,arrayBuffer:async()=>stored.slice().buffer}},
 api:async(path,body)=>{requests.push({method:'POST',path,body});if(path==='/api/avatar'){if(failUpload)throw Error('upload failed');stored=new Uint8Array(body)}return {ok:true}}
});
vm.runInContext(algorithm+'\n'+save,context);
(async()=>{
 await context.loadStoredPortrait(true);
 assert.equal(context.portraitPreset,4);assert.equal(context.portraitDirty,false);assert.equal($('portraitPresetColor').disabled,false);
 context.setPortraitPreset(2);assert.equal(requests.filter(r=>r.method==='POST').length,0,'switching only previews until save');
 await context.save();
 assert.equal(stored[5],1);assert.deepEqual(Array.from(stored.slice(8)),Array.from(original.slice(8)));
 assert.equal(context.portraitDirty,false);
 await context.loadStoredPortrait(true);assert.equal(context.portraitPreset,2);assert.equal($('portraitPresetFlat').checked,true);
 context.setPortraitPreset(4);await context.save();assert.deepEqual(Array.from(stored),Array.from(original));
 context.setPortraitPreset(2);failUpload=true;await context.save();assert.equal(context.portraitDirty,true,'failed save retains pending choice');assert.deepEqual(Array.from(stored),Array.from(original));
 failUpload=false;await context.save();assert.equal(stored[5],1);
 context.portraitDirty=false;readFailure=true;const writes=requests.filter(r=>r.path==='/api/avatar').length;
 await context.loadStoredPortrait(true);assert.equal($('portraitPresetColor').disabled,true);await context.save();
 assert.equal(requests.filter(r=>r.path==='/api/avatar').length,writes,'read failure must not replace an existing avatar');
 readFailure=false;stored=new Uint8Array(4976);stored.set([80,84,51,53,3,0,0,0]);await context.loadStoredPortrait(true);
 assert.equal(context.portraitPreset,2);assert.equal($('portraitPresetColor').disabled,true);
 context.setPortraitPreset(4);assert.equal(context.portraitPreset,2,'legacy monochrome cannot invent colors');
 context.portraitDirty=false;stored=original;let release;gate=new Promise(resolve=>{release=resolve});
 const pending=context.loadStoredPortrait(true);context.portrait={};context.portraitDirty=true;context.portraitPreset=2;release();await pending;gate=null;
 assert.equal(context.portraitPreset,2);assert.equal(context.storedPortrait,null,'late device response cannot replace a newly selected photo');
 console.log('Phone portrait modes: no-reupload save, persistent restore, original RGB preservation, upload/read failures and late-response protection PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
