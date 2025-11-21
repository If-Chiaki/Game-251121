import random
import uuid
from typing import List, Dict, Optional, Union

# 游戏常量
LOCATIONS = ["起始之地", "武器库", "驯兽场", "好药店", "坏药店", "决胜之地"]
MAX_HP = 12

# 物品类型定义
class ItemType:
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    POTION = "potion"
    MOUNT = "mount" # 兽

class Item:
    def __init__(self, name, i_type, desc="", **kwargs):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.type = i_type
        self.desc = desc
        self.props = kwargs # 存储伤害、耐久、容量等属性

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "desc": self.desc,
            "props": self.props
        }

class Player:
    def __init__(self, name: str, player_id: str):
        self.id = player_id
        self.name = name
        self.hp = MAX_HP
        self.max_hp = MAX_HP
        self.pos = "起始之地"
        self.inventory: List[Item] = []
        self.buffs: List[str] = [] # 简单的buff名称列表: "poison", "berserk", "curse_source", "cursed", "mounted"
        self.is_alive = True
        self.roll_value = 0
        self.tame_progress = 0 # 驯兽进度

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "pos": self.pos,
            "inventory": [i.to_dict() for i in self.inventory],
            "buffs": self.buffs,
            "is_alive": self.is_alive,
            "roll_value": self.roll_value,
            "tame_progress": self.tame_progress
        }

    def get_item(self, item_id):
        for item in self.inventory:
            if item.id == item_id:
                return item
        return None

    def remove_item(self, item_id):
        self.inventory = [i for i in self.inventory if i.id != item_id]

    def check_capacity(self, new_item: Item):
        # 检查背包容量
        # 主手武器：1
        # 副手武器：3
        # 药水：3
        limits = {ItemType.MAIN_HAND: 1, ItemType.OFF_HAND: 3, ItemType.POTION: 3}
        if new_item.type not in limits:
            return True # 其他物品不限? 或者默认无限
        
        current_count = sum(1 for i in self.inventory if i.type == new_item.type)
        return current_count < limits[new_item.type]

