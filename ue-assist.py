import os
import sys
import getopt
import configparser
import json
import re

usage = """UE-Assist is a small set of scripts to accelerate unreal development on Windows.
NOTE: You have to change config.ini to work on your machine.
NOTE: Add its directory to your path so you can call it from anywhere.
NOTE: Only touch the templates if you KNOW what you're doing.
P.S.: Yeah, I create a .dir-locals.el file by default--I use this.

Usage

  ue-assist [options]

Options
  -a <uproject file>      = Add batch scripts to an existing project.
  -p <name> [<directory>] = Creates a project with given name in given directory
                            if directory is not given creates a project in the
                            current directory.
                            - <name> can only be letters.
                            - <directory> must be empty.
  -c <origin> <target>    = Parses origin file for compilation commands and
                            outputs to target.  This is called by generate.bat
                            to make compile_commands.json for the lsp server.
  -v                      = Prints the version & licensing information.
  -h                      = Prints usage information.
"""

def main(cli_args):
    sDir = os.path.dirname(os.path.realpath(cli_args[0]))
    try:
        opts, args = getopt.getopt(cli_args[1:], 'hvap:c')
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(1)
    for o, a in opts:
        if o == '-c':
            if len(args) != 2:
                usage()
                sys.exit(1)
            else:
                compilationDatabase(sDir, args[0], args[1])
                sys.exit(0)
        elif o == '-h':
            print(usage)
            sys.exit(0)
        elif o == '-v':
            print('ue-assist 1.1.0, licensed WTFPLv2')
            sys.exit(0)
        else:
            config = configparser.ConfigParser()
            configPath = os.path.join(sDir, "config.ini")
            config.read(configPath)
            checkConfig(config, configPath)
            if o == '-a':
                if len(args) != 1:
                    print("Pass a .uproject file as an argument!")
                    sys.exit(1)
                else:
                    augmentProject(sDir, args[0], config)
                    sys.exit(0)
            elif o == '-p':
                if len(a) == 0:
                    print("Enter a project name with of non-zero length!")
                    sys.exit(1)
                elif not a.isalpha():
                    print("Project names can only be alphabetic characters!")
                    sys.exit(1)
                if len(args) == 0:
                    createProject(sDir, a, os.getcwd(), config)
                else:
                    createProject(sDir, a, os.path.realpath(args[0]), config)
                sys.exit(0)
    print("unrecognized command, run 'ue-assist -h' for usage")
    sys.exit(1)

def checkConfig(config, configPath):
    badConfig = False
    if not config['Settings']['unreal_version']:
        print('Set "unreal_version" in config.ini!')
        print('  File "{}", line 2'.format(configPath))
        badConfig = True
    if not config['Settings']['unreal_association']:
        print('Set "unreal_association" in config.ini!')
        print('  File "{}", line 3'.format(configPath))
        badConfig = True
    if not os.path.isfile(config['Paths']['editor_exe']):
        print('Bad path to UnrealEditor.exe in config.ini!')
        print('  File "{}", line 6'.format(configPath))
        badConfig = True
    if not os.path.isfile(config['Paths']['ubt_exe']):
        print('Bad path to UnrealBuildTool.exe in config.ini!')
        print('  File "{}", line 7'.format(configPath))
        badConfig = True
    if badConfig:
        sys.exit(1)

def augmentProject(sDir, uproject, config):
    uPath = os.path.realpath(uproject)
    if not os.path.isfile(uPath):
        print("{} is not a file!".format(uproject))
        sys.exit(1)
    result = re.search(r"^(\w+)\.uproject$", uproject)
    pName = ""
    if not result:
        print("{} uPath is not a Unreal project file!")
        sys.exit(1)
    else:
        pName = result.group(1)
    pPath = os.path.dirname(uPath)
    bPaths = copyBatchfiles(sDir, pPath, pName, config)
    print('Batch files created!')
    dlPath = copyDirLocals(sDir, pPath, bPaths, pName)
    print('.dir-locals.el created!')
    copyTemplate(os.path.join(sDir, "templates\\clangd_flags"), os.path.join(pPath, "clangd_flags"))
    print("clangd_flags added!")
    print("Emacs: set default clangd.exe to Microsoft's in .dir-locals.el")
    print('  File "{}", line 1, for proper LSP integration'.format(dlPath))

