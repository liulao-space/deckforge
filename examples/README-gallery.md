# 🖼 DeckForge · 作品墙 (Gallery)

每套 deck 都是**一个 JSON 内容**，换上不同主题预设即可瞬间换装。下面的每一格都是真实产物。

> 想看效果？用 `--watch` 在浏览器打开，滚动即可翻页；或对输出页截图/GIF 后贴回这里。

---

## 主题全家桶（同一内容 · 不同 preset）

| 预览 | 主题 | 构建命令 |
| --- | --- | --- |
| 青绿 Teal | `--preset teal` (默认) | `deckforge examples/choosing-a-framework.json -o out.html --preset teal` |
| 海洋蓝 Ocean | `--preset ocean` | `... --preset ocean` |
| 紫罗兰 Violet | `--preset violet` | `... --preset violet` |
| 落日渐橙 Sunset | `--preset sunset` | `... --preset sunset` |
| 玫红 Rose | `--preset rose` | `... --preset rose` |
| 极简黑白 Mono | `--preset mono` | `... --preset mono` |
| 祖母绿 Emerald | `--preset emerald` | `... --preset emerald` |
| 深色款 (任意 presets + `--dark`) | `--dark` | `... --preset ocean --dark` |

### 深色主题效果
`deckforge examples/orca-herdr.json -o out.html --preset teal --dark`

深色模式下，卡片、文字、描边、阴影、光标与悬浮竖线全部自动翻转，只用一个 accent 主色贯通。

---

## 真实示例（内置 examples/）

### 1. 多 Agent 编排 —— `examples/orca-herdr.json`
适合「介绍两个相近工具 + 如何选择」的主题：
- 封面 → 背景痛点 → 各自介绍（含**动态终端逐行打字**）→ **对比表** → **VS 边界** → **决策 flow** → **实操 steps** → 总结 quote。
- 类型：`pills / cards / card-list / terminal / table / vs / flow / steps / warn / quote`

构建：
```bash
deckforge examples/orca-herdr.json -o out.html
```

### 2. 块类型全覆盖 —— `examples/choosing-a-framework.json`
验证 `vs / flow / steps / warn / terminal` 等全部块都能正确渲染，可作为你写内容时的「块参考模板」。

构建：
```bash
deckforge examples/choosing-a-framework.json -o out.html --preset ocean
```

---

## 如何产出你自己的作品墙素材

1. `deckforge my-deck.json -o out.html --preset violet`
2. 浏览器打开 `out.html`，对每张幻灯片截图（或录屏成 GIF）。
3. 贴到 README 顶部 —— **成品图是第一印象，比任何文字都有效。**

> 小技巧：配合 `--watch` 边写内容边实时预览；用系统截图工具或 `ffmpeg` 把页面录成动图。
