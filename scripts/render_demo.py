import sys,pathlib,json,math,random,subprocess,wave,collections
pathlib.Path('work').mkdir(exist_ok=True)
pathlib.Path('outputs').mkdir(exist_ok=True)
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
O=pathlib.Path('outputs');W,H=1920,1080;FPS=30;DURATION=60
D=json.loads(pathlib.Path('data/data.json').read_text(encoding='utf-8'));N=D['nodes'];R=D['recipes']
C=['#000000','#60cbb2','#74c6ef','#8faaff','#b19aff','#ce93ec','#eda8bc','#ffce87']
def rgb(c):return tuple(bytes.fromhex(c.lstrip('#')))
def fade(c,a):return tuple(int(v*a+bg*(1-a)) for v,bg in zip(rgb(c),(10,18,28)))
font=lambda sz,b=False:ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if b else 'msyh.ttc'),sz)
F={s:font(s) for s in [16,19,22,24,28,32,36,44,56,72]};B={s:font(s,True) for s in [28,36,44,56,72]}
ids=[];positions=[];layers={};byout=collections.defaultdict(list)
for r in R:byout[r['output']].append(r)
def score(r):return max(min(N[i]['level'] for i in g['options']) for g in r['groups'])
for a in byout.values():a.sort(key=lambda r:(score(r),r['id']))
for l in range(1,8):
 a=sorted(i for i,n in N.items() if n['level']==l);rad=22+373*math.sqrt(len(a)/475);layers[l]=(rad,len(a))
 for j,i in enumerate(a):
  t=j*2.3999632297;r=math.sqrt((j+.5)/len(a))*(rad-16);ids.append(i);positions.append([math.cos(t)*r,(l-4)*260,math.sin(t)*r])
P=np.array(positions);idx={i:j for j,i in enumerate(ids)}
def path(item):
 active=set();edges=[];visited=set()
 def go(i):
  active.add(i)
  if i in visited or N[i]['root']:return
  visited.add(i)
  if not byout[i]:return
  r=byout[i][0]
  for g in r['groups']:
   v=min(g['options'],key=lambda j:(N[j]['level'],j));edges.append((v,i));go(v)
 go(item);return active,edges
paths={i:path(i) for i in ['carrot_on_a_stick','piston']}
def project(p,yaw,pitch,zoom=1,cy=0):
 p=np.asarray(p);x=p[...,0]*math.cos(yaw)-p[...,2]*math.sin(yaw);z=p[...,0]*math.sin(yaw)+p[...,2]*math.cos(yaw);y=(p[...,1]-cy)*math.cos(pitch)-z*math.sin(pitch);z=(p[...,1]-cy)*math.sin(pitch)+z*math.cos(pitch);s=.46*zoom*2600/(2600-z)
 return np.stack([760+x*s,510-y*s],axis=-1)
random.seed(34);bg=Image.new('RGB',(W,H),(10,18,28));dr=ImageDraw.Draw(bg)
for j in range(100):
 x=random.randrange(W);y=random.randrange(700);dr.rectangle((x,y,x+2,y+2),fill=(27,41,53))
for x in range(0,W,64):
 if 400<x<1250:continue
 y=800+random.randrange(4)*40;dr.rectangle((x,y,x+64,H),fill=(26,29,29));dr.rectangle((x,y,x+64,y+12),fill=(27,42,34))
for x,y in [(90,530),(300,650),(1750,490),(1550,640)]:
 dr.rectangle((x,y,x+28,1030),fill=(29,30,29));dr.rectangle((x-90,y-90,x+110,y+30),fill=(16,35,30));dr.rectangle((x-120,y,x+145,y+80),fill=(15,32,29))
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def text(draw,xy,s,size=24,color='#dce9f6',bold=False):draw.text(xy,s,font=(B if bold else F)[size],fill=color)
def line(draw,arr,col,width):draw.line([tuple(x) for x in arr],fill=col,width=width,joint='curve')
def tree(draw,yaw,pitch,zoom,cy,alpha):
 def branch(arr,width):line(draw,project(arr,yaw,pitch,zoom,cy),fade('#82684d',alpha),width)
 branch([[0,-860,0],[0,850,0]],max(2,int(12*zoom)))
 branch([[-8,-860,4],[-4,850,4]],max(1,int(2*zoom)))
 for l in range(1,7):
  y=(l-4)*260;rad=layers[l][0]*.65
  for j in range(3):
   t=j*2.094+l*.72;branch([[0,y-95,0],[math.cos(t)*rad*.45,y-40,math.sin(t)*rad*.45],[math.cos(t)*rad,y-8,math.sin(t)*rad]],max(1,int((6-l*.6)*zoom)))
 for j in range(9):
  a=j*math.pi*2/9;r=140+j%3*35;branch([[0,-800,0],[math.cos(a)*50,-867,math.sin(a)*50],[math.cos(a+.12)*r,-905,math.sin(a+.12)*r],[math.cos(a+.18)*(r+45),-925,math.sin(a+.18)*(r+45)]],max(2,int(5*zoom)))