def createProject(sDir, pName, pPath, config):
    if not os.path.exists(pPath):
        os.makedirs(pPath)
    elif len(os.listdir(pPath)) > 0:
        print("directory is not empty!  Please give a path to a non-existant or empty directory to create an Unreal project")
        sys.exit(1)
    print("Creating project: {}".format(pName))
    bPaths = copyBatchfiles(sDir, pPath, pName, config)
    print('Batch files created!')
    dlPath = copyDirLocals(sDir, pPath, bPaths, pName)
    print('.dir-locals.el created!')
    copyTemplate(os.path.join(sDir, "templates\\gitignore"), os.path.join(pPath, ".gitignore"))
    print('.gitignore created!')
    copyTemplate(os.path.join(sDir, "templates\\clangd_flags"), os.path.join(pPath, "clangd_flags"))
    print("clagd_flags created!")
    initProject(sDir, pPath, pName, config)
    print('Project created!')
    print("Run 'git init .' for version control")
    print("Emacs: set default clangd.exe to Microsoft's in .dir-locals.el")
    print('  File "{}", line 1, for proper LSP integration'.format(dlPath))


def copyBatchfiles(sDir, pPath, pName, config):
    replaceName = lambda s: s.replace('PROJECT', pName)
    def temp(s):
        s = s.replace("CONFIG_BUILD_BAT", config['Paths']['ubt_exe'])
        s = s.replace("CONFIG_UBT_EXE", config['Paths']['ubt_exe'])
        s = s.replace("CONFIG_UE5EDITOR_EXE", config['Paths']['editor_exe'])
        return s
    rwReplace(os.path.join(sDir, "templates\\batch_vars"), os.path.join(pPath, "batch_vars.bat"), temp)
    generatePath = os.path.join(pPath, 'generate.bat')
    buildPath = os.path.join(pPath, 'build.bat')
    editorPath = os.path.join(pPath, 'editor.bat')
    rwReplace(os.path.join(sDir, "templates\\generate"), generatePath, replaceName)
    rwReplace(os.path.join(sDir, "templates\\build"), buildPath, replaceName)
    rwReplace(os.path.join(sDir, "templates\\editor"), editorPath, replaceName)
    return {
        "generate": generatePath.replace("\\", "/"),
        "build": buildPath.replace("\\", "/"),
        "editor": editorPath.replace("\\", "/")
    }

def copyDirLocals(sDir, pPath, bPaths, pName):
    def temp(s):
        s = s.replace("GENERATE_BAT", bPaths["generate"])
        s = s.replace("BUILD_BAT", bPaths["build"])
        s = s.replace("EDITOR_BAT", bPaths["editor"])
        s = s.replace('PROJECT', pName.upper())
        return s
    dlPath = os.path.join(pPath, ".dir-locals.el")
    rwReplace(os.path.join(sDir, "templates\\dir-locals"), dlPath, temp)
    return dlPath

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
    copyTemplate(os.path.join(sDir, "templates\\Project.header"), os.path.join(module_path, "{}.h".format(pName)))
    rwReplace(os.path.join(sDir, "templates\\GameModeBase.header"), os.path.join(module_path, "{}GameModeBase.h".format(pName)), lambda s: s.replace('PROJECT', pName.upper()))
    rwReplace(os.path.join(sDir, "templates\\GameModeBase.source"), os.path.join(module_path, "{}GameModeBase.cpp".format(pName)), replaceName)

def rwReplace(origin, destination, fn):
    with open(origin, 'r') as f:
        temp = f.read()
    temp = fn(temp)
    with open(destination, 'w') as f:
        f.write(temp)

def copyTemplate(origin, destination):
    with open(origin, 'r') as f:
        temp = f.read()
    with open(destination, 'w') as f:
        f.write(temp)

def compilationDatabase(sDir, vscodeFilename, targetFilename):
    pPath = os.path.dirname(targetFilename)
    flagsFilename = os.path.join(pPath, "clangd_flags")
    if not os.path.isfile(flagsFilename):
        copyTemplate(os.path.join(sDir, "templates\\clangd_flags"), os.path.join(pPath, "clangd_flags"))
    flagArgs = "@" + flagsFilename
    j = json.load(open(vscodeFilename))
    pattern = re.compile(".+?~$") # skip emacs backup files
    for i in range(len(j) - 1, -1, -1):
        src = j[i]["file"]
        if pattern.match(src):
            j.pop(i)
            continue
        args = j[i]["arguments"]
        j[i]["arguments"] = [ args[0], flagArgs, args[1]]
    with open(targetFilename, "w") as temp:
        temp.write(json.dumps(j, indent='\t'))

if __name__ == '__main__':
    main(sys.argv)
