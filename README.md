# usefulTools
Contains some small (but sometimes really useful) scripts for daily work on programming and handling git.

|filename|usage|
|---|---|
|amIInVirtualenv.py|prints whether the current execution is within a virtualenv (Works with python2 and python3|
|createPdfMakefile|creates a make file for compiling latex files with biber|
|echoGitRootDir|prints the path of the root directory of the git repo currently in|
|findBinariesLibraryOfType|Lists all shared libraries linked to the given binary containing a certain string in any type|
|findLibraryContainingType|Lists all shared libraries recursively in the given directory containing a given string in any type|
|generalUpdate|Executes a complete update and upgrade of the system, removes unneeded packages and cleans (This one is really primitive, but "the small things matter in life")|
|getDirOfThisfile|This is not an executable script but it is quite useful for other scripts when trying to determine where the script containing these lines is located|
|gitadd|A command useful when commiting huge amounts of data or a huge number of files|
|pullAll|Checks all git repos recursively whether they need to be updated and whether they can be. If so then the script asks you whether you want to update|
|pullRebasePush|A single command for pulling, rebasing and pushing your local commits|
|renameFormats|Replaces all files having a given format with the other given format|
