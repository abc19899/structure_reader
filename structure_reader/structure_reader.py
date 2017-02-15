# encoding=utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = '1661'
import copy


class UntreatedError(Exception):
    def __init__(self, *args, **kwargs):
        super(UntreatedError, self).__init__(*args, **kwargs)


class Type(object):
    def __init__(self, type_):
        """

        有四个属性 array_size, is_pointer, array_mutable_size, base_type
        array_size = 0 表示不是一个数组, >0 是一个定长数组, = -1 为不定长数组, 此时数组长度有array_mutable_size决定
        is_pointer为一个指针
        array_mutable_size: 当array_size为-1,, array_mutable_size存放当前命名空间的一个变量的名字,
            该变量的值即为数组的长度
        base_type: 基本类型, 如int, int *, int [3], int [item_number] 的基本类型都是int

        :param type_: ctypes or a tuple in form of (ctypes, number_or_name)
        number_or_name命名空间规则使用C语言命名空间规则, 即
            1. 命名空间使用 :: 来分割, 分割后的各个name记作 name0, name1, ...
            2. 以::开头表示从根命名空间开始查找, 否则从当前命名空间开始查找第一个, 如果当前命名空间下不存在name0,
                则从当前命名空间的上一层查找name0, 依次类推, 直至从根命名空间开始查找
            3. 确定好起始命名空间之后, 在起始命名空间下查找 name1, 找到后, 在name1空间下查找name2...
        """
        if isinstance(type_, tuple):
            type_, number_or_name = type_
        else:
            number_or_name = None

        # todo: pointer not implemented
        self.is_pointer = False
        if number_or_name is not None:
            from .py23 import number_type_list
            if isinstance(number_or_name, number_type_list):
                self.array_size = number_or_name
                self.array_mutable_size = ''
            else:
                self.array_size = -1
                self.array_mutable_size = number_or_name
        else:
            self.array_size = 0
            self.array_mutable_size = ''

        self.base_type = type_

    def __str__(self):
        if self.is_pointer:
            return 'pointer(%s)' % self.base_type
        elif self.array_size > 0:
            return 'array[%d](%s)' % (self.array_size, self.base_type)
        elif self.array_size == -1:
            return 'array[?=%s](%s)' % (self.array_mutable_size, self.base_type)
        else:
            return 'obj(%s)' % self.base_type


class Field(object):
    def __init__(self, type_, name, value=None):
        self.type = type_  # Type类型
        self.name = name  # str类型
        self.value = value  # 当Type为数组是, value为list, 否则为该field的值


class Structure(object):
    def __init__(self, name='', namespace=''):
        self.name = name
        self.namespace = namespace
        self.field_list = list()  # 成员为Field

    def __str__(self):
        return ' '.join(['%s(%s)' % (i.name, str(i.value)) for i in self.field_list])

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.name)

    def dump(self, outfile, indent=' ', max_depth=-1):
        if max_depth == 0:
            return
        for i in self.field_list:
            outfile.write('%s(' % i.name)
            if isinstance(i.value, Structure):
                i.value.dump(outfile, indent, max_depth - 1)
            elif isinstance(i.value, list):
                outfile.write('[')
                for one in i.value:
                    if isinstance(one, Structure):
                        one.dump(outfile, indent, max_depth - 1)
                    else:
                        outfile.write(str(one))
                    outfile.write(',')
                outfile.write(']')
            else:
                outfile.write(str(i.value))
            outfile.write(')%s' % indent)

    def get_value(self, key):
        for i in self.field_list:
            if key == i.name:
                return i.value.value
        raise KeyError('key(%s) not found in structure(%s)' % (key, self.name))

    def get_field_value(self, key):
        for i in self.field_list:
            if key == i.name:
                return i.value
        raise KeyError('key(%s) not found in structure(%s)' % (key, self.name))


def is_absolute_simply_route(route):
    if not route:
        return True

    route_list = route.split('.')
    for i in route_list:
        if not i:
            return False

    return True


def absolute_route_to_route_list(route):
    if route:
        route_tuple = route.split('.')
    else:
        route_tuple = tuple()

    return list(route_tuple)


