import gzip
import importlib.util
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

spec=importlib.util.spec_from_file_location('tokyo_server',Path(__file__).resolve().parents[1]/'scripts/serve.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class CompressionTests(unittest.TestCase):
    def test_gzip_negotiation_and_stale_sidecars(self):
        self.assertTrue(hasattr(module,'ViewerHandler'),'static server does not negotiate compression')
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[4]/'tmp',prefix='tokyo-server-test-') as directory:
            p=Path(directory)/'world.mjs';raw=b'export const city="Tokyo";\n'*200;p.write_bytes(raw)
            sidecar=Path(str(p)+'.gz');sidecar.write_bytes(gzip.compress(raw))
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(module.ViewerHandler,directory=directory))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            url=f'http://127.0.0.1:{server.server_port}/world.mjs'
            try:
                with urlopen(Request(url,headers={'Accept-Encoding':'gzip'})) as r:
                    self.assertEqual(r.headers['Content-Encoding'],'gzip')
                    self.assertIn('javascript',r.headers['Content-Type'])
                    self.assertEqual(r.headers['Vary'],'Accept-Encoding')
                    self.assertEqual(gzip.decompress(r.read()),raw)
                    modified=r.headers['Last-Modified']
                with self.assertRaises(HTTPError) as unchanged:
                    urlopen(Request(url,headers={'Accept-Encoding':'gzip','If-Modified-Since':modified}))
                self.assertEqual(unchanged.exception.code,304)
                self.assertEqual(unchanged.exception.read(),b'')
                with urlopen(Request(url,headers={'Accept-Encoding':'gzip;q=0'})) as r:
                    self.assertIsNone(r.headers['Content-Encoding']);self.assertEqual(r.read(),raw)
                import os
                os.utime(p,(sidecar.stat().st_mtime+2,sidecar.stat().st_mtime+2))
                with urlopen(Request(url,headers={'Accept-Encoding':'gzip'})) as r:
                    self.assertIsNone(r.headers['Content-Encoding']);self.assertEqual(r.read(),raw)
            finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
