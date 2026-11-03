from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,quote
import argparse,json,os,subprocess,sys,time,urllib.request,webbrowser

PORT=8894
ROOT=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        self.send_header('Access-Control-Allow-Origin','*')
        super().end_headers()
    def do_GET(self):
        if urlsplit(self.path).path=='/__cijian_opening_health':
            data=json.dumps({'app':'cijian-opening','root':str(ROOT)},ensure_ascii=False).encode()
            self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        else:super().do_GET()

def healthy(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/__cijian_opening_health',timeout=.4) as r:data=json.load(r)
        return data.get('app')=='cijian-opening' and Path(data.get('root','')).resolve()==ROOT
    except Exception:return False

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--serve-only',action='store_true');parser.add_argument('--port',type=int,default=PORT);args=parser.parse_args()
    if args.serve_only:
        with ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT))) as server:server.serve_forever()
        return
    port=next((p for p in range(args.port,args.port+8) if healthy(p)),None)
    if port is None:
        import socket
        for candidate in range(args.port,args.port+8):
            try:
                with socket.socket() as probe:probe.bind(('127.0.0.1',candidate))
                port=candidate;break
            except OSError:continue
        if port is None:raise RuntimeError('本地预览端口已占用，请稍后重试。')
        flags=(subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP) if os.name=='nt' else 0
        subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--serve-only','--port',str(port)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
        for _ in range(60):
            if healthy(port):break
            time.sleep(.1)
        else:raise RuntimeError('启动失败，请重新双击“启动开头.bat”。')
    webbrowser.open(f'http://127.0.0.1:{port}/'+quote('开头.html'))

if __name__=='__main__':
    try:main()
    except Exception as e:print(e);input('按回车关闭。')