def add_route(route0, route1):
    if not is_absolute_simply_route(route0):
        raise UntreatedError("route0 should be absolute")
    route_list0 = absolute_route_to_route_list(route0)

    dot_num = 0
    for index, i in enumerate(route1):
        if i == '.':
            dot_num += 1
        else:
            to_add_route = route1[index:]
            break
    else:
        to_add_route = ''

    if dot_num == 0:
        raise UntreatedError('route1 should be relative')

    if len(route_list0) < dot_num - 1:
        raise UntreatedError('route0 go beyond top')

    route_list0 = route_list0[:len(route_list0) - (dot_num - 1)]
    route2 = '.'.join(route_list0)

    if route2 and to_add_route:
        route2 += '.' + to_add_route
    else:
        route2 = route2 or to_add_route

    return route2


class Namespace(object):
    def __init__(self, class_=None, sub_namespace=None, root_namespace=None, route=''):
        self.class_ = class_
        self.route = route
        self.sub_namespace = sub_namespace
        self.root_namespace = root_namespace
        if self.sub_namespace is None:
            self.sub_namespace = dict()

    def find_namespace_from_root(self, route):
        """
        if raise KeyError, means route is error
        """
        if not is_absolute_simply_route(route):
            raise UntreatedError("route should not be relative")
        ns = self.root_namespace or RootNamespace
        current_route_list = list()
        for route_one in absolute_route_to_route_list(route):
            current_route_list.append(route_one)
            try:
                ns = ns.sub_namespace[route_one]
            except KeyError:
                return None
                # raise KeyError("route(%s) not exists at %s" % (route, '.'.join(current_route_list)))

        return ns

    def find_or_create_namespace_from_root(self, route):
        """
        if raise KeyError, means route is error
        """
        if not is_absolute_simply_route(route):
            raise UntreatedError("route should not be relative")
        ns = self.root_namespace or RootNamespace
        current_route_list = list()
        for route_one in absolute_route_to_route_list(route):
            current_route_list.append(route_one)
            if route_one in ns.sub_namespace:
                ns = ns.sub_namespace[route_one]
            else:
                new_ns = Namespace()
                self.bind_sub_namespace(route_one, new_ns)
                ns = new_ns

        return ns

    def bind_sub_namespace(self, namespace_route_last, namespace):
        if namespace_route_last in self.sub_namespace:
            raise UntreatedError('already exists sub namespace(%s) at %s' % (namespace_route_last, self.route))
        if namespace.sub_namespace:
            raise UntreatedError("namespace(%s) have children, are you sure to bind?" % namespace_route_last)

        namespace.route = add_route(self.route, '.' + namespace_route_last)
        self.sub_namespace[namespace_route_last] = namespace
        namespace.root_namespace = self.root_namespace

    def find_namespace_by_name_till_top(self, name):
        ns = self
        while True:
            try:
                return ns.sub_namespace[name]
            except KeyError:
                if not ns.route:
                    return None
                parent_route = add_route(ns.route, '..')
                ns = self.find_namespace_from_root(parent_route)

                # route_piece = ns.route.rsplit('.', 1)
                # if len(route_piece) == 1:
                #     ns = ns.root_namespace or RootNamespace
                # else:
                #     ns = ns.find_namespace_from_root(route_piece[0])

    def find_namespace(self, route):
        absolute_route = add_route(self.route, route)
        return self.find_namespace_from_root(absolute_route)


RootNamespace = Namespace()


class Ctx(object):
    def __init__(self, structure_dict=None, namespace=None):
        self.namespace = namespace or RootNamespace
        if isinstance(structure_dict, dict):
            for structure in structure_dict:
                # self.namespace.sub_namespace[k] = Namespace(v)
                self.add_structure_def(structure)
        else:
            # self.structure_dict_ = dict()  # key: string => namespace name, value: [structure, sub_structure_dict()]
            pass

    # @property
    # def structure_dict(self):
    #     return self.namespace.sub_namespace

    def add_structure_def(self, structure):
        if isinstance(structure, Structure):
            namespace = structure.namespace
            if not is_absolute_simply_route(namespace):
                raise UntreatedError("structure(%s) namespace(%s) is relative above top" % (
                    structure.name, structure.namespace))

            namespace_obj = self.namespace.find_or_create_namespace_from_root(
                add_route(self.namespace.route, '.' + namespace))

            if structure.name not in namespace_obj.sub_namespace:
                # namespace_obj.sub_namespace[structure.name] = Namespace(structure)
                namespace_obj.bind_sub_namespace(structure.name, Namespace(structure))
            else:
                this_namespace_obj = namespace_obj.sub_namespace[structure.name]
                if this_namespace_obj.class_ is not None:
                    raise UntreatedError('duplicate structure name(%s) at namespace(%s)' % (
                        structure.name, namespace))
                else:
                    this_namespace_obj.class_ = structure
        else:
            raise UntreatedError('%s is not a Structure type' % (str(structure)))


