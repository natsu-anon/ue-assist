import os
import sys
import getopt
import configparser
import json
import re

usage = """ue-assist is a small set of scripts to accelerate unreal development on Windows.
NOTE: You have to change config.ini to work on your machine.
NOTE: Add its directory to your path so you can call it from anywhere.
NOTE: Only touch the templates if you KNOW what you're doing.

Usage

  ue-assist [options]

Options
  -p <name> [<directory>] = Creates a project with given name in given directory
                            if directory is not given creates a project in the
                            current directory.
                            - <name> can only be letters.
                            - <directory> must be empty.
  -c <origin> <target>    = Parses origin file for compilation commands and
                            outputs to target.  NOTE: called by generate.bat
                            to make compile_commands.json for the lsp server.
  -v                      = Prints the version & licensing information.
  -h                      = Prints usage information.
"""

def main(cli_args):
    try:
        opts, args = getopt.getopt(cli_args[1:], 'hvp:c')
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(1)
    for o, a in opts:
        if o == '-p':
            if not a.isalpha():
                print("Project names can only be alphabetic characters!")
                sys.exit(1)
            sd = os.path.dirname(os.path.realpath(cli_args[0]))
            if len(args) == 0:
                createProject(sd, a)
            else:
                createProject(sd, a, os.path.realpath(args[0]))
            sys.exit(0)
        elif o == '-c':
            if len(args) != 2:
                usage()
                sys.exit(1)
            else:
                compilationDatabase(args[0], args[1])
                sys.exit(0)
        elif o == '-h':
            print(usage)
            sys.exit(0)
        if o == '-v':
            print('ue-assist 1.0.0, licensed WTFPLv2')
            sys.exit(0)
    print("unrecognized command, run 'ue-assist -h' for usage")
    sys.exit(1)

def createProject(sDir, pName, pPath=os.getcwd()):
    if not os.path.exists(pPath):
        os.makedirs(pPath)
    elif len(os.listdir(pPath)) > 0:
        print("directory is not empty!  Please give a path to a non-existant or empty directory to create an Unreal project")
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(os.path.join(sDir, "config.ini"))
    copyBatchfiles(sDir, pPath, pName, config)
    print("Creating project: {}".format(pName))
    print('Batch files created!')
    rwReplace(os.path.join(sDir, "templates\\gitignore"), os.path.join(pPath, ".gitignore"), lambda s : s)
    print('.gitignore created!')
    initProject(sDir, pPath, pName, config)
    print('Project created!')
    print("Run 'git init .' for version control")

def copyBatchfiles(sDir, pPath, pName, config):
    replaceName = lambda s: s.replace('PROJECT', pName)
    def temp(s):
        s = s.replace("CONFIG_BUILD_BAT", config['Paths']['build_bat'])
        s = s.replace("CONFIG_UBT_EXE", config['Paths']['ubt_exe'])
        s = s.replace("CONFIG_UE5EDITOR_EXE", config['Paths']['editor_exe'])
        return s
    rwReplace(os.path.join(sDir, "templates\\batch_vars"), os.path.join(pPath, "batch_vars.bat"), temp)
    rwReplace(os.path.join(sDir, "templates\\editor"), os.path.join(pPath, 'editor.bat'), replaceName)
    rwReplace(os.path.join(sDir, "templates\\build"), os.path.join(pPath, "build.bat"), replaceName)
    rwReplace(os.path.join(sDir, "templates\\generate"), os.path.join(pPath, 'generate.bat'), replaceName)

def initProject(sDir, pPath, pName, config):
    module_path = os.path.join(pPath, 'Source\\{}\\'.format(pName))
    publicPath = os.path.join(module_path, 'Public\\')
    privatePath = os.path.join(module_path, 'Private\\')
    os.makedirs(publicPath)
    os.makedirs(privatePath)
    replaceName = lambda s: s.replace('PROJECT', pName)
    def temp(s):
        s = replaceName(s)
        s = s.replace("VERSION", config['Settings']['unreal_version'])
        return s
    rwReplace(os.path.join(sDir, "templates\\uproject"), os.path.join(pPath, "{}.uproject".format(pName)), temp)
    def temp(s):
        s = replaceName(s)
        s = s.replace("ASSOCIATION", config['Settings']['unreal_association'])
        return s
    rwReplace(os.path.join(sDir, "templates\\Editor.Target"), os.path.join(pPath, "Source\\{}Editor.Target.cs".format(pName)), temp)
    rwReplace(os.path.join(sDir, "templates\\Game.Target"), os.path.join(pPath, "Source\\{}.Target.cs".format(pName)), temp)
    rwReplace(os.path.join(sDir, "templates\\Project.Build"), os.path.join(module_path, "{}.Build.cs".format(pName)), replaceName)
    rwReplace(os.path.join(sDir, "templates\\Project.source"), os.path.join(module_path, "{}.cpp".format(pName)), replaceName)
    rwReplace(os.path.join(sDir, "templates\\Project.header"), os.path.join(module_path, "{}.h".format(pName)), lambda s: s) # lol lomao even
    rwReplace(os.path.join(sDir, "templates\\GameModeBase.header"), os.path.join(module_path, "{}GameModeBase.h".format(pName)), lambda s: s.replace('PROJECT', pName.upper()))
    rwReplace(os.path.join(sDir, "templates\\GameModeBase.source"), os.path.join(module_path, "{}GameModeBase.cpp".format(pName)), replaceName)

def rwReplace(origin, destination, fn):
    with open(origin, 'r') as f:
        temp = f.read()
    temp = fn(temp)
    with open(destination, 'w') as f:
        f.write(temp)

def compilationDatabase(vscodeFilename, targetFilename):
    j = json.load(open(vscodeFilename))
    pattern = re.compile(".+?~$") # skip emacs backup files
    for i in range(len(j) - 1, -1, -1):
        src = j[i]["file"]
        if pattern.match(src):
            j.pop(i)
            continue
        args = j[i]["arguments"]
        j[i]["arguments"] = [ args[0],
                             "/std:c++20", # TOUCH AND DIE
                             "/Wall",
                             "/Gw",
                             "/Gy",
                             "/Zc:inline",
                             "/Zo",
                             "/Z7",
                             "/Zp8",
                             "/Zc:inline",
                             args[1]]
    with open(targetFilename, "w") as temp:
        temp.write(json.dumps(j, indent='\t'))

if __name__ == '__main__':
    main(sys.argv)
