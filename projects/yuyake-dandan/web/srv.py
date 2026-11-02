# 本地测试服务：只绑 127.0.0.1，POST /result 把结果写进文件
import http.server,sys,os,time
root,port=sys.argv[1],int(sys.argv[2])
os.chdir(root)
class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(s):
        n=int(s.headers.get('Content-Length',0)); b=s.rfile.read(n)
        q=s.path.split('?')[-1] if '?' in s.path else 'out'
        if s.path.startswith('/shot'):
            import base64
            open(os.path.join(root,'web','results',q+'.jpg'),'wb').write(base64.b64decode(b.split(b',',1)[1]))
        else:
            with open(os.path.join(root,'web','results',q+'.json'),'ab') as f: f.write(b+b'\n')
        s.send_response(200); s.end_headers()
    def log_message(s,*a): pass
os.makedirs('web/results',exist_ok=True)
http.server.ThreadingHTTPServer(('127.0.0.1',port),H).serve_forever()