class GameState:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.logs: List[str] = []
        self.phase = "WAITING"  # WAITING, ROLL, ACTION, EXTRA_ACTION, SETTLEMENT
        self.turn_order: List[str] = [] 
        self.extra_turn_order: List[str] = [] # 额外行动阶段的顺序
        self.current_actor_index = 0
        
        # 地图物品初始化
        self.map_items: Dict[str, List[Item]] = {loc: [] for loc in LOCATIONS}
        self._init_map_items()

    def _init_map_items(self):
        # B. 武器库
        self.map_items["武器库"].append(Item("刀", ItemType.MAIN_HAND, "伤害3 耐久3", damage=3, durability=3))
        self.map_items["武器库"].append(Item("拳套", ItemType.MAIN_HAND, "伤害2 无限耐久", damage=2, durability=999))
        self.map_items["武器库"].append(Item("盾", ItemType.OFF_HAND, "抵挡1次伤害", durability=1))
        
        # C. 驯兽场
        self.map_items["驯兽场"].append(Item("弓", ItemType.MAIN_HAND, "远程 伤害2(需箭)", damage=0, durability=999)) # 弓本身无伤，靠箭
        # 箭是副手，无限数量，这里放几个意思一下，或者逻辑上特殊处理
        for _ in range(5):
            self.map_items["驯兽场"].append(Item("箭", ItemType.OFF_HAND, "消耗品 伤害2", damage=2, durability=1))
        # 兽作为特殊物品/交互对象，这里简化为物品，但不可拾取，只能驯服
        self.map_items["驯兽场"].append(Item("兽", ItemType.MOUNT, "需驯服", hp=2))

        # D. 好药店
        self.map_items["好药店"].append(Item("治疗药水", ItemType.POTION, "回复生命", capacity=12))
        self.map_items["好药店"].append(Item("净化药水", ItemType.POTION, "清除Buff", capacity=1))
        self.map_items["好药店"].append(Item("改造药水", ItemType.POTION, "特殊合成", capacity=1))

        # E. 坏药店
        self.map_items["坏药店"].append(Item("剧毒药水", ItemType.POTION, "中毒/扣血", capacity=1))
        self.map_items["坏药店"].append(Item("狂暴药水", ItemType.POTION, "伤害翻倍", capacity=1))
        self.map_items["坏药店"].append(Item("诅咒药水", ItemType.POTION, "诅咒光环", capacity=1))

    def add_player(self, name: str, player_id: str):
        if self.phase != "WAITING":
            return False, "游戏已开始，无法加入"
        if player_id in self.players:
            return True, "欢迎回来"
        for p in self.players.values():
            if p.name == name:
                name = f"{name}_{random.randint(10,99)}"
        new_player = Player(name, player_id)
        self.players[player_id] = new_player
        self.log(f"玩家 {name} 加入了游戏。")
        return True, "加入成功"

    def remove_player(self, player_id: str):
        if player_id in self.players:
            name = self.players[player_id].name
            del self.players[player_id]
            self.log(f"玩家 {name} 离开了游戏。")
            if player_id in self.turn_order:
                # 简单处理，不从列表中删除以免索引错乱，轮到他时跳过
                pass

    def start_game(self):
        if len(self.players) < 2:
            return False, "人数不足 (至少2人)"
        self.phase = "ROLL"
        self.log("游戏开始！进入投掷阶段。")
        return True, "游戏开始"

    def roll_dice(self, player_id: str):
        if self.phase != "ROLL":
            return False, "当前不是投掷阶段"
        player = self.players.get(player_id)
        if not player: return False, "玩家不存在"
        if player.roll_value > 0: return False, "已投掷"
        
        val = random.randint(1, 6)
        player.roll_value = val
        self.log(f"{player.name} 投掷了 {val} 点。")
        
        if all(p.roll_value > 0 for p in self.players.values()):
            self._calculate_order()
        return True, f"投掷结果: {val}"

    def _calculate_order(self):
        # 排序：点数大到小
        sorted_players = sorted(self.players.values(), key=lambda p: p.roll_value, reverse=True)
        self.turn_order = [p.id for p in sorted_players]
        
        # 计算额外行动阶段名单
        # 投出 1 的玩家先行动，投出 6 的玩家后行动
        ones = [p.id for p in self.players.values() if p.roll_value == 1]
        sixes = [p.id for p in self.players.values() if p.roll_value == 6]
        self.extra_turn_order = ones + sixes
        
        self.phase = "ACTION"
        self.current_actor_index = 0
        self._start_turn()

    def _start_turn(self):
        # 跳过已离开或死亡的玩家
        while self.current_actor_index < len(self.turn_order):
            pid = self.turn_order[self.current_actor_index]
            player = self.players.get(pid)
            if player and player.is_alive:
                # 检查是否投出1，如果是，跳过普通行动阶段
                if player.roll_value == 1:
                    self.log(f"{player.name} 投出了1，跳过普通行动阶段。")
                    self.current_actor_index += 1
                    continue
                self.log(f"轮到 {player.name} 行动。")
                return
            self.current_actor_index += 1
        
        # 所有人都行动完了
        self._start_extra_phase()

    def _start_extra_phase(self):
        if not self.extra_turn_order:
            self._end_round_settlement()
            return
            
        self.phase = "EXTRA_ACTION"
        self.current_actor_index = 0 # 复用这个索引
        self.turn_order = self.extra_turn_order # 临时替换为额外行动列表
        
        self._start_extra_turn()

    def _start_extra_turn(self):
        while self.current_actor_index < len(self.turn_order):
            pid = self.turn_order[self.current_actor_index]
            player = self.players.get(pid)
            if player and player.is_alive:
                self.log(f"【额外阶段】轮到 {player.name} 行动。")
                return
            self.current_actor_index += 1
        
        self._end_round_settlement()

    def _check_turn(self, player_id):
        if self.phase not in ["ACTION", "EXTRA_ACTION"]:
            return False, "当前不是行动阶段"
        current_pid = self.turn_order[self.current_actor_index]
        if player_id != current_pid:
            return False, "还没轮到你"
        return True, ""

    def _consume_turn(self):
        self.current_actor_index += 1
        if self.phase == "ACTION":
            self._start_turn()
        else:
            self._start_extra_turn()

    # --- 行动逻辑 ---

    def move(self, player_id: str, target_loc: str):
        ok, msg = self._check_turn(player_id)
        if not ok: return False, msg
        
        if target_loc not in LOCATIONS: return False, "无效地点"
        player = self.players[player_id]
        
        if player.pos == "决胜之地" and target_loc != "决胜之地":
            return False, "无法离开决胜之地"
            
        old_pos = player.pos
        player.pos = target_loc
        self.log(f"{player.name} 移动到了 {target_loc}。")
        
        # 诅咒机制：离开诅咒源地图，移除被诅咒状态
        # 简化处理：在结算阶段统一处理，或者这里实时处理
        
        self._consume_turn()
        return True, "移动成功"

    def pick_up(self, player_id: str, item_id: str):
        ok, msg = self._check_turn(player_id)
        if not ok: return False, msg
        
        player = self.players[player_id]
        items_on_ground = self.map_items[player.pos]
        
        target_item = next((i for i in items_on_ground if i.id == item_id), None)
        if not target_item: return False, "物品不存在"
        
        if target_item.type == ItemType.MOUNT:
            return False, "兽无法直接拾取，请驯服"
            
        if not player.check_capacity(target_item):
            return False, "背包已满，请先丢弃或使用物品"
            
        items_on_ground.remove(target_item)
        player.inventory.append(target_item)
        self.log(f"{player.name} 拾取了 {target_item.name}。")
        self._consume_turn()
        return True, "拾取成功"

    def drop_item(self, player_id: str, item_id: str):
        # 丢弃不消耗回合？规则未明确，通常为了整理背包不消耗，或者算作整理
        # 这里假设不消耗回合，随时可做，或者作为拾取的前置
        player = self.players.get(player_id)
        if not player: return False, "玩家不存在"
        
        item = player.get_item(item_id)
        if not item: return False, "物品不存在"
        
        player.remove_item(item_id)
        self.map_items[player.pos].append(item)
        self.log(f"{player.name} 丢弃了 {item.name}。")
        return True, "丢弃成功"

    def attack(self, player_id: str, target_id: str, weapon_id: str):
        ok, msg = self._check_turn(player_id)
        if not ok: return False, msg
        if self.phase == "EXTRA_ACTION": return False, "额外阶段不可攻击"
        
        attacker = self.players[player_id]
        target = self.players.get(target_id)
        if not target or not target.is_alive: return False, "目标无效"
        
        weapon = attacker.get_item(weapon_id)
        # 基础空手
        damage = 1
        is_ranged = False
        
        if weapon:
            if weapon.name == "弓":
                is_ranged = True
                # 检查是否有箭
                arrow = next((i for i in attacker.inventory if i.name == "箭"), None)
                if not arrow: return False, "没有箭"
                attacker.remove_item(arrow.id) # 消耗箭
                damage = 2 # 箭伤害
            else:
                damage = weapon.props.get("damage", 1)
                # 扣耐久
                if "durability" in weapon.props and weapon.props["durability"] < 999:
                    weapon.props["durability"] -= 1
                    if weapon.props["durability"] <= 0:
                        attacker.remove_item(weapon.id)
                        self.log(f"{attacker.name} 的 {weapon.name} 损坏了！")

        # 距离判定
        if not is_ranged and attacker.pos != target.pos:
            return False, "距离太远"
        if is_ranged:
            if "决胜之地" in [attacker.pos, target.pos]:
                return False, "决胜之地无法进行远程攻击"

        # 伤害计算
        final_damage = damage
        if "berserk" in attacker.buffs:
            final_damage *= 2
            
        # 盾牌抵挡
        shield = next((i for i in target.inventory if i.name == "盾"), None)
        if shield and not is_ranged: # 盾通常挡近战
            shield.props["durability"] -= 1
            if shield.props["durability"] <= 0:
                target.remove_item(shield.id)
                self.log(f"{target.name} 的盾牌抵挡了攻击并破碎了！")
            else:
                self.log(f"{target.name} 用盾牌抵挡了攻击！")
            final_damage = 0
            
        if "mounted" in target.buffs and not is_ranged:
             self.log(f"{target.name} 骑乘中，免疫近战伤害！")
             final_damage = 0

        if final_damage > 0:
            target.hp -= final_damage
            self.log(f"{attacker.name} 攻击了 {target.name}，造成 {final_damage} 点伤害！")
            if target.hp <= 0:
                self._handle_death(target)
        else:
            self.log(f"{attacker.name} 攻击了 {target.name}，但未造成伤害。")

        self._consume_turn()
        return True, "攻击完成"

    def use_potion(self, player_id: str, potion_id: str, target_id: Optional[str] = None, is_group: bool = False):
        ok, msg = self._check_turn(player_id)
        if not ok: return False, msg
        if self.phase == "EXTRA_ACTION": return False, "额外阶段不可使用药水"
        
        user = self.players[player_id]
        potion = user.get_item(potion_id)
        if not potion or potion.type != ItemType.POTION: return False, "无效药水"
        
        # 药水逻辑简化实现
        p_name = potion.name
        targets = []
        
        if is_group:
            # 对群：同地图所有单位（或敌方，视药水而定）
            # 简化：对群通常针对同地图所有人
            targets = [p for p in self.players.values() if p.pos == user.pos and p.is_alive]
        else:
            if not target_id:
                return False, "目标不存在"
            t = self.players.get(target_id)
            if not t: return False, "目标不存在"
            targets = [t]

        # 消耗容量逻辑暂略，假设一次用完或按次扣
        # 这里简化为一次性消耗道具，除了治疗药水
        consume_item = True
        
        for t in targets:
            if p_name == "治疗药水":
                # 简单处理：回复2血
                t.hp = min(t.hp + 2, t.max_hp)
                self.log(f"{t.name} 回复了生命。")
                # 治疗药水有容量，这里简化为不消耗物品，或者扣容量
                if "capacity" in potion.props:
                    potion.props["capacity"] -= 4 # 假设喝一口
                    if potion.props["capacity"] <= 0:
                        consume_item = True
                    else:
                        consume_item = False
            elif p_name == "剧毒药水":
                t.hp = 1
                t.buffs.append("poison")
                self.log(f"{t.name} 中毒了！生命降至1。")
            elif p_name == "狂暴药水":
                t.buffs.append("berserk")
                self.log(f"{t.name} 进入狂暴状态！")
            elif p_name == "诅咒药水":
                t.buffs.append("curse_source")
                self.log(f"{t.name} 成为了诅咒之源！")
            elif p_name == "净化药水":
                t.buffs = []
                self.log(f"{t.name} 的状态被净化了。")

        if consume_item:
            user.remove_item(potion.id)
            
        self._consume_turn()
        return True, "使用了药水"

    def tame(self, player_id: str):
        ok, msg = self._check_turn(player_id)
        if not ok: return False, msg
        
        player = self.players[player_id]
        # 检查是否有兽
        beast = next((i for i in self.map_items[player.pos] if i.name == "兽"), None)
        if not beast: return False, "这里没有兽"
        
        player.tame_progress += 1
        self.log(f"{player.name} 正在驯服兽... (进度 {player.tame_progress}/2)")
        
        if player.tame_progress >= 2:
            player.buffs.append("mounted")
            self.map_items[player.pos].remove(beast)
            self.log(f"{player.name} 成功驯服并骑乘了兽！")
            
        self._consume_turn()
        return True, "驯兽行动"

    def _handle_death(self, player: Player):
        player.is_alive = False
        player.hp = 0
        self.log(f"玩家 {player.name} 死亡！")
        # 掉落所有物品
        for item in player.inventory:
            self.map_items[player.pos].append(item)
        player.inventory = []

    def _end_round_settlement(self):
        self.phase = "SETTLEMENT"
        self.log("回合结束，进行结算...")
        
        # 1. Buff 结算
        curse_sources = [p for p in self.players.values() if "curse_source" in p.buffs and p.is_alive]
        
        for p in self.players.values():
            if not p.is_alive: continue
            
            # 中毒
            if "poison" in p.buffs:
                if p.hp > 1:
                    p.hp -= 1
                    self.log(f"{p.name} 因中毒受到伤害。")
            
            # 诅咒判定
            is_cursed = False
            for source in curse_sources:
                if source.id != p.id and source.pos == p.pos:
                    is_cursed = True
                    break
            
            if is_cursed:
                if "cursed" not in p.buffs:
                    p.buffs.append("cursed")
                    self.log(f"{p.name} 受到了诅咒影响！")
                p.hp -= 1
                self.log(f"{p.name} 因诅咒受到伤害。")
            else:
                if "cursed" in p.buffs:
                    p.buffs.remove("cursed")
                    self.log(f"{p.name} 脱离了诅咒。")

            # 决胜之地回血
            if p.pos == "决胜之地":
                # 检查是否所有存活玩家都在
                alive_players = [pl for pl in self.players.values() if pl.is_alive]
                all_in = all(pl.pos == "决胜之地" for pl in alive_players)
                if not all_in:
                    p.hp = min(p.hp + 1, p.max_hp)
                    self.log(f"{p.name} 在决胜之地回复了生命。")

            if p.hp <= 0:
                self._handle_death(p)

        # 检查胜利条件
        alive_count = sum(1 for p in self.players.values() if p.is_alive)
        if alive_count <= 1:
            winner = next((p for p in self.players.values() if p.is_alive), None)
            if winner:
                self.log(f"游戏结束！获胜者是 {winner.name}！")
            else:
                self.log("游戏结束！无人生还。")
            # 游戏可以重置或保持状态
        else:
            # 准备下一回合
            self.phase = "ROLL"
            self.turn_order = []
            self.extra_turn_order = []
            for p in self.players.values():
                p.roll_value = 0
            self.log("--- 新回合开始，请投掷骰子 ---")

    def log(self, message: str):
        self.logs.append(message)
        if len(self.logs) > 50:
            self.logs.pop(0)

    def get_snapshot(self, observer_id: Optional[str] = None):
        observer = self.players.get(observer_id) if observer_id else None
        
        players_data = []
        for p in self.players.values():
            p_data = p.to_dict()
            if observer and p.id != observer_id:
                if p.pos != observer.pos:
                    p_data['pos'] = "???"
            players_data.append(p_data)

        # 物品可见性：只显示当前位置的物品
        visible_items = {}
        if observer:
            visible_items = {observer.pos: [i.to_dict() for i in self.map_items[observer.pos]]}
        else:
            # 全局视角显示所有
            visible_items = {k: [i.to_dict() for i in v] for k, v in self.map_items.items()}

        return {
            "players": players_data,
            "phase": self.phase,
            "logs": self.logs,
            "locations": LOCATIONS,
            "map_items": visible_items, # 新增：地图物品
            "current_actor": self.turn_order[self.current_actor_index] if (self.phase in ["ACTION", "EXTRA_ACTION"] and self.current_actor_index < len(self.turn_order)) else None
        }

game = GameState()

