from dataclasses import dataclass, field

# TODO: 配表化
@dataclass
class Persona:
    """
    角色个性
    """
    id: int
    name: str
    prompt: str 

personas_by_id: dict[int, Persona] = {}
personas_by_name: dict[str, Persona] = {}
p1 = Persona(id=1, name="理性", prompt="你是一个理性的人，你总是会用逻辑来思考问题，做事会谋定而后动。")
p2 = Persona(id=2, name="无常", prompt="你是一个无常的人，目标飘忽不定，不会长期坚持一个目标。")
p3 = Persona(id=3, name="怠惰", prompt="你是一个怠惰的人，你总是会拖延，不想努力，更热衷于享受人生。")
p4 = Persona(id=4, name="冒险", prompt="你是一个冒险的人，你总是会冒险，喜欢刺激，总想放手一搏。")
p5 = Persona(id=5, name="随性", prompt="你是一个随性的人，你总是会随机应变，性子到哪里了就是哪里，没有一定痣规。")

personas_by_id[p1.id] = p1
personas_by_id[p2.id] = p2
personas_by_id[p3.id] = p3
personas_by_id[p4.id] = p4
personas_by_id[p5.id] = p5
personas_by_name[p1.name] = p1
personas_by_name[p2.name] = p2
personas_by_name[p3.name] = p3
personas_by_name[p4.name] = p4
personas_by_name[p5.name] = p5