cues=[(0,5,'如果把 Minecraft 的合成配方，种成一棵树？'),(5,10,'1,491 个物品与药水状态，分布在七个层级。'),(10,15,'从底部的边界原料，到高层的合成产物。'),(15,20,'选择“胡萝卜钓竿”，它的前置路径才会出现。'),(20,25,'钓鱼竿和胡萝卜，共同汇入最终产物。'),(25,29,'沿着钓鱼竿，还能继续追溯木棍和线。'),(29,34,'再看活塞：木板、圆石、铁锭和红石粉。'),(34,39,'多种输入必须齐备，每条连线直接落在物品中心。'),(39,44,'连线跟随来源层配色，光点沿合成方向流动。'),(44,50,'隐藏无关节点，专注当前这条合成路径。'),(50,55,'主干、分枝与树根，让配方结构长成一棵树。'),(55,60,'物品合成树：搜索一个物品，看见它的来路。')]
def frame(t):
 im=bg.copy();draw=ImageDraw.Draw(im)
 item='carrot_on_a_stick' if 15<=t<29 else 'piston' if 29<=t<50 else None
 only=44<=t<50
 active,edges=paths[item] if item else (set(),[])
 yaw=.42+t*.035;pitch=.30+.07*math.sin(t*.17);zoom=.88;cy=0
 if item:
  yaw=.45+(.12*math.sin(t*.22));zoom=1.65;cy=-430
 if t>=50:yaw=.42+(t-50)*.08
 coords=project(P,yaw,pitch,zoom,cy);tree(draw,yaw,pitch,zoom,cy,.24 if item else .62)
 for l,(rad,count) in layers.items():
  a=np.linspace(0,2*math.pi,90);ring=np.stack([rad*np.cos(a),np.full_like(a,(l-4)*260),rad*np.sin(a)],axis=-1);line(draw,project(ring,yaw,pitch,zoom,cy),fade(C[l],.16),1)
  p=project([-rad-45,(l-4)*260,0],yaw,pitch,zoom,cy)
  if 150<p[1]<930:text(draw,(p[0]-110,p[1]-12),f'L{l} · {count} 项',19,C[l])
 for j,(a,b) in enumerate(edges):
  p,q=coords[idx[a]],coords[idx[b]];col=C[N[a]['level']];line(draw,[p,q],fade(col,.85),2)
  for k in range(2):
   u=(t*.6+k*.5)%1;c=p+(q-p)*u;draw.ellipse((c[0]-4,c[1]-4,c[0]+4,c[1]+4),fill=col)
 for j,i in enumerate(ids):
  if only and i not in active:continue
  x,y=coords[j]
  if not(90<x<1330 and 145<y<950):continue
  on=i in active;sz=5 if on else 2.5;col=fade(C[N[i]['level']],1 if on or not item else .10);draw.ellipse((x-sz,y-sz,x+sz,y+sz),fill=col)
 # Non-overlapping labels with leaders preserve exact node endpoints.
 used=[]
 for i in sorted(active,key=lambda i:coords[idx[i]][1]):
  x,y=coords[idx[i]];label=N[i]['name'];tw=draw.textbbox((0,0),label,font=F[24])[2]
  tx=x+15;ty=y-32
  for _ in range(30):
   box=(tx-4,ty-2,tx+tw+8,ty+32)
   if all(box[2]<a or box[0]>c or box[3]<b or box[1]>d for a,b,c,d in used):break
   ty-=34
  used.append(box);draw.rounded_rectangle(box,radius=5,fill=(11,23,34));line(draw,[[x,y],[tx,ty+18]],fade(C[N[i]['level']],.6),1);text(draw,(tx,ty),label,24)
  if i==item:draw.ellipse((x-11,y-11,x+11,y+11),outline='#ffffff',width=2)
 # Clean demo framing, not a claimed browser screen recording.
 draw.rectangle((0,0,W,138),fill=(10,18,28));text(draw,(64,30),'MINECRAFT  /  JAVA 26.3',19,'#83cbb8');text(draw,(62,63),'物品合成树',44,bold=True)
 text(draw,(1000,73),'3D 配方可视化 · 演示动画',22,'#8c9faf')
 draw.rounded_rectangle((1370,175,1856,880),radius=22,fill=(17,30,45),outline=(42,61,78),width=2)
 if item:
  text(draw,(1400,205),'当前选择',19,'#8caaad');text(draw,(1400,247),N[item]['name'],36,bold=True);text(draw,(1400,308),f'第 {N[item]["level"]} 层  ·  '+('仅显示当前路径' if only else '前置合成路径'),22,'#85d5be')
  r=byout[item][0];text(draw,(1400,365),'以下输入全部需要',24)
  yy=420
  for g in r['groups']:
   v=min(g['options'],key=lambda j:(N[j]['level'],j));draw.rounded_rectangle((1396,yy-7,1828,yy+50),radius=8,fill=(26,43,59));text(draw,(1414,yy),f'{g["count"]} × {N[v]["name"]}',24);yy+=80
  text(draw,(1400,775),'替代配方与材料可在网页中切换',19,'#9cb1c3');text(draw,(1400,815),'连线：材料 → 产物',22,'#9cb1c3')
 else:
  text(draw,(1400,220),'让配方长成一棵树',28,bold=True)
  for yy,big,small in [(320,'7 层','从边界原料到合成产物'),(470,'1,491 个节点','含独立药水状态'),(620,'选中才连线','清晰追溯当前合成路径')]:text(draw,(1400,yy),big,36,'#a8e1c7',True);text(draw,(1400,yy+58),small,22,'#a6bbcc')
  text(draw,(1400,795),'支持旋转、缩放与中文搜索',22,'#a6bbcc')
 draw.rectangle((0,970,W,H),fill=(6,12,20));caption=next((s for a,b,s in cues if a<=t<b),'');box=draw.textbbox((0,0),caption,font=F[32]);text(draw,((W-box[2])/2,988),caption,32)
 text(draw,(64,1043),'第 1 层含配方范围外取得的材料；层级不代表游戏进度。',16,'#8093a6');text(draw,(1630,1043),f'{int(t):02d} / 60',16,'#8093a6')
 draw.rectangle((0,1076,int(W*t/60),1079),fill='#77d8b5')
 return im
