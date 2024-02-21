# UE-Assist

A small collection of scripts to assist developing Unreal projects in Windows.

## Setup
1. Clone or download the repo.
2. Add its directory to your path.
3. Enter the appropriate values in `config.ini`.

### Example `config.ini`

Since I still have Unreal 5.2 and installed it via the EGS _my_ `config.ini` is the following:

``` ini
[Settings]
unreal_version: 5.2
unreal_association: 5_2

[Paths]
editor_exe: C:\Program Files\Epic Games\UE_5.2\Engine\Binaries\Win64\UnrealEditor.exe
ubt_exe: C:\Program Files\Epic Games\UE_5.2\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe
build_bat: C:\Program Files\Epic Games\UE_5.2\Engine\Build\BatchFiles\Build.bat
```

## Usage

```ue-assist [options]```

* `-a <uproject file>` Adds batch scripts to an existing project & creates a `.dir-locals.el` file (overwriting any existing one).
* `-p <name> [<directory>]` Creates a project with given name in given directory if directory is not given creates a project in the current directory.  Creates a basic `.gitignore` and prompts you to run `git init .` for version control.
  - `<name>` can only be letters
  - `<directory>` must be empty
* `-c <origin> <target>` Parses origin file for compilation commands and outputs to target.  NOTE: called by `generate.bat` to make `compile_commands.json` for the lsp server.  This gets run automatically by `generate.bat` (don't expect good results if you run it manually).
* `-v` Prints the version & licensing information.
* `-h` Prints usage information.

## LSP Notes

The LSP server only works Microsoft's `clangd`.  You can install it by either downloading (or modifying an existing installation of) Visual Studios _OR_ Visual Studio Build Tools.  After that choose to install individual components and make sure to have both `MSBuild support for LLVM toolset` and `C++ Clang Compiler for Windows` selected for installation.  If you already have another `clangd` living in your path you have to set up each project to use Microsoft's `clangd` instead.  If you're using Emacs `ue-assist.py` creates a `.dir-locals.el` file you can use to set said variable.

### Project Batch Scripts

`ue-assist` creates batch-scripts to assist in IDE-less development on windows.  No debugging options atm, but I still use VS for that :(

* `build.bat` builds the editor.
* `editor.bat` launches the editor.
* `generate.bat` creates `compile_commands.json` so you can use [clangd](https://github.com/clangd/clangd) as your [LSP](https://github.com/microsoft/language-server-protocol) server.  This allows for code-completion, jump-to-definitions, syntax highlighting, linting, etc.  ~~The output `compile_commands.json` works great for source files but is still kind of buggy for header files~~ As of `1.1.0` it works for header files!  Whenever you add, remove, or rename a source or header file you need to run this then restart your LSP (`lsp-workspace-restart` on emacs) for it to pick up the new changes.  Overall, much faster than by creating source & header files in the editor.
  - NOTE: `-noIntelliSense` appears to be bugged :(
  
You should bind them to macros/functions if your text editor allows for it.

#### Why `-vscode` in `generate.bat`?

I know UBT can generate `compile_commands.json` via `-projectFiles -mode=GenerateClangDatabase`, but I tested it with `clangd` and it __did not__ work well (this is for Windows, after all).  I'd much rather use `-mode=GenerateClangDatabase` since it doesn't generate (ultimately) extraneous files, so if you know how to get it working on a Windows machine I'd love the help!
