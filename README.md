# MC_tree · 物品合成树

Minecraft Java 26.3 合成依赖可视化，包含二维总图、七层 3D 合成树和一分钟演示视频。

## 使用

无需构建或安装前端依赖。在项目根目录运行：

```sh
python -m http.server 8000 --directory web
```

访问 http://localhost:8000/3d.html 查看 3D 树，访问 http://localhost:8000/ 查看完整配方总图。无背景回退版本为 3d-plain.html。

## 功能

- 七层布局、按物品数量调整层宽、圆形节点。
- 默认隐藏连线，选择物品后显示代表性前置路径；支持搜索、旋转、缩放和替代配方。
- 来源层决定连线颜色，动态光点指向产物，多材料直接连接实际产物节点。
- 可切换 Minecraft 风格背景，以及主干、分枝、树根装饰。

## 目录

- web/：当前可直接运行的网站源码及数据，graph3d.js 是 3D 主程序。
- data/：归一化数据、官方版本元数据与中文名称。
- scripts/：官方客户端下载校验、配方提取、连线检查、演示动画生成。
- docs/：范围说明、完整分层索引、B 站发布文案。
- media/：1080p 演示视频、封面与字幕。

## 数据范围

版本为 Java 26.3。图中共 1,491 个物品与独立药水状态；2,042 个配方文件中，1,993 个固定输出配方进入依赖图，49 个动态特殊配方另列。具体范围见 docs/。

层级表示本图内的依赖关系，不代表游戏进度。第一层包含从图外机制获得的边界材料。多输入、替代材料与循环意味着实际关系是依赖图，而非严格树；选择时展示一条代表性前置路径。酿造按单瓶转化表达，不作为批次耗材估算。

官方客户端 SHA-1：e877b6a07acd633fb3bb475002175cec036e7b87。下载地址和版本信息保存在 data/version.json；游戏客户端与依赖库未包含在工程包中。

## 检查与再生成

```sh
node scripts/audit_edges.cjs
python -m pip install -r requirements.txt
python scripts/render_demo.py --preview
python scripts/render_demo.py
```

视频脚本当前使用 Windows 微软雅黑字体（C:/Windows/Fonts/msyh.ttc 等）；其他系统需调整字体路径。视频为基于相同数据制作的演示动画，含中文字幕与合成器配乐，不是浏览器录屏。

如需重新提取官方数据，依次运行 python scripts/download.py 和 python scripts/extract.py；这将更新数据文件，但不会自动重新嵌入各网页。日常界面编辑直接修改 web/ 即可。

Minecraft 名称及游戏内容属于其各自权利人。本项目为非官方可视化工程。
