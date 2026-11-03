// 照片存储：IndexedDB 存图片 Blob 和元信息。
// 浏览器不允许时（隐私模式等）退回内存，照片仍能拍、能下载，只是刷新后会丢，界面要提示。

const DB_NAME = 'cijian-photos';
const STORE = 'photos';
export const ALBUM_LIMIT = 30;

function openDb() {
  return new Promise((resolve, reject) => {
    let req;
    try {
      req = indexedDB.open(DB_NAME, 1);
    } catch (e) {
      reject(e);
      return;
    }
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: 'id' });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function tx(db, mode, fn) {
  return new Promise((resolve, reject) => {
    const t = db.transaction(STORE, mode);
    const out = fn(t.objectStore(STORE));
    t.oncomplete = () => resolve(out && 'result' in out ? out.result : undefined);
    t.onerror = () => reject(t.error);
    t.onabort = () => reject(t.error);
  });
}

export class PhotoStore {
  constructor() {
    this.persistent = false;
    this.memory = new Map();
    this.ready = openDb()
      .then((db) => {
        this.db = db;
        this.persistent = true;
      })
      .catch(() => {
        this.persistent = false;
      });
  }

  async put(record) {
    await this.ready;
    if (!this.persistent) {
      this.memory.set(record.id, record);
      return;
    }
    try {
      await tx(this.db, 'readwrite', (s) => s.put(record));
    } catch (e) {
      // 空间不够等写入失败：这张照片留在内存里，不丢
      this.persistent = false;
      this.memory.set(record.id, record);
      throw e;
    }
  }

  async list() {
    await this.ready;
    let rows = [...this.memory.values()];
    if (this.db) {
      try {
        rows = rows.concat(await tx(this.db, 'readonly', (s) => s.getAll()));
      } catch {
        /* 读失败时只返回内存里的 */
      }
    }
    const seen = new Set();
    return rows
      .filter((r) => !seen.has(r.id) && seen.add(r.id))
      .sort((a, b) => a.meta.createdOrder - b.meta.createdOrder);
  }

  async remove(id) {
    await this.ready;
    this.memory.delete(id);
    if (this.db) await tx(this.db, 'readwrite', (s) => s.delete(id));
  }

  async count() {
    return (await this.list()).length;
  }
}