class TypeLength(object):
    _type_name_to_len = dict()

    @classmethod
    def register_type_len(cls, type_name, len_):
        if type_name in cls._type_name_to_len:
            if cls._type_name_to_len[type_name] != len_:
                raise KeyError('type(%s)(%d) is already registered with another value(%d)' % (
                    type_name, len_, cls._type_name_to_len[type_name]
                ))
        cls._type_name_to_len[type_name] = len_

    @classmethod
    def get_type_len(cls, type_name):
        if type_name in valid_ctype_list:
            return ctypes.sizeof(type_name)
        try:
            return cls._type_name_to_len[type_name]
        except KeyError:
            raise KeyError('type(%s) is not registered' % type_name)


import ctypes


def pack(ctype_instance):
    buf = ctypes.string_at(ctypes.byref(ctype_instance), ctypes.sizeof(ctype_instance))
    return buf


def unpack(ctype, buf):
    """ if buf is not long enough, will fixup
    :param ctype:
    :param buf:
    :return:
    """
    cstring = ctypes.create_string_buffer(buf)
    ctype_instance = ctypes.cast(ctypes.pointer(cstring), ctypes.POINTER(ctype)).contents
    return ctype_instance


valid_ctype_match_list = [
    (ctypes.c_ushort, ('SHORT', 'unsigned short'), ),
    (ctypes.c_short, ('short', ), ),
    (ctypes.c_byte, ('byte', 'signed byte'), ),
    (ctypes.c_ubyte, ('unsigned byte', 'BYTE', ), ),
    (ctypes.c_char, ('char', 'signed char'), ),
    (ctypes.c_wchar, ('w_char', ), ),
    (ctypes.c_int, ('int', 'signed int', ), ),
    (ctypes.c_uint, ('unsigned int', ), ),
    (ctypes.c_longlong, ('long long', 'signed long long', ), ),
    (ctypes.c_ulonglong, ('unsigned long long', ), ),
    (ctypes.c_double, ('double', 'double float', ), ),
    (ctypes.c_float, ('float', ), ),
    (ctypes.c_bool, ('bool', ))
]

valid_ctype_list = list(x[0] for x in valid_ctype_match_list)


