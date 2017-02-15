# encoding=utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = '1661'

import binascii

from structure_reader.structure_reader import *


def check_extra_buf(parser):
    if len(parser.data) > parser.pos:
        print('剩余%d/%d未解析' % (len(parser.data) - parser.pos, len(parser.data)))
        return True

    return False


def assert_ctype(ctype_instance, ctype, value):
    assert isinstance(ctype_instance, ctype)
    assert ctype_instance.value == value


def test_short():
    s = Structure()
    s.field_list.extend([
        Field(ctypes.c_short, 'a', None)
    ])
    data = binascii.a2b_hex(b'0100')
    parser = StructureReader(data, dict())
    parser.read_structure(s)
    assert isinstance(s.get_field_value('a'), ctypes.c_short)
    assert s.get_value('a') == 1
    assert not check_extra_buf(parser)


def test_array():
    s = Structure()
    s.field_list.extend([
        Field(ctypes.c_short, 'a', None),
        Field((ctypes.c_short, 2), 'b', None),
    ])
    data = binascii.a2b_hex(b'010002000300')
    parser = StructureReader(data, dict())
    parser.read_structure(s)
    assert isinstance(s.get_field_value('b'), list)
    b = s.get_field_value('b')
    assert len(b) == 2
    assert_ctype(b[0], ctypes.c_short, 2)
    assert_ctype(b[1], ctypes.c_short, 3)
    assert not check_extra_buf(parser)


def test_mutable_array():
    s = Structure()
    s.field_list.extend([
        Field(ctypes.c_short, 'a', None),
        Field((ctypes.c_short, 'a'), 'b', None),
    ])
    data = binascii.a2b_hex(b'0300020003000400')
    parser = StructureReader(data, dict())
    parser.read_structure(s)
    assert isinstance(s.get_field_value('b'), list)
    b = s.get_field_value('b')
    assert len(b) == 3
    assert_ctype(b[0], ctypes.c_short, 2)
    assert_ctype(b[1], ctypes.c_short, 3)
    assert_ctype(b[2], ctypes.c_short, 4)
    assert not check_extra_buf(parser)


def test_sub_structure():
    s = Structure()
    s.field_list.extend([
        Field(ctypes.c_short, 'a', None),
        Field((ctypes.c_short, 'a'), 'b', None),
        Field('s2', 'c', None),
    ])
    s2 = Structure()
    s2.name = 's2'
    s2.field_list.extend([
        Field(ctypes.c_short, 'a', None),
        Field((ctypes.c_short, 'a'), 'b', None),
    ])
    data = binascii.a2b_hex('0300020003000400' + '0300040006000a00')
    parser = StructureReader(data, dict(s2=s2))
    parser.read_structure(s)
    assert isinstance(s.get_field_value('b'), list)
    b = s.get_field_value('b')
    assert len(b) == 3
    assert_ctype(b[0], ctypes.c_short, 2)
    assert_ctype(b[1], ctypes.c_short, 3)
    assert_ctype(b[2], ctypes.c_short, 4)
    c = s.get_field_value('c')
    assert c.name == 's2'
    assert c.get_value('a') == 3
    cb = c.get_field_value('b')
    assert_ctype(cb[0], ctypes.c_short, 4)
    assert_ctype(cb[1], ctypes.c_short, 6)
    assert_ctype(cb[2], ctypes.c_short, 10)
    assert not check_extra_buf(parser)


