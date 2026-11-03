// 《此间》东京章节的剧情数据：角色、图鉴点、配对事件对白、终章旁白。
// 依据：东京悉尼_MVP主线与接入方案 v0.2（单玩家 + 三 NPC；东京只遇见情侣对象；悉尼海滩四人首次集合）。
// 台词为本轮可玩版本，DSH 可按 TASK_DSH_DIALOGUE.md 在本文件内润色，保持字段结构不变。
// 坐标为 Blender 坐标 (x 南, y 东)，与 world.js 的 me.x / me.y 一致。

export const ROLES = {
 rin:{id:'rin',name:'凛',latin:'RIN',from:'日本 · 京都',mark:'声音',height:1.6,partner:'linchuan',pairSpot:'TOKYO-02',camera:'instant',
  line:'想找到一个真正想去的地方。',card:'旅行笔记里记满了别人推荐的地方，却没有一处是自己想去的。'},
 linchuan:{id:'linchuan',name:'林川',latin:'LIN CHUAN',from:'中国 · 杭州',mark:'街巷',height:1.78,partner:'rin',pairSpot:'TOKYO-02',camera:'rangefinder',
  line:'在查一条不会走错的旅行路线。',card:'他把每段路都排进了时间表，唯独没给自己留出停下来的地方。'},
 camille:{id:'camille',name:'Camille',latin:'CAMILLE',from:'法国 · 巴黎',mark:'色彩',height:1.68,partner:'noah',pairSpot:'TOKYO-03',camera:'rangefinder',
  line:'在翻一本服装参考，找一种颜色。',card:'她替许多人挑过颜色，却总把自己留在画面之外。'},
 noah:{id:'noah',name:'Noah',latin:'NOAH',from:'澳大利亚 · 悉尼',mark:'海岸',height:1.84,partner:'camille',pairSpot:'TOKYO-03',camera:'instant',
  line:'借了一本旅行影集，想看看海之外的生活。',card:'朋友的合影都是他拍的，他自己却很少出现在照片里。'},
};
export const ROLE_ORDER=['rin','linchuan','camille','noah'];

// 图鉴点。view：玩家应站立的取景点；target：要拍进画面的目标（three 世界坐标在运行时换算）。
export const SPOTS = {
 'TOKYO-01':{id:'TOKYO-01',title:'街区初见',caption:'新的街道，等一次认真驻足。',
  hint:'站在夕阳台阶上，为整条街拍下第一张照片',view:{x:1.2,y:12.5},viewRadius:9,target:{x:0,y:-28,z:3.5},radius:4,minCoverage:.004},
 'TOKYO-02':{id:'TOKYO-02',title:'樱花树下',caption:'让花瓣替这一刻留白。',
  hint:'去雷门前的空地，把那棵樱花拍进书里',view:{x:30.5,y:-15},viewRadius:14,target:'sakura',minCoverage:.04},
 'TOKYO-03':{id:'TOKYO-03',title:'烟花之夜',caption:'天光落下，夜色盛开。',
  hint:'夜色降临——在宝蔵门前，抬头拍下门顶上空的烟花',view:{x:56,y:-9.5},viewRadius:16,target:'fireworks',minCoverage:.01},
};
export const SPOT_ORDER=['TOKYO-01','TOKYO-02','TOKYO-03'];

export const PLACES={
 spawn:{x:1.2,y:15.6,yaw:-Math.PI/2},
 sakura:{x:33.2,y:-17.6},
 sakuraNpc:{x:31.6,y:-16.2},
 fireworksNpc:{x:56,y:-6.6},
 fireworksCenter:{x:96,y:-9.5,z:56},
 courtTrigger:{x:56,y:-9.5,r:10},
 door:{x:66.5,y:-9.5},
};

export const PRESET_REGIONS=[
 {region:'杭州',latin:'HANGZHOU',note:'此前的旅程 · 已集齐',entries:[['HZ-01','西湖全景','湖光与城市，被收进同一页。'],['HZ-02','雷峰塔','拾级而上，把暖光留在塔檐。'],['HZ-03','拱宸桥','桥拱映水，水面留下来时的光。']]},
 {region:'巴黎',latin:'PARIS',note:'此前的旅程 · 已集齐',entries:[['PARIS-01','埃菲尔铁塔','抬头的瞬间，风也慢了下来。'],['PARIS-02','塞纳河畔','沿河走一会儿，把时间交给水。'],['PARIS-03','巴黎街角','在街角停留，收藏日常的温柔。']]},
];
export const SYDNEY_ENTRIES=[['SYDNEY-01','海边咖啡店','海风与咖啡，都是今天的开场。'],['SYDNEY-02','海岸步道','沿着海岸，把脚步放慢。'],['SYDNEY-03','海滩日落','把最后一束光，留给相逢。']];

