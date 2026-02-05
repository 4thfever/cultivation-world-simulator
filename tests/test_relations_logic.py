import pytest
from src.classes.relation.relation import Relation
from src.classes.relation.relations import update_second_degree_relations, set_relation
from src.classes.avatar import Avatar, Gender
from src.classes.age import Age
from src.classes.cultivation import Realm
from src.classes.calendar import MonthStamp
from src.utils.id_generator import get_avatar_id

def create_avatar(world, name, gender=Gender.MALE):
    return Avatar(
        world=world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=MonthStamp(0),
        age=Age(20, Realm.Qi_Refinement),
        gender=gender,
        pos_x=0, pos_y=0
    )

def test_family_relations(base_world):
    grandpa = create_avatar(base_world, "Grandpa")
    father = create_avatar(base_world, "Father")
    son = create_avatar(base_world, "Son")
    daughter = create_avatar(base_world, "Daughter", Gender.FEMALE)
    
    # Setup relations: Grandpa -> Father -> Son/Daughter
    # Father's parent is Grandpa
    set_relation(father, grandpa, Relation.PARENT)
    # Son's parent is Father
    set_relation(son, father, Relation.PARENT)
    # Daughter's parent is Father
    set_relation(daughter, father, Relation.PARENT)
    
    # Update logic
    for p in [grandpa, father, son, daughter]:
        update_second_degree_relations(p)
        
    # Assertions
    
    # 1. Sibling check (Son <-> Daughter)
    # Son perspective
    assert son.computed_relations.get(daughter) == Relation.SIBLING
    # Daughter perspective
    assert daughter.computed_relations.get(son) == Relation.SIBLING
    
    # 2. Grandparent check (Son/Daughter -> Grandpa)
    assert son.computed_relations.get(grandpa) == Relation.GRAND_PARENT
    assert daughter.computed_relations.get(grandpa) == Relation.GRAND_PARENT
    
    # 3. Grandchild check (Grandpa -> Son/Daughter)
    assert grandpa.computed_relations.get(son) == Relation.GRAND_CHILD
    assert grandpa.computed_relations.get(daughter) == Relation.GRAND_CHILD
    
    # 4. Father should not have Sibling/Grandparent (in this limited set)
    assert Relation.SIBLING not in father.computed_relations.values()
    assert Relation.GRAND_PARENT not in father.computed_relations.values()

def test_sect_relations(base_world):
    master = create_avatar(base_world, "Master")
    disciple_a = create_avatar(base_world, "DiscipleA")
    disciple_b = create_avatar(base_world, "DiscipleB")
    grand_master = create_avatar(base_world, "GrandMaster")
    
    # Setup: GrandMaster -> Master -> A/B
    # Master is disciple of GrandMaster
    set_relation(master, grand_master, Relation.MASTER) # master.relations[GM] = MASTER, GM.relations[master] = APPRENTICE
    
    # A is disciple of Master
    set_relation(disciple_a, master, Relation.MASTER)
    
    # B is disciple of Master
    set_relation(disciple_b, master, Relation.MASTER)
    
    # Update
    for p in [grand_master, master, disciple_a, disciple_b]:
        update_second_degree_relations(p)
        
    # Assertions
    
    # 1. Martial Sibling (A <-> B)
    assert disciple_a.computed_relations.get(disciple_b) == Relation.MARTIAL_SIBLING
    assert disciple_b.computed_relations.get(disciple_a) == Relation.MARTIAL_SIBLING
    
    # 2. Martial Grandmaster (A/B -> GrandMaster)
    assert disciple_a.computed_relations.get(grand_master) == Relation.MARTIAL_GRANDMASTER
    assert disciple_b.computed_relations.get(grand_master) == Relation.MARTIAL_GRANDMASTER
    
    # 3. Martial Grandchild (GrandMaster -> A/B)
    assert grand_master.computed_relations.get(disciple_a) == Relation.MARTIAL_GRANDCHILD
    assert grand_master.computed_relations.get(disciple_b) == Relation.MARTIAL_GRANDCHILD
