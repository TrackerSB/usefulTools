# usefulTools
Contains some small (but sometimes really useful) scripts for daily work on programming and handling git.

|filename|usage|
|---|---|
|echoGitRootDir|prints the path of the root directory of the git repo currently in|
|findBinariesLibraryOfType|Lists all shared libraries linked to the given binary containing a certain string in any type|
|findLibraryContainingType|Lists all shared libraries recursively in the given directory containing a given string in any type|
|generalUpdate|Executes a complete update and upgrade of the system, removes unneeded packages and cleans (This one is really primitive, but "the small things matter in life")
|getDirOfThisfile|This is not an executable script but it is quite useful for other scripts when trying to determine where the script containing these lines is located|
|pullAll|Checks all git repos recursively whether they need to be updated and whether they can be. If so then the script asks you whether you want to update|
|pullRebasePush|A single command for pulling, rebasing and pushing your local commits|
