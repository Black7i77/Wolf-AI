const assert=require('node:assert/strict');
const {tokenize}=require('./web/format.js');
const code='import tkinter as tk\n\nclass App:\n    def run(self):\n        print("hello")\n';
const parts=tokenize('Example:\n```python\n'+code+'```\nDone.');
assert.equal(parts.filter(p=>p.type==='code').length,1);
assert.equal(parts.find(p=>p.type==='code').text,code);
assert.equal(parts.find(p=>p.type==='code').language,'python');
const html=tokenize('```html\n<script>alert(1)</script>\n```');
assert.equal(html[0].text,'<script>alert(1)</script>\n');
assert.equal(tokenize('```python\nprint(1)')[0].closed,false);
assert.equal(tokenize('~~~python\nx=1\n~~~')[0].language,'python');
assert.equal(tokenize('hello')[0].text,'hello');
assert.equal(tokenize('````python\n```\n````')[0].text,'```\n');
console.log('Code formatting: 8 assertions passed');
class Element {
 constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.events={};}
 append(...children){this.children.push(...children);}
 setAttribute(){}
 addEventListener(name,fn){this.events[name]=fn;}
 set innerHTML(value){throw new Error('Unsafe HTML injection');}
}
global.document={createElement:tag=>new Element(tag),createTextNode:text=>new Element('#text',text)};
const {render}=require('./web/format.js');
const rendered=render('**Hello** <script>alert(1)</script>\n```python\n'+code+'```');
function nodes(root){return [root,...root.children.flatMap(nodes)];}
const all=nodes(rendered);
assert.equal(all.some(n=>n.tag==='script'),false);
assert.equal(all.find(n=>n.tag==='pre').children[0].textContent,code);
assert.equal(all.find(n=>n.tag==='button').textContent,'Copy code');
console.log('Safe rendering: 3 assertions passed');