export const OPENING_LINES=[
 '书里已经写满了两座城市：杭州的湖，巴黎的河。',
 '下一页是空白的，只印着一行小字——',
 '“三次日落之前，让你的旅行页显影。”',
 '翻到旅程的当前页：东京。',
];

// 配对事件。以「玩家角色」为键：npc 为对方，hub 的三组选项中 key:true 的那一组唯一推进。
// {who:'npc'|'me'|'narr', text}；选项 reply 为对方回应。
export const PAIR_EVENTS={
 rin:{npc:'linchuan',place:'樱花树下',
  intro:[
   {who:'narr',text:'樱花树下站着一个低头看地图的人。你举起相机时，他下意识侧过脸，往画面外让了一步。'},
   {who:'npc',text:'抱歉，挡到你了吧？这里的光线是最好的，你拍，我马上走。'},
  ],
  hub:'他已经把地图折好，准备离开。',
  options:[
   {label:'“这棵树，你也觉得好看吗？”',reply:[{who:'npc',text:'……好看。我本来只打算在这里停两分钟，结果站了快二十分钟。'},{who:'npc',text:'路线表上没有这一项，可它比表上的地方都好看。'}]},
   {label:'“你从哪里来？”',reply:[{who:'npc',text:'杭州。我习惯把每一段路都排进时间表，下一站在四点十分。'},{who:'me',text:'那现在是四点十二分。'},{who:'npc',text:'……那就算我迟到了。'}]},
   {label:'“别走——留下来，我们互相拍一张吧？”',key:true,reply:[{who:'npc',text:'我？我很少出现在照片里。'},{who:'me',text:'那这一次就当作例外。你站在花下面，我先拍你，然后换你拍我。'},{who:'npc',text:'……好。我把地图收起来。'}]},
  ],
  exchangeHint:'为林川拍一张照片：让他和樱花一起出现在取景框里',
  gift:'林川用你的相机，认真地为你拍了一张。',
  farewell:[
   {who:'npc',text:'谢谢你。我第一次没有看地图，只是看着一棵树。'},
   {who:'npc',text:'我还有书里最后一页要完成——等你拍完，给我看看你眼里的最后一张。'},
   {who:'narr',text:'他把那张照片的副本夹进自己的书里，向另一条小路走去。'},
  ]},
 linchuan:{npc:'rin',place:'樱花树下',
  intro:[
   {who:'narr',text:'樱花树下，一个女孩举着录音笔，安静地收着风吹花瓣的声音。你下意识让出取景的位置。'},
   {who:'npc',text:'啊——你也要拍这棵树吗？没关系，我只是在录声音，不占画面的。'},
  ],
  hub:'她低头看了看录音笔上跳动的波形。',
  options:[
   {label:'“你在录什么声音？”',reply:[{who:'npc',text:'花瓣落地的声音。很小，要屏住呼吸才听得见。'},{who:'npc',text:'我想找一个“真正想去的地方”，也许先从真正想听的声音开始。'}]},
   {label:'“你从哪里来？”',reply:[{who:'npc',text:'京都。可我好像一直在去别人推荐的地方。'},{who:'me',text:'我是照着路线表来的，表上没有这棵树。'},{who:'npc',text:'那它就是我们两个都没被推荐过的地方。'}]},
   {label:'“我们互相拍一张吧——你站进画面里。”',key:true,reply:[{who:'npc',text:'……可以吗？我总是把自己录在声音外面。'},{who:'me',text:'这次换我来记。你站在花下，我先拍你，然后你也拍我。'},{who:'npc',text:'嗯。那我主动一次——请你留下来，拍完再走。'}]},
  ],
  exchangeHint:'为凛拍一张照片：让她和樱花一起出现在取景框里',
  gift:'凛接过相机，为你拍下了站在花下的样子。',
  farewell:[
   {who:'npc',text:'这一张，我会和花瓣的声音放在同一页。'},
   {who:'npc',text:'等你拍完，给我看看你眼里的最后一张。'},
   {who:'narr',text:'她把照片的副本夹进书里，朝另一条小路走去，录音笔的红灯还亮着。'},
  ]},
 camille:{npc:'noah',place:'宝蔵门前',
  intro:[
   {who:'narr',text:'烟花升起前的人群边缘，一个高个子的人正举着相机，替每一个陌生人都留出了最好的位置。'},
   {who:'npc',text:'你一直在画面外面。想拍烟花的话，这里的角度更好——我让给你。'},
  ],
  hub:'他把相机挂回胸前，等着下一束烟花。',
  options:[
   {label:'“烟花你看过很多次吧？”',reply:[{who:'npc',text:'在悉尼看过很多次，每次都在取景框里看。'},{who:'npc',text:'这一次我想先用眼睛看一遍。'}]},
   {label:'“你拍的都是别人？”',reply:[{who:'npc',text:'朋友的合影都是我拍的。拍照的人，总是不在照片里。'},{who:'me',text:'我也是。我替别人挑颜色，自己却总穿着灰色。'}]},
   {label:'“那这次，我们互相拍对方吧。”',key:true,reply:[{who:'npc',text:'……你想留下一个什么样的自己？'},{who:'me',text:'站在烟花下面、没有躲开镜头的自己。也请你站进来一次。'},{who:'npc',text:'好。那就你先拍我，下一束烟花，换我拍你。'}]},
  ],
  exchangeHint:'为 Noah 拍一张照片：让他和烟花一起出现在取景框里',
  gift:'下一束烟花亮起时，Noah 为你按下了快门。',
  farewell:[
   {who:'npc',text:'这是我第一次，被别人认真地拍下来。'},
   {who:'npc',text:'照片要各自放进书里才算数。下次见面——这次还替我拍吗？'},
   {who:'narr',text:'烟花的余光里，他朝人群的另一边走去，回头挥了挥手。'},
  ]},
 noah:{npc:'camille',place:'宝蔵门前',
  intro:[
   {who:'narr',text:'人群边缘，一个围着丝巾的女孩举着相机等烟花。你注意到她每一张都把自己留在了画面之外。'},
   {who:'npc',text:'抱歉，我是不是挡住你的机位了？我拍完这一张就让开。'},
  ],
  hub:'她低头翻看着刚才拍下的几张。',
  options:[
   {label:'“你在找什么颜色？”',reply:[{who:'npc',text:'一种夜里也不会褪掉的颜色。我在巴黎替很多人找过，还没给自己找到。'}]},
   {label:'“你拍的都是风景？”',reply:[{who:'npc',text:'风景和别人。我习惯站在镜头后面。'},{who:'me',text:'我也是。拍照的人总是不在照片里。'}]},
   {label:'“站进画面里来吧——我们互相拍一张。”',key:true,reply:[{who:'npc',text:'……你想把我拍成什么样子？'},{who:'me',text:'你想留下的那个样子。然后，也请你拍我一次。'},{who:'npc',text:'好。那下一束烟花，轮到你站进来。'}]},
  ],
  exchangeHint:'为 Camille 拍一张照片：让她和烟花一起出现在取景框里',
  gift:'下一束烟花亮起时，Camille 为你按下了快门。',
  farewell:[
   {who:'npc',text:'这是我第一次，在照片里而不是在照片外。'},
   {who:'npc',text:'照片要各自放进书里才算数。下次见面——这次还替我拍吗？'},
   {who:'narr',text:'她把照片收进书页，朝人群的另一边走去。烟花的余光落在她的丝巾上。'},
  ]},
};

