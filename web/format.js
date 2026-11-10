(function(root){
'use strict';
function tokenize(text){
 const lines=String(text).match(/[^\n]*\n|[^\n]+$/g)||[];
 const parts=[];let prose='',code='',fence=null,language='';
 for(const line of lines){
  if(!fence){
   const match=line.match(/^ {0,3}(`{3,}|~{3,})([^\n]*)\n?$/);
   if(match){if(prose){parts.push({type:'text',text:prose});prose='';}fence=match[1];language=match[2].trim().split(/\s+/)[0].toLowerCase().replace(/[^a-z0-9_+#.-]/g,'')||'text';code='';}
   else prose+=line;
  }else{
   const trimmed=line.trim();
   if(trimmed.length>=fence.length && [...trimmed].every(c=>c===fence[0])){parts.push({type:'code',text:code,language,closed:true});fence=null;code='';}
   else code+=line;
  }
 }
 if(fence)parts.push({type:'code',text:code,language,closed:false});
 if(prose)parts.push({type:'text',text:prose});
 return parts;
}
function inline(parent,text){
 const regex=/(\*\*([^*\n]+)\*\*|`([^`\n]+)`)/g;let last=0;let match;
 while((match=regex.exec(text))){parent.append(document.createTextNode(text.slice(last,match.index)));const el=document.createElement(match[2]?'strong':'code');el.textContent=match[2]||match[3];parent.append(el);last=regex.lastIndex;}
 parent.append(document.createTextNode(text.slice(last)));
}
function render(text){
 const out=document.createElement('div');out.className='formatted-reply';
 for(const part of tokenize(text)){
  if(part.type==='text'){const p=document.createElement('p');inline(p,part.text);out.append(p);continue;}
  const block=document.createElement('div');block.className='code-block';
  const bar=document.createElement('div');bar.className='code-toolbar';
  const language=document.createElement('span');language.textContent=part.language+(part.closed?'':' · incomplete block');
  const copy=document.createElement('button');copy.type='button';copy.textContent='Copy code';copy.setAttribute('aria-label','Copy '+part.language+' code');
  const pre=document.createElement('pre');const code=document.createElement('code');code.textContent=part.text;pre.append(code);
  copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(part.text);copy.textContent='Copied';setTimeout(()=>copy.textContent='Copy code',1800);}catch{const range=document.createRange();range.selectNodeContents(code);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);copy.textContent='Selected · press Ctrl+C';}});
  bar.append(language,copy);block.append(bar,pre);out.append(block);
 }
 return out;
}
const api={tokenize,render};if(typeof module==='object')module.exports=api;else root.WolfFormat=api;
})(typeof window==='object'?window:globalThis);