def test_complex_structure_reader():
    # [gg][65604] 2017/01/19 16:26:07
    # json_string = """{"gg_block_x":4,"gg_block_y":3,"gg_map_index":7,"players":[{"VIPLevel":0,"bonus_buff":[{"type":101,"value":9598}],"chenghao":255,"chengzhang":0,"country":0,"egg_type":0,"equip_info":{"equip_1":0,"equip_2":0,"equip_3":0,"num_1":0,"num_2":0,"num_3":0},"guild_index":0,"hp":1779,"hp_max":1779,"last_act_time":1484814367,"lingxing":0,"lingyun_star":0,"major":0,"major_plus":0,"model":500,"modelSize":10,"modelid":-1,"mp":0,"mp_max":0,"sex":1,"skill_num":0,"string_bonus_buff":null,"target_building_id":0,"teamnum":0,"type_id":-1,"user_id":2147482064,"username":"步兵","usertype":1,"version":4,"weapon":-1,"x":1831,"xianling_name":"","y":1031,"zizhi":0}]}"""
    origin_data = "01 00 00 00 D0 F9 FF 7F 27 07 00 00 07 04 00 00 1F 78 80 58 01 00 00 00 00 E6 AD A5 E5 85 B5 00 00 00 00 00 90 D0 8F 44 20 01 F3 06 00 00 F3 06 00 00 00 00 00 00 00 00 00 00 00 FF FF FF FF 00 00 00 FF F4 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FF FF FF FF 00 00 20 D0 8F 44 20 7F 00 00 3B 45 6F 00 00 00 00 04 00 0A FF FF FF FF 01 00 65 7E 25 00 00"
    hex_data = ''.join(x for x in origin_data.split(' '))
    bytes_data = binascii.a2b_hex(hex_data)
    csr = ComplexStructureReader()

    PushChangeMap = Structure('PushChangeMap')
    PushChangeMap.field_list.extend([
        Field(ctypes.c_int, 'num'),
        Field(('OtherPlayer', 'num'), 'other_player'),
    ])
    csr.add_structure(PushChangeMap)

    OtherPlayer = Structure('OtherPlayer')
    OtherPlayer.field_list.extend([
        Field(ctypes.c_int, 'user_id'),
        Field(ctypes.c_int, 'x'),
        Field(ctypes.c_int, 'y'),
        Field(ctypes.c_int, 'last_act_time'),
        Field(ctypes.c_byte, 'usertype'),
        Field(ctypes.c_int, 'target_building_id'),
        Field((ctypes.c_char, 16), 'username'),
        Field(ctypes.c_char, 'sex'),
        Field(ctypes.c_int, 'hp'),
        Field(ctypes.c_int, 'hp_max'),
        Field(ctypes.c_int, 'mp'),
        Field(ctypes.c_int, 'mp_max'),
        Field(ctypes.c_char, 'country'),
        Field(ctypes.c_int, 'weapon'),
        Field(ctypes.c_byte, 'major'),
        Field(ctypes.c_byte, 'major_plus'),
        Field(ctypes.c_byte, 'VIPLevel'),
        Field(ctypes.c_byte, 'chenghao'),
        Field(ctypes.c_int, 'model'),
        Field(ctypes.c_byte, 'teamnum'),
        Field(ctypes.c_int, 'guild_index'),
        Field('EquipInfos', 'equip_infos'),
        Field((ctypes.c_char, 40), 'guild_name'),
        Field('XianLingInfo', 'm_xianling'),
        Field(ctypes.c_byte, 'bonus_buff_num'),
        Field(ctypes.c_byte, 'string_bonus_buf_num'),
        Field(('BonusBuff', 'bonus_buff_num'), 'bonus_buff'),
        Field(('StringBonusBuff', 'string_bonus_buf_num'), 'string_bonus_buf'),
    ])
    csr.add_structure(OtherPlayer)

    BonusBuff = Structure('BonusBuff')
    BonusBuff.field_list.extend([
        Field(ctypes.c_byte, 'type'),
        Field(ctypes.c_int, 'value'),
    ])
    csr.add_structure(BonusBuff)

    StringBonusBuff = Structure('StringBonusBuff')
    StringBonusBuff.field_list.extend([
        Field(ctypes.c_byte, 'type'),
        Field(ctypes.c_byte, 'value_len'),
        Field((ctypes.c_char, 'value_len'), 'value'),
    ])
    csr.add_structure(StringBonusBuff)

    EquipInfos = Structure('EquipInfos')
    EquipInfos.field_list.extend([
        Field(ctypes.c_byte, 'equip_1'),
        Field(ctypes.c_byte, 'num_1'),
        Field(ctypes.c_byte, 'equip_2'),
        Field(ctypes.c_byte, 'num_2'),
        Field(ctypes.c_byte, 'equip_3'),
        Field(ctypes.c_byte, 'num_3'),
    ])
    csr.add_structure(EquipInfos)

    XianLingInfo = Structure('XianLingInfo')
    XianLingInfo.field_list.extend([
        Field(ctypes.c_byte, 'zizhi'),
        Field(ctypes.c_byte, 'chengzhang'),
        Field(ctypes.c_byte, 'lingxing'),
        Field(ctypes.c_byte, 'lingyun_star'),
        Field(ctypes.c_int, 'modelid'),
        Field((ctypes.c_char, 16), 'name'),
        Field(ctypes.c_byte, 'skill_num'),
        Field(ctypes.c_byte, 'version'),
        Field(ctypes.c_byte, 'egg_type'),
        Field(ctypes.c_byte, 'modelSize'),
        Field(ctypes.c_int, 'type_id'),
    ])
    csr.add_structure(XianLingInfo)

    # push_change_map, read_len = csr.parse(PushChangeMap, bytes_data=bytes_data)
    # assert read_len == len(bytes_data)
    push_change_map = csr.parse_entire(PushChangeMap, bytes_data=bytes_data)
    assert push_change_map.get_value('num') == 1
    other_player = push_change_map.get_field_value('other_player')
    assert len(other_player) == 1
    player = other_player[0]
    assert_ctype(player.get_field_value('VIPLevel'), ctypes.c_byte, 0)
    assert len(player.get_field_value('string_bonus_buf')) == 0
    bonus_buf = player.get_field_value('bonus_buff')
    assert len(bonus_buf) == player.get_value('bonus_buff_num') == 1
    # {"type":101,"value":9598}
    assert_ctype(bonus_buf[0].get_field_value('type'), ctypes.c_byte, 101)
    assert_ctype(bonus_buf[0].get_field_value('value'), ctypes.c_int, 9598)