// 悉尼书页章节：插画 + 旁白；四人在海滩首次集合。
export function finaleScript(roleId){
 const r=ROLES[roleId],p=ROLES[r.partner];
 const others=['rin','linchuan','camille','noah'].filter(k=>k!==roleId&&k!==r.partner).map(k=>ROLES[k]);
 const reunion=(roleId==='rin'||roleId==='linchuan')
  ?(roleId==='rin'
   ?[{who:'me',text:'今天不用看地图了？'},{who:'npc',id:p.id,text:'这次，我先看见你了。'}]
   :[{who:'npc',id:p.id,text:'今天不用看地图了？'},{who:'me',text:'这次，我先看见你了。'}])
  :[{who:'npc',id:p.id,text:'这次还替我拍吗？'},{who:'me',text:'这次，我们一起在照片里。'}];
 return {
  pages:[
   {art:'SYDNEY-01',eyebrow:'DAY 2 · SYDNEY',title:'海边咖啡店',text:'书页门在身后合上，海风先到。悉尼的第一张，留给一杯咖啡和一扇朝海的窗。'},
   {art:'SYDNEY-02',eyebrow:'DAY 2 · COASTAL WALK',title:'海岸步道',text:`沿着海岸慢慢走。你翻出东京的那张照片——${p.name}站在${PAIR_EVENTS[roleId].place}，没有躲开镜头。书签上浮出一行字：“最后一页，在日落时完成。”`},
   {art:'SYDNEY-03',eyebrow:'DAY 3 · THE BEACH',title:'海滩日落',text:'沿着路标和书里的取景轮廓，你走到海边。浪声里，先传来一个熟悉的声音。'},
  ],
  reunion,
  intro:[
   {who:'narr',text:`${p.name}身后，还站着两个陌生人——${others[0].name}与${others[1].name}。他们也带着一本一模一样的书。`},
   {who:'npc',id:others[0].id,text:`我是${others[0].name}，来自${others[0].from.split(' · ')[1]}。${others[0].line}`},
   {who:'npc',id:others[1].id,text:`我是${others[1].name}，来自${others[1].from.split(' · ')[1]}。${others[1].line}`},
   {who:'narr',text:'四本书同时亮了起来。每个人的书里，都浮出了一块属于自己的拼图。'},
  ],
 };
}
