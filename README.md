一个用于序列化和反序列化C/C++结构体的模块

注意: 目前只实现了反序列化

序列化是按照C/C++的结构体在内存中的存储方式, 使用小端+pack(1)模式进行的, 一个典型的应用是 结构体 ==> 网络数据 ==> 结构体

不仅支持标准C/C++结构体, 还支持可变长结构体, 比如

	struct A
	{
		int a;
		int b[a];
	}
	这个A包含一个int型的a, 以及一个长度为a的int型数组b


本模块不能直接读取C/C++代码中的结构体, 需要事先把结构体转成本模块中的structure对象.(可以使用我开发的另外一个模块gen_code_for_structure_reader, 自动从C/C++代码中读取结构体,转换成structure)

与python struct模块的区别:

	优点:

		struct.unpack/pack接口输出/输入的是一个元组, 需要程序员自行拆分/组合元组, 而structure_reader反序列化后, 是以python对象的方式存储的,具有自省能力
		struct没有对结构体嵌套进行相关处理, structure_reader可以随意嵌套(当然不能递归嵌套自己!)

	确定:

		structure_reader需要事先生成供内部使用的structure对象才能使用. 如果你只有少量的结构体, 建议你手动书写代码. 另外可以用我写的另外一个模块gen_code_for_structure_reader来批量生成代码, 但是配置方面会复杂一些.




A module for serializing and deserializing C / C ++ structures

Note: Currently only deserialization is achieved

Serialization is in accordance with the C / C + + structure in memory storage, small ending and pack(1) mode. a typical usage is c structure ==> network data ==> c structure

Not only supports standard C / C ++ structures, but also supports variable-length structures, such as

	struct A
	{
		int a;
		int b [a];
	}
	A contains an int type a, and an int array b of length a

This module can not directly read the structure of the C / C ++ code, it is necessary to transform the c/c++ structure into the structure object in the module in advance. (You can use the other module gen_code_for_structure_reader that I developed to automatically read the structure from C / C ++ code And converted into structure)

Differences from python builtin struct modules:

	Advantages:

		Struct.unpack / pack interface's output / input is a tuple, rogrammers needs to split / combination tuple, while structure_reader's deserialization output is a python objects with self-exploration ability
		Struct doesn't support nesting structure, while structure_reader do.(of course, can not recursively nest!)

	Disadvantages:

		you needs to generate a structure_reader structure in advance before using structure_reader. If you have only a few structure, I suggests generate code manually. Another choice is to use another module i wrote "gen_code_for_structure_reader", but it'll be a little complex.
