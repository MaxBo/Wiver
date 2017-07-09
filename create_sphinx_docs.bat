
Set CURRENTDIR=%~dp0
Set CURRENTDRIVE==%~d0

cd %CURRENTDIR%wiver

SET SC=%CURRENTDIR%wiver\src\wiver
sphinx-apidoc -f --separate -o %CURRENTDIR%docs_rst\wiver %SC% %SC%\tests 

cd %CURRENTDIR%
%CURRENTDRIVE%

