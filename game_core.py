import random
from typing import List, Dict, Optional

# 游戏常量
LOCATIONS = ["起始之地", "武器库", "驯兽场", "好药店", "坏药店", "决胜之地"]
MAX_HP = 12

class Player:
    def __init__(self, name: str, player_id: str):
        self.id = player_id
        self.name = name
        self.hp = MAX_HP
        self.max_hp = MAX_HP
        self.pos = "起始之地"
        self.inventory = []  # 简单的物品列表
        self.buffs = []
        self.is_alive = True
        self.roll_value = 0  # 本回合投掷点数

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "pos": self.pos,
            "inventory": self.inventory,
            "buffs": self.buffs,
            "is_alive": self.is_alive,
            "roll_value": self.roll_value
        }

class GameState:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.logs: List[str] = []
        self.phase = "WAITING"  # WAITING, ROLL, ACTION, SETTLEMENT
        self.turn_order: List[str] = [] # 玩家ID列表，按行动顺序
        self.current_actor_index = 0
        
    def add_player(self, name: str, player_id: str):
        if self.phase != "WAITING":
            return False, "游戏已开始，无法加入"
        if player_id in self.players:
            return True, "欢迎回来"
        
        # 简单的重名处理
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
            
            # 如果游戏进行中有人离开，可能需要重置或特殊处理，这里简化为继续
            if player_id in self.turn_order:
                self.turn_order.remove(player_id)

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
        if not player:
            return False, "玩家不存在"
            
        if player.roll_value > 0:
            return False, "你已经投掷过了"
            
        # 1d6
        val = random.randint(1, 6)
        player.roll_value = val
        self.log(f"{player.name} 投掷了 {val} 点。")
        
        # 检查是否所有人都投掷了
        all_rolled = all(p.roll_value > 0 for p in self.players.values())
        if all_rolled:
            self._calculate_order()
            
        return True, f"投掷结果: {val}"

    def _calculate_order(self):
        # 简单的排序，暂不处理平局的1d20规则，直接按点数降序
        # 实际规则中：点数相同需1d20，这里简化处理
        sorted_players = sorted(
            self.players.values(), 
            key=lambda p: p.roll_value, 
            reverse=True
        )
        self.turn_order = [p.id for p in sorted_players]
        self.phase = "ACTION"
        self.current_actor_index = 0
        
        first_player = self.players[self.turn_order[0]]
        self.log(f"行动顺序已确定。当前行动: {first_player.name}")

    def move(self, player_id: str, target_loc: str):
        if self.phase != "ACTION":
            return False, "当前不是行动阶段"
            
        current_player_id = self.turn_order[self.current_actor_index]
        if player_id != current_player_id:
            return False, "还没轮到你行动"
            
        if target_loc not in LOCATIONS:
            return False, "无效的地点"
            
        player = self.players[player_id]
        
        # 决胜之地规则：进入后无法离开
        if player.pos == "决胜之地" and target_loc != "决胜之地":
            return False, "进入决胜之地后无法离开！"
            
        old_pos = player.pos
        player.pos = target_loc
        self.log(f"{player.name} 从 {old_pos} 移动到了 {target_loc}。")
        
        self._next_turn()
        return True, "移动成功"

    def _next_turn(self):
        self.current_actor_index += 1
        if self.current_actor_index >= len(self.turn_order):
            # 所有人都行动完了，进入下一回合（这里简化，直接回到投掷阶段）
            self.phase = "ROLL"
            self.turn_order = []
            for p in self.players.values():
                p.roll_value = 0
            self.log("所有玩家行动结束。新回合开始，请投掷骰子！")
        else:
            next_pid = self.turn_order[self.current_actor_index]
            next_player = self.players[next_pid]
            self.log(f"轮到 {next_player.name} 行动。")

    def log(self, message: str):
        self.logs.append(message)
        if len(self.logs) > 50:
            self.logs.pop(0)

    def get_snapshot(self):
        return {
            "players": [p.to_dict() for p in self.players.values()],
            "phase": self.phase,
            "logs": self.logs,
            "locations": LOCATIONS,
            "current_actor": self.turn_order[self.current_actor_index] if self.phase == "ACTION" and self.turn_order else None
        }

# 全局游戏实例
game = GameState()
