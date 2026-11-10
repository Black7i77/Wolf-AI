"""Parse generated Python for syntax only. Never execute model output."""
import ast
import re

def check_python(text):
    results=[];fence=None;language='';code=[];index=-1
    def finish(closed):
        if language not in ('python','py','python3'):return
        item={'block':index,'valid':False,'message':'Python block is incomplete; not executed.'}
        if closed:
            try:
                ast.parse(''.join(code))
                item.update(valid=True,message='Python syntax checked; not executed. Dependencies and behaviour still need testing.')
            except (SyntaxError,ValueError) as exc:
                item.update(message='Python syntax issue: '+str(exc),line=getattr(exc,'lineno',None))
        results.append(item)
    for line in text.splitlines(keepends=True):
        if fence is None:
            m=re.match(r'^ {0,3}(`{3,}|~{3,})([^\n]*)\n?$',line)
            if m:
                fence=m[1];info=m[2].strip().split();language=info[0].lower() if info else 'text';code=[];index+=1
        elif len(line.strip())>=len(fence) and set(line.strip())=={fence[0]}:
            finish(True);fence=None
        else:code.append(line)
    if fence is not None:finish(False)
    return results
