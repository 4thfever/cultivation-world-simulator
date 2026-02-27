import pytest
from src.classes.relation.relation import Relation
from src.classes.relation.relations import update_second_degree_relations, set_relation
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.systems.time import MonthStamp
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
    father.acknowledge_parent(grandpa)
    # Son's parent is Father
    son.acknowledge_parent(father)
    # Daughter's parent is Father
    daughter.acknowledge_parent(father)
    
    # Update logic
    for p in [grandpa, father, son, daughter]:
        update_second_degree_relations(p)
        
    # Assertions
    
    # 1. Sibling check (Son <-> Daughter)
    # Son perspective
    assert son.computed_relations.get(daughter) == Relation.IS_SIBLING_OF
    # Daughter perspective
    assert daughter.computed_relations.get(son) == Relation.IS_SIBLING_OF
    
    # 2. Grandparent check (Son/Daughter -> Grandpa)
    assert son.computed_relations.get(grandpa) == Relation.IS_GRAND_PARENT_OF
    assert daughter.computed_relations.get(grandpa) == Relation.IS_GRAND_PARENT_OF
    
    # 3. Grandchild check (Grandpa -> Son/Daughter)
    assert grandpa.computed_relations.get(son) == Relation.IS_GRAND_CHILD_OF
    assert grandpa.computed_relations.get(daughter) == Relation.IS_GRAND_CHILD_OF
    
    # 4. Father should not have Sibling/Grandparent (in this limited set)
    assert Relation.IS_SIBLING_OF not in father.computed_relations.values()
    assert Relation.IS_GRAND_PARENT_OF not in father.computed_relations.values()

def test_sect_relations(base_world):
    master = create_avatar(base_world, "Master")
    disciple_a = create_avatar(base_world, "DiscipleA")
    disciple_b = create_avatar(base_world, "DiscipleB")
    grand_master = create_avatar(base_world, "GrandMaster")
    
    # Setup: GrandMaster -> Master -> A/B
    # Master is disciple of GrandMaster
    master.acknowledge_master(grand_master)
    
    # A is disciple of Master
    disciple_a.acknowledge_master(master)
    
    # B is disciple of Master
    disciple_b.acknowledge_master(master)
    
    # Update
    for p in [grand_master, master, disciple_a, disciple_b]:
        update_second_degree_relations(p)
        
    # Assertions
    
    # 1. Martial Sibling (A <-> B)
    assert disciple_a.computed_relations.get(disciple_b) == Relation.IS_MARTIAL_SIBLING_OF
    assert disciple_b.computed_relations.get(disciple_a) == Relation.IS_MARTIAL_SIBLING_OF
    
    # 2. Martial Grandmaster (A/B -> GrandMaster)
    assert disciple_a.computed_relations.get(grand_master) == Relation.IS_MARTIAL_GRANDMASTER_OF
    assert disciple_b.computed_relations.get(grand_master) == Relation.IS_MARTIAL_GRANDMASTER_OF
    
    # 3. Martial Grandchild (GrandMaster -> A/B)
    assert grand_master.computed_relations.get(disciple_a) == Relation.IS_MARTIAL_GRANDCHILD_OF
    assert grand_master.computed_relations.get(disciple_b) == Relation.IS_MARTIAL_GRANDCHILD_OF

def test_master_disciple_sect_binding(base_world):
    from src.classes.core.sect import Sect, SectHeadQuarter
    from src.classes.alignment import Alignment
    from src.classes.sect_ranks import SectRank
    from pathlib import Path
    
    master = create_avatar(base_world, "Master")
    disciple = create_avatar(base_world, "Disciple")
    
    # Create a simple sect
    sect = Sect(
        id=1,
        name="TestSect",
        desc="A test sect",
        member_act_style="style",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="HQ", desc="HQ Desc", image=Path("")),
        technique_names=[]
    )
    
    # Master joins sect
    master.join_sect(sect, SectRank.Elder)
    
    # Disciple acknowledges master
    disciple.acknowledge_master(master)
    
    # Disciple should be in master's sect now
    assert disciple.sect is sect
    assert disciple.sect_rank is not None
    
    # Test accept_disciple logic as well
    master2 = create_avatar(base_world, "Master2")
    disciple2 = create_avatar(base_world, "Disciple2")
    master2.join_sect(sect, SectRank.Elder)
    
    master2.accept_disciple(disciple2)
    assert disciple2.sect is sect
    assert disciple2.sect_rank is not None
