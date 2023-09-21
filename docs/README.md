# effect填写逻辑

## 概要

> 结构示例
 
* 此小节说明的字段，在各类effect中均生效
 * `referencetarget`相关字段不影响计算，此处不展示
 * 不同类别effect中字段效果有差异的，后面分别说明
 * 各类型字段未填写时的默认值
   * 字符串类型：空字符串
   * 数值类型：maxStack为1，其他字段为0
   * 布尔类型：false
   * 数组类型：空数组

```json
{
	"iid": "1", // 必填，内容随意，在当前effect数组内保持唯一即可，老数据统一加的类似"1"、"2"、"3"等
	"type": "buff", // 必填，effect类型
	"addtarget": "hp", // 后面说明
	"multipliertarget": "atk", // 后面说明
	"multiplier": 5, // 效果的值或者对应levelmultiplier的索引，目前代码中判断如果当前结构中存在levelmultiplier并且此值小于等于levelmultiplier的长度，则认为是索引，否则认为是值
	"multipliervalue": "1", // 效果的固定值，如果填写则会忽略multiplier对应的值，注意是字符串，便于后续扩展支持计算公式，multiplier和multipliervalue至少填写一个
	"multipliermax": "100", // 暂未使用，可不填写
	"maxStack": 6, // 选填，此效果可堆叠的层数，如果>1，则会在界面展示选项可选择层数，<5时展示组件为ChoiceChip，>=5时展示组件为DropdownMenu，值会乘到此效果计算的结果上
	"group": "1", // 选填，用于聚合形如10%生命+20%攻击力这类组合倍率，同一个skill内需要组合的多个effect填写相同的group即可，跨skill目前不支持聚合，具体内容不限，可参考刃的终结技
	"tag": [ // 后面说明
		"self",
		"ultatk"
	],
	"hide": true // true则不会在wiki界面展示此tag，当此effect仅用于计算器时可使用
}
```

## 增益/减益

### buff

> 计算器加载的合法buff的条件：

* `type == 'buff'`，并且：
  1. 自身buff：`tag.contains('allally') || tag.contains('self')`
  2. 可给队友的buff：`tag.contains('allally') || tag.contains('singleally')`
* 并且`addtarget`是合法的属性值，支持的属性见最后表格

### debuff

> 计算器加载的合法debuff的条件

* `type == 'debuff' && (tag.contains('allenemy') || tag.contains('singleenemy'))`并且`addtarget`是合法的属性值，支持的属性见最后表格

### 字段表示的语义逻辑

* 无`multipliertarget`时：对目标属性`addtarget`，加成`multiplier`或`multipliervalue`的值
* 存在`multipliertarget`时：基于`multipliertarget`对应的属性，加成`multiplier`或`multipliervalue`百分比的值，加成的目标属性为`addtarget`

### 无选项的buff示例

* 作用于自身，攻击力提高4%，如果存在`levelmultiplier`并且`2`能够对应上索引，则提高的值从`levelmultiplier`中获取，是否为百分比提升取决于`addtarget`对应的是否为百分比属性，此处`atk`对应攻击力百分比
* debuff类似填写即可

```json
{
	"iid": "1",
	"type": "buff",
	"addtarget": "atk",
	"multiplier": 2,
	"tag": [
		"self",
		"alldmg"
	]
}
```

### 带叠层选项的buff示例

* 艾丝妲天赋：增加攻击力百分比，最多可叠加5层，展示效果如图

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/352d05be-f040-4ad9-8795-9d9a69cb69ed)

```json
{
	"iid": "1",
	"type": "buff",
	"addtarget": "atk",
	"multiplier": 1,
	"maxstack": 5,
	"tag": [
		"allally",
		"atk"
	]
}
```

* 刃星魂4：增加20%生命值，最多可叠加2层，展示效果如图

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/ab4868b3-8ecd-4cbf-8e8f-5201bf646260)

```json
{
	"iid": "1",
	"type": "buff",
	"addtarget": "hp",
	"multiplier": 20,
	"maxstack": 2,
	"tag": [
		"self",
		"hp"
	]
}
```

### 带填写数值的buff示例

* 当`multipliertarget`不为空时，表示此buff需要基于某项属性的数值提升`addtarget`，则会展示一个输入框用于填写，在buff/debuff类型中，此功能目前只用于来自他人的效果，例如鸭鸭的终结技
* 此处同时展示组合倍率的填写，效果如图

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/f98e05ef-8c62-48f4-a4ad-3d4726470a0b)

```json
{
	"iid": "2",
	"type": "buff",
	"referencetarget": "bronya",
	"referencetargetEN": "Bronya",
	"referencetargetCN": "布洛妮娅",
	"referencetargetJP": "ブローニャ",
	"addtarget": "critdmg",
	"multipliertarget": "critdmg",
	"multiplier": 2,
	"group": "1",
	"tag": [
		"allally",
		"critdmg"
	]
},
{
	"iid": "3",
	"type": "buff",
	"addtarget": "critdmg",
	"multiplier": 3,
	"group": "1",
	"tag": [
		"allally",
		"critdmg"
	]
}
```