import pytest

def test_is_absolute_simply_route():
    assert is_absolute_simply_route('')
    assert is_absolute_simply_route('a')
    assert is_absolute_simply_route('a.b')
    assert not is_absolute_simply_route('.')
    assert not is_absolute_simply_route('..')
    assert not is_absolute_simply_route('.a')
    assert not is_absolute_simply_route('a.')
    assert not is_absolute_simply_route('.a.b')
    assert not is_absolute_simply_route('a.b.')
    assert not is_absolute_simply_route('a..b')


def test_absolute_route_to_route_list():
    assert absolute_route_to_route_list('') == []
    assert absolute_route_to_route_list('a') == ['a']
    assert absolute_route_to_route_list('a.b') == ['a', 'b']
    assert absolute_route_to_route_list('.a') == ['', 'a']
    assert absolute_route_to_route_list('a.') == ['a', '']
    assert absolute_route_to_route_list('a.b') == ['a', 'b']
    assert absolute_route_to_route_list('a.b.') == ['a', 'b', '']


def test_add_route():
    assert add_route('', '.') == ''
    assert add_route('', '.a') == 'a'
    assert add_route('', '.a.b') == 'a.b'
    with pytest.raises(UntreatedError) as excinfo:
        add_route('', '..')
    with pytest.raises(UntreatedError) as excinfo:
        add_route('', '..a')

    assert add_route('a', '.') == 'a'
    assert add_route('a', '.a') == 'a.a'
    assert add_route('a', '.a.b') == 'a.a.b'
    assert add_route('a', '..') == ''
    assert add_route('a', '..b') == 'b'
    with pytest.raises(UntreatedError) as excinfo:
        add_route('a', '...')
    with pytest.raises(UntreatedError) as excinfo:
        add_route('a', '...a')

    assert add_route('a.b', '.') == 'a.b'
    assert add_route('a.b', '.a') == 'a.b.a'
    assert add_route('a.b', '.a.b') == 'a.b.a.b'
    assert add_route('a.b', '..') == 'a'
    assert add_route('a.b', '..c') == 'a.c'
    assert add_route('a.b', '...') == ''
    assert add_route('a.b', '...c') == 'c'
    with pytest.raises(UntreatedError) as excinfo:
        add_route('a.b', '....')
    with pytest.raises(UntreatedError) as excinfo:
        add_route('a.b', '....a')


def test_namespace():
    csr = ComplexStructureReader()

    Parent = Structure('Parent')
    Parent.field_list.extend([
        Field(ctypes.c_int, 'a'),
        Field('Child', 'child'),
        Field('Brother', 'brother'),
    ])
    csr.add_structure(Parent)

    Child = Structure('Child')
    Child.namespace = 'Parent'
    Child.field_list.extend([
        Field(ctypes.c_int, 'ca'),
    ])
    csr.add_structure(Child)

    Brother = Structure('Brother')
    Brother.field_list.extend([
        Field(ctypes.c_int, 'ba'),
    ])
    csr.add_structure(Brother)
    bytes_data = binascii.b2a_hex(b'010000000200000003000000')
    csr.parse(Parent, bytes_data)


def test_get_bytes_from_list():
    list_ = [
        ctypes.c_char(b'2'),
        ctypes.c_byte(0x33),
        ctypes.c_byte(0x33),
        ctypes.c_byte(0),
        ctypes.c_byte(0x33),
        ctypes.c_byte(0x33),
    ]

    assert get_bytes_from_list(list_) == b'233'