class StructureReader(object):
    def __init__(self, data, namespace_or_structure_dict):
        self.data = data
        self.pos = 0
        # self.op_to_structure_dict = op_to_structure_dict
        if isinstance(namespace_or_structure_dict, dict):
            self.namespace = RootNamespace
            for structure_name, structure in namespace_or_structure_dict.items():
                # self.namespace.sub_namespace[structure_name] = Namespace(structure)
                self.namespace.bind_sub_namespace(structure_name, Namespace(structure))
        elif isinstance(namespace_or_structure_dict, Namespace):
            self.namespace = namespace_or_structure_dict
        else:
            raise UntreatedError("error namespace_or_structure_dict type(%s), expect %s or %s" % (
                type(namespace_or_structure_dict), dict, Namespace
            ))
        # self.structure_name_dict = structure_name_dict
        # if outfile:
        #     self.outfile = outfile
        # else:
        #     self.outfile = sys.stdout
        self.debug_info = dict()

    def read_base_type(self, type_):
        value = self.peek_base_type(type_)
        self.pos += TypeLength.get_type_len(type_)
        return value

    def peek_base_type(self, type_):
        if type_ in valid_ctype_list:
            if len(self.data) < self.pos + ctypes.sizeof(type_):
                raise IndexError('buf not long enough, now in (%s/%s), need %s' % (
                    self.pos, len(self.data), ctypes.sizeof(type_)))

            v = unpack(type_, self.data[self.pos: self.pos + ctypes.sizeof(type_)])
            return v
        else:
            raise UntreatedError('invalid type(%s)' % type_)

    def read_sub_structure(self, structure_namespace_name_c_style, now_namespace):
        bak_to_find, bak_find_from = structure_namespace_name_c_style, now_namespace
        if structure_namespace_name_c_style.startswith('::'):
            absolute_route = structure_namespace_name_c_style.split('::')
            del absolute_route[0]
            now_namespace = now_namespace.find_namespace_from_root('.'.join(absolute_route))
        else:
            top_name = structure_namespace_name_c_style.split('::', 1)[0]
            now_namespace = now_namespace.find_namespace_by_name_till_top(top_name)
            if now_namespace is None:
                raise UntreatedError("don't find type(%s) at namespace(%s), find first fail" % (
                    bak_to_find, bak_find_from))
            rest_to_find = structure_namespace_name_c_style.split('::')[1:]

            if rest_to_find:
                rest_to_find.insert(0, '')
                relative_route = '.'.join(rest_to_find)
                now_namespace = now_namespace.find_namespace(relative_route)
            else:
                pass  # use now_namespace
        if now_namespace is None:
            raise UntreatedError("don't find type(%s) at namespace(%s), find first but following fail" % (
                bak_to_find, bak_find_from))

        this_structure = copy.deepcopy(now_namespace.class_)
        self.read_structure(this_structure, now_namespace)
        return this_structure

    def read_structure(self, structure, namespace=None):
        """从self.data中按照obj的格式读出一个obj, 给obj中成员中的c复制
        """
        if namespace is None:
            namespace = self.namespace.find_namespace('.' + structure.name)
            if namespace is None:
                raise UntreatedError("don't find sub namespace(%s) from namespace(%s)" % (
                    structure.name, self.namespace.route
                ))
        self.debug_info.setdefault('sub_structure', []).append(add_route(namespace.route, '.' + structure.name))
        for field in structure.field_list:
            self.debug_info.setdefault('field', []).append(field.name)
            type_ = field.type
            styled_type = Type(type_)
            if styled_type.is_pointer:
                field.value = self.read_base_type('pointer')
            elif styled_type.array_size != 0:
                if styled_type.array_size > 0:
                    real_size = styled_type.array_size
                else:
                    real_size = structure.get_value(styled_type.array_mutable_size)
                field.value = list()
                for k in range(real_size):
                    try:
                        value = self.read_base_type(styled_type.base_type)
                    except UntreatedError:
                        value = self.read_sub_structure(styled_type.base_type, namespace)
                    field.value.append(value)
            else:
                try:
                    value = self.read_base_type(styled_type.base_type)
                except UntreatedError:
                    value = self.read_sub_structure(styled_type.base_type, namespace)
                field.value = value


class ComplexStructureReader(object):
    def __init__(self, bytes_data=None, ctx=None):
        self.bytes_data = bytes_data
        self.ctx = ctx or Ctx()

    def add_structure(self, structure):
        self.ctx.add_structure_def(structure)

    def parse_entire(self, sample_structure, bytes_data=None):
        structure, pos = self.parse(sample_structure=sample_structure, bytes_data=bytes_data)
        assert pos == len(self.bytes_data)
        return structure

    def parse(self, sample_structure, bytes_data=None):
        """parse a structure with a sample structure from bytes_data

        :param sample_structure: the structure to parse with,
        it will NOT be modified because inner with use a copy to parse
        :param bytes_data: the bytes_data to parse from.
        if bytes_data is already set at __init__, it's no need to set again
        :return: tuple(structure, pos)
        structure: a structure copy from begin_structure while it's data is parsed from bytes_data
        pos: already parsed data len of bytes_data
        """
        if bytes_data is not None:
            self.bytes_data = bytes_data
        if self.bytes_data is None:
            raise ValueError('bytes_data is not set')

        reader = StructureReader(self.bytes_data, self.ctx.namespace)
        import copy
        structure = copy.deepcopy(sample_structure)
        reader.read_structure(structure)
        # print(reader.debug_info)
        return structure, reader.pos


def get_bytes_from_list(ctypes_inst_list):
    """ 把一个单字节的数组连起来, 当成char *来读取字符串
    """
    len_ = len(ctypes_inst_list)
    buf = ctypes.create_string_buffer(len_)

    offset = 0
    for ctypes_ins in ctypes_inst_list:
        this_size = ctypes.sizeof(ctypes_ins)
        assert offset + this_size <= len_
        ctypes.memmove(ctypes.addressof(buf) + offset, ctypes.addressof(ctypes_ins), this_size)
        offset += this_size

    assert offset == len_

    return buf.value
