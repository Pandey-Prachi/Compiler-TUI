# C-DAC COMPILER TUI (Text User Interface)

The C-DAC Compiler TUI is a Text User Interface for people interested in trying out GCC and LLVM compilers and for those learning about the different optimization passes available in these compilers. 

While working with compilers we realized that identifying the right optimization flags with GCC and LLVM compilers is very tedious. There are a lot of flags/options available with the compilers for optimization and it is very time consuming to explore all the flags and select the appropriate ones. Hence, we came up with the idea of developing a TUI for the compilers. 

The flags are organized into categories to make it easier to find them. The user can select their desired flags, compile and run any C program using those flags and view the output. It is also possible to generate dumps for different stages of compilation like CFG, AST etc. which can be viewed in our in-built editor. We have also given the support for parallel programming using OpenMP along with the option to modify environment variables.





### Features of the C-DAC compiler TUI:
* Multiple compiler support (GCC & LLVM)
* Navigation and selection of program files
* Option for selecting any optimization level (eg. O2, Ofast etc.)
* Options for selecting optimization and transformation flags for compilation
* Provides information for each flag/Options
* Generate dump files
* Easy Compilation and execution
* Set OpenMP environment variables
* Search feature for flags and environment variables
* Displays information about the environment variables that can be set
* View Errors & Warnings
* Built-in editor to modify any program files
* Menu for accessing different types of flags: optimization, dumps, and OpenMP



### Responsive layout of the TUI:


### HOME

The HOME screen allows the user to navigate through folders and select any file easily which we can compile with a click of a mouse or using keyboard shortcuts.

The HOME screen also displays the flags which are well organized into categories and users can select them according to their need or the information provided by the TUI.  The flags can also be searched by pressing the <kbd>Ctrl</kbd> + <kbd>F</kbd> shortcut.

Pressing the <kbd>Ctrl</kbd> + <kbd>X</kbd> shortcut key allows the user to access the menu, which contains options for changing the type of flags displayed and also an option to access the OpenMP environment variables screen.

After compilation is done it displays the output in the terminal, which can be accessed from the compiler screen by pressing <kbd>Ctrl</kbd> + <kbd>W</kbd>.

The TUI currently provides support for GCC and LLVM compilers and we can switch between the two with the key binding <kbd>Ctrl</kbd> + <kbd>T</kbd>.


<!--<p align=center> <img src="https://user-images.githubusercontent.com/131694745/235921178-9bdf32be-0cd5-4e57-84f8-ecd8e5479fbf.png"> </p>-->

![image](https://github.com/Pandey-Prachi/Compiler-TUI/assets/82259448/c88d1498-8955-4b65-b97c-855dac981de5)


Home Screen Menu...


![image](https://github.com/Pandey-Prachi/Compiler-TUI/assets/82259448/dffc8b05-63cb-4d2a-b0b5-d1a6ddf2d6e3)


### ENVIRONMENT VARIABLES

The environment variables screen allows the user to set various environment variables for OpenMP programming. This makes it easier for the user to set the OpenMP environment and allows them to learn about the different variables by looking at the information provided about each of them.


![image](https://github.com/Pandey-Prachi/Compiler-TUI/assets/82259448/21342b44-724c-4d1b-bc18-fd00282a0ed2)


### EDITOR

The purpose of the built-in editor is to make it easier for the user to refer to the warnings and errors while editing the program file. This eliminates the extra steps of exiting the TUI and opening an editor to modify the program file.


![image](https://github.com/Pandey-Prachi/Compiler-TUI/assets/82259448/c36024c3-bbec-4dba-b8c0-60dea40e45db)


## Prerequisites:

  * Python (version 2.x or version 3.x)
  
  * Python Curses library
  
  * [Npyscreen library](https://pypi.org/project/npyscreen/) (included)
  
  * GCC or LLVM compiler
  
  
## Instructions:

  **Step 1:** Download the files
  
  **Step 2:** Run the python script (main.py)


Experiment with GCC and LLVM compilers using our user friendly Compiler TUI 

## Interacting with the TUI:

  * <kbd>F5</kbd>: To Compile and Run
  
  * <kbd>Ctl</kbd>+<kbd>W</kbd> : To view warnings
  
  * <kbd>Ctl</kbd>+<kbd>E</kbd> : To edit the file (Editor)
  
  * <kbd>Ctl</kbd>+<kbd>T</kbd> : To toggle between the compilers
  
  * <kbd>Ctl</kbd>+<kbd>F</kbd> : Flag search
  
  * <kbd>Ctl</kbd>+<kbd>X</kbd> : Open menu
  
  * <kbd>Ctl</kbd>+<kbd>Q</kbd>: To exit the TUI

  Press <kbd>Tab</kbd> and <kbd>Shift</kbd> + <kbd>Tab</kbd> to move between widgets. Use the arrow keys <kbd>&uarr;</kbd> <kbd>&darr;</kbd> <kbd>&larr;</kbd> <kbd>&rarr;</kbd> to move inside widgets. Press <kbd>Space</kbd>, <kbd>Enter</kbd> or the mouse to select items.