## 伤害/治疗/护盾

* 对应`type`分别为`dmg`、`heal`、`shield`，另外`revive`也视为治疗技能，因为复活必然能够回复一定血量，例如杰帕德天赋
* 如果是伤害技能，`tag`中需要包含伤害类型和元素属性，会在计算时应用对应的加成，可选的值如下：
  * `basicatk`或`normalatk`：普通攻击，由于老数据两种都有，所以这里都支持了
  * `skillatk`：战技攻击
  * `ultatk`：终结技攻击
  * `dotatk`：持续伤害
  * `followupatk`：追加攻击
  * `additionalatk`：附加攻击
  * `physicaldmg`：物理属性伤害
  * `firedmg`：火属性伤害
  * `icedmg`：冰属性伤害
  * `lightningdmg`：雷属性伤害
  * `winddmg`：风属性伤害
  * `quantumdmg`：量子属性伤害
  * `imaginarydmg`：虚数属性伤害
* 治疗和护盾对`tag`字段无特殊要求

### 字段表示的语义逻辑

以`multiplier`或`multipliervalue`的值为倍率，以`multipliertarget`对应的属性为基数，造成伤害/治疗/护盾

### 无选项的伤害技能示例

* 希儿战技：战技攻击、量子属性伤害、倍率为`1`对应到`levelmultiplier`中的值，基于攻击力造成伤害

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/df3cf27b-c649-4cbc-b4a0-ad046247182a)

```json
{
	"iid": "1",
	"type": "dmg",
	"multipliertarget": "atk",
	"multiplier": 1,
	"tag": [
		"singleatk",
		"skillatk",
		"quantumatk"
	]
}
```

### 带叠层选项的伤害技能示例

* 景元的神君：追加攻击，雷属性伤害，最多可叠加10层
* 叠层选项的值会直接乘到`multiplier`对应的倍率上，效果如图

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/3e5c9a12-5599-4d2e-882c-ee8f6569f6f3)

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/a58fe196-d4c2-41f6-b498-9855784cdae8)

```json
{
	"iid": "1",
	"type": "dmg",
	"multipliertarget": "atk",
	"multiplier": 1,
	"maxstack": 10,
	"tag": [
		"aoe",
		"followupatk",
		"lightningatk"
	]
}
```

### 倍率对应的属性不存在的情况

* 例如刃的技能倍率中有`x%的已损失生命值`，卡芙卡技能倍率中有`y%的当前全部持续伤害`
* 目前的思路是人为构造这些本不存在的属性，即把`已损失生命值`或者`当前全部持续伤害`视为角色身上的某个属性，那么可以用构造buff的方式解决

#### 已损失生命值

* 构造buff如下，加成目标属性为`losthpratio`，即`已损失生命值百分比`，基于`1`计算加成值，最大堆叠层数为90（技能限制），wiki界面隐藏
* 此buff最终取值为`[0.01-0.9]`（界面无法选0）最终会用于计算战斗属性`已损失生命值`，对应`losthp`

```json
{
	"iid": "7",
	"type": "buff",
	"addtarget": "losthpratio",
	"multipliervalue": "1",
	"maxstack": 90,
	"tag": [
		"self",
		"losthp"
	],
	"hide": true
}
```

* 基于`已损失生命值`的伤害技能可填写为

```json
{
	"iid": "6",
	"type": "dmg",
	"multipliertarget": "losthp",
	"multiplier": 6,
	"group": "2",
	"tag": [
		"allenemy",
		"windatk"
	]
}
```

* 效果如下

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/0befc496-b000-4db9-8a3e-db715fc3a276)

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/2031c56a-8288-4103-a850-014db3b18923)

#### 当前全部持续伤害

* 构造buff如下，加成目标属性为`alldotdmg`，即`当前全部持续伤害`，基于`1`计算加成值，`multipliertarget`必须填写用于展示输入框和提示，无实际计算意义，wiki界面隐藏
* 最终会用于计算战斗属性`当前全部持续伤害`

```json
{
	"iid": "4",
	"type": "buff",
	"addtarget": "alldotdmg",
	"multipliertarget": "alldotdmg",
	"multipliervalue": "1",
	"tag": [
		"self",
		"alldotdmg"
	],
	"hide": true
}
```

* 基于`当前全部持续伤害`的伤害技能可填写为

```json
{
	"iid": "3",
	"type": "dmg",
	"referencetarget": "dotatk",
	"referencetargetEN": "all DoTs currently",
	"referencetargetCN": "当前承受的所有持续伤害",
	"referencetargetJP": "付与された全持続ダメージ",
	"multipliertarget": "alldotdmg",
	"multiplier": 2,
	"tag": [
		"dotatk",
		"lightningatk"
	]
}
```

