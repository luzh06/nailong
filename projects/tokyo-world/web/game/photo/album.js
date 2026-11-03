// 相册和回忆卡界面。正式版的书签菜单可以直接调用 open() / buildCard()。
import { framePhoto, composeMemoryCard, canvasToBlob, downloadBlob, blobToImage } from './card.js';
import { CAMERA_STYLES } from './styles.js';
import { ALBUM_LIMIT } from './store.js';

export class Album {
  constructor(photo, container) {
    this.photo = photo;
    this.isOpen = false;
    this.selected = new Set();
    this.urls = [];
    this.cardInfo = () => ({});

    const root = document.createElement('div');
    root.className = 'album';
    root.innerHTML = `
      <div class="album-sheet">
        <header>
          <h2>相册</h2>
          <span class="album-note"></span>
          <button data-act="close">合上</button>
        </header>
        <div class="album-grid"></div>
        <footer>
          <span class="album-sel">选 1—3 张放进回忆卡</span>
          <button data-act="card" disabled>生成回忆卡</button>
        </footer>
      </div>
      <div class="card-view">
        <img alt="回忆卡">
        <div class="card-actions">
          <button data-act="card-download">下载回忆卡</button>
          <button data-act="card-back">返回相册</button>
        </div>
      </div>`;
    container.appendChild(root);
    this.root = root;
    this.grid = root.querySelector('.album-grid');
    this.note = root.querySelector('.album-note');
    this.cardBtn = root.querySelector('[data-act="card"]');
    this.selLabel = root.querySelector('.album-sel');
    this.cardImg = root.querySelector('.card-view img');

    root.addEventListener('click', (e) => {
      const act = e.target.closest('[data-act]')?.dataset.act;
      if (act === 'close') this.close();
      else if (act === 'card') this.buildCard();
      else if (act === 'card-back') root.classList.remove('show-card');
      else if (act === 'card-download' && this.cardBlob) downloadBlob(this.cardBlob, `此间_回忆卡_${stamp()}.png`);
    });

    // 拍完之后屏幕角落弹出的显影小照片
    this.toast = document.createElement('div');
    this.toast.className = 'develop-toast';
    container.appendChild(this.toast);
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  async open() {
    this.isOpen = true;
    this.root.classList.add('on');
    this.root.classList.remove('show-card');
    await this.refresh();
  }

  close() {
    this.isOpen = false;
    this.root.classList.remove('on');
    this._revoke();
  }

  _revoke() {
    this.urls.forEach((u) => URL.revokeObjectURL(u));
    this.urls = [];
  }

  async refresh() {
    this._revoke();
    const rows = await this.photo.store.list();
    this.rows = rows;
    const store = this.photo.store;
    this.note.textContent = store.persistent
      ? `${rows.length} / ${ALBUM_LIMIT} 张${rows.length > ALBUM_LIMIT ? '，已超过上限，请删掉几张' : ''}`
      : `这个浏览器不能保存照片，刷新后会丢失，请及时下载（${rows.length} 张）`;
    this.grid.innerHTML = '';
    if (!rows.length) {
      this.grid.innerHTML = '<p class="album-empty">还没有照片。按 C 拿起相机，拍下这里吧。</p>';
    }
    for (const r of rows) {
      const url = URL.createObjectURL(r.blob);
      this.urls.push(url);
      const cell = document.createElement('figure');
      cell.className = `album-item style-${r.meta.cameraStyle}`;
      if (this.selected.has(r.id)) cell.classList.add('sel');
      cell.innerHTML = `
        <img src="${url}" alt="">
        <figcaption>${CAMERA_STYLES[r.meta.cameraStyle]?.name ?? ''} · ${r.meta.camera.focalMm}mm</figcaption>
        <div class="album-item-actions">
          <button data-a="pick">选入</button>
          <button data-a="dl">下载</button>
          <button data-a="del">删除</button>
        </div>`;
      cell.addEventListener('click', async (e) => {
        const a = e.target.closest('[data-a]')?.dataset.a;
        if (a === 'dl') await this.downloadPhoto(r);
        else if (a === 'del') {
          await this.photo.store.remove(r.id);
          this.selected.delete(r.id);
          await this.refresh();
        } else if (a === 'pick') {
          if (this.selected.has(r.id)) this.selected.delete(r.id);
          else if (this.selected.size < 3) this.selected.add(r.id);
          cell.classList.toggle('sel', this.selected.has(r.id));
          this._updateSel();
        }
      });
      this.grid.appendChild(cell);
    }
    // 删掉的照片不再算已选
    for (const id of [...this.selected]) if (!rows.find((r) => r.id === id)) this.selected.delete(id);
    this._updateSel();
  }

  _updateSel() {
    const n = this.selected.size;
    this.cardBtn.disabled = n === 0;
    this.selLabel.textContent = n ? `已选 ${n} 张（最多 3 张）` : '选 1—3 张放进回忆卡';
  }

  // 下载的是冲印好的照片（带相纸边）
  async downloadPhoto(r) {
    const img = await blobToImage(r.blob);
    const framed = framePhoto(img, r.meta.cameraStyle);
    img.close?.();
    const blob = await canvasToBlob(framed, 'image/jpeg', 0.94);
    downloadBlob(blob, `此间_${r.meta.createdOrder}_${stamp(new Date(r.meta.createdAt))}.jpg`);
  }

  async buildCard() {
    const picked = this.rows.filter((r) => this.selected.has(r.id));
    if (!picked.length) return;
    this.cardBtn.disabled = true;
    try {
      const canvas = await composeMemoryCard(picked, this.cardInfo(picked));
      this.cardBlob = await canvasToBlob(canvas, 'image/png');
      if (this.cardUrl) URL.revokeObjectURL(this.cardUrl);
      this.cardUrl = URL.createObjectURL(this.cardBlob);
      this.cardImg.src = this.cardUrl;
      this.root.classList.add('show-card');
      this.photo.dispatchEvent(new CustomEvent('card', { detail: { blob: this.cardBlob, photos: picked.map((p) => p.id) } }));
    } finally {
      this._updateSel();
    }
    return this.cardBlob;
  }

  // 拍完：照片从角落滑出，按相机风格显影。source 是刚拍好的 canvas
  showDevelop(source, styleId) {
    const k = Math.min(1, 640 / Math.max(source.width, source.height));
    const small = document.createElement('canvas');
    small.width = Math.round(source.width * k);
    small.height = Math.round(source.height * k);
    small.getContext('2d').drawImage(source, 0, 0, small.width, small.height);
    const el = framePhoto(small, styleId);
    el.className = `develop develop-${CAMERA_STYLES[styleId]?.develop ?? 'ink'}`;
    this.toast.replaceChildren(el);
    this.toast.classList.remove('show');
    void this.toast.offsetWidth;
    this.toast.classList.add('show');
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => this.toast.classList.remove('show'), 5200);
  }

  dispose() {
    this._revoke();
    this.root.remove();
    this.toast.remove();
  }
}

function stamp(d = new Date()) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}
