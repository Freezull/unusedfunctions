import glob
import re
import pathlib

#folder_pathh = "C:\\Users\\E1432180\\Desktop\\SECMono_02\\Source\\"
#folder_path = str(pathlib.Path().resolve()).replace('\\', "\\\\")+"\\\\"
folder_path = str(pathlib.Path().resolve())+"\\"
regex_for_scopes = r"[ \t]*\([a-zA-Z0-9_\[\]\n\t ,.()&:=|/+\-<>\*!?]*\)"
regex_for_functions = r"\n[\ta-zA-Z _*0-9]+\([a-zA-Z0-9_\[\]\n\t ,.()\*]+\)[ \t]*[\n]?[ \t]*{"

accepted_file_types = ["h", "c"]
dir_path = folder_path + r'*.[' + "".join(accepted_file_types) + ']'
excludes = ["struct", "if", "switch", "defined", "define", "else", "while", "for"]


def get_functions(files):
    all_functions = []
    for file in files:
        f = open(file, "r")
        lines = f.readlines()
        f.close()
        text = "".join(lines)
        functions = re.finditer(regex_for_functions, text)
        for function in functions:
            name = function.group().split("(")[0].split(" ")
            if type(name) is list:
                while name[-1] == "" and len(name) > 1:
                    name.pop()
            name = name[-1]
            if name not in excludes and name != "" and name.find("DecTree") == -1:
                all_functions.append([function.group().split(")")[0] + ")", [function.span(), file]])
    return all_functions


def get_includes(files):
    all_includes_by_module = {}
    file_names = [f.split("\\")[-1] for f in files]
    for file in files:
        f = open(file, "r")
        lines = f.readlines()
        f.close()
        text = "".join(lines)
        includes = re.findall(r'#include[ ]*["<][a-zA-Z._0-9]+[">]', text)
        file_name = file.split("\\")[-1]
        all_includes_by_module[file_name] = [file_name]
        for include in includes:
            if include.find('"') != -1:
                name = include.split('"')[1]
            else:
                name = include.split("<")[-1].split(">")[0]
            if name in file_names:
                if include.find('"') == -1:
                    print("use \"\" instead of <> for including local modules, file:", file_name, "value:", include)
                all_includes_by_module[file_name].append(name)
    return all_includes_by_module


def get_scope(file, include_map):
    output = []
    stack = []
    for k, v in include_map.items():
        if file in v:
            stack.append(k)
            output.append(k)

    while len(stack) > 0:
        value = stack[0]
        if value not in output:
            output.append(value)
        stack.pop(0)
        for k, v in include_map.items():
            if value in v:
                if k not in output:
                    stack.append(k)
    return output


def find_functions(files, functions):
    output = {}
    for function in functions:
        for file in files:
            f = open(file, "r")
            text = "".join(f.readlines())
            f.close()
            try:
                functions = re.finditer(
                    function.replace("(", "\(").replace(")", "\)").replace("]", "\]").replace("[", "\[").replace("_",
                                                                                                                 "\_") + ";",
                    text)
                lenght = 0
                value = None
                for el in functions:
                    lenght += 1
                    value = el
                if lenght > 1:
                    print("Multiple times declared in", file, "this :", function)
                else:
                    if lenght == 1:
                        if file in output:
                            output[file].append(value)
                        else:
                            output[file] = [value]
            except:
                print("ERROR with", file, function)
    return output


def check_cross(a, b):
    x1 = a[0]
    y1 = a[1]
    x2 = b[0]
    y2 = b[1]
    if x2 < x1 < y2 or x2 < y1 < y2 or x1 < x2 < y1 or x1 < y2 < y1:
        return True
    return False


def find_calls(current_file, files, function, exception):
    calls = {}
    name = function.group().split("(")[0].split(" ")[-1]
    for file in files + [current_file]:
        f = open(file, "r")
        text = "".join(f.readlines())
        f.close()
        try:
            functions = re.finditer(name.replace("_", "\_") + regex_for_scopes, text)
            for ff in functions:
                # do not check declaration
                if (file != current_file or check_cross(function.span(), ff.span()) is False) and\
                        (file != exception[1] or check_cross(ff.span(), exception[0]) is False):    # do not check definition
                    if name not in calls:
                        calls[name] = [file]
                    else:
                        calls[name].append(file)
        except:
            print("ERROR with", file, function)
    return calls


all_functions = get_functions(glob.glob(dir_path))
all_includes = get_includes(glob.glob(dir_path))
all_mapped_functions = find_functions(glob.glob(dir_path), [x[0] for x in all_functions])
all_file_scopes = {}

#  file = open("input.txt", "r")
#  all_mapped_functions = eval(file.read())
#  file.close()

for file in glob.glob(dir_path):
    all_file_scopes[file] = get_scope(file.split("\\")[-1], all_includes)

for file, v in all_mapped_functions.items():
    for func in v:
        scopes = [folder_path + x for x in all_file_scopes[file]]
        exception = [None, None]
        for vect in all_functions:
            name0 = vect[0].split("(")[0].split(" ")[-1]
            name1 = func.group().split("(")[0].split(" ")[-1]
            if name0 == name1:
                exception = vect[1]
        search = find_calls(file, scopes, func, exception)
        if len(search) == 0:
            print(file, ":", func.group().replace("\n", ""))