* 效果如下

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/96f7e56d-5d79-4331-9464-cfd9f82c7f43)

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/faa79d41-f67e-4878-a672-7bc585991ea5)

#### 已预埋的人为构造属性

* `losthpratio`：已损失生命值，伤害技能中对应`losthp`
* `alldotdmg`：全部持续伤害
* `shockeddotdmg`：感电持续伤害
* `burndotdmg`：灼烧持续伤害
* `windsheardotdmg`：风化持续伤害
* `bleeddotdmg`：裂伤持续伤害

#### 属性展示

在`debug`模式中，会在其他面板展示这些属性的值，如下：

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/179555ad-4ce1-4cbf-85e0-21cd254292a9)

![image](https://github.com/Kamihimmel/HSRwiki/assets/2188512/1dd4c082-56ff-4581-a97d-443d774109c3)

## 属性对应表

|属性key|含义|其他说明|
|--|--|--|
|maxhp|生命值上限|只用于技能倍率属性|
|hppt|生命数值加成||
|hp|生命值百分比加成||
|allatk|总攻击力|暂未使用|
|atkpt|攻击力数值加成||
|atk|攻击力|buff类技能中表示攻击力百分比加成，伤害技能中表示倍率基于总攻击力|
|alldef|总防御力|暂未使用|
|defpt|防御力数值加成||
|def|防御力|buff类技能中表示防御力百分比加成，伤害技能中表示倍率基于总防御力|
|energyregenrate|能量回复效率||
|spd|速度|暂未使用|
|speedpt|速度数值加成||
|speed|速度百分比加成||
|taunt|嘲讽值||
|healrate|治疗加成||
|shielddmgabsorb|护盾加成||
|effecthit|效果命中||
|effectres|效果抵抗||
|critrate|暴击率||
|critdmg|暴击伤害||
|normalcrit|普通攻击暴击率||
|skillcrit|战技暴击率||
|ultcrit|终结技暴击率||
|followupcrit|追加攻击暴击率||
|normalcritdmg|普通攻击暴击伤害||
|skillcritdmg|战技暴击伤害||
|ultcritdmg|终结技暴击伤害||
|followupcritdmg|追加攻击暴击伤害||
|breakeffect|击破特攻||
|alldmg|伤害加成||
|physicaldmg|物理属性伤害加成||
|firedmg|火属性伤害加成||
|icedmg|冰属性伤害加成||
|lightningdmg|雷属性伤害加成||
|winddmg|风属性伤害加成||
|quantumdmg|量子属性伤害加成||
|imaginarydmg|虚数属性伤害加成||
|dotatk|持续伤害加成||
|additionalatk|附加攻击伤害加成||
|normalatk|普通攻击伤害加成||
|skillatk|战技伤害加成||
|ultatk|终结技伤害加成||
|followupatk|追加攻击伤害加成||
|allres|全属性抗性降低/全属性穿透||
|specificres|特定属性抗性降低/特性属性穿透|在计算时默认为当前角色属性|
|physicalpen|物理属性抗性降低/物理属性穿透|
|firepen|火属性抗性降低/火属性穿透||
|icepen|冰属性抗性降低/冰属性穿透||
|lightningpen|雷属性抗性降低/雷属性穿透||
|windpen|风属性抗性降低/风属性穿透||
|quantumpen|量子属性抗性降低/量子属性穿透||
|imaginarypen|虚数属性抗性降低/虚数属性穿透||
|ignoredef|无视防御力||
|controlresist|控制类效果抵抗||
|dmgreduction|减伤|角色自身buff|
|dmgreceive|受到伤害增加|敌方debuff|
|physicaldmgreceive|受到物理属性伤害增加|敌方debuff|
|firedmgreceive|受到火属性伤害增加|敌方debuff|
|icedmgreceive|受到冰属性伤害增加|敌方debuff|
|lightningdmgreceive|受到雷属性伤害增加|敌方debuff|
|winddmgreceive|受到风属性伤害增加|敌方debuff|
|quantumdmgreceive|受到量子属性伤害增加|敌方debuff|
|imaginarydmgreceive|受到虚数属性伤害增加|敌方debuff|
|dotdmgreceive|受到持续伤害增加|敌方debuff|
|additionaldmgreceive|受到附加攻击伤害增加|敌方debuff|
|reducedef|降低防御力|敌方debuff|
|reducespeed|减速|敌方debuff|
|effectresreduce|降低效果抵抗|敌方debuff|
|losthp|已损失生命值|人为构造属性|
|losthpratio|已损失生命值百分比|人为构造属性|
|alldotdmg|全部持续伤害|人为构造属性|
|shockeddotdmg|感电持续伤害|人为构造属性|
|burndotdmg|灼烧持续伤害|人为构造属性|
|windsheardotdmg|风化持续伤害|人为构造属性|
|bleeddotdmg|裂伤持续伤害|人为构造属性|
