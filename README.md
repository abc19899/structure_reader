一个用于序列化和反序列化C/C++结构体的模块

注意: 目前只实现了反序列化

序列化是按照C/C++的结构体在内存中的存储方式, 使用小端+pack(1)模式进行的, 一个典型的应用是 结构体 ==> 网络数据 ==> 结构体


本模块不能直接读取C/C++代码中的结构体, 需要事先把结构体转成本模块中的structure对象.(可以使用我开发的另外一个模块gen_code_for_structure_reader, 自动从C/C++代码中读取结构体,转换成structure)


A module for serializing and deserializing C / C ++ structures

Note: Currently only deserialization is achieved

Serialization is in accordance with the C / C + + structure in memory storage, small ending and pack(1) mode. a typical usage is c structure ==> network data ==> c structure

This module can not directly read the structure of the C / C ++ code, it is necessary to transform the c/c++ structure into the structure object in the module in advance. (You can use the other module gen_code_for_structure_reader that I developed to automatically read the structure from C / C ++ code And converted into structure)