def music():
 sr=44100;a=np.zeros(sr*60,dtype=np.float32);chords=[[130.81,164.81,196],[110,130.81,164.81],[87.31,110,130.81],[98,123.47,146.83]]
 for beat in range(120):
  start=int(beat*.5*sr);duration=1.8;tt=np.arange(int(duration*sr))/sr;freq=chords[(beat//8)%4][beat%3]*2
  tone=(np.sin(2*np.pi*freq*tt)+.25*np.sin(2*np.pi*freq*2*tt))*np.exp(-tt*3)*np.minimum(tt/.018,1)*.045
  count=min(len(tone),len(a)-start);a[start:start+count]+=tone[:count]
 for bar in range(15):
  start=int(bar*4*sr);tt=np.arange(sr*4)/sr;env=np.sin(np.pi*tt/4)**2
  for freq in chords[bar%4]:a[start:start+len(tt)]+=.012*np.sin(2*np.pi*freq*tt)*env
 a*=np.minimum(np.arange(len(a))/sr/2,1)*np.minimum((len(a)-np.arange(len(a)))/sr/3,1)
 with wave.open('work/demo-music.wav','wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((a*32767).astype('<i2').tobytes())
def timestamp(t):return f'00:{int(t)//60:02d}:{int(t)%60:02d},000'
def cover():
 im=frame(3);d=ImageDraw.Draw(im)
 d.rectangle((0,0,W,138),fill=(10,18,28))
 text(d,(62,34),'把 Minecraft 合成表，种成一棵树',56,bold=True)
 d.rounded_rectangle((1370,175,1856,880),radius=22,fill=(17,30,45),outline=(42,61,78),width=2)
 text(d,(1410,260),'物品合成树',56,bold=True)
 for y,a,b in [(390,'7 层结构','从材料到产物'),(540,'1,491 节点','一眼看清依赖'),(690,'动态路径','选中物品即展开')]:
  text(d,(1410,y),a,36,'#a8e1c7',True);text(d,(1410,y+57),b,28,'#a6bbcc')
 d.rectangle((0,970,W,H),fill=(6,12,20));text(d,(64,990),'MINECRAFT JAVA 26.3  ·  3D 配方可视化',36,'#83cbb8',True)
 return im
if __name__=='__main__':
 for t in [3,22,36,47,54]:frame(t).save(f'work/video-preview-{t}.png')
 cover().save(O/'物品合成树-视频封面.png')
 (O/'物品合成树-中文字幕.srt').write_text('\n\n'.join(f'{j+1}\n{timestamp(a)} --> {timestamp(b)}\n{s}' for j,(a,b,s) in enumerate(cues)),encoding='utf-8')
 if '--preview' in sys.argv:sys.exit()
 music();ff=imageio_ffmpeg.get_ffmpeg_exe();output=str(O/'物品合成树-B站演示-1080p.mp4')
 cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','-','-i','work/demo-music.wav','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-t','60',output]
 with open('work/video-encode.log','w') as log:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  for k in range(FPS*60):
   proc.stdin.write(frame(k/FPS).tobytes())
   if k%150==0:print(f'Rendered {k//FPS}/60 seconds',flush=True)
  proc.stdin.close();code=proc.wait();assert code==0,code
 print('Completed',output,flush=True)
