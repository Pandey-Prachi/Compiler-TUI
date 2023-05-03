# C-DAC COMPILER TUI (Text User Interface)

The C-DAC Compiler TUI is a Text User Interface for people interested in trying out GCC and LLVM compilers and for those learning about the different optimization passes available in these compilers. 


While working with compilers we realized that identifying the right optimization flags with GCC and LLVM compilers is very tedious. There are a lot of flags/options available with the compilers for optimization and it is very time consuming to explore all the flags and select the appropriate ones. Hence, we came up with the idea of developing a TUI for the compilers. 


The flags are organized into categories to make it easier to find them. The user can select their desired flags, compile and run any C program using those flags and view the output. It is also possible to generate dumps for different stages of compilation like CFG, AST etc. which can be viewed in our in-built editor. A separate screen is provided for viewing the warnings and errors.
We have also given the option to enable external projects like “POLLY”.




### Features of the C-DAC compiler TUI:
* Multiple compiler support (GCC & LLVM)
* Navigation and selection of program files
* Option for selecting any optimization level (eg. O2, Ofast etc.)
* Options for selecting optimization and transformation flags for compilation
* Provides information for each flag/Options
* Generate dump files
* Easy Compilation and execution
* View Errors & Warnings
* Built-in editor to modify any program files


We have divided the features into 3 modules:


### HOME

The HOME screen allows the user to navigate through folders and select any file easily which we can compile with a click of a mouse or using keyboard shortcuts.

The HOME screen also displays the flags which are well organized into categories and User can select them according to their need or the information provided by the TUI. 

After compilation is done it displays the output in a popup screen.

The TUI currently provides support for GCC and LLVM compilers and we can switch between the two with the key binding Ctrl + T.

<p align=center> <img src="https://user-images.githubusercontent.com/131694745/235921178-9bdf32be-0cd5-4e57-84f8-ecd8e5479fbf.png"> </p>

After compilation...


<p align=center> <img src="https://user-images.githubusercontent.com/131694745/235923208-83f97ba4-727b-4eba-a288-5968c885034d.png"> </p>


### OUTPUT, ERRORS and WARNINGS

If any errors or warnings are generated, the TUI allows the user to view it in our ERRORS and WARNINGS page which can be accessed by pressing Ctrl + W. This page also displays the output.


<p align=center> <img src="https://user-images.githubusercontent.com/131694745/235923447-0707a7ee-056c-4aaa-b211-7a97865b6030.png"> </p>


### EDITOR

The purpose of the built-in editor is to make it easier for the user to refer to the warnings and errors while editing the program file. This eliminates the extra steps of exiting the TUI and opening an editor to modify the program file.


<p align=center> <img src="https://user-images.githubusercontent.com/131694745/235923632-8d3827e8-0526-416a-8d3b-f8956360f83a.png"> </p>




## Prerequisites:

  * Python (version 2.x or version 3.x)
  
  * Python Curses library
  
  * Npyscreen library (included)
  
  * GCC or LLVM compiler
  
  
## Instructions:

  **Step 1:** Download the files
  
  **Step 2:** Run the python script (main.py)


Experiment with GCC and LLVM compilers using our user friendly Compiler TUI 

## Shortcuts:

  * F5: To Compile and Run
  
  * Ctl+w : To view warnings
  
  * Ctl+e : To edit the file (Editor)
  
  * Ctl+t : To toggle between the compilers
  
  * Ctl+q: To exit the TUI
  

