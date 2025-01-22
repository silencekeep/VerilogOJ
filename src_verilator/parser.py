from __future__ import absolute_import
from __future__ import print_function
#from pprint import pprint
import sys
import os
from optparse import OptionParser

import pyverilog
from pyverilog.vparser.parser import parse
import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

#生活不易，代码爹求你一定好好跑起来啊
def traverse_ast(ast, typex, x):
    # find module def
    for c in ast.children():
        traverse_ast(c, typex, x)
    if ast.__class__.__name__ == typex:
        x.append(ast)
    return x

""" def print_object_members(obj):
    # Get all members of the object
    members = dir(obj)
    #pprint(members)
    for member in members:
        # Skip built-in methods and special attributes
        if member.startswith('__'):
            continue
        
        try:
            value = getattr(obj, member)
            pprint(f"{member}: {value}")
        except AttributeError:
            pprint(f"{member} not accessible") """

def convert_ports_to_ansi(module_def):
    ports = []
    items_to_remove = []
    portlist = module_def.portlist.ports
    port_names = set()
    for port in portlist:
        #此处注释是对Python/Python312/site-packages/pyverilog/vparser/ast.py下的结构分析后的结果
        #它内部的结构是复杂的继承关系 比如Wire->Variable->Value->Node

        #打印类型的函数
        #pprint(port)#<pyverilog.vparser.ast.Ioport object at 0x00000178B4BF1280>
        #pprint(port.first)#<pyverilog.vparser.ast.Input object at 0x00000178B4BF0DD0>
        #pprint(port.second)#<pyverilog.vparser.ast.Wire object at 0x00000178B4BF0470>
        #pprint(port.lineno)#int

        #pprint(dir(port))
        #class Wire(Variable)
        #class Variable(Value): def __init__(self, name, width=None, signed=False, dimensions=None, value=None, lineno=0):
        #class Value(Node): def __init__(self, value, lineno=0):

        #class Ioport(Node): def __init__(self, first, second=None, lineno=0):
        first = port.first if port.first is not None else pyverilog.vparser.ast.Inout(pyverilog.vparser.ast.Variable('<<unk_name?>>'))
        second = port.second if port.second is not None else pyverilog.vparser.ast.Wire(pyverilog.vparser.ast.Variable('<<unk_name?>>'))
        port = pyverilog.vparser.ast.Ioport(first=first, second=second, lineno=port.lineno)
        if port.first is not None: port_names.add(port.first.name)

        ports.append(port)
        #if isinstance(ioitem, vast.Ioport):
    new_portlist = vast.Portlist(tuple(ports))
    module_def.portlist = new_portlist

    #pprint(port_names)

    for item in module_def.items:
        if isinstance(item, (vast.Wire, vast.Reg)):
            for signal in item.list:
                if signal.name in port_names:
                    items_to_remove.append(signal)
    
    module_def.items = [item for item in module_def.items 
                        if not any(signal.name in port_names for signal in getattr(item, 'list', []))]

def main():
    optparser = OptionParser()
    (options, args) = optparser.parse_args()
    #args = ['C:\\Users\\56279\\Desktop\\prj-ansi\\src\\non_ansi.v']
    filelist = args
    for f in filelist:
        if not os.path.exists(f):
            raise IOError("file not found: " + f)

    ast, directives = parse(filelist)

    # Traverse the AST to find all ModuleDefs
    modules = traverse_ast(ast, "ModuleDef", [])

    # 逐个模块转换
    for module in modules:
        convert_ports_to_ansi(module)

    # 再产生代码
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    print(rslt)


if __name__ == '__main__':
    iverilog_home = '填入iverilog的路径/已有全局PATH的不用填'#C:\\Users\\56279\\Desktop\\i-verilog-assistant\\packed\\2022a\\iverilogAssistant\\iverilog\\bin'  # 根据你的安装路径进行调整
    os.environ['PATH'] = iverilog_home
    main()
